import bpy

from bpy.props import (
    CollectionProperty,
    StringProperty	,
    BoolProperty	,
    EnumProperty	,
    FloatProperty	,
    PointerProperty ,
    IntProperty     ,
    IntVectorProperty,
    FloatVectorProperty,
)

#Idk why it needs this
class ReferencedObject(bpy.types.PropertyGroup):
   object : PointerProperty(type = bpy.types.Object)


class Thing(bpy.types.PropertyGroup):
    bool: BoolProperty()
    collapsed: BoolProperty(default = True)
    name: StringProperty(maxlen=0x10)
    singular_published: IntProperty()
    version: IntProperty()
    unused0: IntProperty()
    unused1: IntProperty()
    parent_id: IntProperty()
    parent: PointerProperty(type = bpy.types.Object)

class Object(bpy.types.PropertyGroup):
    bool: BoolProperty()
    collapsed: BoolProperty(default = True)
    model_name: StringProperty(maxlen=0x10)
    exp: IntProperty()
    zoom_smooth: IntProperty()
    unused0: IntProperty()
    unused1: IntProperty()
    name: StringProperty()
    desc: StringProperty()
    size: IntProperty()
    rarity: IntProperty()
    value: IntProperty()
    provenance: IntProperty()
    purpose: IntProperty()

class Socket(bpy.types.PropertyGroup):
    type: IntProperty()
    usage: IntProperty()

class SWeapon(bpy.types.PropertyGroup):
    bool: BoolProperty()
    collapsed: BoolProperty(default = True)
    material_seed: StringProperty()
    quality: IntProperty()
    wear: IntProperty()
    dirt: IntProperty()
    variance: IntProperty()
    unused_stats: StringProperty()
    rank_points: IntProperty()
    sound: IntProperty()
    ability: IntProperty()
    sockets: CollectionProperty(type = Socket)

class WeaponMat(bpy.types.PropertyGroup):
    material: IntProperty()
    unused0: IntProperty()
    unused1: IntProperty()
    luster: IntProperty()
    color: IntProperty()
    unused2: IntProperty()
    unused3: IntProperty()
    theme: IntProperty()

class PWeapon(bpy.types.PropertyGroup):
    bool: BoolProperty()
    collapsed: BoolProperty(default = True)
    grip_type:      IntProperty()
    sword_flags:    IntProperty() 
    haft_materials: IntProperty()
    weapon_flags:   IntProperty()
    factory_seed:   StringProperty()
    material_seed:  StringProperty()
    quality:        IntProperty()
    wear:           IntProperty()
    dirt:           IntProperty()
    variance:       IntProperty()
    collapsed_materials: BoolProperty(default = True)
    materials:      CollectionProperty(type = WeaponMat)
    weight:         IntProperty()
    balance:        IntProperty()
    impact:         IntProperty()
    thrust:         IntProperty()
    eff_near:       IntProperty()
    eff_mid:        IntProperty()
    eff_end:        IntProperty()
    slash:          IntProperty()
    crush:          IntProperty()
    pierce:         IntProperty()
    flip:           IntProperty()
    f_eff_near:     IntProperty()
    f_eff_far:      IntProperty()
    f_slash:        IntProperty()
    f_crush:        IntProperty()
    f_pierce:       IntProperty()
    grade:          IntProperty() 
    sounds:         IntProperty()
    rank_points:    IntProperty()
    statunk7:       IntProperty()
    collapsed_sockets: BoolProperty(default = True)
    sockets:        CollectionProperty(type = Socket)
    components:     IntVectorProperty(size = 16)

class Shield(bpy.types.PropertyGroup):
    bool: BoolProperty()
    collapsed: BoolProperty(default = True)
    unused00:     IntProperty()
    unused04:     IntProperty()
    unused08:     IntProperty()
    weapon_flags: IntProperty()
    weight:       IntProperty()
    impact:       IntProperty()
    encumbrance:  IntProperty()
    unused1C:     IntProperty()
    rank_points:  IntProperty()
    unused:       StringProperty()

class Torch(bpy.types.PropertyGroup):
    bool: BoolProperty()
    collapsed: BoolProperty(default = True)
    data: StringProperty()

class ApparelMat(bpy.types.PropertyGroup):
    layer:    IntProperty()
    part:     IntProperty()
    element:  IntProperty()
    design:   IntProperty()
    material: IntProperty()
    unused0:  IntProperty()
    unused1:  IntProperty()
    trait:    IntProperty()
    color:    IntProperty()
    unused2:  IntProperty()
    unused3:  IntProperty()
    theme:    IntProperty()

class Apparel(bpy.types.PropertyGroup):
    bool: BoolProperty()
    collapsed: BoolProperty(default = True)
    model:         StringProperty()
    usage:         StringProperty()
    visibility:    StringProperty()
    coverage:      StringProperty()
    impact:        IntProperty()
    slash:         IntProperty()
    crush:         IntProperty()
    pierce:        IntProperty()
    av_coverage:   IntProperty()
    encumbrance:   IntProperty()
    sound:         IntProperty()
    bulk:          IntProperty()
    type:          IntProperty()
    grade:         IntProperty()
    trait:         IntProperty()
    rank_points:   IntProperty()
    material_seed: StringProperty()
    quality:       IntProperty()
    wear:          IntProperty()
    dirt:          IntProperty()
    variance:      IntProperty()
    collapsed_materials: BoolProperty(default = True)
    materials:     CollectionProperty(type = ApparelMat)
    ability:       IntProperty()
    collapsed_sockets: BoolProperty(default = True)
    sockets:       CollectionProperty(type = Socket)
    set_uid:       IntProperty()

