import bpy,gpu,math,bmesh

from mathutils import Vector
from mathutils.kdtree import KDTree

import time,os

from gpu_extras.batch import batch_for_shader
from bpy_extras import view3d_utils

from bpy.props import StringProperty,FloatProperty

from ..py_modules import b_funcs as bf

#From the blender modal draw template.
def draw_callback_px(context,mouse_path,line_width = 2.0):
    gpu.state.blend_set('ALPHA')
    shader = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
    shader.uniform_float("color", (1.0, 0.0, 0.0, 1.0))
    shader.uniform_float("viewportSize", (context.area.width, context.area.height))
    shader.uniform_float('lineWidth', line_width)
    batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": mouse_path})
    batch.draw(shader)
    gpu.state.blend_set('NONE')

def get_x_y_bbox(obj: bpy.types.Object):
    world_bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return (min(v.x for v in world_bbox), #Min x
            max(v.x for v in world_bbox),
            min(v.y for v in world_bbox), #Min y
            max(v.y for v in world_bbox))

def get_ray_specs(region,rv3d,coord) -> tuple[Vector,Vector]:
    return (view3d_utils.region_2d_to_origin_3d(region,rv3d,coord),
            view3d_utils.region_2d_to_vector_3d(region,rv3d,coord))

def check_raycast_and_add_to_tree(location: tuple[float,float,float], region, rv3d, desgraph, scene, objs_in_kdtree, kdtree_adding_func, func_args) -> None:
    screen_coord = view3d_utils.location_3d_to_region_2d(region,rv3d,location)
    #The point may be behind the view in perspective projection which returns None.
    if screen_coord:
        __, o_location, __, __, o_obj, __ = scene.ray_cast(desgraph,*get_ray_specs(region,rv3d,screen_coord))
        if o_obj and o_obj not in objs_in_kdtree: kdtree_adding_func(*func_args,o_obj)


def check_if_paint_neighbor(bbox_dict, location, obj, vert_distance, region, rv3d, scene, desgraph, kdtree, tree_verts, objs_in_kdtree, kdtree_adding_func, func_args) -> None:
    #step_spacing: float = 20*0x1F/4
    #Check if the edge of the brush will be in another object. This will allow painting across multiple objects allowing brush influences to propagate
    if obj not in bbox_dict:
        min_obj_x,max_obj_x,min_obj_y,max_obj_y = get_x_y_bbox(obj)
        bbox_dict[obj] = min_obj_x,max_obj_x,min_obj_y,max_obj_y
    else: 
        min_obj_x,max_obj_x,min_obj_y,max_obj_y = bbox_dict[obj]
    offset = vert_distance #* i
    xp,xm = location.x + offset, location.x - offset #plus, minus
    yp,ym = location.y + offset, location.y - offset
    if xp > max_obj_x: #+,0. Raycast if any of these are met.
        check_raycast_and_add_to_tree((xp,location.y,location.z),region, rv3d, desgraph, scene, objs_in_kdtree, kdtree_adding_func, func_args)
    if xm < min_obj_x: #-,0
        check_raycast_and_add_to_tree((xm,location.y,location.z),region, rv3d, desgraph, scene, objs_in_kdtree, kdtree_adding_func, func_args)
    if yp > max_obj_y: #0,+
        check_raycast_and_add_to_tree((location.x,yp,location.z),region, rv3d, desgraph, scene, objs_in_kdtree, kdtree_adding_func, func_args)
    if ym < min_obj_y: #0,-
        check_raycast_and_add_to_tree((location.x,ym,location.z),region, rv3d, desgraph, scene, objs_in_kdtree, kdtree_adding_func, func_args)
    #Diagonals
    if xp > max_obj_x and yp > max_obj_y: #+,+
        check_raycast_and_add_to_tree((xp,yp,location.z),region, rv3d, desgraph, scene, objs_in_kdtree, kdtree_adding_func, func_args)
    if xm < min_obj_x and yp > max_obj_y: #-,+
        check_raycast_and_add_to_tree((xm,yp,location.z),region, rv3d, desgraph, scene, objs_in_kdtree, kdtree_adding_func, func_args)
    if xp > max_obj_x and ym < min_obj_y: #+,-
        check_raycast_and_add_to_tree((xp,ym,location.z),region, rv3d, desgraph, scene, objs_in_kdtree, kdtree_adding_func, func_args)
    if xm < min_obj_x and ym < min_obj_y: #-,-
        check_raycast_and_add_to_tree((xm,ym,location.z),region, rv3d, desgraph, scene, objs_in_kdtree, kdtree_adding_func, func_args)

