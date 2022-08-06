from app.data.skill_components import SkillComponent
from app.data.components import Type

from app.engine import equations, action, item_funcs, static_random, skill_system
from app.engine.game_state import game

class Ability(SkillComponent):
    nid = 'ability'
    desc = "Give unit an item as an extra ability"
    tag = "advanced"

    expose = Type.Item

    def extra_ability(self, unit):
        # Find if any item already exists with the name we need
        for item in game.item_registry.values():
            if item.nid == self.value and item.owner_nid == unit.nid:
                new_item = item
                break
        else:
            new_item = item_funcs.create_item(unit, self.value)
            game.register_item(new_item)
        return new_item

    def end_combat(self, playback, unit, item, target, mode):
        if item and item.nid == self.value:
            action.do(action.TriggerCharge(unit, self.skill))

class CombatArt(SkillComponent):
    nid = 'combat_art'
    desc = "Unit has the ability to apply an extra effect to next attack"
    tag = 'advanced'

    expose = Type.Skill
    _action = None

    def init(self, skill):
        self.skill.data['active'] = False

    def combat_art(self, unit):
        return self.value

    def start_combat(self, playback, unit, item, target, mode):
        if self._action:
            playback.append(('attack_pre_proc', unit, self._action.skill_obj))

    def on_activation(self, unit):
        # I don't think this needs to use an action
        # because there will be no point in the turnwheel
        # where you could stop it at True
        self.skill.data['active'] = True
        self._action = action.AddSkill(unit, self.value)
        action.do(self._action)

    def on_deactivation(self, unit):
        self.skill.data['active'] = False
        # Remove the added combat art skill
        if self._action and self._action.skill_obj:
            action.do(action.RemoveSkill(unit, self._action.skill_obj))
        self._action = None

    def end_combat(self, playback, unit, item, target, mode):
        if self.skill.data.get('active'):
            action.do(action.TriggerCharge(unit, self.skill))
        self.skill.data['active'] = False

    def post_combat(self, playback, unit, item, target, mode):
        if self._action and self._action.skill_obj:
            action.do(action.RemoveSkill(unit, self._action.skill_obj))
        self._action = None

class AutomaticCombatArt(SkillComponent):
    nid = 'automatic_combat_art'
    desc = "Unit will be given skill on upkeep and removed on endstep"
    tag = 'advanced'

    expose = Type.Skill

    def on_upkeep(self, actions, playback, unit):
        actions.append(action.AddSkill(unit, self.value))
        actions.append(action.TriggerCharge(unit, self.skill))

    def on_endstep(self, actions, playback, unit):
        actions.append(action.RemoveSkill(unit, self.value))

class AllowedWeapons(SkillComponent):
    nid = 'allowed_weapons'
    desc = "Defines what weapons are allowed for combat art or proc skill"
    tag = 'advanced'

    expose = Type.String

    def weapon_filter(self, unit, item) -> bool:
        from app.engine import evaluate
        try:
            return bool(evaluate.evaluate(self.value, unit, item=item))
        except Exception as e:
            print("Couldn't evaluate conditional {%s} %s" % (self.value, e))
        return False

class CombatArtSetMaxRange(SkillComponent):
    nid = 'combat_art_set_max_range'
    desc = "Defines what unit's max range is for testing combat art. Combine with 'Limit Max Range' component on subskill."
    tag = 'advanced'
    paired_with = ('combat_art', )

    expose = Type.Int

    def combat_art_set_max_range(self, unit) -> int:
        return max(0, self.value)

class CombatArtModifyMaxRange(SkillComponent):
    nid = 'combat_art_modify_max_range'
    desc = "Modifies unit's max range when testing combat art. Combine with 'Modify Max Range' component on subskill."
    tag = 'advanced'
    paired_with = ('combat_art', )

    expose = Type.Int

    def combat_art_modify_max_range(self, unit) -> int:
        return self.value

def get_proc_rate(unit, skill) -> int:
    for component in skill.components:
        if component.defines('proc_rate'):
            return component.proc_rate(unit)
    return 100  # 100 is default

def get_weapon_filter(skill, unit, item) -> bool:
    for component in skill.components:
        if component.defines('weapon_filter'):
            return component.weapon_filter(unit, item)
    return True
            
