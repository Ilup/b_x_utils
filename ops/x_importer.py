import bpy

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

import time

from ..py_modules.rfp import RFP
from ..py_modules.rfc import parse_rfc
from ..py_modules import b_funcs as bf
import os

class ImportXFile(bpy.types.Operator):
    bl_idname = 'exanima.import_x_file'
    bl_label  = 'Import Exanima File'
    bl_options = {'REGISTER','UNDO'}
    filepath: StringProperty()
    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)
    def execute(self, context):
        os.system('cls' if os.name == 'nt' else 'clear')
        start_time = time.perf_counter()
        print(f'Importing exanima file {self.filepath}')
        addon_name = __package__.split('.')[0]
        p = bpy.context.preferences.addons[addon_name].preferences
        file = open(self.filepath, 'rb')
        print(f'Reading the RFP...')
        rfp = RFP.parse(p.exanima_dir)
        scene = context.scene
        print(f'Cleaning collections...')
        for col in scene.collection.children: bf.purge_col(col,True)
        import_settings = {'import_sectors':p.import_sectors,'import_props':p.import_props,'import_items':p.import_items,'import_chars':p.import_chars}
        itemdb_dict = {0x0: rfp.itemdb}
        parse_rfc(rfp = rfp, name = os.path.basename(self.filepath), file = file, size = os.path.getsize(self.filepath), scene = scene, import_settings = import_settings, itemdb_dict = itemdb_dict)
        print(f'Took {time.perf_counter() - start_time} seconds to import...')
        print(f"Finished importing RFC!")
        return {'FINISHED'}

classes = [ImportXFile]

def register():
    for cls in classes: bpy.utils.register_class(cls)

def unregister():
    for cls in classes: bpy.utils.unregister_class(cls)