from app.data.item_components import ItemComponent
from app.data.components import Type

from app.utilities import utils
from app.engine import action, combat_calcs, image_mods, engine

class Effective(ItemComponent):
    nid = 'effective'
    desc = 'Item does extra damage against certain units'
    # requires = ['damage']
    paired_with = ('effective_tag',)
    tag = 'extra'

    expose = Type.Int
    value = 0

    def init(self, item):
        item.data['effective'] = self.value

class EffectiveTag(ItemComponent):
    nid = 'effective_tag'
    desc = "Item does extra damage against units with these tags"
    # requires = ['damage']
    paired_with = ('effective',)
    tag = 'extra'

    expose = (Type.List, Type.Tag)
    value = []

    def _check_negate(self, target) -> bool:  
        # Returns whether it DOES negate the effectiveness
        # Still need to check negation (Fili Shield, etc.)
        if any(skill.negate for skill in target.skills):
            return True
        for skill in target.skills:
            # Do the tags match?
            if skill.negate_tags and skill.negate_tags.value and \
                    any(tag in self.value for tag in skill.negate_tags.value):
                return True
        # No negation, so proceed with effective damage
        return False

    def dynamic_damage(self, unit, item, target, mode, attack_info, base_value) -> int:
        if any(tag in target.tags for tag in self.value):
            if self._check_negate(target):
                return 0
            return item.data.get('effective', 0)
        return 0

    def item_icon_mod(self, unit, item, target, sprite):
        if any(tag in target.tags for tag in self.value):
            if self._check_negate(target):
                return sprite
            sprite = image_mods.make_white(sprite.convert_alpha(), abs(250 - engine.get_time()%500)/250)
        return sprite

    def danger(self, unit, item, target) -> bool:
        if self._check_negate(target):
            return False
        return any(tag in target.tags for tag in self.value)

class Brave(ItemComponent):
    nid = 'brave'
    desc = "Item multi-attacks"
    tag = 'extra'

    def dynamic_multiattacks(self, unit, item, target, mode, attack_info, base_value):
        return 1

class BraveOnAttack(ItemComponent):
    nid = 'brave_on_attack'
    desc = "Item multi-attacks only when attacking"
    tag = 'extra'

    def dynamic_multiattacks(self, unit, item, target, mode, attack_info, base_value):
        return 1 if mode == 'attack' else 0

class Lifelink(ItemComponent):
    nid = 'lifelink'
    desc = "Heals user %% of damage dealt"
    # requires = ['damage']
    tag = 'extra'

    expose = Type.Float
    value = 0.5

    def after_hit(self, actions, playback, unit, item, target, mode, attack_info):
        total_damage_dealt = 0
        playbacks = [p for p in playback if p[0] in ('damage_hit', 'damage_crit') and p[1] == unit]
        for p in playbacks:
            total_damage_dealt += p[5]

        damage = utils.clamp(total_damage_dealt, 0, target.get_hp())
        true_damage = int(damage * self.value)
        actions.append(action.ChangeHP(unit, true_damage))

        playback.append(('heal_hit', unit, item, unit, true_damage, true_damage))

class DamageOnMiss(ItemComponent):
    nid = 'damage_on_miss'
    desc = "Does %% damage even on miss"
    # requires = ['damage']
    tag = 'extra'

    expose = Type.Float
    value = 0.5

    def on_miss(self, actions, playback, unit, item, target, target_pos, mode, attack_info):
        damage = combat_calcs.compute_damage(unit, target, item, target.get_weapon(), mode)
        damage = int(damage * self.value)

        true_damage = min(damage, target.get_hp())
        actions.append(action.ChangeHP(target, -damage))

        # For animation
        playback.append(('damage_hit', unit, item, target, damage, true_damage))
        if true_damage == 0:
            playback.append(('hit_sound', 'No Damage'))
            playback.append(('hit_anim', 'MapNoDamage', target))

class Eclipse(ItemComponent):
    nid = 'Eclipse'
    desc = "Target loses half current HP on hit"
    tag = 'extra'

    def on_hit(self, actions, playback, unit, item, target, target_pos, mode, attack_info):
        true_damage = damage = target.get_hp()//2
        actions.append(action.ChangeHP(target, -damage))

        # For animation
        playback.append(('damage_hit', unit, item, target, damage, true_damage))
        if damage == 0:
            playback.append(('hit_sound', 'No Damage'))
            playback.append(('hit_anim', 'MapNoDamage', target))

class NoDouble(ItemComponent):
    nid = 'no_double'
    desc = "Item cannot double"
    tag = 'extra'

    def can_double(self, unit, item):
        return False

class CannotCounter(ItemComponent):
    nid = 'cannot_counter'
    desc = "Item cannot counter"
    tag = 'extra'

    def can_counter(self, unit, item):
        return False

class CannotBeCountered(ItemComponent):
    nid = 'cannot_be_countered'
    desc = "Item cannot be countered"
    tag = 'extra'

    def can_be_countered(self, unit, item):
        return False

class IgnoreWeaponAdvantage(ItemComponent):
    nid = 'ignore_weapon_advantage'
    desc = "Item will not be affected by the weapon triangle"
    tag = 'extra'

    def ignore_weapon_advantage(self, unit, item):
        return True

class Reaver(ItemComponent):
    nid = 'reaver'
    desc = "Item will have double reverse weapon triangle"
    tag = 'extra'

    def modify_weapon_triangle(self, unit, item):
        return -2

class DoubleTriangle(ItemComponent):
    nid = 'double_triangle'
    desc = "Item will have double weapon triangle"
    tag = 'extra'

    def modify_weapon_triangle(self, unit, item):
        return 2

class StatusOnEquip(ItemComponent):
    nid = 'status_on_equip'
    desc = "Item gives status while equipped"
    tag = 'extra'

    expose = Type.Skill  # Nid

    def on_equip_item(self, unit, item):
        if self.value not in [skill.nid for skill in unit.skills]:
            act = action.AddSkill(unit, self.value)
            action.do(act)

    def on_unequip_item(self, unit, item):
        action.do(action.RemoveSkill(unit, self.value))

class StatusOnHold(ItemComponent):
    nid = 'status_on_hold'
    desc = "Item gives status while in unit's inventory"
    tag = 'extra'

    expose = Type.Skill  # Nid

    def on_add_item(self, unit, item):
        action.do(action.AddSkill(unit, self.value))

    def on_remove_item(self, unit, item):
        action.do(action.RemoveSkill(unit, self.value))

class GainManaAfterCombat(ItemComponent):
    nid = 'gain_mana_after_combat'
    desc = "Item grants X Mana at the end of combat solved dynamically"
    tag = 'extra'
    author = 'KD'

    expose = Type.String

    def end_combat(self, playback, unit, item, target, mode):
        from app.engine import evaluate
        try:
            if target:
                mana_gain = int(evaluate.evaluate(self.value, unit, target, position=unit.position))
                action.do(action.ChangeMana(unit, mana_gain))
        except Exception as e:
            print("Could not evaluate %s (%s)" % (self.value, e))
            return True
