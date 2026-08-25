import bpy

from .. panels import convenience_funcs as cf

def display_apparel(layout, char) -> None:
    apparel = char.apparel
    header = layout.row(align=True)
    icon_style = 'TRIA_DOWN' if not char.apparel_collapsed else 'TRIA_RIGHT'
    header.prop(char, "apparel_collapsed", text="Apparel", icon=icon_style, emboss=False)
    if not char.apparel_collapsed:
        if apparel: 
            for a_e in apparel: #apparel entry
                row = layout.row()
                row.prop(a_e,'item')
                if a_e.item: cf.add_op_to_row(row = row, op_idname = 'exanima.edit_x_item',  args = [('obj_name',a_e.item.name)], icon = 'PROPERTIES', text = '')
                row.prop(a_e,'flag')
        else:
            row = layout.row()
            row.alignment = 'CENTER'
            row.label(text = f'Character has no apparel!')

def display_skill(layout, skill_group) -> None:
    cf.display_props_on_new_row(layout,skill_group,['xp','group_type'])
    row = layout.row()
    for skill in skill_group.skills:
        row.prop(skill,skill_group.group_type, text = '')

def display_skills(layout, char) -> None:
    skills = char.skills
    header = layout.row(align=True)
    icon_style = 'TRIA_DOWN' if not char.skills_collapsed else 'TRIA_RIGHT'
    header.prop(char, "skills_collapsed", text="Skill", icon=icon_style, emboss=False)
    if not char.skills_collapsed:
        for skill_group in skills:
            display_skill(layout.box(),skill_group)

def display_inventory(layout, char) -> None:
    inv = char.inventory
    header = layout.row(align=True)
    icon_style = 'TRIA_DOWN' if not char.inventory_collapsed else 'TRIA_RIGHT'
    header.prop(char, "inventory_collapsed", text="Inventory", icon=icon_style, emboss=False)
    if not char.inventory_collapsed:
        for citem in inv:
            row = layout.row()
            row.prop(citem.charitem,'item')
            if item := citem.charitem:
                cf.add_op_to_row(row = row, op_idname = 'exanima.edit_x_item',  args = [('obj_name',item.name)], icon = 'PROPERTIES', text = '')
            row.prop(citem.charitem,'flag')
            cf.display_props_on_row(row,citem,['pos_x','pos_y'])

def display_old_roles(layout, char) -> None:
    o_roles = char.old_roles
    header = layout.row(align=True)
    icon_style = 'TRIA_DOWN' if not char.old_roles_collapsed else 'TRIA_RIGHT'
    header.prop(char, "old_roles_collapsed", text="Old Roles", icon=icon_style, emboss=False)
    if not char.old_roles_collapsed:
        for o_role in o_roles:
            cf.display_props_on_new_row(layout,o_role,['role_id','unk'])

def display_role_variables(layout, role) -> None:
    header = layout.row(align=True)
    icon_style = 'TRIA_DOWN' if not role.variables_collapsed else 'TRIA_RIGHT'
    header.prop(role, "variables_collapsed", text="Variables", icon=icon_style, emboss=False)
    if not role.variables_collapsed:
        if role.filled_variables:
            for var in role.filled_variables:
                cf.display_props_on_new_row(layout,var,['var_type','name','value'])
        else:
            row = layout.row()
            row.alignment = 'CENTER'
            row.label(text = f'Role {role.name} has no variables!')


def display_roles(layout, char) -> None:
    roles = char.roles
    header = layout.row(align=True)
    icon_style = 'TRIA_DOWN' if not char.roles_collapsed else 'TRIA_RIGHT'
    header.prop(char, "roles_collapsed", text="Roles", icon=icon_style, emboss=False)
    if not char.roles_collapsed:
        for role in roles:
            #FIX THE ROLE DATA POPULATION
            cf.display_props_on_new_row(layout,role,['role_name','unk_float'])
            if role.filled_variables:
                display_role_variables(layout.box(),role)

def display_relation(layout, rel) -> None:
    row = layout.row()
    if rel.char:
        row.prop(rel,'char')
        cf.add_op_to_row(row = row, op_idname = 'exanima.edit_x_char',  args = [('obj_name',rel.char.name)], icon = 'PROPERTIES', text = '')
        #Create op to locate character
    else: row.prop(rel,'char_id')
    cf.display_props_on_row(row,rel,['rel_type','reputation','unk'])

def display_relations(layout, rels_container, rel_type: str) -> None: #swap this to a generic relations function
    rels = rels_container.relations
    header = layout.row(align=True)
    icon_style = 'TRIA_DOWN' if not rels_container.collapsed else 'TRIA_RIGHT'
    header.prop(rels_container, "collapsed", text=rel_type, icon=icon_style, emboss=False)
    if not rels_container.collapsed:
        if rels:
            for rel in rels:
                display_relation(layout,rel)
        else:
            row = layout.row()
            row.alignment = 'CENTER'
            row.label(text = f'There are no relations')

