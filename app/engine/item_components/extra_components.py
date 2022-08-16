from app.data.item_components import ItemComponent, ItemTags
from app.data.components import Type

from app.utilities import utils
from app.engine import action, combat_calcs, image_mods, engine, item_system, skill_system
from app.engine.combat import playback as pb

class Effective(ItemComponent):
    nid = 'effective'
    desc = 'If this item is effective against an enemy its damage value will be increased by the integer chosen here instead. This is not a multiplier, but an addition.'
    # requires = ['damage']
    paired_with = ('effective_tag',)
    tag = ItemTags.EXTRA

    expose = Type.Int
    value = 0

    def init(self, item):
        item.data['effective'] = self.value

class EffectiveTag(ItemComponent):
    nid = 'effective_tag'
    desc = "Item will be considered effective if the targeted enemy has any of the tags listed in this component."
    # requires = ['damage']
    paired_with = ('effective',)
    tag = ItemTags.EXTRA

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

    def target_icon(self, target, item, unit) -> bool:
        if not skill_system.check_enemy(target, unit):
            return None
        if self._check_negate(target):
            return None
        if any(tag in target.tags for tag in self.value):
            return 'danger'
        return None

class Brave(ItemComponent):
    nid = 'brave'
    desc = "Weapon has the brave property, doubling its attacks."
    tag = ItemTags.EXTRA

    def dynamic_multiattacks(self, unit, item, target, mode, attack_info, base_value):
        return 1

class BraveOnAttack(ItemComponent):
    nid = 'brave_on_attack'
    desc = "The weapon is only brave when making an attack, and acts as a normal weapon when being attacked."
    tag = ItemTags.EXTRA

    def dynamic_multiattacks(self, unit, item, target, mode, attack_info, base_value):
        return 1 if mode == 'attack' else 0

class Lifelink(ItemComponent):
    nid = 'lifelink'
    desc = "The unit heals this percentage of damage dealt to an enemy on hit. Chosen value should be between 0 and 1."
    # requires = ['damage']
    tag = ItemTags.EXTRA

    expose = Type.Float
    value = 0.5

    def after_hit(self, actions, playback, unit, item, target, mode, attack_info):
        total_damage_dealt = 0
        playbacks = [p for p in playback if p.nid in ('damage_hit', 'damage_crit') and p.attacker == unit]
        for p in playbacks:
            total_damage_dealt += p.true_damage

        damage = utils.clamp(total_damage_dealt, 0, target.get_hp())
        true_damage = int(damage * self.value)
        actions.append(action.ChangeHP(unit, true_damage))

        playback.append(pb.HealHit(unit, item, unit, true_damage, true_damage))

class DamageOnMiss(ItemComponent):
    nid = 'damage_on_miss'
    desc = "Item deals a percentage of it's normal damage on a miss."
    tag = ItemTags.EXTRA

    expose = Type.Float
    value = 0.5

    def on_miss(self, actions, playback, unit, item, target, target_pos, mode, attack_info):
        damage = combat_calcs.compute_damage(unit, target, item, target.get_weapon(), mode, attack_info)
        damage = int(damage * self.value)

        true_damage = min(damage, target.get_hp())
        actions.append(action.ChangeHP(target, -damage))

        # For animation
        playback.append(pb.DamageHit(unit, item, target, damage, true_damage))
        if true_damage == 0:
            playback.append(pb.HitSound('No Damage'))
            playback.append(pb.HitAnim('MapNoDamage', target))

class Eclipse(ItemComponent):
    nid = 'Eclipse'
    desc = "Target loses half current HP on hit"
    tag = ItemTags.EXTRA

    def on_hit(self, actions, playback, unit, item, target, target_pos, mode, attack_info):
        true_damage = damage = target.get_hp()//2
        actions.append(action.ChangeHP(target, -damage))

        # For animation
        playback.append(pb.DamageHit(unit, item, target, damage, true_damage))
        if true_damage == 0:
            playback.append(pb.HitSound('No Damage'))
            playback.append(pb.HitAnim('MapNoDamage', target))

