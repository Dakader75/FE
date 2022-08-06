from app.data.database import DB

from app.utilities import utils
from app.engine import item_system, skill_system
from app.engine.objects.item import ItemObject
from app.engine.objects.skill import SkillObject

import logging

def is_magic(unit, item, distance=0) -> bool:
    if item.magic or (item.magic_at_range and distance > 1):
        return True
    return False

def is_ranged(unit, item) -> bool:
    if max(get_range(unit, item), default=0) > 1:
        return True
    return False

def available(unit, item) -> bool:
    return item_system.available(unit, item) and skill_system.available(unit, item)

def has_magic(unit) -> bool:
    return any(is_magic(unit, item) for item in unit.items if available(unit, item))

def can_use(unit, item) -> bool:
    if item_system.can_use(unit, item) and available(unit, item):
        defender, splash = item_system.splash(unit, item, unit.position)
        if item_system.target_restrict(unit, item, defender, splash):
            return True
    return False

def buy_price(unit, item):
    value = item_system.buy_price(unit, item)
    if value:
        value *= skill_system.modify_buy_price(unit, item)
    else:
        return 0
    return int(value)

def sell_price(unit, item):
    value = item_system.sell_price(unit, item)
    if value:
        if unit:
            value *= skill_system.modify_sell_price(unit, item)
    else:
        return 0
    return int(value)

# def can_wield(unit, item) -> bool:
#     weapon = item_system.is_weapon(unit, item)
#     spell = item_system.is_weapon(unit, item)
#     avail = available(unit, item)
#     if (weapon or spell):
#         if avail:
#             return True
#         else:
#             return False
#     return True

def create_item(unit, item_nid, droppable=False):
    item_prefab = DB.items.get(item_nid)
    if not item_prefab:
        logging.error("Couldn't find %s" % item_nid)
        return
    item = ItemObject.from_prefab(item_prefab)
    if unit:
        item.owner_nid = unit.nid
    item.droppable = droppable
    item_system.init(item)

    def create_subitem(subitem_nid):
        subitem_prefab = DB.items.get(subitem_nid)
        subitem = ItemObject.from_prefab(subitem_prefab)
        # Make self.item in components always point to parent item
        for component in subitem.components:
            component.item = item
        if unit:
            subitem.owner_nid = unit.nid
        item_system.init(subitem)
        item.subitem_uids.append(subitem.uid)
        item.subitems.append(subitem)
        subitem.parent_item = item

    if item.multi_item:
        for subitem_nid in item.multi_item.value:
            create_subitem(subitem_nid)

    elif item.sequence_item:
        for subitem_nid in item.sequence_item.value:
            create_subitem(subitem_nid)

    return item

def create_items(unit, item_nid_list: list) -> list:
    items = []
    for val in item_nid_list:
        if isinstance(val, tuple) or isinstance(val, list):
            item_nid, droppable = val
        else:
            item_nid = val
            droppable = False
        item = create_item(unit, item_nid, droppable)
        items.append(item)
    return items

def get_all_items(unit) -> list:
    """
    Use this to get all weapons if you want to be able to handle multi_items
    """
    items = []
    for item in unit.items:
        if item.multi_item:
            for subitem in item.subitems:
                items.append(subitem)
        else:
            items.append(item)
    return items

def get_all_tradeable_items(unit) -> list:
    items = []
    for item in unit.items:
        if not item_system.locked(unit, item):
            items.append(item)
    return items

def get_num_items(unit) -> int:
    return DB.constants.value('num_items') + skill_system.num_items_offset(unit)

def get_num_accessories(unit) -> int:
    return DB.constants.value('num_accessories') + skill_system.num_accessories_offset(unit)

def too_much_in_inventory(unit) -> bool:
    return len(unit.accessories) > get_num_accessories(unit) or \
        len(unit.nonaccessories) > get_num_items(unit)

def inventory_full(unit, item) -> bool:
    if item_system.is_accessory(unit, item):
        return len(unit.accessories) >= get_num_accessories(unit)
    else:
        return len(unit.nonaccessories) >= get_num_items(unit)

def get_range(unit, item) -> set:
    min_range, max_range = 0, 0
    for component in item.components:
        if component.defines('minimum_range'):
            min_range = component.minimum_range(unit, item)
            break
    if item._force_max_range is not None:
        max_range = item._force_max_range
    else:
        for component in item.components:
            if component.defines('maximum_range'):
                max_range = component.maximum_range(unit, item)
                break

    max_range += skill_system.modify_maximum_range(unit, item)
    limit_max = skill_system.limit_maximum_range(unit, item)
    max_range = utils.clamp(max_range, 0, limit_max)

    return set(range(min_range, max_range + 1))

def get_range_string(unit, item):
    if unit:
        item_range = get_range(unit, item)
        min_range = min(item_range, default=0)
        max_range = max(item_range, default=0)
    else:
        min_range = item_system.minimum_range(None, item)
        max_range = item_system.maximum_range(None, item)
    if max_range >= 99:
        rng = '%d+' % min_range
    elif min_range != max_range:
        rng = '%d-%d' % (min_range, max_range)
    else:
        rng = '%d' % max_range
    return rng

def create_skill(unit, skill_nid):
    skill_prefab = DB.skills.get(skill_nid)
    if not skill_prefab:
        logging.error("Couldn't find skill %s" % skill_nid)
        return None
    skill = SkillObject.from_prefab(skill_prefab)
    if unit:
        skill.owner_nid = unit.nid
    skill_system.init(skill)

    def create_subskill(subskill_nid):
        subskill_prefab = DB.skills.get(subskill_nid)
        subskill = SkillObject.from_prefab(subskill_prefab)
        # Child skills are not owned by their parent skill unit
        # Since they are given to others
        # if unit:  
        #     subskill.owner_nid = unit.nid
        skill_system.init(subskill)
        skill.subskill_uid = subskill.uid
        skill.subskill = subskill
        subskill.parent_skill = skill

    if skill.aura:
        child_skill_nid = skill.aura.value
        create_subskill(child_skill_nid)

    return skill

def create_skills(unit, skill_nid_list: list) -> list:
    skills = []
    for skill_nid in skill_nid_list:
        skill = create_skill(unit, skill_nid)
        if skill:
            skills.append(skill)
    return skills