def add_brush_weight_to_kdtree(kdtree: KDTree, tree_verts: list[bpy.types.MeshVertex], objs_in_kdtree: set[bpy.types.Object], attr_name: str, obj: bpy.types.Object) -> None:
    if obj.type != 'MESH': raise Exception(f'Cannot add a non mesh object ({obj.name}) to a kdtree!')
    mesh = obj.data
    attr = mesh.attributes.get(attr_name) or mesh.attributes.new(attr_name, 'FLOAT', 'POINT')
    w_matrix = obj.matrix_world
    index_start = len(tree_verts)
    for vert in mesh.vertices:
        x,y,_ = w_matrix @ vert.co
        kdtree.insert((x,y,0),index_start + vert.index)
        tree_verts.append((attr.data,vert.index))
    kdtree.balance()
    objs_in_kdtree.add(obj)

def paint_brush(op, spacing: float = 5.0) -> None:
    vert_distance = op.vert_distance
    kdtree,objs_in_kdtree,tree_verts = op.kdtree,op.objs_in_kdtree,op.tree_verts
    scene = op.scene
    region,rv3d = op.region,op.rv3d
    desgraph = op.desgraph
    brush_name,weight,hardness = op.brush_name,op.weight,op.hardness
    hard_radius = op.hard_radius
    bbox_dict = op.bbox_dict
    objs = op.objs
    dist = (op.prev_loc - op.curr_loc).length
    steps = max(1, math.ceil(dist / spacing)) if dist > spacing else 1
    for i in range(1, steps + 1):
        coord = op.prev_loc.lerp(op.curr_loc, i / steps)
        _, location, _, _, obj, _ = scene.ray_cast(desgraph,*get_ray_specs(region,rv3d,coord))
        if obj and obj in objs:
            
            check_if_paint_neighbor(bbox_dict, location, obj, vert_distance, region, rv3d, scene, desgraph, kdtree, tree_verts, objs_in_kdtree, add_brush_weight_to_kdtree,
                                    (kdtree, tree_verts, objs_in_kdtree, brush_name))

            if obj not in objs_in_kdtree: add_brush_weight_to_kdtree(kdtree, tree_verts, objs_in_kdtree, brush_name, obj)
            
            x,y,_ = location
            for ___,tree_idx,pos_dist in kdtree.find_range((x,y,0),vert_distance):
                attr_data,vert_idx = tree_verts[tree_idx]
                if   hardness >= 1.0:         influence = 1.0
                elif pos_dist <= hard_radius: influence = 1.0
                else:                         influence = (vert_distance - pos_dist) / (vert_distance - hard_radius)
                old = attr_data[vert_idx].value
                attr_data[vert_idx].value = old + (weight - old) * (influence * hardness)


class EXANIMA_OT_paint_brush_weights(bpy.types.Operator):
    bl_idname = "exanima.paint_brush_weight"
    bl_label = "Paint Terrain Brush Weight"
    bl_options = {'REGISTER','UNDO'}
    def invoke(self, context, event):
        os.system('cls' if os.name == 'nt' else 'clear')
        wm = context.window_manager
        scene = context.scene
        if not scene.active_exanima_brush:
            self.report({'WARNING'}, "No brush name was provided")
            return {'CANCELLED'}
        if context.area.type == 'VIEW_3D':
            self.scene = scene
            self.objs = set(bf.verify_colname_in_scene(scene, 'Terrain').objects)
            self.prev_loc,self.curr_loc = None,Vector((event.mouse_region_x,event.mouse_region_y))
            self.bbox_dict = {}
            self.region,self.rv3d = context.region,context.region_data
            self.desgraph = context.evaluated_depsgraph_get()
            self.kdtree,self.tree_verts,self.objs_in_kdtree = KDTree(sum(len(obj.data.vertices) for obj in self.objs)),[],set()
            self.brush_name,self.weight,self.vert_radius,self.hardness = scene.active_exanima_brush,scene.exanima_brush_paint_weight,scene.exanima_brush_paint_radius,scene.exanima_brush_hardness
            self.vert_distance = self.vert_radius * 20 #20 = Terrain scale default size
            self.hard_radius = self.vert_distance * self.hardness
            # self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, (context,self.mouse_path), 'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}
    def modal(self, context, event):
        #Note: the keybind is set to be left click so the first event's type will never be leftmouse.
        #      It will only see when you release leftmouse
        context.area.tag_redraw()
        if event.type == 'MOUSEMOVE': #Drawing
            self.prev_loc = self.curr_loc
            self.curr_loc = Vector((event.mouse_region_x,event.mouse_region_y))
            paint_brush(self)
        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE': #Letting go of the left click
            # paint_tbrushes_using_brush_name_weight_and_mouse_path(context,self.mouse_path)
            # bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'}
        return {'RUNNING_MODAL'}

