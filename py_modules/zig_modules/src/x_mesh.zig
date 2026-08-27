const std = @import("std");

// const c = @cImport({
//     @cDefine("PY_SSIZE_T_CLEAN", {});
//     @cInclude("Python.h");
// });

const py_wr = @import("py_wrapper_funcs.zig");
const py = py_wr.py;

const dr_m = @import("data_reader.zig");
const Vector3df = dr_m.Vector3df;
const Vector2df = dr_m.Vector2df;
const DataReader = dr_m.DataReader;
const MaterialRange = dr_m.MaterialRange;
const Tripleu32 = dr_m.Tripleu32;
const Tripleu16 = dr_m.Tripleu16;
const PhysicsSphere = dr_m.PhysicsSphere;

pub const Allocator: type = std.mem.Allocator;

const print = std.debug.print;

pub const ParserError = error{ NotImplemented, UnknownSignature, UnknownVertexType, UnsupportedBitwidth, UnknownMapType, UnknownFaceChunk, UnknownMeshChunk, UnknownPhysicsChunk };

pub const VertexBundle = struct { verts: []Vector3df = &.{}, uverts: []Vector2df = &.{} };

pub fn read_verts(dr: *DataReader, allocator: Allocator) !VertexBundle {
    var vb: VertexBundle = .{};
    for (0..dr.read_u32() + 1) |_| {
        const vstart: u32 = dr.pos;
        const vflag: u32 = dr.read_u32();
        const vtype: u32 = dr.read_u32();
        const verts_n: u32 = dr.read_u32() + 1;
        // print("Reading vertex type 0x{x} @ 0x{x}\n", .{ vtype, vstart });
        _ = vflag; //unused. dunno what it's for.
        switch (vtype & 0xFF0000) {
            0xF30000 => {
                vb.verts = try allocator.alloc(Vector3df, verts_n);
                for (vb.verts) |*vert| {
                    vert.* = dr.read_3dfvec();
                }
            },
            0xF20000 => {
                vb.uverts = try allocator.alloc(Vector2df, verts_n);
                for (vb.uverts) |*uvert| {
                    uvert.* = dr.read_2dfvec();
                }
            },
            0xB40000 => {
                dr.pos += 4 * verts_n; //vert colors. unused?
            },
            0xA40000 => {
                dr.pos += verts_n * 32; //bone weights. unused?
            },
            else => {
                print("Found an unknown vertex type 0x{x} starting @ 0x{x}\n", .{ vtype, vstart });
                return error.UnknownVertexType;
            },
        }
    }
    // print("Finished reading verts @ 0x{x}\n", .{dr.pos});
    // print("First Vertex: {f}\n", .{vb.verts[0]});
    // print("First UVertex: {f}\n", .{vb.uverts[0]});
    return vb;
}

pub const MeshMapBundle = struct {
    cmpverts: u32 = 0,
    bitwidth: u8 = 16,
    materials: []MaterialRange = &.{},
    edgemap: []u32 = &.{},
    uvmap: []u32 = &.{},
};

pub fn read_map(allocator: Allocator, bitwidth: u8, cmpverts: u32, dr: *DataReader) ![]u32 {
    // For reading the vertexmaps to be used in the facemap.
    // Store them as u32 so it will always have enough bits to store them without needing extra logipy.
    const result: []u32 = try allocator.alloc(u32, cmpverts);
    switch (bitwidth) {
        16 => {
            for (0..cmpverts) |i| {
                result[i] = dr.read_u16();
            }
        },
        32 => {
            for (0..cmpverts) |i| {
                result[i] = dr.read_u32();
            }
        },
        else => {
            return error.UnsupportedBitwidth;
        },
    }
    return result;
}

