from . import x_importer, items, chars

def register():
    x_importer.register()
    items.register()
    chars.register()

def unregister():
    x_importer.unregister()
    items.unregister()
    chars.unregister()