class AttackProc(SkillComponent):
    nid = 'attack_proc'
    desc = "Allows skill to proc on a single attacking strike"
    tag = 'advanced'

    expose = Type.Skill
    _did_action = False

    def start_sub_combat(self, actions, playback, unit, item, target, mode, attack_info):
        if mode == 'attack' and target and skill_system.check_enemy(unit, target):
            if not get_weapon_filter(self.skill, unit, item):
                return
            proc_rate = get_proc_rate(unit, self.skill)
            if static_random.get_combat() < proc_rate:
                act = action.AddSkill(unit, self.value)
                action.do(act)
                playback.append(('attack_proc', unit, act.skill_obj))
                self._did_action = True
        
    def end_sub_combat(self, actions, playback, unit, item, target, mode, attack_info):
        if self._did_action:
            action.do(action.RemoveSkill(unit, self.value))

class DefenseProc(SkillComponent):
    nid = 'defense_proc'
    desc = "Allows skill to proc when defending a single strike"
    tag = 'advanced'

    expose = Type.Skill
    _did_action = False

    def start_sub_combat(self, actions, playback, unit, item, target, mode, attack_info):
        if mode == 'defense' and target and skill_system.check_enemy(unit, target):
            if not get_weapon_filter(self.skill, unit, item):
                return
            proc_rate = get_proc_rate(unit, self.skill)
            if static_random.get_combat() < proc_rate:
                act = action.AddSkill(unit, self.value)
                action.do(act)
                playback.append(('defense_proc', unit, act.skill_obj))
                self._did_action = True
        
    def end_sub_combat(self, actions, playback, unit, item, target, mode, attack_info):
        if self._did_action:
            action.do(action.RemoveSkill(unit, self.value))

class AttackPreProc(SkillComponent):
    nid = 'attack_pre_proc'
    desc = "Allows skill to proc when initiating combat. Lasts entire combat."
    tag = 'advanced'

    expose = Type.Skill
    _did_action = False

    def start_combat(self, playback, unit, item, target, mode):
        if mode == 'attack' and target and skill_system.check_enemy(unit, target):
            if not get_weapon_filter(self.skill, unit, item):
                return
            proc_rate = get_proc_rate(unit, self.skill)
            if static_random.get_combat() < proc_rate:
                act = action.AddSkill(unit, self.value)
                action.do(act)
                playback.append(('attack_pre_proc', unit, act.skill_obj))
                self._did_action = True
        
    def end_combat(self, playback, unit, item, target, mode):
        if self._did_action:
            action.do(action.RemoveSkill(unit, self.value))
            self._did_action = False

class DefensePreProc(SkillComponent):
    nid = 'defense_pre_proc'
    desc = "Allows skill to proc when defending in combat. Lasts entire combat."
    tag = 'advanced'

    expose = Type.Skill
    _did_action = False

    def start_combat(self, playback, unit, item, target, mode):
        if mode == 'defense' and target and skill_system.check_enemy(unit, target):
            if not get_weapon_filter(self.skill, unit, item):
                return
            proc_rate = get_proc_rate(unit, self.skill)
            if static_random.get_combat() < proc_rate:
                act = action.AddSkill(unit, self.value)
                action.do(act)
                playback.append(('defense_pre_proc', unit, act.skill_obj))
                self._did_action = True
        
    def end_combat(self, playback, unit, item, target, mode):
        if self._did_action:
            action.do(action.RemoveSkill(unit, self.value))
            self._did_action = False

class ProcRate(SkillComponent):
    nid = 'proc_rate'
    desc = "Set the proc rate"
    tag = 'advanced'

    expose = Type.Equation

    def proc_rate(self, unit):
        return equations.parser.get(self.value, unit)

class DeathTether(SkillComponent):
    nid = 'death_tether'
    desc = "Remove all skills in the game that I initiated on my death"
    tag = 'advanced'

    def on_death(self, unit):
        for other_unit in game.units:
            for skill in other_unit.skills:
                if skill.initiator_nid == unit.nid:
                    action.do(action.RemoveSkill(other_unit, skill))

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

class Condition_is_ranged(SkillComponent):
    nid = 'is_ranged'
    desc = "Checks if unit is facing an enemy that has a weapon with a range greater than or equal to 2"
    tag = 'advanced'
    
    def is_ranged(self, unit, target):
        if target.position()[0] > unit.position()[0] + 2 or target.position()[0] > unit.position()[0] - 2 or target.position()[1] > unit.position()[1] + 2 or target.position()[1] > unit.position()[1] - 2:
            return True
        else:
            return False