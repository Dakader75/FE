# Takes in unit, returns False if not present
# All default hooks are exclusive
formula = ('damage_formula', 'resist_formula', 'accuracy_formula', 'avoid_formula',
           'crit_accuracy_formula', 'crit_avoid_formula', 'attack_speed_formula', 'defense_speed_formula')
default_behaviours = (
    'pass_through', 'vantage', 'ignore_terrain', 'crit_anyway',
    'ignore_region_status', 'no_double', 'def_double', 'alternate_splash',
    'ignore_rescue_penalty', 'ignore_forced_movement', 'distant_counter',
    'ignore_fatigue')
# Takes in unit, returns default value
exclusive_behaviours = ('can_select', 'movement_type', 'sight_range', 'empower_splash', 'num_items_offset', 'num_accessories_offset', 'change_variant', 'change_animation', 'change_ai', 'witch_warp')

exclusive_behaviours += formula
# Takes in unit and item, returns default value
item_behaviours = ('modify_buy_price', 'modify_sell_price', 'limit_maximum_range', 'modify_maximum_range', 'wexp_usable_skill')
# Takes in unit and target, returns default value
targeted_behaviours = ('check_ally', 'check_enemy', 'can_trade', 'exp_multiplier', 'enemy_exp_multiplier', 'wexp_multiplier', 'enemy_wexp_multiplier', 'steal_icon', 'has_canto', 'empower_heal')
# Takes in unit, item returns bonus
modify_hooks = (
    'modify_damage', 'modify_resist', 'modify_accuracy', 'modify_avoid',
    'modify_crit_accuracy', 'modify_crit_avoid', 'modify_attack_speed',
    'modify_defense_speed')
# Takes in unit, item, target, mode, attack_info, base_value, returns bonus
dynamic_hooks = ('dynamic_damage', 'dynamic_resist', 'dynamic_accuracy', 'dynamic_avoid',
                 'dynamic_crit_accuracy', 'dynamic_crit_avoid', 'dynamic_attack_speed', 'dynamic_defense_speed',
                 'dynamic_multiattacks')
# Takes in unit, item, target, mode, attack_info, base_value, returns bonus
multiply_hooks = ('damage_multiplier', 'resist_multiplier', 'crit_multiplier')

# Takes in unit
simple_event_hooks = ('on_death',)
# Takes in playback, unit, item, target, mode
combat_event_hooks = ('start_combat', 'cleanup_combat', 'end_combat', 'pre_combat', 'post_combat', 'test_on', 'test_off')
# Takes in actions, playback, unit, item, target, mode, attack_info
subcombat_event_hooks = ('after_hit', 'after_take_hit', 'start_sub_combat', 'end_sub_combat')
# Takes in unit, item
item_event_hooks = ('on_add_item', 'on_remove_item', 'on_equip_item', 'on_unequip_item')


