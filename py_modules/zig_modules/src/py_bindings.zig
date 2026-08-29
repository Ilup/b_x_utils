const std = @import("std");
const py = @import("python");

pub const OOM = error {OutOfMemory};
pub const OOR = error {OutOfRange};

pub const Object = extern struct {
    ptr: *py.PyObject,
};
pub const TypeObject = extern struct {
    ptr: *py.PyTypeObject,
    pub fn downcast(self: @This(), T: type) T {
        switch (T) {
            Object => {},
            else => @compileError("Unsupported subtype."),
        }
        return .{.ptr = @ptrCast(self.ptr)};
    }
    pub fn fromSpec(spec: *py.PyType_Spec) !@This() {
        const res = py.PyType_FromSpec(spec) orelse return error.Failed;
        return .{.ptr = @ptrCast(res)};
    }
};

pub fn listSet(container: *py.PyObject, item_i: usize, item: *py.PyObject) OOR!void {
    if (py.PyList_SetItem(container, @intCast(item_i), item) != 0) return error.OutOfRange;
}

pub fn listSetUnchecked(container: *py.PyObject, item_i: usize, item: *py.PyObject) void {
    _ = py.PyList_SetItem(container, @intCast(item_i), item);
}

pub fn tupleSet(container: *py.PyObject, item_i: usize, item: *py.PyObject) OOR!void {
    if (py.PyTuple_SetItem(container, @intCast(item_i), item) != 0) return error.OutOfRange;
}

pub fn tupleSetUnchecked(container: *py.PyObject, item_i: usize, item: *py.PyObject) void {
    _ = py.PyTuple_SetItem(container, @intCast(item_i), item);
}

pub fn list(len: usize) OOM!*py.PyObject {
    return py.PyList_New(@intCast(len)) orelse error.OutOfMemory;
}

pub fn tuple(len: usize) OOM!*py.PyObject {
    return py.PyTuple_New(@intCast(len)) orelse error.OutOfMemory;
}

pub fn float(value: f64) OOM!*py.PyObject {
    return py.PyFloat_FromDouble(value) orelse error.OutOfMemory;
}

fn sortedLongLongAndLongByBitwidth(signedness: std.builtin.Signedness) struct {Longest: type, Shortest: type} {
    // Bless C for not defining these types relative to each other. So we must look at the compilation settings via metaprogramming.
    const ll, const l = switch (signedness) {
        .signed => .{c_longlong, c_long},
        .unsigned => .{c_ulonglong, c_ulong},
    };
    return if (@bitSizeOf(ll) > @bitSizeOf(l))
        .{.Longest = ll, .Shortest = l}
    else
        .{.Longest = l, .Shortest = ll};
}
pub fn long(value: anytype) OOM!*py.PyObject {
    const preferFn = comptime @"fn":{
        if (@TypeOf(value) == comptime_int) return long(@as(std.math.IntFittingRange(value, value), value));
        const ll_and_l = sortedLongLongAndLongByBitwidth(@typeInfo(@TypeOf(value)).int.signedness);
        const prefer_type: type = switch (@TypeOf(value)) {
            usize, isize => |T| T,
            else => if (@bitSizeOf(@TypeOf(value)) <= @bitSizeOf(ll_and_l.Shortest)) ll_and_l.Shortest else ll_and_l.Longest,
        };
        
        break :@"fn" switch (prefer_type) {
            usize => py.PyLong_FromSize_t,
            isize => py.PyLong_FromSsize_t,
            c_long => py.PyLong_FromLong,
            c_ulong => py.PyLong_FromUnsignedLong,
            c_longlong => py.PyLong_FromLongLong,
            c_ulonglong => py.PyLong_FromUnsignedLongLong,
            else => unreachable,
        };
    };
    return preferFn(value) orelse error.OutOfMemory;
}