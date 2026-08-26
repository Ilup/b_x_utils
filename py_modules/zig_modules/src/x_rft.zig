const std: type = @import("std");

const py_wr = @import("py_wrapper_funcs.zig");
const py = py_wr.py;

pub const Allocator: type = std.mem.Allocator;

const dr_module = @import("data_reader.zig");
const DataReader: type = dr_module.DataReader;
const Vector3df = dr_module.Vector3df;

const print = std.debug.print;

pub const TerrainError: type = error{ UnknownTTileChunk, UnknownTerrainBlock, InvalidTerrain, SectorOutOfBounds, TerrainTileNotFound };

const TSECTOR_SIZE = sector_width * sector_width;

const BrushSector: type = struct { name: [16]u8 = [_]u8{0} ** 16, map: [TSECTOR_SIZE]u8 = [_]u8{0} ** (TSECTOR_SIZE) };

const sector_face_amount = (sector_width - 1) * (sector_width - 1);
const TerrainSector: type = struct {
    pos_x: u32 = 0,
    pos_y: u32 = 0,
    scale: f32 = 20.0,
    heightmap: [TSECTOR_SIZE]f32 = [_]f32{0} ** (TSECTOR_SIZE),
    brushes: []BrushSector = &.{},
    //holes
    pub fn format(self: @This(), writer: *std.Io.Writer) std.Io.Writer.Error!void {
        try writer.print("TerrainSector(pos_x=0x{x}, pos_y=0x{x}, scale={}, min_height={}, max_height={}, brushes_n=0x{x})\n", .{ self.pos_x, self.pos_y, self.scale, std.mem.min(f32, &self.heightmap), std.mem.max(f32, &self.heightmap), self.brushes.len });
    }
    pub fn heightmap_to_positions_py(self: @This()) ?*py.PyObject {
        const pos_offset = -self.scale * (sector_width - 1) / 2;
        const vectors_list = py.PyList_New(TSECTOR_SIZE);
        const vertical_scaling = self.scale * 0.1;
        for (0..sector_width) |y| {
            const y_pos = @as(f32, @floatFromInt(y)) * self.scale + pos_offset;
            for (0..sector_width) |x| {
                const tuple = py.PyTuple_New(3);
                _ = py.PyTuple_SetItem(tuple, 0, py.PyFloat_FromDouble(@as(f32, @floatFromInt(x)) * self.scale + pos_offset));
                _ = py.PyTuple_SetItem(tuple, 1, py.PyFloat_FromDouble(y_pos));
                _ = py.PyTuple_SetItem(tuple, 2, py.PyFloat_FromDouble(self.heightmap[y * sector_width + x] * vertical_scaling));
                _ = py.PyList_SetItem(vectors_list, @intCast(y * sector_width + x), tuple);
            }
        }
        return vectors_list;
    }
    pub fn generate_face_indices(self: @This()) ?*py.PyObject {
        _ = self;
        const face_width = sector_width - 1;
        const faces_list = py.PyList_New(face_width * face_width);
        for (0..face_width) |y| {
            for (0..face_width) |x| {
                const vertex: u32 = @intCast(y * sector_width + x);
                const tuple = py.PyTuple_New(4);
                _ = py.PyTuple_SetItem(tuple, 0, py.PyLong_FromUnsignedLong(vertex));
                _ = py.PyTuple_SetItem(tuple, 1, py.PyLong_FromUnsignedLong(vertex + 1));
                _ = py.PyTuple_SetItem(tuple, 2, py.PyLong_FromUnsignedLong(vertex + sector_width + 1));
                _ = py.PyTuple_SetItem(tuple, 3, py.PyLong_FromUnsignedLong(vertex + sector_width));
                _ = py.PyList_SetItem(faces_list, @intCast((y * face_width + x)), tuple);
            }
        }
        return faces_list;
    }
};

pub const Brush: type = struct { name: [16]u8 = [_]u8{0} ** 16, map: [0xF1 * 0xF1]u8 = [_]u8{0} ** (0xF1 * 0xF1) };

