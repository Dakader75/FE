from app.data.database import DB
from app.data.difficulty_modes import GrowthOption
from app.engine import item_funcs, static_random
from app.engine.game_state import game
from app.utilities import utils

import logging

def get_leveling_method(unit, custom_method=None) -> str:
    if custom_method:
        method = custom_method
    if unit.team == 'player':
        method = game.current_mode.growths
    else:
        method = DB.constants.value('enemy_leveling')
        if method == 'Match':
            method = game.current_mode.growths
    return method

def get_next_level_up(unit, custom_method=None) -> dict:
    method = get_leveling_method(unit, custom_method)

    stat_changes = {nid: 0 for nid in DB.stats.keys()}
    klass = DB.classes.get(unit.klass)
    difficulty_growth_bonus = game.mode.get_growth_bonus(unit)
    if method == 'BEXP':
        _rd_bexp_levelup(unit, unit.get_internal_level(), klass, stat_changes)
    else:
        level = unit.get_internal_level()
        rng = static_random.get_levelup(unit.nid, level)
        for nid in DB.stats.keys():
            growth = unit.growths[nid] + unit.growth_bonus(nid) + klass.growth_bonus.get(nid, 0) + difficulty_growth_bonus.get(nid, 0)

            if method == GrowthOption.FIXED:
                if growth > 0:
                    stat_changes[nid] = (unit.growth_points[nid] + growth) // 100
                    unit.growth_points[nid] = (unit.growth_points[nid] + growth) % 100
                elif growth < 0:
                    stat_changes[nid] = (-unit.growth_points[nid] + growth) // 100
                    unit.growth_points[nid] = (unit.growth_points[nid] - growth) % 100

            elif method == GrowthOption.RANDOM:
                stat_changes[nid] += _random_levelup(rng, unit, level, growth)
            elif method == GrowthOption.DYNAMIC:
                _dynamic_levelup(rng, unit, level, stat_changes, unit.growth_points, nid, growth)

            stat_changes[nid] = utils.clamp(stat_changes[nid], -unit.stats[nid], klass.max_stats.get(nid, 30) - unit.stats[nid])

    return stat_changes

def _random_levelup(rng, unit, level, growth_rate):
    counter = 0
    if growth_rate > 0:
        while growth_rate > 0:
            counter += 1 if rng.randint(0, 99) < growth_rate else 0
            growth_rate -= 100
    elif growth_rate < 0:
        growth_rate = -growth_rate
        while growth_rate > 0:
            counter -= 1 if rng.randint(0, 99) < growth_rate else 0
            growth_rate -= 100
    return counter

def _dynamic_levelup(rng, unit, level, stats, growth_points, growth_nid, growth_rate):
    variance = 10
    if growth_rate > 0:
        start_growth = growth_rate + growth_points[growth_nid]
        if start_growth <= 0:
            growth_points[growth_nid] += growth_rate / 5.
        else:
            free_levels = growth_rate // 100
            stats[growth_nid] += free_levels
            new_growth = growth_rate % 100
            start_growth = new_growth + growth_points[growth_nid]
            if rng.randint(0, 99) < int(start_growth):
                stats[growth_nid] += 1
                growth_points[growth_nid] -= (100 - new_growth) / variance
            else:
                growth_points[growth_nid] += new_growth/variance
    elif growth_rate < 0:
        growth_rate = -growth_rate
        start_growth = growth_rate + growth_points[growth_nid]
        if start_growth <= 0:
            growth_points[growth_nid] += growth_rate / 5.
        else:
            free_levels = growth_rate // 100
            stats[growth_nid] -= free_levels
            new_growth = growth_rate % 100
            start_growth = new_growth + growth_points[growth_nid]
            if rng.randint(0, 99) < int(start_growth):
                stats[growth_nid] -= 1
                growth_points[growth_nid] -= (100 - new_growth) / variance
            else:
                growth_points[growth_nid] += new_growth/variance

