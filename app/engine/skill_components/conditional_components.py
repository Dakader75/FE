from app.data.skill_components import SkillComponent
from app.data.components import Type

class CombatCondition(SkillComponent):
    nid = 'combat_condition'
    desc = "Status is conditional based on combat properties"
    tag = "advanced"

    expose = Type.String
    value = 'False'

    ignore_conditional = True
    _condition = False

    def pre_combat(self, playback, unit, item, target, mode):
        from app.engine import evaluate
        try:
            x = bool(evaluate.evaluate(self.value, unit, target, item, mode=mode))
            self._condition = x
            return x
        except Exception as e:
            print("%s: Could not evaluate combat condition %s" % (e, self.value))

    def post_combat(self, playback, unit, item, target, mode):
        self._condition = False

    def condition(self, unit):
        return self._condition

    def test_on(self, playback, unit, item, target, mode):
        self.pre_combat(playback, unit, item, target, mode)

    def test_off(self, playback, unit, item, target, mode):
        self._condition = False

class Condition(SkillComponent):
    nid = 'condition'
    desc = "Status is conditional"
    tag = "advanced"

    expose = Type.String
    value = 'False'

    ignore_conditional = True

    def condition(self, unit):
        from app.engine import evaluate
        try:
            return bool(evaluate.evaluate(self.value, unit))
        except Exception as e:
            print("%s: Could not evaluate condition %s" % (e, self.value))
