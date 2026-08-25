'''
This module is for the charroles.rdb file in Exanima. 
It parses version 3 fully and version 1 partially. 
Version1 databases are used for updating older charater versions to the most up to date versions-i.e., for hellmode
'''

from __future__ import annotations

from ..parsing_funcs import *
from ..writing_funcs import *

from copy import deepcopy
from dataclasses import dataclass,field,replace

from typing import Any

import os
import bpy

@dataclass
class Relation:
    use_affinity: bool = False
    role: Role | None = None
    context_id:  int = 0x0
    basetrust:   int = 0x0 #signed: [-100,100]. When set to use affinity, the trust becomes affinity/basetrust
    hesistation: int = 0x0
    r_1: int = 0x0 #reserved, no use?
    r_2: int = 0x0
    @classmethod
    def parse(cls, file: BufferedReader, roledb: RoleDB, flags: int = 0x0, *args, **kwargs) -> Relation:
        use_affinity = False
        if flags & 0x1000: use_affinity = True
        role = roledb.get_role(id = read_uints(file,1))
        context_id = read_uints(file,1)
        basetrust = read_sbytes(file,1)
        hesitation,r_1,r_2 = read_ubytes(file,3)
        return Relation(use_affinity = use_affinity, 
                         role        = role,
                        context_id  = context_id,
                        basetrust   = basetrust,
                        hesistation = hesitation,
                        r_1 = r_1,
                        r_2 = r_2)
    def write(self, roledb: RoleDB, *args, **kwargs) -> bytes:
        signature = 0x0
        if self.use_affinity: signature |= 0x1000
        return write_uint(signature) + write_uints((roledb.r_roles[self.role] if self.role else 0, self.context_id)) + write_sbyte(self.basetrust) + write_ubytes((self.hesistation,self.r_1,self.r_2))
    def __repr__(self) -> str:
        return f'Relation(role_name={self.role.name if self.role else None}, aggression={hex(self.aggression)}, trust={hex(self.trust)}, unk1={hex(self.unk1)}, unk2={hex(self.unk2)})'

@dataclass
class Function:
    version: int = 0x4
    pre_unks: tuple[int,int,int] = (0,0,0)
    code: str = ''
    @classmethod
    def parse(cls, file: BufferedReader, flags: int = 0x0, version: int = 0x4, *args, **kwargs) -> Function:
        return Function(version = version | flags,
                        pre_unks = read_uints(file,3),
                        code = read_string(file))
    def write(self, *args, **kwargs) -> bytes:
        return write_uint(self.version) + write_uints(self.pre_unks) + write_string(self.code)

@dataclass
class Actor:
    name: str = ''
    type: int = 0x0
    unks: list[int] = field(default_factory = list)
    @classmethod
    def parse(cls, file: BufferedReader) -> Actor:
        name,type = read_name(file),read_uints(file,1)
        if   type == 0x1: unks = []
        elif type == 0x2: unks = read_uints(file,13)
        else: unks = read_uints(file,2)
        return Actor(name = name,
                     type = type,
                     unks = unks)
    def write(self) -> bytes:
        d = write_name(self.name) + write_uint(self.type)
        if self.type != 0x1: d += write_uints(self.unks)
        return d

@dataclass
class DialogueBranch:
    unk1:        int = 0
    dialogues:   list[tuple[Actor,str]] = field(default_factory = list)
    responses:   list[DialogueBranch] = field(default_factory = list)
    terms_code:  str = ''
    effect_code: str = ''
    @classmethod
    def parse(cls, file: BufferedReader, actors: list[Actor]) -> DialogueBranch:
        # print(f'\tReading dialogue branch @ {hex(file.tell())}')
        length,unk1 = read_uints(file,2)
        dialogues = [(actors[read_uints(file,1) - 1], read_string(file)) for _ in range(read_uints(file,1))]
        terms_code = read_string(file)
        effect_code = read_string(file)
        responses = [DialogueBranch.parse(file, actors) for _ in range(read_uints(file,1))]
        return DialogueBranch(unk1 = unk1,
                              dialogues = dialogues,
                              terms_code = terms_code,
                              effect_code = effect_code,
                              responses = responses)
    def write(self, actors: list[Actor]) -> bytes:
        d = write_uint(self.unk1)
        d += write_uint(len(self.dialogues))
        for actor,dialogue in self.dialogues: d += write_uint(actors.index(actor) + 1) + write_string(dialogue)
        d += write_string(self.terms_code)
        d += write_string(self.effect_code)
        d += write_uint(len(self.responses))
        for response in self.responses: d += response.write(actors)
        return write_uint(len(d) + 4) + d
    

