from app.engine.exp_calculator import ExpCalcType, ExpCalculator
import math

from app.data.database import DB

from app.data.item_components import ItemComponent, ItemTags
from app.data.components import Type

from app.engine import skill_system, action

class Exp(ItemComponent):
    nid = 'exp'
    desc = "Item gives a fixed integer of EXP each use. Useful for staves like Warp or Rescue."
    tag = ItemTags.EXP

    expose = Type.Int
    value = 15

    def exp(self, playback, unit, item, target) -> int:
        return self.value

class LevelExp(ItemComponent):
    nid = 'level_exp'
    desc = "Gives EXP based on the level difference between attacker and defender. How EXP is normally calculated for weapons. Equation for EXP can be edited in the Constants menu."
    tag = ItemTags.EXP

    def _check_for_no_damage(self, playback, unit, item, target) -> bool:
        no_damage = False
        for brush in playback:
            if brush.nid in ('damage_hit', 'damage_crit') and brush.attacker == unit and brush.defender == target:
                if brush.damage != 0:
                    return False
                else:
                    no_damage = True
        return no_damage

    def exp(self, playback, unit, item, target) -> int:
        if skill_system.check_enemy(unit, target) and \
                not self._check_for_no_damage(playback, unit, item, target):
            if DB.constants.value('promote_level_reset'):
                level_diff = target.get_internal_level() - unit.get_internal_level()
            else:
                level_diff = target.level - unit.level
            if DB.constants.value('exp_formula') == ExpCalcType.STANDARD.value:
                return ExpCalculator.classical_curve_calculator(level_diff,
                                                                DB.constants.value('exp_offset'),
                                                                DB.constants.value('exp_curve'),
                                                                DB.constants.value('exp_magnitude'))
            elif DB.constants.value('exp_formula') == ExpCalcType.GOMPERTZ.value:
                return ExpCalculator.gompertz_curve_calculator(level_diff,
                                                               DB.constants.value('gexp_max'),
                                                               DB.constants.value('gexp_min'),
                                                               DB.constants.value('gexp_slope'),
                                                               DB.constants.value('gexp_intercept'))
            else:
                return 0
        else:
            exp_gained = 0
        return exp_gained

class HealExp(ItemComponent):
    nid = 'heal_exp'
    desc = "Item gives exp to user based on amount of damage healed"
    tag = ItemTags.EXP

    def exp(self, playback, unit, item, target) -> int:
        healing_done = 0
        for brush in playback:
            if brush.nid == 'heal_hit' and brush.attacker == unit and brush.defender == target:
                healing_done += brush.true_damage
        if healing_done <= 0:
            return 0
        if DB.constants.value('promote_level_reset'):
            heal_diff = healing_done - unit.get_internal_level()
        else:
            heal_diff = healing_done - unit.level
        heal_diff += DB.constants.get('heal_offset').value
        exp_gained = DB.constants.get('heal_curve').value * heal_diff
        exp_gained += DB.constants.get('heal_magnitude').value
        return max(exp_gained, DB.constants.get('heal_min').value)

class Wexp(ItemComponent):
    nid = 'wexp'
    desc = "Item gives a custom number of wexp to user while using"
    tag = ItemTags.EXP

    expose = Type.Int
    value = 2

    def wexp(self, playback, unit, item, target):
        return self.value - 1  # Because 1 will already be given by WeaponComponent

class Fatigue(ItemComponent):
    nid = 'fatigue'
    desc = "If fatigue is enabled, increases the amount of fatigue a user suffers while using this item. Can be negative in order to remove fatigue."
    tag = ItemTags.EXP

    expose = Type.Int
    value = 1

    def end_combat(self, playback, unit, item, target, mode):
        if mode != 'attack':
            return
        marks = [mark for mark in playback if mark.nid.startswith('mark') and mark.attacker is unit and mark.item is item]
        if marks:
            action.do(action.ChangeFatigue(unit, self.value))