def display_locale_relations(layout, char) -> None:
    l_rels = char.locale_relations
    header = layout.row(align=True)
    icon_style = 'TRIA_DOWN' if not char.locale_relations_collapsed else 'TRIA_RIGHT'
    header.prop(char, "locale_relations_collapsed", text="Locale Relations", icon=icon_style, emboss=False)
    if not char.locale_relations_collapsed:
        if l_rels:
            for l_rel in l_rels:
                box = layout.box()
                display_relations(box, l_rel, 'Locale Relation')
        else:
            row = layout.row()
            row.alignment = 'CENTER'
            row.label(text = f'There are no locale relations')

def display_conditions(layout, char) -> None:
    conds = char.conditions
    header = layout.row(align=True)
    icon_style = 'TRIA_DOWN' if not char.conditions_collapsed else 'TRIA_RIGHT'
    header.prop(char, "conditions_collapsed", text="Conditions", icon=icon_style, emboss=False)
    if not char.conditions_collapsed:
        if conds:
            for cond in conds:
                cf.display_props_on_new_row(layout,cond,['cond_type','remainder'])
        else:
            row = layout.row()
            row.alignment = 'CENTER'
            row.label(text = f'Character has no conditions')


def display_loadout_apparel(layout, loadout) -> None:
    apparel = loadout.apparel
    header = layout.row(align=True)
    icon_style = 'TRIA_DOWN' if not loadout.apparel_collapsed else 'TRIA_RIGHT'
    header.prop(loadout, "apparel_collapsed", text="Apparel", icon=icon_style, emboss=False)
    if not loadout.apparel_collapsed:
        if apparel: 
            for a_e in apparel: #apparel entry
                row = layout.row()
                row.prop(a_e,'item')
                if a_e.item: cf.add_op_to_row(row = row, op_idname = 'exanima.edit_x_item',  args = [('obj_name',a_e.item.name)], icon = 'PROPERTIES', text = '')
                row.prop(a_e,'flag')
        else:
            row = layout.row()
            row.alignment = 'CENTER'
            row.label(text = f'Loadout has no apparel!')

def display_loadout(layout, loadout) -> None:
    header = layout.row(align=True)
    icon_style = 'TRIA_DOWN' if not loadout.collapsed else 'TRIA_RIGHT'
    header.prop(loadout, "collapsed", text="Apparel", icon=icon_style, emboss=False)
    if not loadout.collapsed:
        layout.row().prop(loadout,'a')
        row = layout.row()
        row.prop(loadout.hand_r,'item', text = 'hand_r')
        if loadout.hand_r.item: cf.add_op_to_row(row = row, op_idname = 'exanima.edit_x_item',  args = [('obj_name',char.hand_r.item.name)], icon = 'PROPERTIES', text = '')
        row.prop(loadout.hand_r,'flag')
        row.prop(loadout.hand_l,'item', text = 'hand_l')
        if loadout.hand_l.item: cf.add_op_to_row(row = row, op_idname = 'exanima.edit_x_item',  args = [('obj_name',char.hand_l.item.name)], icon = 'PROPERTIES', text = '')
        row.prop(loadout.hand_l,'flag')
        row = layout.row()
        row.prop(loadout.alt_hand_r,'item', text = 'alt_hand_r')
        if loadout.alt_hand_r.item: cf.add_op_to_row(row = row, op_idname = 'exanima.edit_x_item',  args = [('obj_name',char.alt_hand_r.item.name)], icon = 'PROPERTIES', text = '')
        row.prop(loadout.alt_hand_r,'flag')
        row.prop(loadout.alt_hand_l,'item', text = 'alt_hand_l')
        if loadout.alt_hand_l.item: cf.add_op_to_row(row = row, op_idname = 'exanima.edit_x_item',  args = [('obj_name',char.alt_hand_l.item.name)], icon = 'PROPERTIES', text = '')
        row.prop(loadout.alt_hand_r,'flag')

def display_loadouts(layout, char) -> None:
    loadouts = char.loadouts
    header = layout.row(align=True)
    icon_style = 'TRIA_DOWN' if not char.loadouts_collapsed else 'TRIA_RIGHT'
    header.prop(char, "loadouts_collapsed", text="Loadouts", icon=icon_style, emboss=False)
    if not char.loadouts_collapsed:
        if loadouts:
            for loadout in loadouts:
                display_loadout(layout.box(),loadout)
        else:
            row = layout.row()
            row.alignment = 'CENTER'
            row.label(text = f'Character has no loadouts')

def display_kb_spells(layout, thaum) -> None:
    kb_spells = thaum.keybound_spells
    header = layout.row(align=True)
    icon_style = 'TRIA_DOWN' if not thaum.kb_spells_collapsed else 'TRIA_RIGHT'
    header.prop(thaum, "kb_spells_collapsed", text="Keybound Spells", icon=icon_style, emboss=False)
    if not thaum.kb_spells_collapsed:
        for kb_spell in thaum.keybound_spells: 
            cf.display_props_on_new_row(layout,kb_spell,['name','is_active'])