def compile_skill_system():
    import os
    dir_path = os.path.dirname(os.path.realpath(__file__))
    compiled_skill_system = open(os.path.join(dir_path, '..', 'skill_system.py'), 'w')
    skill_system_base = open(os.path.join(dir_path, 'skill_system_base.py'), 'r')
    warning_msg = open(os.path.join(dir_path, 'warning_msg'), 'r')

    # write warning msg
    for line in warning_msg.readlines():
        compiled_skill_system.write(line)

    # copy skill system base
    for line in skill_system_base.readlines():
        compiled_skill_system.write(line)

    # compile skill system
    for behaviour in default_behaviours:
        func = """
def %s(unit):
    for skill in unit.skills:
        for component in skill.components:
            if component.defines('%s'):
                if component.ignore_conditional or condition(skill, unit):
                    return component.%s(unit)
    return False""" \
            % (behaviour, behaviour, behaviour)
        compiled_skill_system.write(func)
        compiled_skill_system.write('\n')

    for behaviour in exclusive_behaviours:
        func = """
def %s(unit):
    for skill in unit.skills:
        for component in skill.components:
            if component.defines('%s'):
                if component.ignore_conditional or condition(skill, unit):
                    return component.%s(unit)
    return Defaults.%s(unit)""" \
            % (behaviour, behaviour, behaviour, behaviour)
        compiled_skill_system.write(func)
        compiled_skill_system.write('\n')

    for behaviour in targeted_behaviours:
        func = """
def %s(unit1, unit2):
    for skill in unit1.skills:
        for component in skill.components:
            if component.defines('%s'):
                if component.ignore_conditional or condition(skill, unit1):
                    return component.%s(unit1, unit2)
    return Defaults.%s(unit1, unit2)""" \
            % (behaviour, behaviour, behaviour, behaviour)
        compiled_skill_system.write(func)
        compiled_skill_system.write('\n')

    for behaviour in item_behaviours:
        func = """
def %s(unit, item):
    for skill in unit.skills:
        for component in skill.components:
            if component.defines('%s'):
                if component.ignore_conditional or condition(skill, unit):
                    return component.%s(unit, item)
    return Defaults.%s(unit, item)""" \
            % (behaviour, behaviour, behaviour, behaviour)
        compiled_skill_system.write(func)
        compiled_skill_system.write('\n')

    for hook in modify_hooks:
        func = """
def %s(unit, item):
    val = 0
    for skill in unit.skills:
        for component in skill.components:
            if component.defines('%s'):
                if component.ignore_conditional or condition(skill, unit):
                    val += component.%s(unit, item)
    return val""" \
            % (hook, hook, hook)
        compiled_skill_system.write(func)
        compiled_skill_system.write('\n')

    for hook in dynamic_hooks:
        func = """
def %s(unit, item, target, mode, attack_info, base_value):
    val = 0
    for skill in unit.skills:
        for component in skill.components:
            if component.defines('%s'):
                if component.ignore_conditional or condition(skill, unit):
                    val += component.%s(unit, item, target, mode, attack_info, base_value)
    return val""" \
            % (hook, hook, hook)
        compiled_skill_system.write(func)
        compiled_skill_system.write('\n')

    for hook in multiply_hooks:
        func = """
def %s(unit, item, target, mode, attack_info, base_value):
    val = 1
    for skill in unit.skills:
        for component in skill.components:
            if component.defines('%s'):
                if component.ignore_conditional or condition(skill, unit):
                    val *= component.%s(unit, item, target, mode, attack_info, base_value)
    return val""" \
            % (hook, hook, hook)
        compiled_skill_system.write(func)
        compiled_skill_system.write('\n')

    for hook in simple_event_hooks:
        func = """
def %s(unit):
    for skill in unit.skills:
        for component in skill.components:
            if component.defines('%s'):
                if component.ignore_conditional or condition(skill, unit):
                    component.%s(unit)""" \
            % (hook, hook, hook)
        compiled_skill_system.write(func)
        compiled_skill_system.write('\n')

    for hook in combat_event_hooks:
        func = """
def %s(playback, unit, item, target, mode):
    for skill in unit.skills:
        for component in skill.components:
            if component.defines('%s'):
                if component.ignore_conditional or condition(skill, unit):
                    component.%s(playback, unit, item, target, mode)""" \
            % (hook, hook, hook)
        compiled_skill_system.write(func)
        compiled_skill_system.write('\n')

    for hook in subcombat_event_hooks:
        func = """
def %s(actions, playback, unit, item, target, mode, attack_info):
    for skill in unit.skills:
        for component in skill.components:
            if component.defines('%s'):
                component.%s(actions, playback, unit, item, target, mode, attack_info)""" \
            % (hook, hook, hook)
        compiled_skill_system.write(func)
        compiled_skill_system.write('\n')

    for hook in item_event_hooks:
        func = """
def %s(unit, item):
    for skill in unit.skills:
        for component in skill.components:
            if component.defines('%s'):
                component.%s(unit, item)""" \
            % (hook, hook, hook)
        compiled_skill_system.write(func)
        compiled_skill_system.write('\n')