pub fn read_meshmaps(dr: *DataReader, allocator: Allocator) !MeshMapBundle {
    // Make sure it's reading the maps.
    const maps_sig: u32 = dr.read_u32();
    const maps_length: u32 = dr.read_u32();
    _ = maps_length;
    if (maps_sig != 0x3DC0) {
        return error.UnknownSignature;
    }

    var meshmap: MeshMapBundle = .{};

    dr.pos += 4; //null, unused?
    meshmap.cmpverts = dr.read_u32() + 1;
    meshmap.materials = try allocator.alloc(MaterialRange, dr.read_u32() + 1);
    for (meshmap.materials) |*mat| {
        mat.* = dr.read_material_range();
        // print("{f}\n", .{mat});
    }

    //The values in the maps are either 16bits or 32bits based on how many cmpverts there are.
    if (meshmap.cmpverts > 0xFFFF) {
        meshmap.bitwidth = 32;
    } else {
        meshmap.bitwidth = 16;
    }

    // print("Reading edgemaps @ 0x{x}\n", .{dr.pos});
    for (0..dr.read_u32() + 1) |_| {
        const vmflag: u32 = dr.read_u32();
        switch (vmflag & 0xFF) {
            0x1 => {
                meshmap.edgemap = try read_map(allocator, meshmap.bitwidth, meshmap.cmpverts, dr);
            },
            0x10 => {
                meshmap.uvmap = try read_map(allocator, meshmap.bitwidth, meshmap.cmpverts, dr);
            },
            0x2 => {
                dr.pos += meshmap.bitwidth / 8 * meshmap.cmpverts; //Unknown map
            },
            else => {
                return error.UnknownMapType;
            },
        }
    }
    // const edgemap = meshmap.edgemap;
    // const uvmap = meshmap.uvmap;
    // print("First three edgemap values: 0x{x}, 0x{x}, 0x{x}\n", .{ edgemap[0], edgemap[1], edgemap[2] });
    // print("First three uvmap values: 0x{x}, 0x{x}, 0x{x}\n", .{ uvmap[0], uvmap[1], uvmap[2] });

    return meshmap;
}

pub const FaceChunk: type = struct {
    faces_n: u32 = 0,
    faces: []Tripleu32 = &.{},
    material_indices: []u8 = &.{},
    ints: []u8 = &.{},
    flags: []u32 = &.{},
};

pub fn read_faces(dr: *DataReader, meshmaps: MeshMapBundle, allocator: Allocator, length: u32, is_prop: bool) !FaceChunk {
    const start: u32 = dr.pos;
    dr.pos += 4; //null
    var facechunk: FaceChunk = .{};
    facechunk.faces_n = dr.read_u32() + 1;
    facechunk.faces = try allocator.alloc(Tripleu32, facechunk.faces_n);
    // print("Reading faces indices @ 0x{x}\n", .{dr.pos});
    for (facechunk.faces) |*face| {
        switch (meshmaps.bitwidth) {
            16 => {
                const indices: Tripleu16 = dr.read_tripleu16();
                face.* = .{
                    .a = indices.a,
                    .b = indices.b,
                    .c = indices.c,
                };
            },
            32 => {
                face.* = dr.read_tripleu32();
            },
            else => {
                return error.UnsupportedBitwidth;
            },
        }
    }
    // print("Reading material reminders @ 0x{x}\n", .{dr.pos});
    facechunk.material_indices = try allocator.alloc(u8, facechunk.faces_n);
    for (0..meshmaps.materials.len) |i| { //Material Definitions.
        for (dr.read_u32()..dr.read_u32() + 1) |j| { //start, stop.
            facechunk.material_indices[j] = @intCast(i);
        }
    }
    if (!is_prop) {
        // print("Finished reading faces @ 0x{x}\n", .{dr.pos});
        while (dr.pos - start < length) {
            // const chunk_start: u32 = dr.pos;
            const chunktag: u32 = dr.read_u32();
            const chunklength: u32 = dr.read_u32();
            // print("Reading face chunk 0x{x} @ 0x{x}\n", .{ chunktag, chunk_start });
            _ = chunklength;
            switch (chunktag & 0xFF0F) {
                0x3D02 => {
                    facechunk.ints = try allocator.alloc(u8, facechunk.faces_n);
                    for (facechunk.ints) |*val| {
                        val.* = dr.read_u8();
                    }
                },
                0x3D03 => {
                    facechunk.flags = try allocator.alloc(u32, facechunk.faces_n);
                    for (facechunk.flags) |*val| {
                        val.* = dr.read_u32();
                    }
                },
                else => {
                    return error.UnknownFaceChunk;
                },
            }
        }
    } else {
        dr.pos = start + length;
    }

    // print("First Face Map Indices: {f}\n", .{facechunk.faces[0]});
    return facechunk;
}