def display_spells(layout, thaum) -> None:
    spells = thaum.spells
    header = layout.row(align=True)
    icon_style = 'TRIA_DOWN' if not thaum.spells_collapsed else 'TRIA_RIGHT'
    header.prop(thaum, "spells_collapsed", text="Spells", icon=icon_style, emboss=False)
    if not thaum.spells_collapsed:
        if spells:
            for spell in spells:
                cf.display_props_on_new_row(layout,spell,['name','xp','empowered','no_prereqs'])
        else:
            row = layout.row()
            row.alignment = 'CENTER'
            row.label(text = f'Character knows no spells')

def display_thaumaturgy(layout, char) -> None:
    thaum = char.thaumaturgy
    header = layout.row(align=True)
    icon_style = 'TRIA_DOWN' if not char.thaumaturgy_collapsed else 'TRIA_RIGHT'
    header.prop(char, "thaumaturgy_collapsed", text="Thaumaturgy", icon=icon_style, emboss=False)
    if not char.thaumaturgy_collapsed:
        cf.display_props_on_new_row(layout,thaum,['version','potential'])
        display_kb_spells(layout.box(),thaum)
        display_spells(layout.box(),thaum)

class OBJECT_OT_edit_x_char(bpy.types.Operator):
    bl_idname = 'exanima.edit_x_char'
    bl_label = "Edit Exanima Char"
    bl_options = {'REGISTER', 'UNDO'}
    obj_name: bpy.props.StringProperty()
    def draw(self, context):
        layout = self.layout
        i_obj = bpy.data.objects.get(self.obj_name) if self.obj_name else context.active_object
        if not i_obj: return
        obj = cf.get_root_in_hierarchy(i_obj)
        char = obj.x_char
        row = layout.row()
        row.alignment = 'CENTER'
        row.label(text = f'Inspecting Char {obj.name}')
        cf.display_props_on_new_row(layout,char,['state','version'])
        cf.display_props_on_new_row(layout,char,['name','surname'])
        cf.display_props_on_new_row(layout,char,['muscle','fat','height','age'])
        cf.display_props_on_new_row(layout,char,['skin_x','skin_y'])
        cf.display_props_on_new_row(layout,char,['hair_style','hair_x','hair_y','hair_suppress','hair_null'])
        cf.display_props_on_new_row(layout,char,['face_style0','face_style1'])
        cf.display_props_on_new_row(layout,char,['voice','voice_pitch'])
        cf.display_props_on_new_row(layout,char,['gender','hair_flags','loadout','last_locale']) #gender,race,hair_flags,loadout
        row = layout.row()
        row.prop(char.hand_r,'item', text = 'hand_r')
        if char.hand_r.item: cf.add_op_to_row(row = row, op_idname = 'exanima.edit_x_item',  args = [('obj_name',char.hand_r.item.name)], icon = 'PROPERTIES', text = '')
        row.prop(char.hand_r,'flag')
        row.prop(char.hand_l,'item', text = 'hand_l')
        if char.hand_l.item: cf.add_op_to_row(row = row, op_idname = 'exanima.edit_x_item',  args = [('obj_name',char.hand_l.item.name)], icon = 'PROPERTIES', text = '')
        row.prop(char.hand_l,'flag')
        row = layout.row()
        row.prop(char.alt_hand_r,'item', text = 'alt_hand_r')
        if char.alt_hand_r.item: cf.add_op_to_row(row = row, op_idname = 'exanima.edit_x_item',  args = [('obj_name',char.alt_hand_r.item.name)], icon = 'PROPERTIES', text = '')
        row.prop(char.alt_hand_r,'flag')
        row.prop(char.alt_hand_l,'item', text = 'alt_hand_l')
        if char.alt_hand_l.item: cf.add_op_to_row(row = row, op_idname = 'exanima.edit_x_item',  args = [('obj_name',char.alt_hand_l.item.name)], icon = 'PROPERTIES', text = '')
        row.prop(char.alt_hand_r,'flag')
        display_apparel(layout.box(), char)
        layout.row().prop(char,'zombification')
        cf.display_props_on_new_row(layout,char,['stamina','health','focus_stamina','focus_health'])
        cf.display_props_on_new_row(layout,char,['combat_skill','undead_voice'])
        cf.display_props_on_new_row(layout,char,['trustfulness','bravery','ben_ach','neuroticism'])
        cf.display_props_on_new_row(layout,char,['rng_seed','raw_xp','null'])
        display_skills(layout.box(),char)
        display_inventory(layout.box(),char)
        if char.old_roles: display_old_roles(layout.box(),char)
        else: display_roles(layout.box(),char)
        display_relations(layout.box(),char.global_relations, 'Global Relations') #Global rels
        display_locale_relations(layout.box(),char)
        display_conditions(layout.box(),char)
        display_thaumaturgy(layout.box(),char)
    def execute(self, context):
        return {'FINISHED'}
    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=1200)

classes = [OBJECT_OT_edit_x_char]

def edit_x_char_func(self, context):
    self.layout.separator()
    self.layout.operator(OBJECT_OT_edit_x_char.bl_idname, icon='OBJECT_DATA')

def register():
    for cls in classes: bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_object.append(edit_x_char_func)

def unregister():
    for cls in classes: bpy.utils.unregister_class(cls)
    bpy.types.VIEW3D_MT_object.remove(edit_x_char_func)