@dataclass
class Topic:
    unk1:     int = 0x0
    name:     str = ''
    position: tuple[float,float] = (0.0,0.0)
    unk_list: list[int] = field(default_factory = list) #relations?
    branches: list[DialogueBranch] = field(default_factory = list)
    @classmethod
    def parse(cls, file: BufferedReader, actors: list[Actor]) -> Topic:
        length,start = read_uints(file,1),file.tell()-4
        unk1,name = read_uints(file,1),read_name(file)
        # print(f'\tReading topic {name} @ {hex(start)}')
        position = read_floats(file,2)
        unk_list = [read_uints(file,1) for _ in range(read_uints(file,1))]
        branches = [DialogueBranch.parse(file, actors) for _ in range(read_uints(file,1))]
        return Topic(unk1 = unk1,
                     name = name,
                     position = position,
                     unk_list = unk_list,
                     branches = branches)
    def write(self, actors: list[Actor], *args, **kwargs) -> bytes:
        d = write_uint(self.unk1) + write_name(self.name) + write_floats(self.position)
        d += write_uint(len(self.unk_list))
        for unk in self.unk_list: d += write_uint(unk)
        d += write_uint(len(self.branches))
        for branch in self.branches: d += branch.write(actors)
        return write_uint(len(d) + 4) + d

@dataclass
class Dialogue:
    node_version: int = 0x0
    flags: int = 0x0
    pre_unks: tuple[int,int,int] = (0,0,0)
    class_version:    int = 0
    actors:  list[Actor] = field(default_factory = list)
    topics:  list[Topic] = field(default_factory = list)
    trigger_code:    str = ''
    @classmethod
    def parse(cls, file: BufferedReader, flags: int = 0x0, version: int = 0x2, *args, **kwargs) -> Dialogue:
        pre_unks = read_uints(file,3)
        class_start = file.tell()
        class_version,total_class_length = read_uints(file,2)
        # print(f'Reading Dialogue class {hex(class_version)} @ {hex(class_start)} in {file.name}')
        actors = [Actor.parse(file) for _ in range(read_uints(file,1))]
        topics = [Topic.parse(file, actors) for _ in range(read_uints(file,1))]
        trigger_code = ''
        if (flags & 0x1000 or class_version == 0x0) and version == 0x6:
            # print(f'Reading dialogue code @ {hex(file.tell())} in {file.name}')
            trigger_code = read_string(file)
        # print(f'Finished reading dialogue node @ {hex(file.tell())}')
        return Dialogue(node_version = version,
                        flags = flags,
                        pre_unks = pre_unks,
                        class_version = class_version,
                        actors = actors,
                        topics = topics,
                        trigger_code = trigger_code)
    def write(self, *args, **kwargs) -> bytes:
        d = write_uint(len(self.actors))
        for actor in self.actors: d += actor.write()
        d += write_uint(len(self.topics))
        for topic in self.topics: d += topic.write(actors = self.actors)
        signature = self.node_version
        if (self.flags == 0x1000 or self.class_version == 0x0) and self.node_version == 0x6: 
            d += write_string(self.trigger_code)
            signature |= self.flags #could be 0x0 or 0x1000
        return write_uint(signature) + write_uints(self.pre_unks) + write_uints((self.class_version,len(d) + 8)) + d
    def __repr__(self) -> str:
        return f'Dialogue(actors={[actor.name for actor in self.actors]}, topic_names={[topic.name for topic in self.topics]})'

node_data_dict = {
    0x2: Dialogue,
    0x6: Dialogue,
    0x0: Relation,
    0x4: Function,
    0x20: Function,
}