const MotionConstraint: type = extern struct { type: u32 = 0, v1: Vector3df = .{}, v2: Vector3df = .{}, radius: f32 = 0.0, stiffness: f32 = 0.0, damping: f32 = 0.0, v3: Vector3df = .{} };

pub fn read_constraint(dr: *DataReader) MotionConstraint {
    var constraint: MotionConstraint = .{};
    constraint.type = dr.read_u32();
    constraint.v1 = dr.read_3dfvec();
    constraint.v2 = dr.read_3dfvec();
    constraint.radius = dr.read_f32();
    constraint.stiffness = dr.read_f32();
    constraint.damping = dr.read_f32();
    if (constraint.type & 4 != 0) {
        constraint.v3 = dr.read_3dfvec();
    }
    return constraint;
}

const Physics: type = struct { raw_data: []u8 = &.{}, density: f32 = 0.0, spheres: []PhysicsSphere = &.{}, motion_constraints: []MotionConstraint = &.{}, sound: [16]u8 = @splat(0) };

pub fn read_physics(dr: *DataReader, allocator: Allocator, length: u32, is_prop: bool) !Physics {
    const start: u32 = dr.pos;
    // print("Reading physics @ 0x{x}\n", .{start - 8}); //Where the signature is at.
    var physics: Physics = .{};
    if (!is_prop) {
        physics.raw_data = dr.data[dr.pos .. dr.pos + length];
        const unk_int: u32 = dr.read_u32();
        _ = unk_int;
        physics.density = dr.read_f32();
        dr.pos += 0x54; //Mostly unused data. Useless for the parser.
        while (dr.pos - start < length) {
            const chunktag: u32 = dr.read_u32();
            const chunklength: u32 = dr.read_u32();
            _ = chunklength;
            switch (chunktag) {
                0xCD00 => { //Collision
                    dr.pos += 4; //null
                    physics.spheres = try allocator.alloc(PhysicsSphere, dr.read_u32());
                    for (physics.spheres) |*sphere| {
                        sphere.* = dr.read_physicssphere();
                    }
                },
                0xDDB0 => { //Constraints
                    physics.motion_constraints = try allocator.alloc(MotionConstraint, dr.read_u32());
                    for (physics.motion_constraints) |*constraint| {
                        constraint.* = read_constraint(dr);
                    }
                },
                0xDDB3 => { //Sound
                    return error.NotImplemented;
                },
                else => {
                    return error.UnknownPhysicsChunk;
                },
            }
        }
    } else {
        dr.pos += length;
    }
    return physics;
}

const Statics: type = struct { raw_data: []u8 = &.{}, size: u32 = 0, spheres: []Vector3df = &.{} };

pub fn read_statics(dr: *DataReader, allocator: Allocator, chunktag: u32, length: u32, is_prop: bool) !Statics {
    const start: u32 = dr.pos;
    var statics: Statics = .{};
    if (!is_prop) {
        statics.raw_data = dr.data[dr.pos .. dr.pos + length];
        if (chunktag == 0x3D0CEC04) {
            dr.pos += 4; //Null
            statics.spheres = try allocator.alloc(Vector3df, dr.read_u32());
            statics.size = dr.read_u32();
        } else {
            statics.size = dr.read_u32();
            statics.spheres = try allocator.alloc(Vector3df, dr.read_u32());
        }
    }
    dr.pos = start + length; //Since the spheres will be recreated by the exporter dont bother parsing it.
    return statics;
}

const SoftBody: type = struct { data: []u8 = &.{} };

pub fn read_softbody(dr: *DataReader, length: u32) !SoftBody {
    const sb: SoftBody = .{ .data = dr.data[dr.pos .. dr.pos + length] };
    dr.pos += length;
    return sb;
}

pub const MeshResult: type = struct { vertexbundle: VertexBundle, meshmaps: MeshMapBundle, facechunk: FaceChunk, physics: Physics, statics: Statics, softbody: SoftBody };