class StoredItem(bpy.types.PropertyGroup):
    # item_id: IntProperty() #Fallback incase there isnt an item. ie, when there's a universal item without a provided universal DB
    item:    PointerProperty(type = bpy.types.Object)
    pos_x:   IntProperty()
    pos_y:   IntProperty()

class Container(bpy.types.PropertyGroup):
    bool: BoolProperty()
    collapsed: BoolProperty(default = False)
    width:    IntProperty()
    height:   IntProperty()
    # key_id:   IntProperty()
    key:      PointerProperty(type = bpy.types.Object)
    capacity: IntProperty()
    max_size: IntProperty()
    unk1:     IntProperty()
    unk2:     IntProperty()
    items:    CollectionProperty(type = StoredItem)

class DTItem(bpy.types.PropertyGroup):
    # item_id:  IntProperty()
    item:     PointerProperty(type = bpy.types.Object)
    chance:   IntProperty()
    rarity:   IntProperty()
    min:      IntProperty()
    max:      IntProperty()
    flag:     IntProperty()
    amount:   IntProperty()
    wear_var: IntProperty()
    dirt_var: IntProperty()
    unk1:     IntProperty()
    unk2:     IntProperty()
    unk3:     IntProperty()
    unk4:     IntProperty()

class Droptable(bpy.types.PropertyGroup):
    bool: BoolProperty()
    collapsed: BoolProperty(default = False)
    unk1:      IntProperty()
    specitem1: IntProperty() #Special item index in the droptable?
    specitem2: IntProperty()
    unk2:      IntProperty()
    unk3:      IntProperty()
    items:     CollectionProperty(type = DTItem)

class Map(bpy.types.PropertyGroup):
    bool: BoolProperty()
    collapsed: BoolProperty(default = True)
    unk1: IntProperty()
    unk2: IntProperty()
    unk3: IntProperty()
    unk4: IntProperty()
    name: StringProperty(maxlen=0x10)

class Zone(bpy.types.PropertyGroup):
    bool: BoolProperty()
    collapsed: BoolProperty(default = True)
    size_x:    IntProperty()
    size_y:    IntProperty()
    size_z:    IntProperty()
    unk1:      IntProperty()
    function:  IntProperty()
    trigger:   IntProperty()
    unk2:      IntProperty()
    unk3:      IntProperty()
    unk4:      IntProperty()
    target_id: IntProperty() #Could be a locale or game event or something
    code:      StringProperty()

class Operator(bpy.types.PropertyGroup):
    bool: BoolProperty()
    collapsed: BoolProperty(default = True)
    version: IntProperty(default = 0x8)
    type: IntProperty()
    flag: IntProperty()
    val1: IntProperty()
    val2: IntProperty()
    val3: IntProperty()
    val4: IntProperty()
    val5: IntProperty()
    val6: IntProperty()
    target_1_id: IntProperty()
    target_1:    PointerProperty(type = bpy.types.Object)
    target_2_id: IntProperty()
    target_2:    PointerProperty(type = bpy.types.Object)
    target_ids:  IntVectorProperty(size = 8)
    targets:     CollectionProperty(type = ReferencedObject)
    sound:       StringProperty()
    code:        StringProperty()

class Door(bpy.types.PropertyGroup):
    bool: BoolProperty()
    collapsed: BoolProperty(default = True)
    unk1: IntProperty()
    unk2: IntProperty()
    unk3: IntProperty()
    lock_when_closed: BoolProperty() 
    pop_open:         BoolProperty() #Op input
    noninteractable:  BoolProperty()
    full_open:        BoolProperty() #Op inputs
    full_close:       BoolProperty()
    invert_input:     BoolProperty()
    # key_id: IntProperty()
    key:    PointerProperty(type = bpy.types.Object)
    unk4:   IntProperty()
    unk5:   IntProperty()
    unk6:   IntProperty()

class Item(bpy.types.PropertyGroup):
    instance_of: PointerProperty(type = bpy.types.Object)
    thing:     PointerProperty(type = Thing)
    object:    PointerProperty(type = Object)
    sweapon:   PointerProperty(type = SWeapon)
    pweapon:   PointerProperty(type = PWeapon)
    shield:    PointerProperty(type = Shield)
    torch:     PointerProperty(type = Torch)
    apparel:   PointerProperty(type = Apparel)
    container: PointerProperty(type = Container)
    droptable: PointerProperty(type = Droptable)
    map:       PointerProperty(type = Map)
    zone:      PointerProperty(type = Zone)
    operator:  PointerProperty(type = Operator)
    door:      PointerProperty(type = Door)

classes = [ReferencedObject,
           Thing,Object,Socket,SWeapon,WeaponMat,PWeapon,Shield,Torch,ApparelMat,Apparel,StoredItem,Container,DTItem,Droptable,Map,Zone,Operator,Door,Item]

def register():
    for cls in classes: bpy.utils.register_class(cls)
    bpy.types.Object.x_item = PointerProperty(type = Item)
    bpy.types.Scene.suppress_item_updates = BoolProperty()

def unregister():
    del bpy.types.Object.x_item
    del bpy.types.Scene.suppress_item_updates
    for cls in classes: bpy.utils.unregister_class(cls)