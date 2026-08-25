import bpy

from bpy.props import PointerProperty,BoolProperty,IntProperty,StringProperty

def register():
    bpy.types.Object.root_node = PointerProperty(type = bpy.types.Object)
    bpy.types.Object.node_index = IntProperty()
    bpy.types.Object.is_race_base = BoolProperty()
    bpy.types.Object.tileset = StringProperty()

def unregister():
    del bpy.types.Object.root_node
    del bpy.types.Object.node_index
    del bpy.types.Object.is_race_base