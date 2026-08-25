import bpy

from .. panels import convenience_funcs as cf

def x_item_contains_object(x_item, target: bpy.types.Object, deep_search: bool = False) -> bool:
    if x_item.container.bool:
        for c_item in x_item.container.items:
            if not c_item.item: continue
            if c_item.item == target: return True
            elif c_item.item.x_item.instance_of == target: return True
            if deep_search and c_item.item and x_item_contains_object(c_item.item.x_item, target, deep_search):
                return True
    if x_item.droptable.bool:
        for p_item in x_item.droptable.items:
            if not p_item.item: continue
            if p_item.item == target: return True
            elif p_item.item.x_item.instance_of == target: return True
            if deep_search and p_item.item and x_item_contains_object(p_item.item.x_item, target, deep_search):
                return True
    return False

def get_holders_of_x_item_in_scene(scene: bpy.types.Scene, t_obj: bpy.types.Object, deep_search: bool = False) -> list[bpy.types.Object]:
    users = []
    for obj in scene.objects:
        if obj.x_item.instance_of == t_obj:                        users.append(obj)
        if x_item_contains_object(obj.x_item, t_obj, deep_search): users.append(obj)
    print(f'Found {len(users)} users of {t_obj}')
    return users

class OBJECT_OT_LocateXItems(bpy.types.Operator):
    bl_idname = 'exanima.locate_x_items'
    bl_label = "Locate X Item Object(s)"
    bl_options = {'REGISTER', 'UNDO'}
    obj_name: bpy.props.StringProperty()
    deep_search: bpy.props.BoolProperty(name = "Deep Search", description = "Search recursively inside containers and droptables", default = False,)

    def draw(self, context):
        self.layout.prop(self, "deep_search")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=250)
    def execute(self, context):
        i_obj = bpy.data.objects.get(self.obj_name) or context.active_object
        obj = cf.get_root_node(i_obj)
        if not obj: 
            self.report({'WARNING'}, f'No object found with the name {self.obj_name}')
            return {'CANCELLED'}
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area_3d = area
                for region in area.regions:
                    if region.type == 'WINDOW':
                        region_3d = region
                        break
                break
        if not area_3d or not region_3d:
            self.report({'WARNING'}, "No 3D Viewport found.")
            return {'CANCELLED'}
        if obj.name in context.scene.objects:
            # bpy.context.view_layer.objects.active = obj
            for o_obj in context.selected_objects: o_obj.select_set(False)
            obj.select_set(True)
            with context.temp_override(area=area_3d, region=region_3d):
                bpy.ops.view3d.view_selected()
        elif scene_users := get_holders_of_x_item_in_scene(context.scene, obj, self.deep_search):
            for o_obj in context.selected_objects: o_obj.select_set(False)
            for u_obj in scene_users: u_obj.select_set(True)
            with context.temp_override(area=area_3d, region=region_3d):
                bpy.ops.view3d.view_selected()
        else:
            self.report({'WARNING'}, f'Object {self.obj_name} is not in the current scene!')
            return {'CANCELLED'}
        return {'FINISHED'}

def draw_thing(layout, x_item) -> None:
    t = x_item.thing
    header = layout.row(align=True)
    icon_style = 'TRIA_DOWN' if not t.collapsed else 'TRIA_RIGHT'
    header.prop(t, "collapsed", text="Thing Class", icon=icon_style, emboss=False)
    if not t.collapsed:
        layout.row().prop(t,'name')
        cf.display_props_on_new_row(layout, t, ['singular_published','version','unused0','unused1'])
        layout.row().prop(t,'parent_id')
        row = layout.row()
        row.prop(t,'parent')
        if t.parent:
            cf.add_op_to_row(row = row, op_idname = 'exanima.edit_x_item',  args = [('obj_name',t.parent.name)], icon = 'PROPERTIES', text = '')
            cf.add_op_to_row(row = row, op_idname = 'exanima.locate_x_items',args = [('obj_name',t.parent.name)], icon = 'VIEWZOOM',   text = '')

