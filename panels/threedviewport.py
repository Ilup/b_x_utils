import bpy,os

from bpy.props import (
    CollectionProperty,
    StringProperty	,
    BoolProperty	,
    EnumProperty	,
    FloatProperty	,
    PointerProperty ,
    IntProperty     ,
    IntVectorProperty,
    FloatVectorProperty,
)


class XUtils_PT_Panel(bpy.types.Panel):
    bl_label = "Exanima Utils"
    bl_idname = "XUtils_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Exanima Utils'
    def draw(self, context):
        addon_name = __package__.split('.')[0]
        if not (addon := context.preferences.addons.get(addon_name)):
            self.layout.label(text="Addon preferences unavailable")
            return
        p = addon.preferences
        layout = self.layout
        layout.row().prop(p, 'import_path')
        row = layout.row()
        row.prop(p,'import_sectors')
        row.prop(p,'import_props')
        row = layout.row()
        row.prop(p,'import_items')
        row.prop(p,'import_chars')
        op = layout.row().operator('exanima.import_x_file')
        op.filepath = p.import_path

class XUtils_DBEntry_Editor_PT_Panel(bpy.types.Panel):
    bl_label = "Database Panel"
    bl_idname = "XUtils_DBEntry_Editor_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Exanima Utils'
    bl_parent_id = "XUtils_PT_Panel"
    def draw(self, context):
        layout = self.layout
        layout.row().operator('exanima.edit_x_item')
        layout.row().operator('exanima.edit_x_char')

class ExanimaBrush(bpy.types.PropertyGroup):
    name: StringProperty()

def get_brush_items(self, context):
    return [(brush.name,brush.name,'') for brush in context.scene.exanima_brushes]

class XUtils_Terrain_PT_Panel(bpy.types.Panel):
    bl_label = "Terrain Panel"
    bl_idname = "XUtils_Terrain_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Exanima Utils'
    bl_parent_id = "XUtils_PT_Panel"
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        box = layout.box()
        box.label(text = 'Painting Keybind is SHIFT + ALT + Leftlick')
        box.row().prop(scene,'active_exanima_brush')
        box.row().prop(scene,'exanima_brush_paint_weight',text = 'Weight')
        box.row().prop(scene,'exanima_brush_paint_radius',text = 'Radius')
        box.row().prop(scene,'exanima_brush_hardness', text = 'Hardness')
        box = layout.box()
        box.label(text = 'Painting Keybind is SHIFT + ALT + Rightclick')
        box.row().prop(scene,'exanima_brush_height', text = 'Height')
        box.row().prop(scene,'exanima_brush_height_vertex_radius',text = 'Radius')
        box.row().prop(scene,'exanima_brush_height_hardness', text = 'Hardness')


classes = [XUtils_PT_Panel,XUtils_DBEntry_Editor_PT_Panel,
           ExanimaBrush, XUtils_Terrain_PT_Panel]

def register():
    for cls in classes: bpy.utils.register_class(cls)
    bpy.types.Scene.exanima_brushes = CollectionProperty(type = ExanimaBrush)
    bpy.types.Scene.active_exanima_brush = EnumProperty(items = get_brush_items)
    bpy.types.Scene.exanima_brush_paint_weight = FloatProperty(default = 0.5, min = 0.0, max = 1.0)
    bpy.types.Scene.exanima_brush_paint_radius = IntProperty(default = 1, min = 1)
    bpy.types.Scene.exanima_brush_hardness = FloatProperty(default = 0.5, min = 0.0, max = 1.0)
    bpy.types.Scene.exanima_brush_height = FloatProperty()
    bpy.types.Scene.exanima_brush_height_vertex_radius = IntProperty(default = 1, min = 1)
    bpy.types.Scene.exanima_brush_height_hardness = FloatProperty(min = 0.0, max = 1.0)

def unregister():
    del bpy.types.Scene.exanima_brushes
    del bpy.types.Scene.active_exanima_brush
    del bpy.types.Scene.exanima_brush_paint_weight
    del bpy.types.Scene.exanima_brush_paint_radius
    del bpy.types.Scene.exanima_brush_hardness
    del bpy.types.Scene.exanima_brush_height
    del bpy.types.Scene.exanima_brush_height_vertex_radius
    del bpy.types.Scene.exanima_brush_height_hardness
    for cls in classes: bpy.utils.unregister_class(cls)