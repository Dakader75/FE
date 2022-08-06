from app.data.database import DB
from app.data.skill_components import SkillComponent
from app.data.components import Type
from app.engine import equations

class StatChange(SkillComponent):
    nid = 'stat_change'
    desc = "Gives stat bonuses"
    tag = 'combat'

    expose = (Type.Dict, Type.Stat)
    value = []

    def stat_change(self, unit=None):
        return {stat[0]: stat[1] for stat in self.value}

    def tile_def(self):
        total_value = 0
        for stat_nid, stat_value in self.value:
            if stat_nid == 'DEF':
                total_value += stat_value
        return total_value

class StatMultiplier(SkillComponent):
    nid = 'stat_multiplier'
    desc = "Gives stat bonuses"
    tag = 'combat'

    expose = (Type.FloatDict, Type.Stat)
    value = []

    def stat_change(self, unit):
        return {stat[0]: int((stat[1]-1)*unit.stats[stat[0]]) for stat in self.value}

class GrowthChange(SkillComponent):
    nid = 'growth_change'
    desc = "Gives growth rate % bonuses"
    tag = 'combat'

    expose = (Type.Dict, Type.Stat)
    value = []

    def growth_change(self, unit):
        return {stat[0]: stat[1] for stat in self.value}

class EquationGrowthChange(SkillComponent):
    nid = 'equation_growth_change'
    desc = "Gives growth rate % bonuses equal to chosen equation"
    tag = 'combat'

    expose = Type.Equation

    def growth_change(self, unit):
        value = equations.parser.get(self.value, unit)
        return {stat_nid: value for stat_nid in DB.stats.keys()}

class Damage(SkillComponent):
    nid = 'damage'
    desc = "Gives +X damage"
    tag = 'combat'

    expose = Type.Int
    value = 3

    def modify_damage(self, unit, item):
        return self.value

class EvalDamage(SkillComponent):
    nid = 'eval_damage'
    desc = "Gives +X damage solved using evaluate"
    tag = 'combat'

    expose = Type.String

    def modify_damage(self, unit, item):
        from app.engine import evaluate
        try:
            return int(evaluate.evaluate(self.value, unit, item=item))
        except:
            print("Couldn't evaluate %s conditional" % self.value)
        return 0

class Resist(SkillComponent):
    nid = 'resist'
    desc = "Gives +X damage resist"
    tag = 'combat'

    expose = Type.Int
    value = 2

    def modify_resist(self, unit, item_to_avoid):
        return self.value

class Hit(SkillComponent):
    nid = 'hit'
    desc = "Gives +X accuracy"
    tag = 'combat'

    expose = Type.Int
    value = 15

    def modify_accuracy(self, unit, item):
        return self.value

class Avoid(SkillComponent):
    nid = 'avoid'
    desc = "Gives +X avoid"
    tag = 'combat'

    expose = Type.Int
    value = 20

    def modify_avoid(self, unit, item_to_avoid):
        return self.value

    def tile_avoid(self):
        return self.value

class Crit(SkillComponent):
    nid = 'crit'
    desc = "Gives +X crit"
    tag = 'combat'

    expose = Type.Int
    value = 30

    def modify_crit_accuracy(self, unit, item):
        return self.value

class CritAvoid(SkillComponent):
    nid = 'crit_avoid'
    desc = "Gives +X crit avoid"
    tag = 'combat'

    expose = Type.Int
    value = 10

    def modify_crit_avoid(self, unit, item_to_avoid):
        return self.value

class AttackSpeed(SkillComponent):
    nid = 'attack_speed'
    desc = "Gives +X attack speed"
    tag = 'combat'

    expose = Type.Int
    value = 4

    def modify_attack_speed(self, unit, item):
        return self.value

class DefenseSpeed(SkillComponent):
    nid = 'defense_speed'
    desc = "Gives +X defense speed"
    tag = 'combat'

    expose = Type.Int
    value = 4

    def modify_defense_speed(self, unit, item_to_avoid):
        return self.value

class DamageMultiplier(SkillComponent):
    nid = 'damage_multiplier'
    desc = "Multiplies damage given by a fraction"
    tag = 'combat'

    expose = Type.Float
    value = 0.5

    def damage_multiplier(self, unit, item, target, mode, attack_info, base_value):
        return self.value

class DynamicDamageMultiplier(SkillComponent):
    nid = 'dynamic_damage_multiplier'
    desc = "Multiplies damage given by a fraction"
    tag = 'combat'

    expose = Type.String

    def damage_multiplier(self, unit, item, target, mode, attack_info, base_value):
        from app.engine import evaluate
        try:
            return float(evaluate.evaluate(self.value, unit, target, item, mode=mode, skill=self.skill, attack_info=attack_info, base_value=base_value))
        except Exception:
            print("Couldn't evaluate %s conditional" % self.value)
            return 1

class ResistMultiplier(SkillComponent):
    nid = 'resist_multiplier'
    desc = "Multiplies damage taken by a fraction"
    tag = 'combat'

    expose = Type.Float
    value = 0.5

    def resist_multiplier(self, unit, item, target, mode, attack_info, base_value):
        return self.value

class PCC(SkillComponent):
    nid = 'pcc'
    desc = "Multiplies crit chance by a stat on second strike"
    tag = 'combat'

    expose = Type.Stat

    def crit_multiplier(self, unit, item, target, mode, attack_info, base_value):
        return unit.get_stat(self.value) if attack_info[0] > 0 else 1

class test(SkillComponent):
    nid = 'test'
    desc = "Tests to see if this will work"
    tag = 'combat'

    def testing(self):
        pass
