const std: type = @import("std");

const py_wr = @import("py_wrapper_funcs.zig");
const py = py_wr.py;

const dr_module = @import("data_reader.zig");
const DataReader: type = dr_module.DataReader;

const Allocator: type = std.mem.Allocator;

pub const RFIError: type = error{UnknownImageFormat};

const print = std.debug.print;

fn to_f32(value: anytype) f32 {
    return @floatFromInt(value);
}

const PixelColor = struct {
    r: f32 = 0.0,
    g: f32 = 0.0,
    b: f32 = 0.0,
};

const b_mask = 0b11111;
const g_mask = 0b111111;
const r_mask = 0b11111;
const a_mask = 0xFF;

const b_mask_float = to_f32(b_mask);
const g_mask_float = to_f32(g_mask);
const r_mask_float = to_f32(r_mask);
const a_mask_float = to_f32(a_mask);

fn create_bc1_color(raw_color: u64) PixelColor {
    return .{
        .b = to_f32((raw_color & b_mask)) / b_mask_float,
        .g = to_f32((raw_color >> 5) & g_mask) / g_mask_float,
        .r = to_f32((raw_color >> 11) & r_mask) / r_mask_float,
    };
}

pub fn read_bc1_py(dr: *DataReader, width: u32, height: u32) !?*py.PyObject {
    // print("Decompressing bc1...\n", .{});
    const blocks_x: u32 = (width + 3) / 4;
    const blocks_y: u32 = (height + 3) / 4;
    const pixels_list = py.PyList_New(@intCast(width * height * 4)); //Blender holds pixels as a flattened rgba list; [r0,g0,b0,a0,r1,g1,b1,a1,...]
    // for (0..blocks_y) |block_y| { //row
    var block_y = blocks_y;
    while (block_y > 0) { //Read the blocks upside down...
        block_y -= 1;
        const block_pos_y = block_y * width;
        for (0..blocks_x) |block_x| { //cell
            const block_pos = block_pos_y + block_x;

            const color_block = dr.read_u64();

            const color0_raw = color_block & 0xFFFF;
            const color1_raw = (color_block >> 16) & 0xFFFF;
            const color0: PixelColor = create_bc1_color(color0_raw);
            const color1: PixelColor = create_bc1_color(color1_raw);
            const colors: [4]PixelColor = .{
                color0,
                color1,
                .{
                    .r = (2.0 * color0.r + color1.r) / 3.0,
                    .g = (2.0 * color0.g + color1.g) / 3.0,
                    .b = (2.0 * color0.b + color1.b) / 3.0,
                },
                .{
                    .r = (color0.r + 2.0 * color1.r) / 3.0,
                    .g = (color0.g + 2.0 * color1.g) / 3.0,
                    .b = (color0.b + 2.0 * color1.b) / 3.0,
                },
            };

            var picked_colors = color_block >> 32;
            var j: u32 = 4;
            while (j > 0) { //Read the block upside down
                j -= 1;
                const pixel_y = block_pos * 4 + j * width;
                for (0..4) |i| {
                    const pixel_pos = pixel_y + i;
                    const pixel_index: u32 = @intCast(pixel_pos * 4);
                    const color = colors[picked_colors & 0b11];
                    _ = py.PyList_SetItem(pixels_list, pixel_index, py.PyFloat_FromDouble(color.r));
                    _ = py.PyList_SetItem(pixels_list, pixel_index + 1, py.PyFloat_FromDouble(color.g));
                    _ = py.PyList_SetItem(pixels_list, pixel_index + 2, py.PyFloat_FromDouble(color.b));
                    _ = py.PyList_SetItem(pixels_list, pixel_index + 3, py.PyFloat_FromDouble(1.0));

                    picked_colors >>= 2; //Lop off the color just inspected
                }
            }
        }
    }
    return pixels_list;
}

const one_seventh: f32 = 1.0 / 7.0;
const one_fifth: f32 = 1.0 / 5.0;
fn interpolate_alphas(alpha0: f32, alpha1: f32) [8]f32 {
    if (alpha0 > alpha1) {
        return .{
            alpha0,
            alpha1,
            (6.0 * alpha0 + 1.0 * alpha1) * one_seventh,
            (5.0 * alpha0 + 2.0 * alpha1) * one_seventh,
            (4.0 * alpha0 + 3.0 * alpha1) * one_seventh,
            (3.0 * alpha0 + 4.0 * alpha1) * one_seventh,
            (2.0 * alpha0 + 5.0 * alpha1) * one_seventh,
            (1.0 * alpha0 + 6.0 * alpha1) * one_seventh,
        };
    } else {
        return .{
            alpha0,
            alpha1,
            (6.0 * alpha0 + 1.0 * alpha1) * one_seventh,
            (5.0 * alpha0 + 2.0 * alpha1) * one_seventh,
            (4.0 * alpha0 + 3.0 * alpha1) * one_seventh,
            (3.0 * alpha0 + 4.0 * alpha1) * one_seventh,
            1.0,
            0.0,
        };
    }
}