@dataclass
class Node:
    signature: int = 0x0
    data:      Dialogue | Relation | Function | None = None
    _data_types = {'dialogue':(Dialogue,0x2),
                   'relation':(Relation,0x0),
                   'function':(Function,0x4)}
    @classmethod
    def parse(cls, file: BufferedReader, roledb: RoleDB) -> Node:
        start = file.tell()
        length,node_signature = read_uints(file,2)
        data_class = node_data_dict[node_signature & 0xFF]
        # print(f'Reading node {data_class.__name__}, {hex(node_signature)}, @ {hex(start)}')
        data = data_class.parse(file = file, roledb = roledb, flags = node_signature & 0xFFFFFF00, version = node_signature & 0xFF)
        if file.tell() - start != length: raise Exception(f'Improperly read node {type(data).__name__} ({hex(node_signature)}). Read {hex(file.tell() - start)} bytes instead of {hex(length)}. Started @ {hex(start)} in {file.name}')
        return Node(signature = node_signature, data = data)
    @classmethod
    def create_new(cls, node_type: str) -> Node:
        if node_type not in Node._data_types: raise Exception(f'Cannot create a node using an unknown type {node_type}. The following node types are available: {list(Node._data_types.keys())}')
        d_class,d_type = Node._data_types[node_type]
        return Node(signature = d_type, data = d_class())
    def write(self, roledb: RoleDB) -> bytes:
        d = self.data.write(roledb = roledb)
        return write_uint(len(d) + 4) + d
    def __repr__(self) -> str:
        return f'Node(signature={hex(self.type)}, data={self.data})'

@dataclass
class RoleInstance: #Used in characters
    role: Role | None = None
    unk_float: float = 0.0
    filled_variables: list[tuple[int,str,int]] = field(default_factory = list)
    unk_int: int = 0x0
    def write(self) -> bytes:
        role = self.role
        d = write_uint(role.id) + write_float(self.unk_float)
        for m_t,m_n,val in self.filled_variables: d += write_uint(val)
        return d + write_uint(self.unk_int)
    def to_inst(self, inst) -> None:
        if self.role:
            inst.role_id,inst.role_name = self.role.id,self.role.name
        inst.unk_float = self.unk_float
        inst.filled_variables.clear()
        for type,name,value in self.filled_variables:
            i_v = inst.filled_variables.add()
            i_v.var_type,i_v.name,i_v.value = type,name,value

@dataclass
class OldRoleInstance:
    role_id: int = 0
    unk: int = 0x0
    @classmethod
    def parse(cls, file: BufferedReader) -> OldRoleInstance:
        id,unk = read_uints(file,2)
        return OldRoleInstance(role_id = id,
                               unk = unk)
    def to_inst(self, inst) -> None:
        inst.role_id = self.role_id
        inst.unk = self.unk

@dataclass #For updating to the new v3 db; Hellmode updates.
class OldRole:
    id: int = 0x0
    name: str = ''
    @classmethod
    def parse(cls, file: BufferedReader, id: int = 0x0) -> OldRole:
        null = read_uints(file,1)
        return OldRole(id = id,
                       name = read_name(file))
    def __hash__(self) -> int:
        return self.id

