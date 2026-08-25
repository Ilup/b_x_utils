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

from ..py_modules.rdb import chars as c
from ..py_modules.rfp import RFP

from ..panels import convenience_funcs as cf

def race_model_hotswap_callback(self, context) -> None:
    root = cf.get_root_in_hierarchy(context.active_object)
    addon_name = __package__.split('.')[0]
    p = context.preferences.addons[addon_name].preferences
    rfp = RFP.parse(p.exanima_dir)
    old_base = rfp.get_race_model(root.x_char.race.model_name + 'base.rfc',None)
    pchar_pos = root.location - old_base[0].location
    # new_base = 
    # root.data = new_base[0].data
    # root.location += new_base[0].location

class Race(bpy.types.PropertyGroup):
    collapsed: BoolProperty(default = True)
    export: BoolProperty(default = False)

    name: StringProperty()
    parent_id: IntProperty(min = 0x0)
    model_name: StringProperty()
    model_scale: FloatVectorProperty(size = 2)
    morph_name: StringProperty()
    anim_set:   StringProperty()

    base_speed: FloatProperty()
    step_speed: FloatProperty()

    char_size: FloatProperty()
    char_scale: FloatProperty()
    scale_ratio: FloatProperty()
    char_mass: FloatProperty()

    balance:    FloatProperty()
    rigidity:   FloatProperty()
    steadiness: FloatProperty()
    dampen:     FloatProperty()

    atck_range: FloatProperty(description = 'Unarmed attack range')
    atck_swing: FloatProperty(description = 'How far body swings with attacks')
    atck_sync:  FloatProperty(description = 'Step-attack synchronisation value')
    atck_recvr: FloatProperty(description = 'Recovery time from combat actions')
 
    locomotion: StringProperty(default = '00' * 4 * 5 * 4)

    base_health: FloatProperty()

    blood_color: IntVectorProperty(size = 4, min = 0x0, max = 0xFF)

    mind_type: IntProperty()
    mind_part: IntProperty()
    mind_pos: FloatVectorProperty(size = 3)
    mind_scale: FloatVectorProperty(size = 3, default = (1.0,1.0,1.0))
    mind_ang: FloatProperty()

    vision:     FloatProperty()
    mind_sense: FloatProperty()
    hearing:    FloatProperty()

    resist_impact: IntProperty(min = 0x0, max = 0xFF)
    resist_slash: IntProperty(min = 0x0, max = 0xFF)
    resist_crush: IntProperty(min = 0x0, max = 0xFF)
    resist_pierce: IntProperty(min = 0x0, max = 0xFF)

    resist_shock: IntProperty(min = 0x0, max = 0xFF)
    resist_fire: IntProperty(min = 0x0, max = 0xFF)
    resist_res0: IntProperty(min = 0x0, max = 0xFF)
    resist_res1: IntProperty(min = 0x0, max = 0xFF)

    reserved: IntVectorProperty(size = 4)

    foley_sound: StringProperty()
    step_sound:  StringProperty()
    impact_sound: StringProperty()
    wound_sound: StringProperty()
    voice_set: StringProperty()

    undead_voice: StringProperty()

    foley_gain:  FloatProperty(default = 1.0) 
    foley_pitch: FloatProperty(default = 1.0)

    step_gain:  FloatProperty(default = 1.0)
    step_pitch: FloatProperty(default = 1.0)

    impact_gain:  FloatProperty(default = 1.0)
    impact_pitch: FloatProperty(default = 1.0)

    wound_gain:  FloatProperty(default = 1.0)
    wound_pitch: FloatProperty(default = 1.0)

    voice_gain:  FloatProperty(default = 1.0)
    voice_pitch: FloatProperty(default = 1.0)

    dead_gain:  FloatProperty(default = 1.0)
    dead_pitch: FloatProperty(default = 1.0)

    grunt_freq: IntProperty(default = 4)

    body_parts: IntProperty(description = '??')
    body_vals: StringProperty(default = '00' * 4 * 20)
    body_covr: StringProperty(default = '00' * 4 * 20)

    weak_points: IntProperty()

    #RGF
    usesex:     BoolProperty()
    usemorph:   BoolProperty()
    useapparel: BoolProperty()
    underwear:  BoolProperty()
    usehair:    BoolProperty()
    usebeard:   BoolProperty()
    procskin:   BoolProperty()
    decomp:     BoolProperty()
    edgefade:   BoolProperty()
    #Trait flags
    bleeding:  BoolProperty()
    living:    BoolProperty()
    learns:    BoolProperty()
    korecover: BoolProperty()
    mechanic:  BoolProperty(description = 'Paralyzed when shocked')
    resilient: BoolProperty(description = 'Resistant to stuns')
    ethereal:   BoolProperty()
    floating:  BoolProperty()
    #Behabvior flags
    aggresive:   BoolProperty(description = 'Does not parry and fights aggressively')
    savage:      BoolProperty(description = 'Disregards defence')
    smashattack: BoolProperty(description = 'Replaces overheads')
    grabattack:  BoolProperty(description = 'Replaces thrusts')
    #Weapon flags
    none:  BoolProperty(description = 'Cannot use weapons')
    held:  BoolProperty(description = 'Normal weapons') #
    claws: BoolProperty()
    large: BoolProperty(description = 'Large weapons (Golems)')
    giant: BoolProperty(description = 'Giant weapons (Ogres)')

