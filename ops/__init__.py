from . import x_importer, items, chars, terrain

def register():
    x_importer.register()
    items.register()
    chars.register()
    terrain.register()

def unregister():
    x_importer.unregister()
    items.unregister()
    chars.unregister()
    terrain.unregister()