pub fn read_bc4_py(dr: *DataReader, width: u32, height: u32) !?*py.PyObject {
    // print("Decompressing bc4...\n", .{});
    const blocks_x: u32 = (width + 3) / 4;
    const blocks_y: u32 = (height + 3) / 4;
    const pixels_list = py.PyList_New(width * height * 4); //Blender holds pixels as a flattened rgba list; [r0,g0,b0,a0,r1,g1,b1,a1,...]

    var block_y = blocks_y;
    while (block_y > 0) { //Read it upside down...
        block_y -= 1;
        const block_pos_y = block_y * width;
        for (0..blocks_x) |block_x| { //cell
            const block_pos = block_pos_y + block_x;

            const alpha_block = dr.read_u64();

            const alpha0 = to_f32(alpha_block & a_mask) / a_mask_float;
            const alpha1 = to_f32((alpha_block >> 8) & a_mask) / a_mask_float;
            const alphas = interpolate_alphas(alpha0, alpha1);

            var picked_alphas = alpha_block >> 16;
            var j: u32 = 4;
            while (j > 0) {
                j -= 1;
                const pixel_y = block_pos * 4 + j * width;
                for (0..4) |i| {
                    const pixel_pos = pixel_y + i;
                    const pixel_index: u32 = @intCast(pixel_pos * 4);
                    const alpha = alphas[picked_alphas & 0b111];

                    _ = py.PyList_SetItem(pixels_list, pixel_index, py.PyFloat_FromDouble(alpha));
                    _ = py.PyList_SetItem(pixels_list, pixel_index + 1, py.PyFloat_FromDouble(alpha));
                    _ = py.PyList_SetItem(pixels_list, pixel_index + 2, py.PyFloat_FromDouble(alpha));
                    _ = py.PyList_SetItem(pixels_list, pixel_index + 3, py.PyFloat_FromDouble(1.0));

                    picked_alphas >>= 3; //Lop off the color just inspected
                }
            }
        }
    }
    return pixels_list;
}

pub fn read_bc3_py(dr: *DataReader, width: u32, height: u32) !?*py.PyObject {
    // print("Decompressing bc3...\n", .{});
    const blocks_x: u32 = (width + 3) / 4;
    const blocks_y: u32 = (height + 3) / 4;
    const pixels_list = py.PyList_New(width * height * 4); //Blender holds pixels as a flattened rgba list; [r0,g0,b0,a0,r1,g1,b1,a1,...]

    var block_y = blocks_y;
    while (block_y > 0) { //Read it upside down...
        block_y -= 1;
        const block_pos_y = block_y * width;
        for (0..blocks_x) |block_x| { //cell
            const block_pos = block_pos_y + block_x;

            const alpha_block = dr.read_u64();

            const alpha0 = to_f32(alpha_block & a_mask) / a_mask_float;
            const alpha1 = to_f32((alpha_block >> 8) & a_mask) / a_mask_float;
            const alphas = interpolate_alphas(alpha0, alpha1);

            var picked_alphas = alpha_block >> 16;

            const color_block = dr.read_u64();

            const color0_raw = color_block & 0xFFFF;
            const color1_raw = (color_block >> 16) & 0xFFFF;
            const color0: PixelColor = create_bc1_color(color0_raw);
            const color1: PixelColor = create_bc1_color(color1_raw);
            const colors: [4]PixelColor = .{
                color0,
                color1,
                .{
                    .r = (2.0 * color0.r + color1.r) / 3.0,
                    .g = (2.0 * color0.g + color1.g) / 3.0,
                    .b = (2.0 * color0.b + color1.b) / 3.0,
                },
                .{
                    .r = (color0.r + 2.0 * color1.r) / 3.0,
                    .g = (color0.g + 2.0 * color1.g) / 3.0,
                    .b = (color0.b + 2.0 * color1.b) / 3.0,
                },
            };

            var picked_colors = color_block >> 32;

            var j: u32 = 4;
            while (j > 0) {
                j -= 1;
                const pixel_y = block_pos * 4 + j * width;
                for (0..4) |i| {
                    const pixel_pos = pixel_y + i;
                    const pixel_index: u32 = @intCast(pixel_pos * 4);
                    const alpha = alphas[picked_alphas & 0b111];
                    const color = colors[picked_colors & 0b11];

                    _ = py.PyList_SetItem(pixels_list, pixel_index, py.PyFloat_FromDouble(color.r));
                    _ = py.PyList_SetItem(pixels_list, pixel_index + 1, py.PyFloat_FromDouble(color.g));
                    _ = py.PyList_SetItem(pixels_list, pixel_index + 2, py.PyFloat_FromDouble(color.b));
                    _ = py.PyList_SetItem(pixels_list, pixel_index + 3, py.PyFloat_FromDouble(alpha));

                    picked_alphas >>= 3; //Lop off the color just inspected
                    picked_colors >>= 2; //Lop off the color just inspected
                }
            }
        }
    }
    return pixels_list;
}