pub fn parse_mesh(allocator: Allocator, data: []u8, is_prop: bool) !MeshResult {
    var dr: DataReader = .{ .data = data, .pos = 0 };
    dr.pos += 4; //geomflag

    const vertexbundle: VertexBundle = try read_verts(&dr, allocator);

    const meshmaps: MeshMapBundle = try read_meshmaps(&dr, allocator);

    var facechunk: FaceChunk = undefined;
    var physics: Physics = undefined;
    var statics: Statics = undefined;
    var softbody: SoftBody = undefined;
    while (dr.pos < dr.data.len) {
        const chunktag: u32 = dr.read_u32();
        const chunklength: u32 = dr.read_u32();
        switch (chunktag & 0xFFFFFF00) {
            0x3D00 => { //Faces
                facechunk = try read_faces(&dr, meshmaps, allocator, chunklength, is_prop);
            },
            0x3DD0B000 => { //Physics
                physics = try read_physics(&dr, allocator, chunklength, is_prop);
            },
            0x3D0CEC00 => { //Statics
                statics = try read_statics(&dr, allocator, chunktag, chunklength, is_prop);
            },
            0x3DD0C000 => { //Softbody
                softbody = try read_softbody(&dr, chunklength);
            },
            else => {
                return error.UnknownMeshChunk;
            },
        }
    }
    return MeshResult{ .vertexbundle = vertexbundle, .meshmaps = meshmaps, .facechunk = facechunk, .physics = physics, .statics = statics, .softbody = softbody };
}

fn facechunk_to_py(vertexbundle: VertexBundle, meshmaps: MeshMapBundle, facechunk: FaceChunk, is_prop: bool) struct { face_vert_indices: ?*py.PyObject, loop_uvs: ?*py.PyObject, material_indices: ?*py.PyObject, faceints: ?*py.PyObject, faceflags: ?*py.PyObject } {
    const uverts: []Vector2df = vertexbundle.uverts;
    const edgemap: []u32 = meshmaps.edgemap;
    const uvmap: []u32 = meshmaps.uvmap;
    const faces: []Tripleu32 = facechunk.faces;

    const face_vert_indices_list = py.PyList_New(@intCast(faces.len));
    const loop_uvs_list = py.PyList_New(@intCast(faces.len * 3 * 2)); //for use in bpy.types.Mesh.loops.foreach_set ; Need to hold the uvs for each loop.
    for (faces, 0..) |face, i| {
        const tuple = py.PyTuple_New(3);
        _ = py.PyTuple_SetItem(tuple, 0, py.PyLong_FromUnsignedLong(edgemap[face.c]));
        _ = py.PyTuple_SetItem(tuple, 1, py.PyLong_FromUnsignedLong(edgemap[face.b]));
        _ = py.PyTuple_SetItem(tuple, 2, py.PyLong_FromUnsignedLong(edgemap[face.a]));
        _ = py.PyList_SetItem(face_vert_indices_list, @intCast(i), tuple);
        const base_index = i * 6; //For the uv indexing
        for ([3]u32{ face.c, face.b, face.a }, 0..) |index, j| {
            const uv = uverts[uvmap[index]];
            _ = py.PyList_SetItem(loop_uvs_list, @intCast(base_index + j * 2), py.PyFloat_FromDouble(uv.x));
            _ = py.PyList_SetItem(loop_uvs_list, @intCast(base_index + j * 2 + 1), py.PyFloat_FromDouble(uv.y));
        }
    }
    const material_indices_list = py.PyList_New(@intCast(facechunk.material_indices.len));
    for (facechunk.material_indices, 0..) |mat_i, i| {
        _ = py.PyList_SetItem(material_indices_list, @intCast(i), py.PyLong_FromUnsignedLong(mat_i));
    }

    const faceints_list = py.PyList_New(@intCast(facechunk.ints.len));
    const faceflags_list = py.PyList_New(@intCast(facechunk.flags.len));
    if (!is_prop) {
        for (facechunk.ints, 0..) |fi, i| {
            _ = py.PyList_SetItem(faceints_list, @intCast(i), py.PyLong_FromUnsignedLong(fi));
        }

        for (facechunk.flags, 0..) |ff, i| {
            _ = py.PyList_SetItem(faceflags_list, @intCast(i), py.PyLong_FromUnsignedLong(ff));
        }
    }
    return .{ .face_vert_indices = face_vert_indices_list, .loop_uvs = loop_uvs_list, .material_indices = material_indices_list, .faceints = faceints_list, .faceflags = faceflags_list };
}