def draw_object(layout, x_item) -> None:
    o = x_item.object
    header = layout.row(align=True)
    icon_style = 'TRIA_DOWN' if not o.collapsed else 'TRIA_RIGHT'
    header.prop(o, "collapsed", text="Object Class", icon=icon_style, emboss=False)
    if not o.collapsed:
        layout.row().prop(o,'model_name')
        cf.display_props_on_new_row(layout, o, ['exp','zoom_smooth','unused0','unused1'])
        layout.row().prop(o,'name')
        layout.row().prop(o,'desc')
        cf.display_props_on_new_row(layout, o, ['size','rarity'])
        layout.row().prop(o,'value')
        cf.display_props_on_new_row(layout, o, ['provenance','purpose'])


def draw_sweapon(layout, x_item) -> None:
    w = x_item.sweapon
    header = layout.row(align=True)
    icon_style = 'TRIA_DOWN' if not w.collapsed else 'TRIA_RIGHT'
    header.prop(w, "collapsed", text="Static Weapon Class", icon=icon_style, emboss=False)
    if not w.collapsed:
        layout.row().prop(w,'material_seed')
        cf.display_props_on_new_row(layout, w, ['quality','wear','dirt','variance'])
        layout.row().prop(w,'unused_stats')
        cf.display_props_on_new_row(layout, w, ['rank_points','sound'])
        layout.row().prop(w,'ability')
        row = layout.row()
        row.alignment = 'CENTER'
        row.label(text = f'Sockets')
        box = layout.box()
        for socket in w.sockets:
            cf.display_props_on_new_row(box,socket,['type','usage'])



def draw_pweapon(layout, x_item) -> None:
    w = x_item.pweapon
    header = layout.row(align=True)
    icon_style = 'TRIA_DOWN' if not w.collapsed else 'TRIA_RIGHT'
    header.prop(w, "collapsed", text="Procedural Weapon Class", icon=icon_style, emboss=False)
    if not w.collapsed:
        cf.display_props_on_new_row(layout,w,['grip_type','sword_flags','haft_materials','weapon_flags'])
        cf.display_props_on_new_row(layout,w,['factory_seed','material_seed'])
        cf.display_props_on_new_row(layout,w,['quality','wear','dirt','variance'])
        box = layout.box()
        header = box.row(align=True)
        icon_style = 'TRIA_DOWN' if not w.collapsed_materials else 'TRIA_RIGHT'
        header.prop(w, "collapsed_materials", text="Materials", icon=icon_style, emboss=False)
        if not w.collapsed_materials:
            for mat in w.materials:
                cf.display_props_on_new_row(box,mat,['material','luster','color','theme'])
        cf.display_props_on_new_row(layout,w,['weight','impact','balance','slash','crush','pierce','thrust'])
        cf.display_props_on_new_row(layout,w,['eff_near','eff_mid','eff_end'])
        cf.display_props_on_new_row(layout,w,['flip','f_eff_near','f_eff_far','flip_slash','flip_crush','flip_pierce'])
        cf.display_props_on_new_row(layout,w,['grade','sound','rank_points','statunk7'])
        layout.row().prop(w,'ability')
        box = layout.box()
        header = box.row(align=True)
        icon_style = 'TRIA_DOWN' if not w.collapsed_sockets else 'TRIA_RIGHT'
        header.prop(w, "collapsed_sockets", text="Sockets", icon=icon_style, emboss=False)
        if not w.collapsed_sockets:
            for socket in w.sockets:
                cf.display_props_on_new_row(box,socket,['type','usage'])
        layout.row().prop(w,'components')

def draw_shield(layout, x_item) -> None:
    s = x_item.shield
    header = layout.row(align=True)
    icon_style = 'TRIA_DOWN' if not s.collapsed else 'TRIA_RIGHT'
    header.prop(s, "collapsed", text="Shield Class", icon=icon_style, emboss=False)
    if not s.collapsed:
        cf.display_props_on_new_row(layout,s,['weapon_flags','weight','impact','encumbrance'])
        layout.row().prop(s,'rank_points')    

def draw_torch(layout, x_item) -> None:
    t = x_item.shield
    header = layout.row(align=True)
    icon_style = 'TRIA_DOWN' if not t.collapsed else 'TRIA_RIGHT'
    header.prop(t, "collapsed", text="Torch Class", icon=icon_style, emboss=False)
    if not t.collapsed:
        layout.row().prop(t,'data')

