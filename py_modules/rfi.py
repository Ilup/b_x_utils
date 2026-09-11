import bpy
import numpy as np

from .parsing_funcs import *

from .zig_modules import x_rfi_zig

def parse_image(data: bytes, name: str) -> bpy.types.Image:
    width,height,pixels = x_rfi_zig.parse_rfi(data)
    img = bpy.data.images.new(name,width,height)
    img.pixels = pixels
    return img