fn meshresult_to_py(mr: MeshResult, is_prop: bool) ?*py.PyObject {
    const result = py.PyTuple_New(7); //verts, vert_indices, loop_uvs, faceints, faceflags // DO THIS LATER physics, statics, softbody
    const p_verts = py_wr.vector3df_slice_to_python(mr.vertexbundle.verts);
    const material_names = py.PyTuple_New(@intCast(mr.meshmaps.materials.len));
    for (mr.meshmaps.materials, 0..) |mat, i| {
        _ = py.PyTuple_SetItem(material_names, @intCast(i), py.PyUnicode_Decode(&mat.name, @intCast(mat.name.len), "cp1252", null));
    }
    const p_fc = facechunk_to_py(mr.vertexbundle, mr.meshmaps, mr.facechunk, is_prop);
    const items: []const ?*py.PyObject = &[_]?*py.PyObject{
        p_verts,
        p_fc.face_vert_indices,
        p_fc.loop_uvs,
        p_fc.material_indices,
        material_names,
        p_fc.faceints,
        p_fc.faceflags,
    };
    py_wr.fill_py_tuple(result, items);
    return result;
}

//Wrapper for the zig function. Converts py objects to zig objects and vice versa when needed.
export fn parse_mesh_py(self: ?*py.PyObject, args: ?*py.PyObject) callconv(.c) ?*py.PyObject {
    _ = self;

    // const allocator = std.heap.smp_allocator;

    // var dba: std.heap.DebugAllocator(.{}) = .init;
    // defer _ = dba.deinit();
    // const allocator: mp.Allocator = dba.allocator();

    var arena = std.heap.ArenaAllocator.init(std.heap.c_allocator);
    defer arena.deinit();

    const allocator = arena.allocator();

    var ptr: [*]u8 = undefined;
    var len: py.Py_ssize_t = undefined;
    var is_prop: bool = undefined;

    if (py.PyArg_ParseTuple(args, "y#p", &ptr, &len, &is_prop) == 0) { //Read the args, check the format, fill in the zig ids with the unpacked result.
        return null; // Python exception already set
    }

    const data: []u8 = ptr[0..@intCast(len)];

    const mesh_result: MeshResult = parse_mesh(allocator, data, is_prop) catch |err| {
        std.debug.print("parse_mesh failed: {}\n", .{err});
        return null;
    };

    return meshresult_to_py(mesh_result, is_prop);
}

var methods = [_]py.PyMethodDef{
    .{
        .ml_name = "parse_mesh",
        .ml_meth = parse_mesh_py,
        .ml_flags = py.METH_VARARGS,
        .ml_doc = "Parse a RFC mesh",
    },
    .{
        .ml_name = null,
        .ml_meth = null,
        .ml_flags = 0,
        .ml_doc = null,
    },
};

var module = py.PyModuleDef{
    .m_base = .{},
    .m_name = "x_mesh_zig",
    .m_doc = "Zig mesh parser",
    .m_size = -1,
    .m_methods = &methods[0],
};

export fn PyInit_x_mesh_zig() callconv(.c) ?*py.PyObject {
    return py.PyModule_Create(&module);
}

// pub fn main(init: std.process.Init) !void {
//     const cwd: std.Io.Dir = .cwd();

//     var dba: std.heap.DebugAllocator(.{}) = .init;
//     // defer _ = dba.deinit();
//     const allocator: Allocator = dba.allocator();

//     const data: []u8 = try cwd.readFileAlloc(init.io, "D:\\Steam Library\\steamapps\\common\\Exanima\\Objlib\\step xaa02 03.rfc", init.gpa, .unlimited);
//     defer init.gpa.free(data);

//     const mesh = try parse_mesh(allocator, data, false);
//     _ = mesh;
// }