def _rd_bexp_levelup(unit, level, klass, stat_changes):
    growths: list = []
    for idx, stat in enumerate(DB.stats):
        nid = stat.nid
        difficulty_growth_bonus = game.mode.get_growth_bonus(unit)
        growth = unit.growths[nid] + unit.growth_bonus(nid) + klass.growth_bonus.get(nid, 0) + difficulty_growth_bonus.get(nid, 0)
        if unit.stats[nid] < klass.max_stats.get(nid, 30) and unit.growths[nid] != 0:
            growths.append(max(growth, 0))
        else:  # Cannot increase this one at all
            growths.append(0)
    rng = static_random.get_levelup(unit.nid, level)
    num_choices = 3

    for i in range(num_choices):
        if sum(growths) <= 0:
            break
        choice = static_random.weighted_choice(growths, rng)
        nid = [stat.nid for stat in DB.stats][choice]
        stat_changes[nid] += 1
        growths[choice] = max(0, growths[choice] - 100)
        if unit.stats[nid] + stat_changes[nid] >= klass.max_stats.get(nid, 30):
            growths[choice] = 0

    return stat_changes

def auto_level(unit, num_levels, starting_level=1, difficulty_growths=False):
    """
    Primarily for generics
    """
    method = get_leveling_method(unit)
    difficulty_growth_bonus = game.mode.get_growth_bonus(unit)

    if method == GrowthOption.FIXED:
        for growth_nid, growth_value in unit.growths.items():
            if difficulty_growths:
                growth_sum = difficulty_growth_bonus.get(growth_nid, 0) * num_levels
            else:
                growth_sum = (growth_value + unit.growth_bonus(growth_nid) + difficulty_growth_bonus.get(growth_nid, 0)) * num_levels
            if growth_value < 0:
                unit.stats[growth_nid] += (growth_sum - unit.growth_points[growth_nid]) // 100
                unit.growth_points[growth_nid] = -(growth_sum - unit.growth_points[growth_nid]) % 100
            else:
                unit.stats[growth_nid] += (growth_sum + unit.growth_points[growth_nid]) // 100
                unit.growth_points[growth_nid] = (growth_sum + unit.growth_points[growth_nid]) % 100

    elif method == GrowthOption.RANDOM:
        for n in range(num_levels):
            level = starting_level + n
            rng = static_random.get_levelup(unit.nid, level)
            for growth_nid, growth_value in unit.growths.items():
                if difficulty_growths:
                    growth_rate = difficulty_growth_bonus.get(growth_nid, 0)
                else:
                    growth_rate = growth_value + unit.growth_bonus(growth_nid) + difficulty_growth_bonus.get(growth_nid, 0)
                unit.stats[growth_nid] += _random_levelup(rng, unit, level, growth_rate)

    elif method == GrowthOption.DYNAMIC:
        for n in range(num_levels):
            level = starting_level + n
            rng = static_random.get_levelup(unit.nid, level)
            for growth_nid, growth_value in unit.growths.items():
                if difficulty_growths:
                    growth_rate = difficulty_growth_bonus.get(growth_nid, 0)
                else:
                    growth_rate = growth_value + unit.growth_bonus(growth_nid) + difficulty_growth_bonus.get(growth_nid, 0)
                _dynamic_levelup(rng, unit, level, unit.stats, unit.growth_points, growth_nid, growth_rate)

    # Make sure we don't exceed max
    klass = DB.classes.get(unit.klass)
    unit.stats = {k: utils.clamp(v, 0, klass.max_stats.get(k, 30)) for (k, v) in unit.stats.items()}
    unit.set_hp(1000)  # Go back to full hp
    unit.set_mana(1000)  # Go back to full mana

