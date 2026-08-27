const std: type = @import("std");

const mp: type = @import("x_mesh.zig");

const c = @import("python");

// fn u32_slice_to_list(u32s: []u32) ?*c.PyObject {
//     const result = c.PyList_New(u32s.len);
//     for (u32s, 0..) |val, i| {
//         c.PyList_SetItem(result, @intCast(i), c.PyLong_FromUnsignedLong(val));
//     }
// }

fn vector3df_to_py(vector: mp.Vector3df) ?*c.PyObject {
    const result = c.PyTuple_New(3);
    _ = c.PyTuple_SetItem(result, 0, c.PyFloat_FromDouble(vector.x));
    _ = c.PyTuple_SetItem(result, 1, c.PyFloat_FromDouble(vector.z));
    _ = c.PyTuple_SetItem(result, 2, c.PyFloat_FromDouble(vector.y));
    return result;
}

fn vector3df_slice_to_python(vectors: []mp.Vector3df) ?*c.PyObject {
    const result = c.PyList_New(@intCast(vectors.len));
    for (vectors, 0..) |vertex, i| {
        _ = c.PyList_SetItem(result, @intCast(i), vector3df_to_py(vertex));
    }
    return result;
}

fn vector2df_to_py(vector: mp.Vector2df) ?*c.PyObject {
    const result = c.PyTuple_New(2);
    _ = c.PyTuple_SetItem(result, 0, c.PyFloat_FromDouble(vector.x));
    _ = c.PyTuple_SetItem(result, 1, c.PyFloat_FromDouble(vector.y));
    return result;
}

fn three_u32s_to_py(val_1: u32, val_2: u32, val_3: u32) ?*c.PyObject {
    const result = c.PyTuple_New(3);
    _ = c.PyTuple_SetItem(result, 0, c.PyLong_FromUnsignedLong(val_1));
    _ = c.PyTuple_SetItem(result, 1, c.PyLong_FromUnsignedLong(val_2));
    _ = c.PyTuple_SetItem(result, 2, c.PyLong_FromUnsignedLong(val_3));
    return result;
}

fn fill_py_tuple(tuple: ?*c.PyObject, items: []const ?*c.PyObject) void {
    for (items, 0..) |item, i| {
        _ = c.PyTuple_SetItem(tuple, @intCast(i), item);
    }
}

fn facechunk_to_py(vertexbundle: mp.VertexBundle, meshmaps: mp.MeshMapBundle, facechunk: mp.FaceChunk, is_prop: bool) struct { face_vert_indices: ?*c.PyObject, loop_uvs: ?*c.PyObject, material_indices: ?*c.PyObject, faceints: ?*c.PyObject, faceflags: ?*c.PyObject } {
    const uverts: []mp.Vector2df = vertexbundle.uverts;
    const edgemap: []u32 = meshmaps.edgemap;
    const uvmap: []u32 = meshmaps.uvmap;
    const faces: []mp.Tripleu32 = facechunk.faces;

    const face_vert_indices_list = c.PyList_New(@intCast(faces.len));
    const loop_uvs_list = c.PyList_New(@intCast(faces.len * 3 * 2)); //for use in bpy.types.Mesh.loops.foreach_set ; Need to hold the uvs for each loop.
    for (faces, 0..) |face, i| {
        _ = c.PyList_SetItem(face_vert_indices_list, @intCast(i), three_u32s_to_py(edgemap[face.c], edgemap[face.b], edgemap[face.a]));
        const base_index = i * 6; //For the uv indexing
        for ([3]u32{ face.c, face.b, face.a }, 0..) |index, j| {
            const uv = uverts[uvmap[index]];
            _ = c.PyList_SetItem(loop_uvs_list, @intCast(base_index + j * 2), c.PyFloat_FromDouble(uv.x));
            _ = c.PyList_SetItem(loop_uvs_list, @intCast(base_index + j * 2 + 1), c.PyFloat_FromDouble(uv.y));
        }
    }
    const material_indices_list = c.PyList_New(@intCast(facechunk.material_indices.len));
    for (facechunk.material_indices, 0..) |mat_i, i| {
        _ = c.PyList_SetItem(material_indices_list, @intCast(i), c.PyLong_FromUnsignedLong(mat_i));
    }

    const faceints_list = c.PyList_New(@intCast(facechunk.ints.len));
    const faceflags_list = c.PyList_New(@intCast(facechunk.flags.len));
    if (!is_prop) {
        for (facechunk.ints, 0..) |fi, i| {
            _ = c.PyList_SetItem(faceints_list, @intCast(i), c.PyLong_FromUnsignedLong(fi));
        }

        for (facechunk.flags, 0..) |ff, i| {
            _ = c.PyList_SetItem(faceflags_list, @intCast(i), c.PyLong_FromUnsignedLong(ff));
        }
    }
    return .{ .face_vert_indices = face_vert_indices_list, .loop_uvs = loop_uvs_list, .material_indices = material_indices_list, .faceints = faceints_list, .faceflags = faceflags_list };
}