@dataclass
class Role:
    id:  int = 0 #for hashing and keeping the original context. The roledb is contextually important since there are users that would need to be updated.
    type:    int = 0x0
    name:    str = ''
    parent:  Role | None = None
    personality: tuple[int,int,int,int] = (0,0,0,0)
    affinity: int = 0x32
    r_1: int = 0x0
    r_2: int = 0x0
    r_3: int = 0x0
    variables: list[tuple[int,str]] = field(default_factory = list)
    constants: list[tuple[str,Any]] = field(default_factory = list)
    unk4:    int = 0x0
    nodes:   list[Node] = field(default_factory = list)
    code:    str = ''
    @classmethod
    def parse(cls, file: BufferedReader, roledb: RoleDB, id) -> Role:
        start = file.tell()
        length,role_type = read_uints(file,2)
        name,parent = read_name(file),roledb.get_role(read_uints(file,1))
        personality = read_ubytes(file,4)
        affinity,r_1,r_2,r_3 = read_ubytes(file,4)
        variables_n,constants_n,unk4,nodes_n = read_uints(file,4)
        code = read_string(file)
        variables = [(read_name(file),read_uints(file,1)) for _ in range(variables_n)]
        constants = [(read_name(file),read_uints(file,1)) for _ in range(constants_n)]
        nodes = [Node.parse(file, roledb) for _ in range(nodes_n)]
        return Role(id          = id,
                    type        = role_type,
                    name        = name,
                    parent      = parent,
                    personality = personality,
                    affinity    = affinity,
                    r_1 = r_1,
                    r_2 = r_2,
                    r_3 = r_3,
                    variables   = variables,
                    constants   = constants, 
                    unk4        = unk4,
                    nodes       = nodes,
                    code        = code)
    def add_node(self, node_type: str) -> Node:
        node = Node.create_new(node_type)
        self.nodes.append(node)
        return node
    def copy(self) -> Role:
        copy = replace(self)
        copy.nodes = [replace(node) for node in copy.nodes]
        return copy
    def __hash__(self):
        return self.id
    def __repr__(self) -> str:
        return f'Role(id={hex(self.id)}, name={self.name}, parent={self.parent.name if self.parent else None}, variables={self.variables}, nodes={[type(node.data).__name__ for node in self.nodes]}, code={repr(self.code)})'
    def to_instance(self) -> RoleInstance:
        return RoleInstance(role = self,
                            filled_variables = [(type,name,0) for type,name in self.variables])
    def parse_instance(self, file: BufferedReader) -> RoleInstance:
        return RoleInstance(role = self,
                            unk_float = read_floats(file,1),
                            filled_variables = [(type,name,val) for (type,name),val in zip(self.variables,read_uints(file,len(self.variables)))],
                            unk_int = read_uints(file,1))
    def write(self, roledb: RoleDB) -> bytes:
        d = write_uint(self.type) + write_name(self.name) + write_uint(roledb.r_roles[self.parent] if self.parent else 0)
        d += write_ubytes(self.personality) + write_ubytes((self.affinity,self.r_1,self.r_2,self.r_3))
        d += write_uints((len(self.variables),len(self.constants),self.unk4,len(self.nodes)))
        d += write_string(self.code)
        for name,m_type in self.variables: d += write_name(name) + write_uint(m_type)
        for name,val    in self.constants: d += write_name(name) + write_uint(val)
        for node in self.nodes: d += node.write(roledb)
        return write_uint(len(d) + 4) + d