class NoDouble(ItemComponent):
    nid = 'no_double'
    desc = "Item cannot double"
    tag = ItemTags.EXTRA

    def can_double(self, unit, item):
        return False

class CannotCounter(ItemComponent):
    nid = 'cannot_counter'
    desc = "Item cannot counter"
    tag = ItemTags.EXTRA

    def can_counter(self, unit, item):
        return False

class CannotBeCountered(ItemComponent):
    nid = 'cannot_be_countered'
    desc = "Item cannot be countered"
    tag = ItemTags.EXTRA

    def can_be_countered(self, unit, item):
        return False

class IgnoreWeaponAdvantage(ItemComponent):
    nid = 'ignore_weapon_advantage'
    desc = "Any weapon advantage relationships defined in the weapon types editor are ignored by this item."
    tag = ItemTags.EXTRA

    def ignore_weapon_advantage(self, unit, item):
        return True

class Reaver(ItemComponent):
    nid = 'reaver'
    desc = "Weapon advantage relationships defined in the weapon types editor are doubled and reversed against this weapon. If two reaver weapons are in combat with each other weapon advantage works as normal. Identical to a custom_triangle_multiplier of -2.0."
    tag = ItemTags.EXTRA

    def modify_weapon_triangle(self, unit, item):
        return -2.0

class DoubleTriangle(ItemComponent):
    nid = 'double_triangle'
    desc = "The effects of weapon advantage relationships are doubled by this item. Identical to a custom_triangle_multiplier of 2.0."
    tag = ItemTags.EXTRA

    def modify_weapon_triangle(self, unit, item):
        return 2.0

class CustomTriangleMultiplier(ItemComponent):
    nid = 'custom_triangle_multiplier'
    desc = "Weapon advantage effects are multiplied by the provided value."
    tag = ItemTags.EXTRA

    expose = Type.Float
    value = 1.0

    def modify_weapon_triangle(self, unit, item):
        return self.value

class StatusOnEquip(ItemComponent):
    nid = 'status_on_equip'
    desc = "A unit with this item equipped will receive the specified status."
    tag = ItemTags.EXTRA

    expose = Type.Skill  # Nid

    def on_equip_item(self, unit, item):
        if self.value not in [skill.nid for skill in unit.skills]:
            act = action.AddSkill(unit, self.value)
            action.do(act)

    def on_unequip_item(self, unit, item):
        action.do(action.RemoveSkill(unit, self.value))

class MultiStatusOnEquip(ItemComponent):
    nid = 'multi_status_on_equip'
    desc = "Item gives these statuses while equipped"
    tag = ItemTags.EXTRA

    expose = (Type.List, Type.Skill)  # Nid

    def on_equip_item(self, unit, item):
        for skl in self.value:
            if skl not in [skill.nid for skill in unit.skills]:
                act = action.AddSkill(unit, skl)
                action.do(act)

    def on_unequip_item(self, unit, item):
        for skl in self.value:
            action.do(action.RemoveSkill(unit, skl))

class StatusOnHold(ItemComponent):
    nid = 'status_on_hold'
    desc = "Item gives status while in unit's inventory"
    tag = ItemTags.EXTRA

    expose = Type.Skill  # Nid

    def on_add_item(self, unit, item):
        action.do(action.AddSkill(unit, self.value))

    def on_remove_item(self, unit, item):
        action.do(action.RemoveSkill(unit, self.value))

class GainManaAfterCombat(ItemComponent):
    nid = 'gain_mana_after_combat'
    desc = "Takes a string that will be evaluated by python. At the end of combat the string is evaluated if the item was used and the result is translated into mana gained by the unit. If you want a flat gain of X mana, enter X, where X is an integer."
    tag = ItemTags.EXTRA
    author = 'KD'

    expose = Type.String

    def end_combat(self, playback, unit, item, target, mode):
        from app.engine import evaluate
        try:
            mana_gain = int(evaluate.evaluate(self.value, unit, target, position=unit.position))
            action.do(action.ChangeMana(unit, mana_gain))
        except Exception as e:
            print("Could not evaluate %s (%s)" % (self.value, e))
            return True