def draw_apparel(layout, x_item) -> None:
    a = x_item.apparel
    header = layout.row(align=True)
    icon_style = 'TRIA_DOWN' if not a.collapsed else 'TRIA_RIGHT'
    header.prop(a, "collapsed", text="Apparel Class", icon=icon_style, emboss=False)
    if not a.collapsed:
        layout.row().prop(a,'model')
        layout.row().prop(a,'usage')
        layout.row().prop(a,'visibility')
        layout.row().prop(a,'coverage')
        cf.display_props_on_new_row(layout,a,['impact','slash','crush','pierce','encumbrance'])
        cf.display_props_on_new_row(layout,a,['av_coverage','sound','bulk'])
        cf.display_props_on_new_row(layout,a,['app_type','app_class','trait','rank_points'])
        layout.row().prop(a,'material_seed')
        cf.display_props_on_new_row(layout,a,['quality','wear','dirt','variance'])
        box = layout.box()
        header = box.row(align=True)
        icon_style = 'TRIA_DOWN' if not a.collapsed_materials else 'TRIA_RIGHT'
        header.prop(a, "collapsed_materials", text="Materials", icon=icon_style, emboss=False)
        if not a.collapsed_materials:
            for mat in a.materials:
                cf.display_props_on_new_row(box,mat,['layer','part','element','design','material','trait','color','theme'])
        layout.row().prop(a,'ability')
        box = layout.box()
        header = box.row(align=True)
        icon_style = 'TRIA_DOWN' if not a.collapsed_sockets else 'TRIA_RIGHT'
        header.prop(a, "collapsed_sockets", text="Sockets", icon=icon_style, emboss=False)
        if not a.collapsed_sockets:
            for socket in a.sockets:
                cf.display_props_on_new_row(box,socket,['type','usage'])
        layout.row().prop(a,'set_uid')

def draw_container(layout, x_item) -> None:
    c = x_item.container
    header = layout.row(align=True)
    icon_style = 'TRIA_DOWN' if not c.collapsed else 'TRIA_RIGHT'
    header.prop(c, "collapsed", text="Container Class", icon=icon_style, emboss=False)
    if not c.collapsed:
        cf.display_props_on_new_row(layout,c,['width','height'])
        row = layout.row()
        row.prop(c,'key')
        if c.key:
            cf.add_op_to_row(row = row, op_idname = 'exanima.edit_x_item',  args = [('obj_name',c.key.name)], icon = 'PROPERTIES', text = '')
            cf.add_op_to_row(row = row, op_idname = 'exanima.locate_x_items',args = [('obj_name',c.key.name)], icon = 'VIEWZOOM',   text = '')
        cf.display_props_on_new_row(layout,c,['capacity,max_size'])
        cf.display_props_on_new_row(layout,c,['unk1','unk2'])
        row = layout.row()
        row.alignment = 'CENTER'
        row.label(text = f'Items')
        box = layout.box()
        for item in c.items:
            row = box.row()
            row.prop(item,'item')
            if obj:= item.item:
                cf.add_op_to_row(row = row, op_idname = 'exanima.edit_x_item',  args = [('obj_name',obj.name)], icon = 'PROPERTIES', text = '')
                cf.add_op_to_row(row = row, op_idname = 'exanima.locate_x_items',args = [('obj_name',obj.name)], icon = 'VIEWZOOM',   text = '')
            cf.display_props_on_row(row,item,['pos_x','pos_y'])
        row = layout.row()
        row.alignment = 'CENTER'
        row.label(text = f'ADD OP TO ADD ENTRIES')