pub fn read_brush(dr: *DataReader) Brush {
    var brush: Brush = .{};
    brush.name = dr.read_name();
    dr.fill_u8_arr(&brush.map);
    return brush;
}

const sector_width = 0xF1 / 8;

pub const TTile: type = struct {
    hole_flag: u32 = 0,
    pos_x: u32 = 0,
    pos_y: u32 = 0,
    u3: u32 = 0,
    heightmap: [0xF4 * 0xF4]f32 = [_]f32{0.0} ** (0xF4 * 0xF4),
    brushes: []Brush = &.{},
    //Holemap data structure is unknown. hold the raw data if it's present.
    hole_data: [0x1D2F]u8 = [_]u8{0.0} ** (0x1D2F),
    pub fn format(self: @This(), writer: *std.Io.Writer) std.Io.Writer.Error!void {
        try writer.print("TTile(hole_flag=0x{x}, pos_x=0x{x}, pos_y=0x{x}, u3=0x{x}, min_height={}, max_height={}, brushes_n=0x{x})\n", .{ self.hole_flag, self.pos_x, self.pos_y, self.u3, std.mem.min(f32, &self.heightmap), std.mem.max(f32, &self.heightmap), self.brushes.len });
    }
    pub fn get_sector(self: @This(), pos_x: u32, pos_y: u32, scale: f32, allocator: Allocator) !TerrainSector {
        const l_pos_x = pos_x % 8; //Relative to the tile's corner
        const l_pos_y = pos_y % 8;
        const start_x = l_pos_x * sector_width; //Positions on the grid
        const start_y = l_pos_y * sector_width;

        var sector: TerrainSector = .{ .pos_x = pos_x, .pos_y = pos_y, .scale = scale, .brushes = try allocator.alloc(BrushSector, self.brushes.len) };

        //Copy the names only once.
        for (self.brushes, sector.brushes) |t_brush, *s_brush| {
            s_brush.name = t_brush.name;
        }

        for (0..sector_width) |y| {
            const h_src_start = (start_y + y) * 0xF4 + start_x;
            const dst_start = y * sector_width;

            @memcpy(sector.heightmap[dst_start .. dst_start + sector_width], self.heightmap[h_src_start .. h_src_start + sector_width]);

            const b_src_start = (start_y + y) * 0xF1 + start_x;
            for (self.brushes, sector.brushes) |t_brush, *s_brush| {
                @memcpy(s_brush.map[dst_start .. dst_start + sector_width], t_brush.map[b_src_start .. b_src_start + sector_width]);
            }
        }
        return sector;
    }
};

pub fn read_ttile(dr: *DataReader, length: u32, allocator: Allocator) !TTile {
    const start = dr.pos;
    var tile: TTile = .{};
    tile.hole_flag = dr.read_u32();
    tile.pos_x = dr.read_u32();
    tile.pos_y = dr.read_u32();
    tile.u3 = dr.read_u32();
    dr.fill_f32_arr(&tile.heightmap);
    if (tile.hole_flag & 0x200 != 0) {
        dr.fill_u8_arr(&tile.hole_data);
    }
    while (dr.pos - start < length) {
        const chunk_start = dr.pos;
        const signature = dr.read_u32();
        const chunk_length = dr.read_u32();
        _ = chunk_length;
        switch (signature) {
            0xBD01 => {
                const brushes_n = dr.read_u32();
                tile.brushes = try allocator.alloc(Brush, brushes_n);
                for (0..brushes_n) |i| {
                    tile.brushes[i] = read_brush(dr);
                }
            },
            else => {
                print("Found an unknown terrain tile chunk 0x{x} starting @ 0x{x}\n", .{ signature, chunk_start });
                return error.UnknownTTileChunk;
            },
        }
    }
    return tile;
}

const TileCoord: type = struct { x: u32, y: u32 };