def apply_stat_changes(unit, stat_changes: dict):
    """
    Assumes stat changes are valid!
    """
    old_max_hp = unit.get_max_hp()
    old_max_mana = unit.get_max_mana()

    # Actually apply changes
    for nid, value in stat_changes.items():
        unit.stats[nid] += value

    current_max_hp = unit.get_max_hp()
    current_max_mana = unit.get_max_mana()

    if current_max_hp > old_max_hp:
        unit.set_hp(current_max_hp - old_max_hp + unit.get_hp())
    if current_max_mana > old_max_mana:
        unit.set_mana(current_max_mana - old_max_mana + unit.get_mana())

def get_starting_skills(unit) -> list:
    # Class skills
    klass_obj = DB.classes.get(unit.klass)
    current_klass = klass_obj
    all_klasses = [klass_obj]
    counter = 5
    while current_klass and current_klass.tier > 1 and counter > 0:
        counter -= 1  # Prevent infinite loops
        if current_klass.promotes_from:
            current_klass = DB.classes.get(current_klass.promotes_from)
            all_klasses.append(current_klass)
        else:
            break
    all_klasses.reverse()

    skills_to_add = []
    feats = DB.skills.get_feats()
    current_skills = [skill.nid for skill in unit.skills]
    for idx, klass in enumerate(all_klasses):
        for learned_skill in klass.learned_skills:
            if (learned_skill[0] <= unit.level or klass != klass_obj) and \
                    learned_skill[1] not in current_skills and \
                    learned_skill[1] not in skills_to_add:
                if learned_skill[1] == 'Feat':
                    if DB.constants.value('generic_feats'):
                        my_feats = [feat for feat in feats if feat.nid not in current_skills and feat.nid not in skills_to_add]
                        random_number = static_random.get_growth() % len(my_feats)
                        new_skill = my_feats[random_number]
                        skills_to_add.append(new_skill.nid)
                else:
                    skills_to_add.append(learned_skill[1])

    klass_skills = item_funcs.create_skills(unit, skills_to_add)
    return klass_skills

def get_personal_skills(unit, prefab):
    skills_to_add = []
    current_skills = [skill.nid for skill in unit.skills]
    for learned_skill in prefab.learned_skills:
        if learned_skill[0] <= unit.level and learned_skill[1] not in current_skills:
            skills_to_add.append(learned_skill[1])

    personal_skills = item_funcs.create_skills(unit, skills_to_add)
    return personal_skills

def get_global_skills(unit):
    skills_to_add = []
    current_skills = [skill.nid for skill in unit.skills]
    for skill_prefab in DB.skills:
        if skill_prefab.components.get('global') and skill_prefab.nid not in current_skills:
            skills_to_add.append(skill_prefab.nid)

    global_skills = item_funcs.create_skills(unit, skills_to_add)
    return global_skills

def can_unlock(unit, region) -> bool:
    from app.engine import item_system, skill_system
    if skill_system.can_unlock(unit, region):
        return True
    for item in item_funcs.get_all_items(unit):
        if item_funcs.available(unit, item) and \
                item_system.can_unlock(unit, item, region):
            return True
    return False

def check_focus(unit, limit=3) -> int:
    from app.engine import skill_system
    from app.engine.game_state import game
    counter = 0
    if unit.position:
        for other in game.units:
            if other.position and \
                    unit is not other and \
                    skill_system.check_ally(unit, other) and \
                    utils.calculate_distance(unit.position, other.position) <= limit:
                counter += 1
    return counter

def check_flanked(unit) -> bool:
    from app.engine import skill_system
    from app.engine.game_state import game
    if unit.position:
        up = game.board.get_unit((unit.position[0], unit.position[1] - 1))
        left = game.board.get_unit((unit.position[0] - 1, unit.position[1]))
        right = game.board.get_unit((unit.position[0] + 1, unit.position[1]))
        down = game.board.get_unit((unit.position[0], unit.position[1] + 1))
        if up and down and skill_system.check_enemy(unit, up) and skill_system.check_enemy(unit, down):
            return True
        if left and right and skill_system.check_enemy(unit, left) and skill_system.check_enemy(unit, right):
            return True
    return False

check_flanking = check_flanked
