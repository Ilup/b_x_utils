import bpy,bmesh

from mathutils import Matrix

def remove_duplicate_id(string: str) -> str:
    if not string or type(string) != str: raise ValueError('Invalid/empty string provided') 
    id_slice = string[-4:]
    if id_slice[0] == '.' and id_slice[1:].isnumeric(): return string[:-4]
    else: return string

def purge_col(col: bpy.types.Collection, remove_col: bool = True) -> None:
    bpy.data.batch_remove(col.objects)
    if remove_col: bpy.data.collections.remove(col)

def verify_colname_in_scene(scene: bpy.types.Scene, colname: str) -> bpy.types.Collection:
    #Cant use the get method because the names could have duplicate IDs on them.
    for col in scene.collection.children:
        if colname in col.name: return col
    else:
        col = bpy.context.blend_data.collections.new(name = colname)
        scene.collection.children.link(col)
        return col
    
def verify_colname_in_col(parent_col: bpy.types.Collection, colname: str) -> bpy.types.Collection:
    #Cant use the get method because the names could have duplicate IDs on them.
    for col in parent_col.children:
        if colname in col.name: return col
    else:
        col = bpy.context.blend_data.collections.new(name = colname)
        parent_col.children.link(col)
        return col

def create_material(name: str) -> bpy.types.Material:
    return bpy.data.materials.new(name)

def get_material(name: str) -> bpy.types.Material:
    #Dont make ten trillion of the same material if they already exist. Get them and if they dont exist, create them.
    return bpy.data.materials.get(name) or bpy.data.materials.new(name)

def create_mesh(name: str, default_type: str = 'None', default_size: float = 50.0) -> bpy.types.Mesh:
    if default_type == 'None': return bpy.data.meshes.new(name)
    elif default_type in {'CUBE','ICOSPHERE'}:
        mesh,bm = bpy.data.meshes.new(name),bmesh.new()
        if   default_type == 'CUBE':      bmesh.ops.create_cube(bm,size = default_size)
        elif default_type == 'ICOSPHERE': bmesh.ops.create_icosphere(bm, radius = default_size)
        bm.to_mesh(mesh)
        return mesh
    else: raise Exception(f'Tried to make a mesh with default type: {default_type}.')

def get_mesh(name: str, default_type: str = 'None', default_size: float = 50.0) -> bpy.types.Mesh:
    return bpy.data.meshes.get(name) or create_mesh(name, default_type, default_size)

def create_object(name: str, data) -> bpy.types.Object:
    return bpy.data.objects.new(name,data)

def create_empty(name: str, col: bpy.types.Collection | None = None) -> bpy.types.Object:
    if col: 
        obj = create_object(name,None)
        col.objects.link(obj)
        return obj
    else: return create_object(name,None)

def create_light(name: str, type: str = 'POINT') -> bpy.types.Light:
    return bpy.data.lights.new(name,type) 

def create_empty(name: str, col: bpy.types.Collection | None = None) -> bpy.types.Object:
    if col: 
        obj = create_object(name,None)
        col.objects.link(obj)
        return obj
    else: return create_object(name,None)

def create_object(name: str, data) -> bpy.types.Object:
    return bpy.data.objects.new(name,data)

def copy_object(obj: bpy.types.Object, linked: bool = True) -> bpy.types.Object:
    if linked: return obj.copy()
    else:      return create_object(obj.name, obj.data.copy() if obj.data else None)

def copy_objects(objects: list[bpy.types.Object], col: bpy.types.Collection = None, linked: bool = True) -> list[bpy.types.Object]:
    copies,copy_dict = [],{} #Need to keep the original sequence
    for obj in objects:
        copy = copy_object(obj,linked)
        copies.append(copy)
        copy_dict[obj] = copy
        if col: col.objects.link(copy)
        if obj.parent and obj.parent in copy_dict: 
            copy.parent = copy_dict[obj.parent]
    # #Changing the root node of the copies. Important for item metadata
    copy_root = copies[0]
    while copy_root.parent and copy_root.parent in copies: copy_root = copy_root.parent
    for copy in copies:
        if copy is not copy_root: copy.root_node = copy_root
    return copies

def get_root(obj: bpy.types.Object) -> bpy.types.Object:
    while obj.parent:
        obj = obj.parent
    return obj

def get_world_matrix(obj: bpy.types.Object) -> Matrix:
    '''
    Since the rfc importer will need to merge objects before world matrices are evaluated, find them the hard way.
    '''
    matrix = Matrix.Identity(4)
    while obj:
        matrix = obj.matrix_basis @ matrix
        obj = obj.parent
    return matrix

