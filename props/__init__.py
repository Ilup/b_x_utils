from . import nodes,items,chars

def register():
    nodes.register()
    items.register()
    chars.register()
    

def unregister():
    nodes.unregister()
    items.unregister()
    chars.unregister()