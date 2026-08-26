pub const py = @import("python");

const dr_module = @import("data_reader.zig");
const Vector3df = dr_module.Vector3df;
const Vector2df = dr_module.Vector2df;

pub fn vector3df_to_py(vector: Vector3df) ?*py.PyObject {
    const result = py.PyTuple_New(3);
    _ = py.PyTuple_SetItem(result, 0, py.PyFloat_FromDouble(vector.x));
    _ = py.PyTuple_SetItem(result, 1, py.PyFloat_FromDouble(vector.z));
    _ = py.PyTuple_SetItem(result, 2, py.PyFloat_FromDouble(vector.y));
    return result;
}

pub fn vector3df_slice_to_python(vectors: []Vector3df) ?*py.PyObject {
    const result = py.PyList_New(@intCast(vectors.len));
    for (vectors, 0..) |vertex, i| {
        _ = py.PyList_SetItem(result, @intCast(i), vector3df_to_py(vertex));
    }
    return result;
}

pub fn vector2df_to_py(vector: Vector2df) ?*py.PyObject {
    const result = py.PyTuple_New(2);
    _ = py.PyTuple_SetItem(result, 0, py.PyFloat_FromDouble(vector.x));
    _ = py.PyTuple_SetItem(result, 1, py.PyFloat_FromDouble(vector.y));
    return result;
}

pub fn fill_py_tuple(tuple: ?*py.PyObject, items: []const ?*py.PyObject) void {
    for (items, 0..) |item, i| {
        _ = py.PyTuple_SetItem(tuple, @intCast(i), item);
    }
}