pub const Terrain = struct {
    arena: std.heap.ArenaAllocator,
    unk: u32 = 0,
    material: [16]u8 = [_]u8{0} ** 16,
    scale: f32 = 20,
    dim_x: u32 = 1,
    dim_y: u32 = 1,
    tile_map: std.AutoHashMapUnmanaged(TileCoord, TTile),

    pub fn init() Terrain {
        return .{
            .arena = std.heap.ArenaAllocator.init(std.heap.page_allocator),
            .tile_map = .{},
        };
    }
    pub fn deinit(self: *Terrain) void {
        self.arena.deinit();
    }
    pub fn format(self: *const @This(), writer: *std.Io.Writer) std.Io.Writer.Error!void {
        try writer.print("Terrain(unk=0x{x}, material={s}, scale={}, dim_x=0x{x}, dim_y=0x{x}, tiles_n=0x{x})\n", .{ self.unk, std.mem.sliceTo(&self.material, 0), self.scale, self.dim_x, self.dim_y, self.tile_map.count() });
    }
    pub fn get_sector(self: *@This(), pos_x: u32, pos_y: u32) !TerrainSector {
        if (pos_x / 8 > self.dim_x or pos_x / 8 > self.dim_y) {
            print("Sector (0x{x},0x{x}) is out of indexing range for terrain with dimensions (0x{x},0x{x})", .{ pos_x, pos_y, self.dim_x, self.dim_y });
            return error.SectorOutOfBounds;
        }
        const ttile = self.tile_map.get(.{ .x = pos_x / 8, .y = pos_y / 8 }) orelse {
            print("Sector (0x{x},0x{x}) does not have a terrain tile! It would fit in tile (0x{x},0x{x})\n", .{ pos_x, pos_y, pos_x / 8, pos_y / 8 });
            return error.TerrainTileNotFound;
        };
        return ttile.get_sector(pos_x, pos_y, self.scale, self.arena.allocator());
    }
};

pub fn read_terrain(dr: *DataReader) !Terrain {
    var terrain: Terrain = Terrain.init();
    const allocator = terrain.arena.allocator();
    terrain.unk = dr.read_u32();
    terrain.material = dr.read_name();
    terrain.scale = dr.read_f32();
    terrain.dim_x = dr.read_u32();
    terrain.dim_y = dr.read_u32();
    const blocks_n = dr.read_u32();
    for (0..blocks_n) |_| {
        const block_start = dr.pos;
        const block_sig = dr.read_u32();
        const block_length = dr.read_u32();
        switch (block_sig) {
            0xBDAD => {
                const ttile = try read_ttile(dr, block_length, allocator);
                // print("{f}", .{ttile});
                try terrain.tile_map.put(allocator, .{ .x = ttile.pos_x, .y = ttile.pos_y }, ttile);
            },
            else => {
                print("Found an unknown terrain block 0x{x} starting @ 0x{x}\n", .{ block_sig, block_start });
                return error.UnknownTTileChunk;
            },
        }
    }
    return terrain;
}

var TerrainType: ?*py.PyTypeObject = null;

pub const TerrainObject = extern struct {
    ob_base: py.PyObject,
    terrain: ?*Terrain,
};

fn terrain_dealloc(self_obj: ?*py.PyObject) callconv(.c) void {
    const self: *TerrainObject = @ptrCast(@alignCast(self_obj));

    if (self.terrain) |terrain| {
        terrain.arena.deinit();
        std.heap.c_allocator.destroy(terrain);
    }

    py.Py_TYPE(self_obj).*.tp_free.?(self_obj);
}

fn sector_to_py(sector: TerrainSector) ?*py.PyObject {
    const result = py.PyTuple_New(2);
    _ = py.PyTuple_SetItem(result, 0, sector.heightmap_to_positions_py());
    _ = py.PyTuple_SetItem(result, 1, sector.generate_face_indices());
    return result;
}

fn terrain_get_sector(self_obj: ?*py.PyObject, args: ?*py.PyObject) callconv(.c) ?*py.PyObject {
    const self: *TerrainObject = @ptrCast(@alignCast(self_obj));

    const terrain = self.terrain orelse {
        return null;
    };

    var pos_x: c_uint = undefined;
    var pos_y: c_uint = undefined;

    if (py.PyArg_ParseTuple(args, "II", &pos_x, &pos_y) == 0) {
        return null;
    }
    const sector = terrain.get_sector(pos_x, pos_y) catch {
        return null;
    };

    return sector_to_py(sector);
}

