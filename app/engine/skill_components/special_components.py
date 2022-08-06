from app.data.skill_components import SkillComponent
from app.data.components import Type

from app.engine import action
from app.engine.game_state import game

class DeathTether(SkillComponent):
    nid = 'death_tether'
    desc = "Remove all skills in the game that I initiated on my death"
    tag = 'advanced'

    def on_death(self, unit):
        for other_unit in game.units:
            for skill in other_unit.skills:
                if skill.initiator_nid == unit.nid:
                    action.do(action.RemoveSkill(other_unit, skill))

class Oversplash(SkillComponent):
    nid = 'oversplash'
    desc = "Grants unit +X area of effect for regular and blast items"
    tag = 'advanced'

    expose = Type.Int
    value = 1

    def empower_splash(self, unit):
        return self.value

    def alternate_splash(self, unit):
        from app.engine.item_components.aoe_components import BlastAOE
        return BlastAOE(0)

class EmpowerHeal(SkillComponent):
    nid = 'empower_heal'
    desc = "Gives +X extra healing"
    tag = 'advanced'

    expose = Type.String

    def empower_heal(self, unit, target):
        from app.engine import evaluate
        try:
            return int(evaluate.evaluate(self.value, unit, target))
        except:
            print("Couldn't evaluate %s conditional" % self.value)
            return 0

class ManaOnKill(SkillComponent):
    nid = 'mana_on_kill'
    desc = 'Gives +X mana on kill'
    tag = 'advanced'

    expose = Type.Int

    def mana(self, playback, unit, item, target):
        if target and target.is_dying:
            return self.value
        return 0