@dataclass
class RoleDB:
    file:         BufferedReader | None = None
    version:      int = 0x3
    lookup_table: dict[int,tuple[int,int,int,int]] = field(default_factory = dict)
    data_start:   int = 0x0
    roles:        dict[int,Role] = field(default_factory = dict)
    r_roles:      dict[Role,int] = field(default_factory = dict)
    @classmethod
    def parse(cls, file: BufferedReader, signature: int = 0xDBCB0D03) -> RoleDB:
        return RoleDB(file = file,
                      version = signature & 0xFF,
                      lookup_table = {entry[0]:entry for entry in [read_uints(file,4) for _ in range(read_uints(file,1)//0x10)][:-1]}, #Cut off the bug entry
                      data_start = file.tell())
    @classmethod
    def parse_file(cls, file_path: str) -> RoleDB:
        file = open(file_path, 'rb')
        signature = read_uints(file,1)
        if signature & 0xFFFFFF00 != 0xDBCB0D00: raise Exception(f'File {file_path} is not a role database!')
        return RoleDB.parse(file = file, signature = signature)
    def __repr__(self) -> str:
        return f'RoleDB(version={hex(self.version)}, roles_n={hex(len(self.lookup_table))})'
    def get_role(self, id: int) -> Role | None:
        if   id not in self.lookup_table: return None #raise Exception(f'Failed to find role ID {(hex(id))}!')
        elif id     in self.roles:        return self.roles[id]
        else:
            file = self.file
            start = file.tell()
            _,__,offset,size = self.lookup_table[id]
            file.seek(self.data_start + offset)
            data_start = file.tell()
            if self.version == 0x3:
                role = Role(id = id)
                self.roles[id] = role #Prevent infinite recursions
                role.__dict__.update(Role.parse(file, self, id).__dict__)
            elif self.version == 0x1:
                role = OldRole(id = id)
                self.roles[id] = role
                role.__dict__.update(OldRole.parse(file).__dict__)
            self.r_roles[role] = id
            data_read = file.tell() - data_start
            # if data_read != size: raise Exception(f'Improperly read role {hex(id)}. Read {hex(data_read)} instead of {hex(size)} bytes. Started @ {hex(data_start)} in {file.name}')
            file.seek(start)
            return role
    def get_roles_by_attributes(self, attrs: list[tuple[str,Any]], fuzzy_match: bool = False) -> list[Role | None]:
        '''
        Get roles by the attributes provided
        attrs: list[tuple[attribute_name:str,attribute_value:Any]]
        fuzzy_match: bool, used for things that can be fuzzy matched: strings
        '''
        matches = []
        for attr_name,val in attrs:
            if fuzzy_match and isinstance(val,str): val = val.lower()
            # print(f'Searching for attribute {attr_name} with value {repr(val)}')
            for id in self.lookup_table:
                role = self.get_role(id)
                if fuzzy_match and isinstance(val,str) and val in getattr(role,attr_name).lower():
                    matches.append(role)
                elif val == getattr(role,attr_name):
                    matches.append(role)
        # if not matches: raise Exception(f'Failed to find any role matches using {attrs}')
        return matches if matches else [None]
    def create_role(self, role_name: str, new_id: int = 0x0) -> Role:
        role = self.get_roles_by_attributes(attrs = [('name',role_name)], fuzzy_match = True)[0]
        if role: return role
        if not new_id: next_id = max(self.lookup_table.keys()) + 1
        else:          next_id = new_id
        role = Role(id = next_id, name = role_name)
        self.lookup_table[next_id] = (next_id,0,0,0) #Gets changed on export.
        self.roles[next_id] = role
        self.r_roles[role] = next_id
        return role
    def duplicate_role(self, role: Role | None, role_id: int = 0x0, id_override: int = 0x0) -> Role:
        if not role: role = self.get_role(role_id)
        biggest_id = max(self.lookup_table.keys())
        next_id = biggest_id + 1
        new_role = role.copy()
        new_role.id = next_id if not id_override else id_override
        self.lookup_table[next_id] = (next_id,0,0,0) #Gets changed on export.
        self.roles[next_id] = new_role
        self.r_roles[new_role] = next_id
        return new_role
    def get_names(self) -> list[str]:
        names = []
        file = self.file
        for _,__,offset,size in self.lookup_table.values():
            file.seek(self.data_start + offset + 8)
            names.append(read_name(file))
        return names
    def write(self) -> bytes:
        lt_d = b'' #lookup table data
        b_d  = b'' #body data
        for id in self.lookup_table.keys(): self.get_role(id) #Get everything stored in case it isnt stored
        for id in sorted(self.lookup_table.keys()): 
            role = self.get_role(id) 
            role_data = role.write(self)
            lt_d += write_uints((id,0,len(b_d),len(role_data)))
            b_d += role_data
        lt_d += write_uints((0,0,0,0)) #Bug entry!
        lt_d = write_uint(len(lt_d)) + lt_d
        print(f'Wrote {hex(len(self.lookup_table))} roles to database {hex(0xDBCB0D00 | self.version)}')
        return write_uint(0xDBCB0D00 | self.version) + lt_d + b_d
    def write_to_file(self, file_dir: str) -> None:
        file = open(os.path.join(file_dir,'charroles.rdb'),'wb')
        file.write(self.write())
        file.close()

if __name__ == '__main__':
    charroles_path = r'C:\Users\jango\Desktop\Exanima 0.9.4.5 Beta\charroles.rdb'
    # charroles_path = r'C:\Program Files (x86)\Steam\steamapps\common\Exanima\Resource\charroles.rdb'
    # charroles_path = r'C:\Users\jango\Desktop\Exanima RoleDB Editor\roledb_modules\charroles.rdb'
    import os
    out_dir = r'C:\Users\jango\Desktop\Exanima RoleDB Editor\roledb_modules'
    with open(charroles_path, 'rb') as file:
        signature = read_uints(file,1)
        roledb = RoleDB.parse(file, signature)
        # for id in roledb.lookup_table: print(roledb.get_role(id))
        role = roledb.get_role(20)
        print(role)
        # node = role.nodes[0]
        # td = node.data
        # td.topics[0].branches[0].dialogues[0] = td.topics[0].branches[0].dialogues[0][0], 'Who the hell are you?'
        # w_file = open(os.path.join(out_dir,'charroles.rdb'),'wb')
        # w_file.write(roledb.write())