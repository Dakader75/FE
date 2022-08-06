from app.data.skill_components import SkillComponent
from app.data.components import Type

from app.engine import equations, action, static_random
from app.engine.game_state import game

class Aura(SkillComponent):
    nid = 'aura'
    desc = "Skill has an aura that gives off child skill"
    tag = 'status'
    paired_with = ('aura_range', 'aura_target')

    expose = Type.Skill

class AuraRange(SkillComponent):
    nid = 'aura_range'
    desc = "Set range of skill's aura"
    tag = 'status'
    paired_with = ('aura', 'aura_target')

    expose = Type.Int
    value = 3

class AuraTarget(SkillComponent):
    nid = 'aura_target'
    desc = "Set target of skill's aura (set to 'ally', 'enemy', or 'unit')"
    tag = 'status'
    paired_with = ('aura', 'aura_range')

    expose = Type.String
    value = 'unit'

class PairUpBonus(SkillComponent):
    nid = 'pairup_bonus'
    desc = "Grants a child skill to lead units while in guard stance."
    tag = 'status'

    expose = Type.Skill

    def on_pairup(self, unit, leader):
        action.do(action.AddSkill(leader, self.value))

    def on_separate(self, unit, leader):
        if self.value in [skill.nid for skill in leader.skills]:
            action.do(action.RemoveSkill(leader, self.value))

class Regeneration(SkillComponent):
    nid = 'regeneration'
    desc = "Unit restores %% of HP at beginning of turn"
    tag = "status"

    expose = Type.Float
    value = 0.2

    def on_upkeep(self, actions, playback, unit):
        max_hp = equations.parser.hitpoints(unit)
        if unit.get_hp() < max_hp:
            hp_change = max_hp * self.value
            actions.append(action.ChangeHP(unit, hp_change))
            # Playback
            playback.append(('hit_sound', 'MapHeal'))
            if hp_change >= 30:
                name = 'MapBigHealTrans'
            elif hp_change >= 15:
                name = 'MapMediumHealTrans'
            else:
                name = 'MapSmallHealTrans'
            playback.append(('cast_anim', name, unit))

class UpkeepDamage(SkillComponent):
    nid = 'upkeep_damage'
    desc = "Unit takes damage at upkeep"
    tag = "status"

    expose = Type.Int
    value = 5

    def on_upkeep(self, actions, playback, unit):
        hp_change = -self.value
        actions.append(action.ChangeHP(unit, hp_change))
        actions.append(action.TriggerCharge(unit, self.skill))

class EndstepDamage(SkillComponent):
    nid = 'endstep_damage'
    desc = "Unit takes damage at endstep"
    tag = "status"

    expose = Type.Int
    value = 5

    def on_endstep(self, actions, playback, unit):
        hp_change = -self.value
        actions.append(action.ChangeHP(unit, hp_change))
        actions.append(action.TriggerCharge(unit, self.skill))

class GBAPoison(SkillComponent):
    nid = 'gba_poison'
    desc = "Unit takes random amount of damage up to num"
    tag = "status"

    expose = Type.Int
    value = 5

    def on_upkeep(self, actions, playback, unit):
        old_random_state = static_random.get_combat_random_state()
        hp_loss = -static_random.get_randint(1, self.value)
        new_random_state = static_random.get_combat_random_state()
        actions.append(action.RecordRandomState(old_random_state, new_random_state))
        actions.append(action.ChangeHP(unit, hp_loss))

class ResistStatus(SkillComponent):
    nid = 'resist_status'
    desc = "Unit is only affected by statuses for a turn"
    tag = "status"

    def on_add(self, unit, skill):
        for skill in unit.skills:
            if skill.time:
                action.do(action.SetObjData(skill, 'turns', min(skill.data['turns'], 1)))

    def on_gain_skill(self, unit, other_skill):
        if other_skill.time:
            action.do(action.SetObjData(other_skill, 'turns', min(other_skill.data['turns'], 1)))

class ImmuneStatus(SkillComponent):
    nid = 'immune_status'
    desc = "Unit is not affected by negative statuses"
    tag = 'status'

    def on_add(self, unit, skill):
        for skill in unit.skills:
            if skill.negative:
                action.do(action.RemoveSkill(unit, skill))

    def on_gain_skill(self, unit, other_skill):
        if other_skill.negative:
            action.do(action.RemoveSkill(unit, other_skill))

class ReflectStatus(SkillComponent):
    nid = 'reflect_status'
    desc = "Unit reflects statuses back to initiator"
    tag = 'status'

    def on_gain_skill(self, unit, other_skill):
        if other_skill.initiator_nid:
            other_unit = game.get_unit(other_skill.initiator_nid)
            if other_unit:
                # Create a copy of other skill
                action.do(action.AddSkill(other_unit, other_skill.nid))