def merge_hierarchy(hierarchy: list[bpy.types.Object], col: bpy.types.Collection | None, purge_original: bool = True) -> bpy.types.Object:
    root = get_root(hierarchy[0])
    dest_obj = copy_object(root)
    if col: col.objects.link(dest_obj)
    target_inv_matrix = root.matrix_basis.inverted()
    mat_dict = {mat:i for i,mat in enumerate(dest_obj.data.materials)}
    bm_target = bmesh.new()
    bm_target.from_mesh(dest_obj.data)
    for obj in hierarchy:
        if not obj or obj is root or obj.type != 'MESH': continue
        old_to_new_mat_idx_dict = {}
        for i, mat in enumerate(obj.data.materials):
            if mat not in mat_dict:
                mat_dict[mat] = len(mat_dict)
                dest_obj.data.materials.append(mat)
            old_to_new_mat_idx_dict[i] = mat_dict[mat]

        bm = bmesh.new()
        bm.from_mesh(obj.data)
        #Local object space -> world space -> dest space
        bm.transform(target_inv_matrix @ get_world_matrix(obj))

        #There isnt a convenient bmesh merging function. Do it the manual way...
        vert_map = {}
        for v in bm.verts:
            vert_map[v] = bm_target.verts.new(v.co)
        for f in bm.faces:
            try: #RFCs can have duplicate faces... for some reason.
                new_face = bm_target.faces.new([vert_map[v] for v in f.verts])
            except:
                continue
            new_face.material_index = old_to_new_mat_idx_dict.get(f.material_index,0)
        bm.free()

    bm_target.to_mesh(dest_obj.data)
    if purge_original: bpy.data.batch_remove(hierarchy)
    return dest_obj
        

# def merge_hierarchy(hierarchy: list[bpy.types.Object], col: bpy.types.Collection | None) -> bpy.types.Object:
#     target = hierarchy[0]
#     mats = []
#     for obj in hierarchy:
#         if obj.data:
#             for mat in obj.data.materials:
#                 if mat not in mats: mats.append(mat)
#     while target.parent:
#         if target.parent in hierarchy:
#             target = target.parent
#     mobj = create_object(target.name, create_mesh('mesh'))
#     mbmesh = bmesh.new() #Merged Bmesh
#     if target.type == 'MESH': mbmesh.from_mesh(target.data)
#     linked_mats = []
#     if target.data:
#         for mat in target.data.materials: 
#             mobj.data.materials.append(mat)
#             linked_mats.append(mat)
#     for i,obj in enumerate(target.children_recursive):
#         if '+F' in obj.name and 'FMA' not in obj.name: continue
#         #Before merging, the meshes-to-merge need to be in the reference frame of the target mesh, not their local frame.
#         real_obj = obj
#         matrix = Matrix()
#         #Keep transforming until the reference frame is the target's frame
#         while obj.parent:
#             if obj.parent in hierarchy:
#                 matrix = obj.matrix_basis @ matrix
#                 obj = obj.parent
#             else: break
#         if real_obj.data:
#             copy = real_obj.data.copy()
#             copy.transform(matrix)
#             #To make sure that materials arent overwritten, do some extra stuff to ensure the mats are separated.
#             #Could do bm.from_mesh() to append the mesh, but this is for making sure the mats ids dont conflict with anything.
#             #This is mainly for making tileset stuffs keep *all* of their materials.
#             for mat in copy.materials:
#                 if mat not in linked_mats: 
#                     mobj.data.materials.append(mat)
#                     linked_mats.append(mat)
#             t_bm = bmesh.new(); t_bm.from_mesh(copy)
#             v_dict = {}
#             for vert in t_bm.verts:
#                 new_vert = mbmesh.verts.new((vert.co))
#                 v_dict[vert] = new_vert
#             mbmesh.verts.ensure_lookup_table()
#             for face in t_bm.faces:
#                 try: 
#                     new_face = mbmesh.faces.new([v_dict[vert] for vert in face.verts])
#                     old_mat = copy.materials[face.material_index]
#                     new_face.material_index = mobj.material_slots.find(old_mat.name)
#                 except:
#                     pass
#         if real_obj.users_collection: real_obj.users_collection[0].objects.unlink(target.children_recursive[i])
#     mbmesh.to_mesh(mobj.data); 
#     if target.users_collection: target.users_collection[0].objects.unlink(target)
#     if col: col.objects.link(mobj)
#     mobj.matrix_local = target.matrix_basis
#     if mats and mobj.data:
#         for mat in mats: mobj.data.materials.append(mat)
#     bpy.data.batch_remove(hierarchy + [obj.data for obj in hierarchy]) #Get rid of the old stuff
#     return mobj