const Terrain_methods = [_]py.PyMethodDef{
    .{
        .ml_name = "get_sector",
        .ml_meth = terrain_get_sector,
        .ml_flags = py.METH_VARARGS,
        .ml_doc = "Get a terrain sector.",
    },
    .{},
};

const Terrain_slots = [_]py.PyType_Slot{
    .{
        .slot = py.Py_tp_dealloc,
        .pfunc = @ptrCast(@constCast(&terrain_dealloc)),
    },
    .{
        .slot = py.Py_tp_methods,
        .pfunc = @ptrCast(@constCast(&Terrain_methods)),
    },
    .{},
};

var Terrain_spec = py.PyType_Spec{
    .name = "x_rft_zig.Terrain",
    .basicsize = @sizeOf(TerrainObject),
    .itemsize = 0,
    .flags = py.Py_TPFLAGS_DEFAULT,
    .slots = @ptrCast(@constCast(&Terrain_slots)),
};

pub fn parse_terrain_py(self: ?*py.PyObject, args: ?*py.PyObject) callconv(.c) ?*py.PyObject {
    _ = self;

    var ptr: []u8 = undefined;
    var len: py.Py_ssize_t = undefined;

    if (py.PyArg_ParseTuple(args, "y#", &ptr, &len) == 0) { //Read the args, check the format, fill in the zig ids with the unpacked result.
        return null; // Python exception already set
    }
    const data: []u8 = ptr[0..@intCast(len)];
    var dr: DataReader = .{ .data = data, .pos = 0 };

    const terrain_ptr = std.heap.c_allocator.create(Terrain) catch {
        return null;
    };

    terrain_ptr.* = read_terrain(&dr) catch {
        std.heap.c_allocator.destroy(terrain_ptr);
        return null;
    };

    const py_type = TerrainType orelse return null;

    const py_obj = py.PyType_GenericAlloc(py_type, 0) orelse return null;

    const obj: *TerrainObject = @ptrCast(@alignCast(py_obj));
    obj.terrain = terrain_ptr;

    return py_obj;
}

var methods = [_]py.PyMethodDef{
    .{
        .ml_name = "parse_terrain",
        .ml_meth = parse_terrain_py,
        .ml_flags = py.METH_VARARGS,
        .ml_doc = "Parse a RFT",
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
    .m_name = "x_rft_zig",
    .m_doc = "Zig RFT parser",
    .m_size = -1,
    .m_methods = &methods[0],
};

export fn PyInit_x_rft_zig() callconv(.c) ?*py.PyObject {
    const mod = py.PyModule_Create(&module) orelse return null;

    const type_obj = py.PyType_FromSpec(&Terrain_spec) orelse {
        py.Py_DECREF(mod);
        return null;
    };

    TerrainType = @ptrCast(type_obj);

    if (py.PyModule_AddObject(mod, "Terrain", type_obj) < 0) {
        py.Py_DECREF(type_obj);
        py.Py_DECREF(mod);
        return null;
    }

    return mod;
}

// pub fn main(init: std.process.Init) !void {
//     const cwd: std.Io.Dir = .cwd();

//     const data: []u8 = try cwd.readFileAlloc(init.io, "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Exanima\\Resource\\exanimac1.rft", init.gpa, .unlimited);
//     defer init.gpa.free(data);

//     var dr: DataReader = .{ .data = data, .pos = 0 };
//     const signature = dr.read_u32();
//     if (signature != 0x3EEFAD01) {
//         print("Was provided an incorrect terrain file. Signature = 0x{x}", .{signature});
//         return error.InvalidTerrain;
//     }

//     var terrain: Terrain = try read_terrain(&dr);
//     print("{f}", .{terrain});

//     const tsector = try terrain.get_sector(16, 16);
//     print("{f}", .{tsector});
// }
