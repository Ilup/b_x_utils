import bpy
from typing import Any

def get_root_in_hierarchy(obj: bpy.types.Object) -> bpy.types.Object:
    while obj.parent:
        obj = obj.parent
    return obj

def get_root_node(obj: bpy.types.Object) -> bpy.types.Object:
    obj = obj.root_node if obj.root_node else obj
    while obj.x_item.instance_of:
        obj = obj.x_item.instance_of
    return obj

def display_props_on_row(row, data, prop_names: list[str]) -> None:
    for prop_name in prop_names:
        row.prop(data,prop_name)

def display_props_on_new_row(layout, data, prop_names: list[str]) -> None:
    row = layout.row()
    for prop_name in prop_names:
        row.prop(data,prop_name)

def add_op_to_row(row, op_idname: str, args: list[tuple[str,Any]], icon: str | None = None, text: str | None = None) -> None:
    kwargs = {}
    if icon is not None: kwargs["icon"] = icon
    if text is not None: kwargs["text"] = text
    op = row.operator(op_idname, **kwargs)
    for name,val in args:
        setattr(op,name,val)
    return op