pub fn read_bc5_py(dr: *DataReader, width: u32, height: u32) !?*py.PyObject {
    // print("Decompressing bc5...\n", .{});
    const blocks_x: u32 = (width + 3) / 4;
    const blocks_y: u32 = (height + 3) / 4;
    const pixels_list = py.PyList_New(width * height * 4);

    var block_y = blocks_y;
    while (block_y > 0) { //Read it upside down...
        block_y -= 1;
        const block_pos_y = block_y * width;
        for (0..blocks_x) |block_x| { //cell
            const block_pos = block_pos_y + block_x;

            const r_block = dr.read_u64();
            const r0 = to_f32(r_block & a_mask) / a_mask_float;
            const r1 = to_f32((r_block >> 8) & a_mask) / a_mask_float;
            const rs = interpolate_alphas(r0, r1);
            const picked_rs = r_block >> 16;

            const g_block = dr.read_u64();
            const g0 = to_f32(g_block & a_mask) / a_mask_float;
            const g1 = to_f32((g_block >> 8) & a_mask) / a_mask_float;
            const gs = interpolate_alphas(g0, g1);
            const picked_gs = g_block >> 16;

            var j: u32 = 4;
            while (j > 0) {
                j -= 1;
                const pixel_y = block_pos * 4 + j * width;
                for (0..4) |i| {
                    const pixel_pos = pixel_y + i;
                    const pixel_index: u32 = @intCast(pixel_pos * 4);
                    const r = rs[picked_rs & 0b111];
                    const g = gs[picked_gs & 0b111];

                    _ = py.PyList_SetItem(pixels_list, pixel_index, py.PyFloat_FromDouble(r));
                    _ = py.PyList_SetItem(pixels_list, pixel_index + 1, py.PyFloat_FromDouble(g));
                    _ = py.PyList_SetItem(pixels_list, pixel_index + 2, py.PyFloat_FromDouble(0.0));
                    _ = py.PyList_SetItem(pixels_list, pixel_index + 3, py.PyFloat_FromDouble(1.0));
                }
            }
        }
    }
    return pixels_list;
}

pub fn read_pixels_py(dr: *DataReader, format: u32, width: u32, height: u32) !?*py.PyObject {
    //this sucks. figure out the proper way of doing this.
    switch (format) {
        0x813BC600, 0x0100C600, 0x01004200 => {
            return read_bc1_py(dr, width, height);
        },
        0x817BE608, 0x827BA408 => {
            return read_bc3_py(dr, width, height);
        },
        0x823BC600, 0x813B4200, 0x01006208 => {
            return read_bc4_py(dr, width, height);
        },
        0x927B8400 => {
            return read_bc5_py(dr, width, height);
        },
        else => {
            print("Found an unknown image format 0x{x}\n", .{format});
            return error.UnknownImageFormat;
        },
    }
}

pub fn read_image_py(dr: *DataReader) ?*py.PyObject {
    const width = dr.read_u32();
    const height = dr.read_u32();
    const single = dr.read_u32();
    const options = dr.read_u32();
    const flags = dr.read_u32();
    const run_flags = dr.read_u32();
    const size = dr.read_u32();
    _ = single; //Do something with these later...
    _ = flags;
    _ = run_flags;
    _ = size;
    const tuple = py.PyTuple_New(3);
    _ = py.PyTuple_SetItem(tuple, 0, py.PyLong_FromUnsignedLong(width));
    _ = py.PyTuple_SetItem(tuple, 1, py.PyLong_FromUnsignedLong(height));
    const pixels = read_pixels_py(dr, options, width, height) catch {
        return null;
    };
    _ = py.PyTuple_SetItem(tuple, 2, pixels);
    return tuple;
}

pub fn py_meth_read_image(self: ?*py.PyObject, args: ?*py.PyObject) callconv(.c) ?*py.PyObject {
    _ = self;

    var ptr: [*]u8 = undefined;
    var len: py.Py_ssize_t = undefined;

    if (py.PyArg_ParseTuple(args, "y#", &ptr, &len) == 0) { //Read the args, check the format, fill in the zig ids with the unpacked result.
        return null; // Python exception already set
    }
    const data: []u8 = ptr[0..@intCast(len)];
    var dr: DataReader = .{ .data = data, .pos = 0 };

    return read_image_py(&dr);
}

var methods = [_]py.PyMethodDef{
    .{
        .ml_name = "parse_rfi",
        .ml_meth = py_meth_read_image,
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
    .m_name = "x_rfi_zig",
    .m_doc = "Zig RFI parser",
    .m_size = -1,
    .m_methods = &methods[0],
};

export fn PyInit_x_rfi_zig() callconv(.c) ?*py.PyObject {
    return py.PyModule_Create(&module);
}
