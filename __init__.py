bl_info = {
	'name'			: 'Blender Exanima Utils',
	'author'		: 'Jango',
	'version'		: (0, 0, 1),
	'blender'		: (5, 2, 0),
	'location'		: 'File > Import/Export',
	'description'	: 'Exanima editing tools',
	'category'		: 'Import-Export',
}

from . import ops,panels,props

import bpy
from bpy.props import StringProperty,BoolProperty

class MyAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__
    exanima_dir: StringProperty(name = 'Exanima Folder', default = r'C:\Program Files (x86)\Steam\steamapps\common\Exanima', subtype = 'FILE_PATH')
    import_path: StringProperty(name = 'Exanima File', default = r'C:\Program Files (x86)\Steam\steamapps\common\Exanima\Resource\exanimac1.rfc', subtype = 'FILE_PATH')
    import_sectors: BoolProperty(name = 'Import Sectors', default = True)
    import_props:   BoolProperty(name = 'Import Props', default = False)
    import_items:   BoolProperty(name = 'Import Items', default = False)
    import_chars:   BoolProperty(name = 'Import Chars', default = False)
    #import_nodes #Expected always to be true.
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "exanima_dir")

def register():
    bpy.utils.register_class(MyAddonPreferences)
    props.register()
    ops.register()
    panels.register()

def unregister():
    bpy.utils.unregister_class(MyAddonPreferences)
    props.unregister()
    ops.unregister()
    panels.unregister()