fn meshresult_to_py(mr: mp.MeshResult, is_prop: bool) ?*c.PyObject {
    const result = c.PyTuple_New(7); //verts, vert_indices, loop_uvs, faceints, faceflags // DO THIS LATER physics, statics, softbody
    const p_verts = vector3df_slice_to_python(mr.vertexbundle.verts);
    const material_names = c.PyTuple_New(@intCast(mr.meshmaps.materials.len));
    for (mr.meshmaps.materials, 0..) |mat, i| {
        _ = c.PyTuple_SetItem(material_names, @intCast(i), c.PyUnicode_Decode(&mat.name, @intCast(mat.name.len), "cp1252", null));
    }
    const p_fc = facechunk_to_py(mr.vertexbundle, mr.meshmaps, mr.facechunk, is_prop);
    const items: []const ?*c.PyObject = &[_]?*c.PyObject{
        p_verts,
        p_fc.face_vert_indices,
        p_fc.loop_uvs,
        p_fc.material_indices,
        material_names,
        p_fc.faceints,
        p_fc.faceflags,
    };
    fill_py_tuple(result, items);
    return result;
}

//Wrapper for the zig function. Converts py objects to zig objects and vice versa when needed.
export fn parse_mesh(self: ?*c.PyObject, args: ?*c.PyObject) callconv(.c) ?*c.PyObject {
    _ = self;

    // const allocator = std.heap.smp_allocator;

    // var dba: std.heap.DebugAllocator(.{}) = .init;
    // defer _ = dba.deinit();
    // const allocator: mp.Allocator = dba.allocator();

    var arena = std.heap.ArenaAllocator.init(std.heap.c_allocator);
    defer arena.deinit();

    const allocator = arena.allocator();

    var ptr: []u8 = undefined;
    var len: c.Py_ssize_t = undefined;
    var is_prop: bool = undefined;

    if (c.PyArg_ParseTuple(args, "y#p", &ptr, &len, &is_prop) == 0) { //Read the args, check the format, fill in the zig ids with the unpacked result.
        return null; // Python exception already set
    }

    const data: []u8 = ptr[0..@intCast(len)];

    const mesh_result: mp.MeshResult = mp.parse_mesh(allocator, data, is_prop) catch |err| {
        std.debug.print("parse_mesh failed: {}\n", .{err});
        return null;
    };

    return meshresult_to_py(mesh_result, is_prop);
}

var methods = [_]c.PyMethodDef{
    .{
        .ml_name = "parse_mesh",
        .ml_meth = parse_mesh,
        .ml_flags = c.METH_VARARGS,
        .ml_doc = "Parse a RFC mesh",
    },
    .{
        .ml_name = null,
        .ml_meth = null,
        .ml_flags = 0,
        .ml_doc = null,
    },
};

var module = c.PyModuleDef{
    .m_base = .{},
    .m_name = "x_mesh_zig",
    .m_doc = "Zig mesh parser",
    .m_size = -1,
    .m_methods = &methods[0],
};

export fn PyInit_x_mesh_zig() callconv(.c) ?*c.PyObject {
    return c.PyModule_Create(&module);
}
