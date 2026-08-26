const std = @import("std");

pub const Allocator: type = std.mem.Allocator;

const print = std.debug.print;

pub const Vector2df: type = extern struct {
    x: f32 = 0.0,
    y: f32 = 0.0,
    pub fn format(self: @This(), writer: *std.Io.Writer) std.Io.Writer.Error!void {
        try writer.print("Vector2df(x={d}, y={d})", .{ self.x, self.y });
    }
};
pub const Vector3df: type = extern struct {
    x: f32 = 0.0,
    y: f32 = 0.0,
    z: f32 = 0.0,
    pub fn format(self: @This(), writer: *std.Io.Writer) std.Io.Writer.Error!void {
        try writer.print("Vector3df(x={d}, y={d}, z={d})", .{ self.x, self.y, self.z });
    }
};
pub const Vector4df: type = extern struct {
    w: f32 = 0.0,
    x: f32 = 0.0,
    y: f32 = 0.0,
    z: f32 = 0.0,
    pub fn format(self: @This(), writer: *std.Io.Writer) std.Io.Writer.Error!void {
        try writer.print("Vector4df(w={d}, x={d}, y={d}, z={d})", .{ self.w, self.x, self.y, self.z });
    }
};

pub const Tripleu16: type = extern struct {
    a: u16 = 0,
    b: u16 = 0,
    c: u16 = 0,
    pub fn format(self: @This(), writer: *std.Io.Writer) std.Io.Writer.Error!void {
        try writer.print("u16({}, {}, {})", .{ self.a, self.b, self.c });
    }
};
pub const Tripleu32: type = extern struct {
    a: u32 = 0,
    b: u32 = 0,
    c: u32 = 0,
    pub fn format(self: @This(), writer: *std.Io.Writer) std.Io.Writer.Error!void {
        try writer.print("u32({}, {}, {})", .{ self.a, self.b, self.c });
    }
};

pub const MaterialRange: type = extern struct {
    ignored: u32 = 0,
    start: u32 = 0,
    stop: u32 = 0,
    name: [16]u8 = .{0} ** 16,
    pub fn format(self: @This(), writer: *std.Io.Writer) std.Io.Writer.Error!void {
        try writer.print("MaterialRef(name={s}, start=0x{x}, stop=0x{x})", .{ std.mem.sliceTo(&self.name, 0), self.start, self.stop });
    }
};

pub const DataReader: type = struct {
    data: []u8,
    pos: u32,
    pub fn read_u8(self: *@This()) u8 {
        const val: u8 = self.data[self.pos];
        self.pos += 1;
        return val;
    }
    pub fn read_u16(self: *@This()) u16 {
        const val: u16 = std.mem.bytesToValue(u16, self.data[self.pos .. self.pos + 2]);
        self.pos += 2;
        return val;
    }
    pub fn read_u32(self: *@This()) u32 {
        const val: u32 = std.mem.bytesToValue(u32, self.data[self.pos .. self.pos + 4]);
        self.pos += 4;
        return val;
    }
    pub fn read_u64(self: *@This()) u64 {
        const val: u64 = std.mem.bytesToValue(u64, self.data[self.pos .. self.pos + 8]);
        self.pos += 8;
        return val;
    }
    pub fn read_f32(self: *@This()) f32 {
        const val: f32 = std.mem.bytesToValue(f32, self.data[self.pos .. self.pos + 4]);
        self.pos += 4;
        return val;
    }
    pub fn read_2dfvec(self: *@This()) Vector2df {
        const val: Vector2df = std.mem.bytesToValue(Vector2df, self.data[self.pos .. self.pos + 8]);
        self.pos += 8;
        return val;
    }
    pub fn read_3dfvec(self: *@This()) Vector3df {
        const val: Vector3df = std.mem.bytesToValue(Vector3df, self.data[self.pos .. self.pos + 12]);
        self.pos += 12;
        return val;
    }
    pub fn read_4dfvec(self: *@This()) Vector4df {
        const val: Vector4df = std.mem.bytesToValue(Vector4df, self.data[self.pos .. self.pos + 16]);
        self.pos += 16;
        return val;
    }
    pub fn read_tripleu16(self: *@This()) Tripleu16 {
        const val: Tripleu16 = std.mem.bytesToValue(Tripleu16, self.data[self.pos .. self.pos + 6]);
        self.pos += 6;
        return val;
    }
    pub fn read_tripleu32(self: *@This()) Tripleu32 {
        const val: Tripleu32 = std.mem.bytesToValue(Tripleu32, self.data[self.pos .. self.pos + 12]);
        self.pos += 12;
        return val;
    }
    pub fn read_material_range(self: *@This()) MaterialRange {
        const val: MaterialRange = std.mem.bytesToValue(MaterialRange, self.data[self.pos .. self.pos + 0x1C]);
        self.pos += 0x1C;
        return val;
    }
    pub fn read_physicssphere(self: *@This()) PhysicsSphere {
        const val: PhysicsSphere = std.mem.bytesToValue(PhysicsSphere, self.data[self.pos .. self.pos + 16]);
        self.pos += 16;
        return val;
    }
};

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
    // Store them as u32 so it will always have enough bits to store them without needing extra logic.
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

const PhysicsSphere: type = extern struct { pos: Vector3df = .{}, size: f32 = 0.0 };

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

const Physics: type = struct { raw_data: []u8 = &.{}, density: f32 = 0.0, spheres: []PhysicsSphere = &.{}, motion_constraints: []MotionConstraint = &.{}, sound: [16]u8 = .{0} ** 16 };

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

pub fn main(init: std.process.Init) !void {
    const cwd: std.Io.Dir = .cwd();

    var dba: std.heap.DebugAllocator(.{}) = .init;
    // defer _ = dba.deinit();
    const allocator: Allocator = dba.allocator();

    const data: []u8 = try cwd.readFileAlloc(init.io, "D:\\Steam Library\\steamapps\\common\\Exanima\\Objlib\\step xaa02 03.rfc", init.gpa, .unlimited);
    defer init.gpa.free(data);

    const mesh = try parse_mesh(allocator, data, false);
    _ = mesh;
}
