from typing import Dict
from app.data.skill_components import SkillComponent, SkillTags
from app.data.components import Type
from app.data.database import DB

from app.engine import action
from app.engine.game_state import game

class Time(SkillComponent):
    nid = 'time'
    desc = "Lasts for some number of turns (checked on upkeep)"
    tag = SkillTags.TIME

    expose = Type.Int
    value = 2

    def init(self, skill):
        self.skill.data['turns'] = self.value
        self.skill.data['starting_turns'] = self.value

    def on_upkeep(self, actions, playback, unit):
        val = self.skill.data['turns'] - 1
        action.do(action.SetObjData(self.skill, 'turns', val))
        if self.skill.data['turns'] <= 0:
            actions.append(action.RemoveSkill(unit, self.skill))

    def text(self) -> str:
        return str(self.skill.data['turns'])

    def on_end_chapter(self, unit, skill):
        action.do(action.RemoveSkill(unit, self.skill))

class EndTime(SkillComponent):
    nid = 'end_time'
    desc = "Lasts for some number of turns (checked on endstep)"
    tag = SkillTags.TIME

    expose = Type.Int
    value = 2

    def init(self, skill):
        self.skill.data['turns'] = self.value
        self.skill.data['starting_turns'] = self.value

    def on_endstep(self, actions, playback, unit):
        val = self.skill.data['turns'] - 1
        action.do(action.SetObjData(self.skill, 'turns', val))
        if self.skill.data['turns'] <= 0:
            actions.append(action.RemoveSkill(unit, self.skill))

    def text(self) -> str:
        return str(self.skill.data['turns'])

    def on_end_chapter(self, unit, skill):
        action.do(action.RemoveSkill(unit, self.skill))

class CombinedTime(SkillComponent):
    nid = 'combined_time'
    desc = "Lasts for twice the number of phases (counts both upkeep and endstep)"
    tag = SkillTags.TIME

    expose = Type.Int
    value = 1

    def init(self, skill):
        self.skill.data['turns'] = self.value * 2
        self.skill.data['starting_turns'] = self.value * 2

    def on_upkeep(self, actions, playback, unit):
        val = self.skill.data['turns'] - 1
        action.do(action.SetObjData(self.skill, 'turns', val))
        if self.skill.data['turns'] <= 0:
            actions.append(action.RemoveSkill(unit, self.skill))

    def on_endstep(self, actions, playback, unit):
        val = self.skill.data['turns'] - 1
        action.do(action.SetObjData(self.skill, 'turns', val))
        if self.skill.data['turns'] <= 0:
            actions.append(action.RemoveSkill(unit, self.skill))

    def text(self) -> str:
        return str(self.skill.data['turns'] // 2)

    def on_end_chapter(self, unit, skill):
        action.do(action.RemoveSkill(unit, self.skill))

class UpkeepStatChange(SkillComponent):
    nid = 'upkeep_stat_change'
    desc = "Gives changing stat bonuses"
    tag = SkillTags.TIME

    expose = (Type.Dict, Type.Stat)
    value = []

    def init(self, skill):
        self.skill.data['counter'] = 0

    def stat_change(self, unit):
        return {stat[0]: stat[1] * self.skill.data['counter'] for stat in self.value}

    def on_upkeep(self, actions, playback, unit):
        val = self.skill.data['counter'] + 1
        action.do(action.SetObjData(self.skill, 'counter', val))

    def on_end_chapter(self, unit, skill):
        action.do(action.RemoveSkill(unit, self.skill))

class LostOnEndstep(SkillComponent):
    nid = 'lost_on_endstep'
    desc = "Remove on next endstep"
    tag = SkillTags.TIME

    def on_endstep(self, actions, playback, unit):
        actions.append(action.RemoveSkill(unit, self.skill))

    def on_end_chapter(self, unit, skill):
        action.do(action.RemoveSkill(unit, self.skill))

class LostOnEndCombat(SkillComponent):
    nid = 'lost_on_end_combat'
    desc = "Remove after combat"
    tag = SkillTags.TIME

    expose = (Type.MultipleOptions)

    value = [["LostOnSelf (T/F)", "T", 'Lost after self combat (e.g. vulnerary)'],["LostOnAlly (T/F)", "T", 'Lost after combat with an ally'],["LostOnEnemy (T/F)", "T", 'Lost after combat with an enemy'],["LostOnSplash (T/F)", "T", 'Lost after combat if using an AOE item']]

    @property
    def values(self) -> Dict[str, str]:
        return {value[0]: value[1] for value in self.value}

    def post_combat(self, playback, unit, item, target, mode):
        from app.engine import skill_system
        if self.values.get('LostOnSelf (T/F)', 'T') == 'T':
            if unit == target:
                action.do(action.RemoveSkill(unit, self.skill))
        if self.values.get('LostOnAlly (T/F)', 'T') == 'T':
            if target:
                if skill_system.check_ally(unit, target):
                    action.do(action.RemoveSkill(unit, self.skill))
        if self.values.get('LostOnEnemy (T/F)', 'T') == 'T':
            if target:
                if skill_system.check_enemy(unit, target):
                    action.do(action.RemoveSkill(unit, self.skill))
        if self.values.get('LostOnSplash (T/F)', 'T') == 'T':
            if not target:
                action.do(action.RemoveSkill(unit, self.skill))

    def on_end_chapter(self, unit, skill):
        action.do(action.RemoveSkill(unit, self.skill))

class LostOnEndChapter(SkillComponent):
    nid = 'lost_on_end_chapter'
    desc = "Remove at end of chapter"
    tag = SkillTags.TIME

    def on_end_chapter(self, unit, skill):
        action.do(action.RemoveSkill(unit, self.skill))

class EventOnRemove(SkillComponent):
    nid = 'event_on_remove'
    desc = "Calls event when removed"
    tag = SkillTags.TIME

    expose = Type.Event

    def on_true_remove(self, unit, skill):
        event_prefab = DB.events.get_from_nid(self.value)
        if event_prefab:
            game.events.trigger_specific_event(event_prefab.nid, unit)
