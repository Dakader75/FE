from app.data.components import Component, Type

tags = ['base', 'target', 'weapon', 'uses', 'exp', 'class_change', 'extra', 'utility', 'special', 'formula', 'aoe', 'aesthetic', 'advanced']

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
