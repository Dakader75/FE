from enum import Enum
from app.data.components import Component, Type

class ItemTags(Enum):
    BASE = 'base'
    TARGET = 'target'
    WEAPON = 'weapon'
    USES = 'uses'
    EXP = 'exp'
    CLASS_CHANGE = 'class_change'
    EXTRA = 'extra'
    UTILITY = 'utility'
    SPECIAL = 'special'
    FORMULA = 'formula'
    AOE = 'aoe'
    AESTHETIC = 'aesthetic'
    ADVANCED = 'advanced'

    CUSTOM = 'custom'
    HIDDEN = 'hidden'
    DEPRECATED = 'deprecated'

class ItemComponent(Component):
    item = None

def get_items_using(expose: Type, value, db) -> list:
    affected_items = []
    for item in db.items:
        for component in item.components:
            if component.expose == expose and component.value == value:
                affected_items.append(item)
    return affected_items

def swap_values(affected_items: list, expose: Type, old_value, new_value):
    for item in affected_items:
        for component in item.components:
            if component.expose == expose and component.value == old_value:
                component.value = new_value
