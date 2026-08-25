from __future__ import annotations

import sys
sys.path.append(r"C:\Users\jango\Desktop\b_x_utils\py_modules")

from .rfc import parse_rfc
from .parsing_funcs import *
from dataclasses import dataclass,field

from .rdb.items import ItemDB
from .rdb.races import RaceDB
from .rdb.locales import LocaleDB
from .rdb.charroles import RoleDB
from .pwr import PowerTree

import os
import bpy

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .rfp import RFP

@dataclass
class RPK:
    file: BufferedReader | None = None
    signature: int = 0xAFBF0C01
    name: str = ''
    lookup_table: dict[str,tuple[int,int,int,int]] = field(default_factory = list)
    data_start: int = 0
    @classmethod
    def parse(cls, rpk_path: str = '', file: BufferedReader | None = None, read_signature: bool = True, signature: int = 0xAFBF0C01) -> RPK:
        if rpk_path and file: raise Exception(f'Please only provide either an rpk path or a buffered reader!')
        if rpk_path: file = open(rpk_path, 'rb')
        if read_signature: signature = read_uints(file,1)
        return RPK(file = file,
                   signature = signature,
                   name = os.path.basename(file.name),
                   lookup_table = {name.lower():data for name,data in [(read_name(file),read_uints(file,4)) for _ in range(read_uints(file)//0x20)]},
                   data_start = file.tell())
    def parse_entry(self, name: str, rfp: RFP | None = None, scene: bpy.types.Scene | None = None, is_prop: bool = False) -> list[bpy.types.Object]:
        name = name.lower()
        if name not in self.lookup_table: raise Exception(f'Entry ({name}) is not in rpk ({self.name}) @ {self.file.name}')
        file = self.file
        offset,size,_,ID = self.lookup_table[name]
        file.seek(self.data_start + offset)
        signature = read_uints(file,1)
        if   signature == 0x3D23AFCF: return parse_rfc(rfp = rfp, name = name, file = file, size = size, scene = scene, read_signature = False, signature = signature, return_nodes = True, is_prop = is_prop)
        elif signature == 0xDBCB0D00: return RaceDB.parse(file = file, version = signature, data_size = size)
        elif signature == 0xDBAE0D01: return LocaleDB.parse(file, signature = signature)
        elif signature & 0xFFFFFF00 == 0xDBCB0D00: return RoleDB.parse(file, signature)
        elif signature == 0xAFCE01CE: return PowerTree.parse(file, length = size - 4)
        else: raise Exception(f'Entry ({name}) has an unknown signature ({hex(signature)}) @ {hex(file.tell())} in {file.name}')
    def parse_itemdb(self) -> ItemDB: #requires special treatment since it needs to access two different files.
        file = self.file
        itemdb = ItemDB(file = file, name = 'Universal', signature = 0x0)
        offset,size,_,ID = self.lookup_table['objdb.rdb']
        file.seek(offset + self.data_start)
        itemdb.parse_itemdb()
        offset,size,_,ID = self.lookup_table['objstrings.rdb']
        file.seek(offset + self.data_start)
        itemdb.parse_strdb()
        return itemdb
    def __repr__(self) -> str:
        return f'RPK(file={self.file.name}, signature={self.signature}, name={self.name}, entries_amount={hex(len(self.lookup_table))}, data_start={hex(self.data_start)})'

        