def add_obj_heights_to_tree(kdtree: KDTree, tree_verts: list[bpy.types.MeshVertex], objs_in_kdtree: set[bpy.types.Object], obj: bpy.types.Object, *args, **kwargs) -> None:
    if obj.type != 'MESH': raise Exception(f'Cannot add a non mesh object ({obj.name}) to a kdtree!')
    mesh = obj.data
    w_matrix = obj.matrix_world
    index_start = len(tree_verts)
    for vert in mesh.vertices:
        x,y,_ = w_matrix @ vert.co
        kdtree.insert((x,y,0),index_start + vert.index)
        tree_verts.append(vert)
    kdtree.balance()
    objs_in_kdtree.add(obj)

def paint_height(op, spacing = 5.0) -> None:
    vert_distance,height = op.vert_distance, op.height
    kdtree,objs_in_kdtree,tree_verts = op.kdtree,op.objs_in_kdtree,op.tree_verts
    scene,region,rv3d,desgraph = op.scene,op.region,op.rv3d,op.desgraph
    hardness,hard_radius = op.hardness,op.hard_radius
    bbox_dict = op.bbox_dict
    objs = op.objs
    dist = (op.prev_loc - op.curr_loc).length
    steps = max(1, math.ceil(dist / spacing)) if dist > spacing else 1
    for i in range(1, steps + 1):
        coord = op.prev_loc.lerp(op.curr_loc, i / steps)
        _, location, _, _, obj, _ = scene.ray_cast(desgraph,*get_ray_specs(region,rv3d,coord))
        if obj and obj in objs:

            check_if_paint_neighbor(bbox_dict, location, obj, vert_distance, region, rv3d, scene, desgraph, kdtree, tree_verts, objs_in_kdtree, add_obj_heights_to_tree,
                                    (kdtree, tree_verts, objs_in_kdtree))

            if obj not in objs_in_kdtree: add_obj_heights_to_tree(kdtree, tree_verts, objs_in_kdtree, obj)
            
            x,y,_ = location
            for ___,idx,dist in kdtree.find_range((x,y,0),vert_distance):
                if   hardness >= 1.0:     influence = 1.0
                elif dist <= hard_radius: influence = 1.0
                else:                     influence = ((vert_distance - dist) / (vert_distance - hard_radius))
                tree_verts[idx].co.z += height * influence

class EXANIMA_OT_paint_height(bpy.types.Operator):
    bl_idname = "exanima.paint_height"
    bl_label = "Paint Terrain Height"
    bl_options = {'REGISTER','UNDO'}
    def invoke(self, context, event):
        # os.system('cls' if os.name == 'nt' else 'clear')
        if context.area.type == 'VIEW_3D':
            scene = context.scene
            self.scene = scene
            self.objs = set(bf.verify_colname_in_scene(scene, 'Terrain').objects)
            self.prev_loc,self.curr_loc = None,Vector((event.mouse_region_x,event.mouse_region_y))
            self.bbox_dict = {}
            self.kdtree,self.tree_verts,self.objs_in_kdtree = KDTree(sum(len(obj.data.vertices) for obj in self.objs)),[],set()
            self.vert_radius,self.hardness,self.height = scene.exanima_brush_height_vertex_radius,scene.exanima_brush_height_hardness,scene.exanima_brush_height
            self.region,self.rv3d = context.region,context.region_data
            self.desgraph = context.evaluated_depsgraph_get()
            self.vert_distance = self.vert_radius * 20 #20 = Terrain scale default size
            self.hard_radius = self.vert_distance * self.hardness
            # self._handle = #Add a function that draws a ring around the cursor based on the paint radius
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}
    def modal(self, context, event):
        context.area.tag_redraw()
        if event.type == 'MOUSEMOVE': #Drawing
            self.prev_loc = self.curr_loc
            self.curr_loc = Vector((event.mouse_region_x,event.mouse_region_y))
            paint_height(self)
        elif event.type == 'RIGHTMOUSE' and event.value == 'RELEASE': #Letting go of the left click
            # bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'}
        return {'RUNNING_MODAL'}

classes = [EXANIMA_OT_paint_brush_weights,EXANIMA_OT_paint_height]

addon_keymaps = []
def register_keymaps():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if not kc: return
    km = kc.keymaps.new(name="3D View", space_type='VIEW_3D')

    kmi = km.keymap_items.new("exanima.paint_brush_weight", type = 'LEFTMOUSE', value = 'PRESS', alt = True, shift = True)
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new("exanima.paint_height", type = 'RIGHTMOUSE', value = 'PRESS', alt = True, shift = True)
    addon_keymaps.append((km, kmi))

def unregister_keymaps():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

def register():
    for cls in classes: bpy.utils.register_class(cls)
    register_keymaps()

def unregister():
    unregister_keymaps()
    for cls in classes: bpy.utils.unregister_class(cls)

