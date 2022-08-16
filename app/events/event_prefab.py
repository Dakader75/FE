from typing import List, Dict, Set

from app.events import event_commands
from app.utilities.data import Data, Prefab


class Trigger(object):
    def __init__(self, nid, unit1=False, unit2=False, position=False, local_args=None):
        self.nid: str = nid
        self.unit1: bool = unit1
        self.unit2: bool = unit2
        self.position: bool = position
        self.local_args: Set = local_args or set()

all_triggers = Data([
    Trigger('level_start'),
    Trigger('level_end'),
    Trigger('overworld_start'),
    Trigger('level_select'),
    Trigger('turn_change'),
    Trigger('enemy_turn_change'),
    Trigger('enemy2_turn_change'),
    Trigger('other_turn_change'),
    Trigger('on_region_interact', True, False, True, {'region'}),
    Trigger('unit_death', True, False, True),
    Trigger('unit_wait', True, False, True, {'region'}),
    Trigger('unit_select', True, False, True),
    Trigger('unit_level_up', True, False, False, {'stat_changes'}),
    Trigger('during_unit_level_up', True, False, False, {'stat_changes'}),
    Trigger('combat_start', True, True, True, {'item', 'is_animation_combat'}),
    Trigger('combat_end', True, True, True, {'item'}),
    Trigger('on_talk', True, True, True),
    Trigger('on_support', True, True, True, {'support_rank_nid'}),  # Item is support rank nid
    Trigger('on_base_convo', True, True, False),
    Trigger('on_prep_start'),
    Trigger('on_base_start'),
    Trigger('on_turnwheel'),
    Trigger('on_title_screen'),
    Trigger('time_region_complete', False, False, False, {'region'}),
    Trigger('on_overworld_node_select', False, False, False, {'entity_nid', 'node_nid'}), # unit1 is entity nid, region is node nid
    Trigger('roam_press_start', True, False, False),
    Trigger('roam_press_info', True, True, False),
    Trigger('roaming_interrupt', True, False, True, {'region'})
])

class EventPrefab(Prefab):
    def __init__(self, name):
        self.name = name
        self.trigger = None
        self.level_nid = None
        self.condition: str = "True"
        self.commands: List[event_commands.EventCommand] = []
        self.only_once = False
        self.priority: int = 20

    @property
    def nid(self):
        if not self.name:
            return None
        if self.level_nid:
            return self.level_nid + " " + self.name
        else:
            return "Global " + self.name

    def save_attr(self, name, value):
        if name == 'commands':
            value = [c.save() for c in value if c]
        else:
            value = super().save_attr(name, value)
        return value

    def restore_attr(self, name, value):
        if name == 'priority':
            if value is None:
                value = 20
            else:
                value = super().restore_attr(name, value)
        elif name == 'commands':
            value = [event_commands.restore_command(c) for c in value]
            value = [v for v in value if v]
        else:
            value = super().restore_attr(name, value)
        return value

    @classmethod
    def default(cls):
        return cls('None')

class EventCatalog(Data[EventPrefab]):
    datatype = EventPrefab

    def get(self, trigger, level_nid):
        return [event for event in self._list if event.trigger == trigger and
                (not event.level_nid or event.level_nid == level_nid)]

    def get_by_level(self, level_nid: str) -> List[EventPrefab]:
        return [event for event in self._list if (not event.level_nid or not level_nid or event.level_nid == level_nid)]

    def get_by_nid_or_name(self, name_or_nid: str, level_nid: None) -> List[EventPrefab]:
        level_events = self.get_by_level(level_nid)
        return [event for event in level_events if
                ((event.nid == name_or_nid) or (event.name == name_or_nid))]

    def get_from_nid(self, key, fallback=None):
        return self._dict.get(key, fallback)
