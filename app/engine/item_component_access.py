from app.utilities.data import Data
from app.data.components import Type
from app.data.item_components import ItemComponent, tags

def get_item_components():
    # Necessary for get_item_components to find all the
    # item components defined in item_components folder
    from app.engine import item_components

    subclasses = ItemComponent.__subclasses__()
    # Sort by tag
    subclasses = sorted(subclasses, key=lambda x: tags.index(x.tag) if x.tag in tags else 100)
    return Data(subclasses)

def get_component(nid):
    _item_components = get_item_components()
    base_class = _item_components.get(nid)
    if base_class:
        return base_class(base_class.value)
    return None

def restore_component(dat):
    nid, value = dat
    _item_components = get_item_components()
    base_class = _item_components.get(nid)
    if base_class:
        if isinstance(base_class.expose, tuple):
            if base_class.expose[0] == Type.List:
                # Need to make a copy
                # so we don't keep the reference around
                copy = base_class(value.copy())
            elif base_class.expose[0] in (Type.Dict, Type.FloatDict):
                val = [v.copy() for v in value]
                copy = base_class(val)
            else:
                copy = base_class(value)
        else:
            copy = base_class(value)
        return copy
    return None

templates = {'Weapon Template': ('weapon', 'value', 'target_enemy', 'min_range', 'max_range', 'damage', 'hit', 'crit', 'weight', 'level_exp', 'weapon_type', 'weapon_rank'),
             'Magic Weapon Template': ('weapon', 'value', 'target_enemy', 'min_range', 'max_range', 'damage', 'hit', 'crit', 'weight', 'level_exp', 'weapon_type', 'weapon_rank', 'magic'),
             'Spell Template': ('spell', 'value', 'min_range', 'max_range', 'weapon_type', 'weapon_rank', 'magic'),
             'Usable Template': ('usable', 'value', 'target_ally', 'uses')}

def get_templates():
    return templates.items()
