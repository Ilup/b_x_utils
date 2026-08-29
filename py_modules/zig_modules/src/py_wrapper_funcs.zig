const py = @import("python");
const pyb = @import("py_bindings.zig");
const structs = @import("structs.zig");

pub fn vector3df_to_py(vector: structs.Vector3df) !*py.PyObject {
    const result = try pyb.tuple(3);
    pyb.tupleSetUnchecked(result, 0, try pyb.float(vector.x));
    pyb.tupleSetUnchecked(result, 1, try pyb.float(vector.z));
    pyb.tupleSetUnchecked(result, 2, try pyb.float(vector.y));
    return result;
}

pub fn vector3df_slice_to_python(vectors: []structs.Vector3df) !*py.PyObject {
    const result = try pyb.list(vectors.len);
    for (vectors, 0..) |vertex, i| {
        pyb.listSetUnchecked(result, i, try vector3df_to_py(vertex));
    }
    return result;
}

pub fn vector2df_to_py(vector: structs.Vector2df) !*py.PyObject {
    const result = try pyb.tuple(2);
    pyb.tupleSetUnchecked(result, 0, try pyb.float(vector.x));
    pyb.tupleSetUnchecked(result, 1, try pyb.float(vector.y));
    return result;
}

pub fn fill_py_tuple(tuple: *py.PyObject, items: []const *py.PyObject) void {
    for (items, 0..) |item, i| {
        pyb.tupleSetUnchecked(tuple, i, item);
    }
}