def draw_droptable(layout, x_item) -> None:
    dt = x_item.droptable
    header = layout.row(align=True)
    icon_style = 'TRIA_DOWN' if not dt.collapsed else 'TRIA_RIGHT'
    header.prop(dt, "collapsed", text="Droptable Class", icon=icon_style, emboss=False)
    if not dt.collapsed:
        layout.row().prop(dt,'unk1')
        cf.display_props_on_new_row(layout,dt,['specitem1','specitem2'])
        cf.display_props_on_new_row(layout,dt,['unk2','unk3'])
        row = layout.row()
        row.alignment = 'CENTER'
        row.label(text = f'Possibilities')
        box = layout.box()
        for dtitem in dt.items:
            row = box.row()
            row.prop(dtitem,'item')
            if obj := dtitem.item:
                cf.add_op_to_row(row = row, op_idname = 'exanima.edit_x_item',  args = [('obj_name',obj.name)], icon = 'PROPERTIES', text = '')
                cf.add_op_to_row(row = row, op_idname = 'exanima.locate_x_items',args = [('obj_name',obj.name)], icon = 'VIEWZOOM',   text = '')
            cf.display_props_on_row(row,dtitem,['chance','rarity','min','max','flag','amount','wear_var','dirt_var'])

def draw_map(layout, x_item) -> None:
    m = x_item.map
    header = layout.row(align=True)
    icon_style = 'TRIA_DOWN' if not m.collapsed else 'TRIA_RIGHT'
    header.prop(m, "collapsed", text="Map Class", icon=icon_style, emboss=False)
    if not m.collapsed:
        cf.display_props_on_new_row(layout, m, ['unk1','unk2','unk3','unk4'])
        layout.row().prop(m, 'name')

def draw_zone(layout, x_item) -> None:
    z = x_item.zone
    header = layout.row(align=True)
    icon_style = 'TRIA_DOWN' if not z.collapsed else 'TRIA_RIGHT'
    header.prop(z, "collapsed", text="Zone Class", icon=icon_style, emboss=False)
    if not z.collapsed:
        cf.display_props_on_new_row(layout,z,['size_x','size_y','size_z','unk1'])
        cf.display_props_on_new_row(layout,z,['function','trigger','unk2','unk3'])
        cf.display_props_on_new_row(layout,z,['unk4','target_id'])
        layout.row().prop(z,'code')

def draw_operator(layout, x_item) -> None:
    op = x_item.operator
    header = layout.row(align=True)
    icon_style = 'TRIA_DOWN' if not op.collapsed else 'TRIA_RIGHT'
    header.prop(op, "collapsed", text="Operator Class", icon=icon_style, emboss=False)
    if not op.collapsed:
        cf.display_props_on_new_row(layout,op,['version','type','flag'])
        cf.display_props_on_new_row(layout,op,['val1','val2','val3','val4','val5','val6'])
        if op.version != 0x9:
            cf.display_props_on_new_row(layout,op,['target_1','target_2'])
        else:
            box = layout.box()
            for t in op.targets: 
                row = box.row()
                row.prop(t,'object')
                if t.object:
                    cf.add_op_to_row(row = row, op_idname = 'exanima.edit_x_item',  args = [('obj_name',t.object.name)], icon = 'PROPERTIES', text = '')
                    cf.add_op_to_row(row = row, op_idname = 'exanima.locate_x_items',args = [('obj_name',t.object.name)], icon = 'VIEWZOOM',   text = '')
        layout.row().prop(op,'sound')
        if op.version == 0x9: layout.row().prop(op,'code')

def draw_door(layout, x_item) -> None:
    d = x_item.door
    header = layout.row(align=True)
    icon_style = 'TRIA_DOWN' if not d.collapsed else 'TRIA_RIGHT'
    header.prop(d, "collapsed", text="Door Class", icon=icon_style, emboss=False)
    if not d.collapsed:
        cf.display_props_on_new_row(layout,d,['unk1','unk2','unk3'])
        cf.display_props_on_new_row(layout,d,['lock_when_closed','pop_open','noninteractable'])
        cf.display_props_on_new_row(layout,d,['full_open','full_close','invert_input'])
        row = layout.row()
        row.prop(d,'key')
        if d.key:
            cf.add_op_to_row(row = row, op_idname = 'exanima.edit_x_item',  args = [('obj_name',d.key.name)], icon = 'PROPERTIES', text = '')
            cf.add_op_to_row(row = row, op_idname = 'exanima.locate_x_items',args = [('obj_name',d.key.name)], icon = 'VIEWZOOM',   text = '')
        cf.display_props_on_new_row(layout,d,['unk4','unk5','unk6'])