class CharItem(bpy.types.PropertyGroup):
    item: PointerProperty(type = bpy.types.Object)
    flag: IntProperty()

class InventoryItem(bpy.types.PropertyGroup):
    charitem: PointerProperty(type = CharItem)
    pos_x: IntProperty(min = 0x0, max = 0xFFFF)
    pos_y: IntProperty(min = 0x0, max = 0xFFFF)

none_enum_list = [('None','None','')]

class Skill(bpy.types.PropertyGroup):
    # rc_skills: #Not implemented in game yet.
    closecombat:   EnumProperty(items = none_enum_list + [(member.name,member.name,'') for member in c.CloseCombatSkills])
    armor:         EnumProperty(items = none_enum_list + [(member.name,member.name,'') for member in c.ArmorSkills])
    shield:        EnumProperty(items = none_enum_list + [(member.name,member.name,'') for member in c.ShieldSkills])
    insight:       EnumProperty(items = none_enum_list + [(member.name,member.name,'') for member in c.InsightSkills])
    concentration: EnumProperty(items = none_enum_list + [(member.name,member.name,'') for member in c.ConcentrationSkills])

def ensure_five_skills(self, context) -> None:
    if context.scene.suppress_char_updates: return
    skills = self.skills
    for _ in range(len(skills) - 5): skills.add()

class SkillGroup(bpy.types.PropertyGroup):
    xp:     IntProperty()
    group_type:   EnumProperty(items = [(member.name,member.name,'') for member in c.SkillCategory])
    collapsed_skills: BoolProperty(default = True)
    skills: CollectionProperty(type = Skill)

class RoleVariable(bpy.types.PropertyGroup):
    var_type: IntProperty()
    name:      StringProperty()
    value:     IntProperty()

def get_role_names(self,context) -> list[tuple[str,str,str]]:
    addon_name = __package__.split('.')[0]
    p = context.preferences.addons[addon_name].preferences
    return RFP.get_role_names(p.exanima_dir)

class RoleInstance(bpy.types.PropertyGroup):
    role_id: IntProperty()
    role_name: EnumProperty(items = get_role_names)
    unk_float: FloatProperty()
    variables_collapsed: BoolProperty(default = True)
    filled_variables: CollectionProperty(type = RoleVariable)

class OldRoleInstance(bpy.types.PropertyGroup):
    role_id: IntProperty()
    unk: IntProperty()

class Relation(bpy.types.PropertyGroup):
    char_id: IntProperty()
    char: PointerProperty(type = bpy.types.Object)
    rel_type: StringProperty()
    reputation: FloatProperty()
    unk: StringProperty()

class GlobalRelations(bpy.types.PropertyGroup):
    collapsed: BoolProperty(default = True)
    relations: CollectionProperty(type = Relation)

class LocaleRelation(bpy.types.PropertyGroup):
    locale_id: IntProperty()
    unk: IntProperty()
    collapsed: BoolProperty(default = True)
    relations: CollectionProperty(type = Relation)

class Condition(bpy.types.PropertyGroup):
    cond_type: EnumProperty(items = [(member.name,member.name,'') for member in c.ConditionType])
    remainder: FloatProperty()

class Loadout(bpy.types.PropertyGroup):
    collapsed: BoolProperty(default = True)
    a: IntProperty()
    hand_r: PointerProperty(type = CharItem)
    hand_l: PointerProperty(type = CharItem)
    alt_hand_r: PointerProperty(type = CharItem)
    alt_hand_l: PointerProperty(type = CharItem)
    apparel_collapsed: BoolProperty(default = True)
    apparel: CollectionProperty(type = CharItem)

class Loadouts(bpy.types.PropertyGroup):
    bool: BoolProperty()
    loadouts: CollectionProperty(type = Loadout)

def get_spell_names(self, context) -> tuple[str,str,str]:
    addon_name = __package__.split('.')[0]
    p = context.preferences.addons[addon_name].preferences
    if not RFP.spell_names:
        rfp = RFP.parse(p.exanima_dir)
        names = []
        for group_id,tree in rfp.pwrs.items():
            if not tree: continue
            for node in tree.nodes:
                names.append(node.name)
        RFP.spell_names = [('None','None','')] + [(name,name,'') for name in names] + [(name,name,'') for name in c.temp_spell_id_to_name_dict.values()]
    return RFP.spell_names 

