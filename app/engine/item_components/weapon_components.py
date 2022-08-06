from app.utilities import utils
from app.data.database import DB

from app.data.item_components import ItemComponent
from app.data.components import Type

from app.engine import action, combat_calcs, equations, item_system, skill_system
from app.engine.game_state import game

class WeaponType(ItemComponent):
    nid = 'weapon_type'
    desc = "Item has a weapon type and can only be used by certain classes"
    tag = 'weapon'

    expose = Type.WeaponType

    def weapon_type(self, unit, item):
        return self.value

    def available(self, unit, item) -> bool:
        klass = DB.classes.get(unit.klass)
        wexp_gain = klass.wexp_gain.get(self.value)
        if wexp_gain:
            klass_usable = wexp_gain.usable or skill_system.wexp_usable_skill(unit, item)
            return unit.wexp[self.value] > 0 and klass_usable
        return False

class WeaponRank(ItemComponent):
    nid = 'weapon_rank'
    desc = "Item has a weapon rank and can only be used by units with high enough rank"
    requires = ['weapon_type']
    tag = 'weapon'

    expose = Type.WeaponRank

    def weapon_rank(self, unit, item):
        return self.value

    def available(self, unit, item):
        required_wexp = DB.weapon_ranks.get(self.value).requirement
        weapon_type = item_system.weapon_type(unit, item)
        if weapon_type:
            return unit.wexp.get(weapon_type) >= required_wexp
        else:  # If no weapon type, then always available
            return True

class Magic(ItemComponent):
    nid = 'magic'
    desc = 'Makes Item use magic damage formula'
    tag = 'weapon'

    def damage_formula(self, unit, item):
        return 'MAGIC_DAMAGE'

    def resist_formula(self, unit, item):
        return 'MAGIC_DEFENSE'

class MagicAtRange(ItemComponent):
    nid = 'magic_at_range'
    desc = 'Makes Item use magic damage formula at range'
    tag = 'weapon'

    def dynamic_damage(self, unit, item, target, mode, attack_info, base_value) -> int:
        running_damage = 0
        if unit.position and target and target.position:
            dist = utils.calculate_distance(unit.position, target.position)
            if dist > 1:
                normal_damage = equations.parser.get('DAMAGE', unit)
                new_damage = equations.parser.get('MAGIC_DAMAGE', unit)
                normal_resist = equations.parser.get('DEFENSE', target)
                new_resist = equations.parser.get('MAGIC_DEFENSE', target)
                running_damage -= normal_damage
                running_damage += new_damage
                running_damage += normal_resist
                running_damage -= new_resist
        return running_damage

class Hit(ItemComponent):
    nid = 'hit'
    desc = "Item has a chance to hit. If left off, item will always hit."
    tag = 'weapon'

    expose = Type.Int
    value = 75

    def hit(self, unit, item):
        return self.value

class Damage(ItemComponent):
    nid = 'damage'
    desc = "Item does damage on hit"
    tag = 'weapon'

    expose = Type.Int
    value = 0

    def damage(self, unit, item):
        return self.value

    def target_restrict(self, unit, item, def_pos, splash) -> bool:
        # Restricts target based on whether any unit is an enemy
        defender = game.board.get_unit(def_pos)
        if defender and skill_system.check_enemy(unit, defender):
            return True
        for s_pos in splash:
            s = game.board.get_unit(s_pos)
            if s and skill_system.check_enemy(unit, s):
                return True
        return False

    def on_hit(self, actions, playback, unit, item, target, target_pos, mode, attack_info):
        playback_nids = [_[0] for _ in playback]
        if 'attacker_partner_phase' in playback_nids or 'defender_partner_phase' in playback_nids:
            damage = combat_calcs.compute_assist_damage(unit, target, item, target.get_weapon(), mode, attack_info)
        else:
            damage = combat_calcs.compute_damage(unit, target, item, target.get_weapon(), mode, attack_info)

        true_damage = min(damage, target.get_hp())
        actions.append(action.ChangeHP(target, -damage))

        # For animation
        playback.append(('damage_hit', unit, item, target, damage, true_damage))
        if damage == 0:
            playback.append(('hit_sound', 'No Damage'))
            playback.append(('hit_anim', 'MapNoDamage', target))

    def on_glancing_hit(self, actions, playback, unit, item, target, target_pos, mode, attack_info):
        playback_nids = [_[0] for _ in playback]
        if 'attacker_partner_phase' in playback_nids or 'defender_partner_phase' in playback_nids:
            damage = combat_calcs.compute_assist_damage(unit, target, item, target.get_weapon(), mode, attack_info)
        else:
            damage = combat_calcs.compute_damage(unit, target, item, target.get_weapon(), mode, attack_info)
        damage = damage // 2  # Because glancing hit

        true_damage = min(damage, target.get_hp())
        actions.append(action.ChangeHP(target, -damage))

        # For animation
        playback.append(('damage_hit', unit, item, target, damage, true_damage))
        if damage == 0:
            playback.append(('hit_anim', 'MapNoDamage', target))

    def on_crit(self, actions, playback, unit, item, target, target_pos, mode, attack_info):
        playback_nids = [_[0] for _ in playback]
        if 'attacker_partner_phase' in playback_nids or 'defender_partner_phase' in playback_nids:
            damage = combat_calcs.compute_assist_damage(unit, target, item, target.get_weapon(), mode, attack_info, crit=True)
        else:
            damage = combat_calcs.compute_damage(unit, target, item, target.get_weapon(), mode, attack_info, crit=True)

        true_damage = min(damage, target.get_hp())
        actions.append(action.ChangeHP(target, -damage))

        playback.append(('damage_crit', unit, item, target, damage, true_damage))
        if damage == 0:
            playback.append(('hit_sound', 'No Damage'))
            playback.append(('hit_anim', 'MapNoDamage', target))

class Crit(ItemComponent):
    nid = 'crit'
    desc = "Item has a chance to crit. If left off, item cannot crit."
    tag = 'weapon'

    expose = Type.Int
    value = 0

    def crit(self, unit, item):
        return self.value

class Weight(ItemComponent):
    nid = 'weight'
    desc = "Item has a weight."
    tag = 'weapon'

    expose = Type.Int
    value = 0

    def modify_attack_speed(self, unit, item):
        return -1 * max(0, self.value - equations.parser.constitution(unit))

    def modify_defense_speed(self, unit, item):
        return -1 * max(0, self.value - equations.parser.constitution(unit))

class Unwieldy(ItemComponent):
    nid = 'Unwieldy'
    desc = "Item lowers unit's defense by X"
    tag = 'weapon'

    expose = Type.Int
    value = 0

    def modify_defense(self, unit, item):
        return -1 * self.value

class StatChange(ItemComponent):
    nid = 'stat_change'
    desc = "Gives stat bonuses"
    tag = 'weapon'

    expose = (Type.Dict, Type.Stat)
    value = []

    def stat_change(self, unit):
        return {stat[0]: stat[1] for stat in self.value}