def verify_is_item(obj: bpy.types.Object) -> bool:
    x_item = obj.x_item
    #this sucks, but whatever.
    if   x_item.thing.bool:     return True
    elif x_item.object.bool:    return True
    elif x_item.sweapon.bool:   return True
    elif x_item.pweapon.bool:   return True
    elif x_item.shield.bool:    return True
    elif x_item.torch.bool:     return True
    elif x_item.apparel.bool:   return True
    elif x_item.container.bool: return True
    elif x_item.droptable.bool: return True
    elif x_item.map.bool:       return True
    elif x_item.zone.bool:      return True
    elif x_item.operator.bool:  return True
    elif x_item.door.bool:      return True
    return False

class OBJECT_OT_edit_x_item(bpy.types.Operator):
    bl_idname = 'exanima.edit_x_item'
    bl_label = "Edit Exanima Item"
    bl_options = {'REGISTER', 'UNDO'}
    obj_name: bpy.props.StringProperty()
    def draw(self, context):
        layout = self.layout
        i_obj = bpy.data.objects.get(self.obj_name) if self.obj_name else context.active_object
        if not i_obj: return
        obj = cf.get_root_node(i_obj)

        x_item = obj.x_item
        row = layout.row()
        row.alignment = 'CENTER'
        row.label(text = f'Inspecting item {i_obj.name}')
        row = layout.row()
        row.alignment = 'CENTER'
        row.prop(i_obj.x_item,'instance_of')
        cf.add_op_to_row(row = row, op_idname = 'exanima.edit_x_item',  args = [('obj_name',obj.name)], icon = 'PROPERTIES', text = '')
        cf.add_op_to_row(row = row, op_idname = 'exanima.locate_x_items',args = [('obj_name',obj.name)], icon = 'VIEWZOOM',   text = '')
        if   x_item.thing.bool:     draw_thing(layout.box(),x_item)
        if   x_item.object.bool:    draw_object(layout.box(),x_item)
        if   x_item.sweapon.bool:   draw_sweapon(layout.box(),x_item) #Only show one of them
        elif x_item.pweapon.bool:   draw_pweapon(layout.box(),x_item)
        if   x_item.shield.bool:    draw_shield(layout.box(),x_item)
        if   x_item.torch.bool:     draw_torch(layout.box(),x_item)
        if   x_item.apparel.bool:   draw_apparel(layout.box(),x_item)
        if   x_item.container.bool: draw_container(layout.box(),x_item)
        if   x_item.droptable.bool: draw_droptable(layout.box(),x_item)
        if   x_item.map.bool:       draw_map(layout.box(),x_item)
        if   x_item.zone.bool:      draw_zone(layout.box(),x_item)
        if   x_item.operator.bool:  draw_operator(layout.box(),x_item)
        if   x_item.door.bool:      draw_door(layout.box(),x_item)
    def execute(self, context):
        return {'FINISHED'}
    def invoke(self, context, event):
        i_obj = bpy.data.objects.get(self.obj_name) if self.obj_name else context.active_object
        if not i_obj: return
        obj = cf.get_root_node(i_obj)
        if is_item := not verify_is_item(obj):
            self.report({'WARNING'}, f"{obj.name} has no item classes enabled! It must not be an item...")
            return {'CANCELLED'}
        return context.window_manager.invoke_popup(self, width=1200)
    
classes = [OBJECT_OT_LocateXItems, OBJECT_OT_edit_x_item]

def locate_x_items_func(self, context):
    self.layout.separator()
    self.layout.operator(OBJECT_OT_LocateXItems.bl_idname, icon='VIEWZOOM')

def edit_x_item_func(self, context):
    self.layout.separator()
    self.layout.operator(OBJECT_OT_edit_x_item.bl_idname, icon='OBJECT_DATA')


def register():
    for cls in classes: bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_object.append(locate_x_items_func)
    bpy.types.VIEW3D_MT_object.append(edit_x_item_func)

def unregister():
    for cls in classes: bpy.utils.unregister_class(cls)
    bpy.types.VIEW3D_MT_object.remove(locate_x_items_func)
    bpy.types.VIEW3D_MT_object.remove(edit_x_item_func)