from app.data.skill_components import SkillComponent
from app.data.components import Type

class DynamicDamage(SkillComponent):
    nid = 'dynamic_damage'
    desc = "Gives +X damage solved dynamically"
    tag = 'dynamic'

    expose = Type.String

    def dynamic_damage(self, unit, item, target, mode, attack_info, base_value) -> int:
        from app.engine import evaluate
        try:
            return int(evaluate.evaluate(self.value, unit, target, item, mode=mode, skill=self.skill, attack_info=attack_info, base_value=base_value))
        except Exception:
            print("Couldn't evaluate %s conditional" % self.value)
            return 0

class DynamicResist(SkillComponent):
    nid = 'dynamic_resist'
    desc = "Gives +X resist solved dynamically"
    tag = 'dynamic'

    expose = Type.String

    def dynamic_resist(self, unit, item, target, mode, attack_info, base_value) -> int:
        from app.engine import evaluate
        try:
            return int(evaluate.evaluate(self.value, unit, target, item, mode=mode, skill=self.skill, attack_info=attack_info, base_value=base_value))
        except Exception:
            print("Couldn't evaluate %s conditional" % self.value)
            return 0

class DynamicAccuracy(SkillComponent):
    nid = 'dynamic_accuracy'
    desc = "Gives +X hit solved dynamically"
    tag = 'dynamic'

    expose = Type.String

    def dynamic_accuracy(self, unit, item, target, mode, attack_info, base_value) -> int:
        from app.engine import evaluate
        try:
            return int(evaluate.evaluate(self.value, unit, target, item, mode=mode, skill=self.skill, attack_info=attack_info, base_value=base_value))
        except Exception:
            print("Couldn't evaluate %s conditional" % self.value)
            return 0

class DynamicAvoid(SkillComponent):
    nid = 'dynamic_avoid'
    desc = "Gives +X avoid solved dynamically"
    tag = 'dynamic'

    expose = Type.String

    def dynamic_avoid(self, unit, item, target, mode, attack_info, base_value) -> int:
        from app.engine import evaluate
        try:
            return int(evaluate.evaluate(self.value, unit, target, item, mode=mode, skill=self.skill, attack_info=attack_info, base_value=base_value))
        except Exception:
            print("Couldn't evaluate %s conditional" % self.value)
            return 0

class DynamicCritAccuracy(SkillComponent):
    nid = 'dynamic_crit_accuracy'
    desc = "Gives +X crit solved dynamically"
    tag = 'dynamic'

    expose = Type.String

    def dynamic_crit_accuracy(self, unit, item, target, mode, attack_info, base_value) -> int:
        from app.engine import evaluate
        try:
            return int(evaluate.evaluate(self.value, unit, target, item, mode=mode, skill=self.skill, attack_info=attack_info, base_value=base_value))
        except Exception:
            print("Couldn't evaluate %s conditional" % self.value)
            return 0

class DynamicCritAvoid(SkillComponent):
    nid = 'dynamic_crit_avoid'
    desc = "Gives +X crit avoid solved dynamically"
    tag = 'dynamic'

    expose = Type.String

    def dynamic_crit_avoid(self, unit, item, target, mode, attack_info, base_value) -> int:
        from app.engine import evaluate
        try:
            return int(evaluate.evaluate(self.value, unit, target, item, mode=mode, skill=self.skill, attack_info=attack_info, base_value=base_value))
        except Exception:
            print("Couldn't evaluate %s conditional" % self.value)
            return 0

class DynamicAttackSpeed(SkillComponent):
    nid = 'dynamic_attack_speed'
    desc = "Gives +X attack speed solved dynamically"
    tag = 'dynamic'

    expose = Type.String

    def dynamic_attack_speed(self, unit, item, target, mode, attack_info, base_value) -> int:
        from app.engine import evaluate
        try:
            return int(evaluate.evaluate(self.value, unit, target, item, mode=mode, skill=self.skill, attack_info=attack_info, base_value=base_value))
        except Exception:
            print("Couldn't evaluate %s conditional" % self.value)
            return 0

class DynamicDefenseSpeed(SkillComponent):
    nid = 'dynamic_defense_speed'
    desc = "Gives +X defense speed solved dynamically"
    tag = 'dynamic'

    expose = Type.String

    def dynamic_defense_speed(self, unit, item, target, mode, attack_info, base_value) -> int:
        from app.engine import evaluate
        try:
            return int(evaluate.evaluate(self.value, unit, target, item, mode=mode, skill=self.skill, attack_info=attack_info, base_value=base_value))
        except Exception:
            print("Couldn't evaluate %s conditional" % self.value)
            return 0

class DynamicMultiattacks(SkillComponent):
    nid = 'dynamic_multiattacks'
    desc = "Gives +X extra attacks per phase solved dynamically"
    tag = 'dynamic'

    expose = Type.String

    def dynamic_multiattacks(self, unit, item, target, mode, attack_info, base_value) -> int:
        from app.engine import evaluate
        try:
            return int(evaluate.evaluate(self.value, unit, target, item, mode=mode, skill=self.skill, attack_info=attack_info, base_value=base_value))
        except Exception:
            print("Couldn't evaluate %s conditional" % self.value)
            return 0