class KeyboundSpell(bpy.types.PropertyGroup):
    spell_id: IntProperty()
    name: EnumProperty(items = get_spell_names)
    is_active: BoolProperty()

class KnownSpell(bpy.types.PropertyGroup):
    spell_id: IntProperty()
    name: EnumProperty(items = get_spell_names)
    xp: IntProperty()
    empowered: BoolProperty()
    no_prereqs: BoolProperty()

class Thaumaturgy(bpy.types.PropertyGroup):
    bool: BoolProperty()
    version: IntProperty()
    potential: FloatProperty()
    kb_spells_collapsed: BoolProperty(default = True)
    keybound_spells: CollectionProperty(type = KeyboundSpell)
    spells_collapsed: BoolProperty(default = True)
    spells: CollectionProperty(type = KnownSpell)

class Character(bpy.types.PropertyGroup):
    state: IntProperty()
    version: IntProperty()
    name: StringProperty()
    surname: StringProperty()
    muscle: FloatProperty()
    fat: FloatProperty()
    height: FloatProperty()
    age: FloatProperty()
    skin_x: IntProperty(min = 0x0, max = 0xFFFF)
    skin_y: IntProperty(min = 0x0, max = 0xFFFF)
    hair_style: IntProperty(min = 0x0)
    hair_x: IntProperty(min = 0x0, max = 0xFF)
    hair_y: IntProperty(min = 0x0, max = 0xFF)
    hair_suppress: IntProperty(min = 0x0, max = 0xFF)
    hair_null: IntProperty(min = 0x0, max = 0xFF)
    face_style0: IntProperty(min = 0x0, max = 0xFFFF)
    face_style1: IntProperty(min = 0x0, max = 0xFFFF)
    voice: StringProperty()
    voice_pitch: FloatProperty()
    gender: IntProperty(min = 0x0)
    race: PointerProperty(type = Race)
    hair_flags: IntProperty()
    loadout: IntProperty()
    last_locale: IntProperty()
    hand_r: PointerProperty(type = CharItem)
    hand_l: PointerProperty(type = CharItem)
    alt_hand_r: PointerProperty(type = CharItem)
    alt_hand_l: PointerProperty(type = CharItem)
    apparel_collapsed: BoolProperty(default = True)
    apparel:    CollectionProperty(type = CharItem)
    zombification: FloatProperty()
    stamina: IntProperty(min = 0x0, max = 0xFFFF)
    health: IntProperty(min = 0x0, max = 0xFFFF)
    focus_stamina: IntProperty(min = 0x0, max = 0xFFFF)
    focus_health: IntProperty(min = 0x0, max = 0xFFFF)
    combat_skill: FloatProperty()
    undead_voice: IntProperty()
    trustfulness: IntProperty(min = 0x0, max = 0xFF)
    bravery: IntProperty(min = 0x0, max = 0xFF)
    ben_ach: IntProperty(min = 0x0, max = 0xFF)
    neuroticism: IntProperty(min = 0x0, max = 0xFF)
    rng_seed: StringProperty()
    raw_xp: IntProperty(min = 0, description = 'Experience to learn with or to distribute to player while fighting.')
    null: IntProperty()
    skills_collapsed: BoolProperty(default = True)
    skills: CollectionProperty(type = SkillGroup)
    inventory_collapsed: BoolProperty(default = True)
    inventory: CollectionProperty(type = InventoryItem)
    old_roles_collapsed: BoolProperty(default = True)
    old_roles: CollectionProperty(type = OldRoleInstance)
    roles_collapsed: BoolProperty(default = True)
    roles: CollectionProperty(type = RoleInstance)
    global_relations_collapsed: BoolProperty(default = True)
    global_relations: PointerProperty(type = GlobalRelations)
    locale_relations_collapsed: BoolProperty(default = True)
    locale_relations: CollectionProperty(type = LocaleRelation)
    conditions_collapsed: BoolProperty(default = True)
    conditions: CollectionProperty(type = Condition)
    loadouts_collapsed: BoolProperty(default = True)
    loadouts: PointerProperty(type = Loadouts)
    thaumaturgy_collapsed: BoolProperty(default = True)
    thaumaturgy: PointerProperty(type = Thaumaturgy)

classes = [Race,
           CharItem,
           Skill,SkillGroup,
           InventoryItem,
           OldRoleInstance,
           RoleVariable,RoleInstance,
           Relation,GlobalRelations,LocaleRelation,
           Condition,
           Loadout,Loadouts,
           KeyboundSpell,KnownSpell,Thaumaturgy,
           Character]

def register():
    for cls in classes: bpy.utils.register_class(cls)
    bpy.types.Object.x_char = PointerProperty(type = Character)
    bpy.types.Scene.suppress_char_updates = BoolProperty()

def unregister():
    del bpy.types.Object.x_char
    del bpy.types.Scene.suppress_char_updates
    for cls in classes: bpy.utils.unregister_class(cls)
