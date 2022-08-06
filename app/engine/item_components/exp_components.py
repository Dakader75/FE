import math

from app.data.database import DB

from app.data.item_components import ItemComponent
from app.data.components import Type

from app.engine import skill_system, action

class Exp(ItemComponent):
    nid = 'exp'
    desc = "Item gives a custom number of exp to user on use"
    tag = 'exp'

    expose = Type.Int
    value = 15

    def exp(self, playback, unit, item, target) -> int:
        return self.value

class LevelExp(ItemComponent):
    nid = 'level_exp'
    desc = "Item gives exp to user based on level difference"
    tag = 'exp'

    def _check_for_no_damage(self, playback, unit, item, target) -> bool:
        no_damage = False
        for record in playback:
            if record[0] == 'damage_hit' and record[1] == unit and record[3] == target:
                if record[4] != 0:
                    return False
                else:
                    no_damage = True
        return no_damage

    def exp(self, playback, unit, item, target) -> int:
        if skill_system.check_enemy(unit, target) and \
                not self._check_for_no_damage(playback, unit, item, target):
            level_diff = target.get_internal_level() - unit.get_internal_level()
            level_diff += DB.constants.value('exp_offset')
            exp_gained = math.exp(level_diff * DB.constants.value('exp_curve'))
            exp_gained *= DB.constants.value('exp_magnitude')
        else:
            exp_gained = 0
        return exp_gained

class HealExp(ItemComponent):
    nid = 'heal_exp'
    desc = "Item gives exp to user based on amount of damage healed"
    # requires = ['heal']
    tag = 'exp'

    def exp(self, playback, unit, item, target) -> int:
        healing_done = 0
        for record in playback:
            if record[0] == 'heal_hit' and record[1] == unit and record[3] == target:
                healing_done += record[5]
        if healing_done <= 0:
            return 0
        heal_diff = healing_done - unit.get_internal_level()
        heal_diff += DB.constants.get('heal_offset').value
        exp_gained = DB.constants.get('heal_curve').value * heal_diff
        exp_gained += DB.constants.get('heal_magnitude').value
        return max(exp_gained, DB.constants.get('heal_min').value)

class Wexp(ItemComponent):
    nid = 'wexp'
    desc = "Item gives a custom number of wexp to user while using"
    tag = 'exp'

    expose = Type.Int
    value = 2

    def wexp(self, playback, unit, item, target):
        return self.value - 1  # Because 1 will already be given by WeaponComponent

class Fatigue(ItemComponent):
    nid = 'fatigue'
    desc = "Item gives extra fatigue to user while using"
    tag = 'exp'

    expose = Type.Int
    value = 1

    def end_combat(self, playback, unit, item, target, mode):
        if mode != 'attack':
            return
        marks = [mark for mark in playback if mark[0].startswith('mark') and mark[1] is unit and mark[4] is item]
        if marks:
            action.do(action.ChangeFatigue(unit, self.value))
