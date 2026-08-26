const std = @import("std");

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

pub const PhysicsSphere: type = extern struct { pos: Vector3df = .{}, size: f32 = 0.0 };

pub const DataReader: type = struct {
    data: []u8,
    pos: u32,
    pub fn read_u8(self: *@This()) u8 {
        const val: u8 = self.data[self.pos];
        self.pos += 1;
        return val;
    }
    pub fn fill_u8_arr(self: *@This(), dest: []u8) void {
        const data_len = dest.len * @sizeOf(u8);
        @memcpy(std.mem.sliceAsBytes(dest), self.data[self.pos .. self.pos + data_len]);
        self.pos += @intCast(data_len);
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
    pub fn fill_f32_arr(self: *@This(), dest: []f32) void {
        const data_len = dest.len * @sizeOf(f32);
        @memcpy(std.mem.sliceAsBytes(dest), self.data[self.pos .. self.pos + data_len]);
        self.pos += @intCast(data_len);
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
    pub fn read_name(self: *@This()) [16]u8 {
        const val: [16]u8 = std.mem.bytesToValue([16]u8, self.data[self.pos .. self.pos + 16]);
        self.pos += 16;
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
