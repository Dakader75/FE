from app.data.item_components import ItemComponent
from app.data.components import Type

class Spell(ItemComponent):
    nid = 'spell'
    desc = "Item will be treated as a spell (cannot counterattack, be counterattacked, or double)"
    tag = 'base'

    def is_spell(self, unit, item):
        return True

    def is_weapon(self, unit, item):
        return False

    def equippable(self, unit, item):
        return False

    def wexp(self, playback, unit, item, target):
        return 1

    def can_double(self, unit, item):
        return False

    def can_counter(self, unit, item):
        return False

    def can_be_countered(self, unit, item):
        return False

class Weapon(ItemComponent):
    nid = 'weapon'
    desc = "Item will be treated as a normal weapon (can double, counterattack, be equipped, etc.)" 
    tag = 'base'

    def is_weapon(self, unit, item):
        return True

    def is_spell(self, unit, item):
        return False

    def equippable(self, unit, item):
        return True

    def can_be_countered(self, unit, item):
        return True

    def can_counter(self, unit, item):
        return True

    def can_double(self, unit, item):
        return True

    def wexp(self, playback, unit, item, target):
        return 1

class SiegeWeapon(ItemComponent):
    nid = 'siege_weapon'
    desc = "Item will be treated as a siege weapon (cannot counterattack or be counterattacked, but can still be equipped and can double)"
    tag = 'base'

    def is_weapon(self, unit, item):
        return True

    def is_spell(self, unit, item):
        return False

    def equippable(self, unit, item):
        return True

    def can_double(self, unit, item):
        return True

    def can_counter(self, unit, item):
        return False

    def can_be_countered(self, unit, item):
        return False

    def wexp(self, playback, unit, item, target):
        return 1

class Usable(ItemComponent):
    nid = 'usable'
    desc = "Item is usable"
    tag = 'base'

    def can_use(self, unit, item):
        return True

class UsableInBase(ItemComponent):
    nid = 'usable_in_base'
    desc = "Item is usable in base"
    tag = 'base'

    def can_use_in_base(self, unit, item):
        return True

class Unrepairable(ItemComponent):
    nid = 'unrepairable'
    desc = "Item cannot be repaired"
    tag = 'base'

    def unrepairable(self, unit, item):
        return True

class Value(ItemComponent):
    nid = 'value'
    desc = "Item has a value and can be bought and sold. Items sell for half their value."
    tag = 'base'
    
    expose = Type.Int
    value = 0

    def full_price(self, unit, item):
        return self.value

    def buy_price(self, unit, item):
        if item.uses:
            frac = item.data['uses'] / item.data['starting_uses']
            return int(self.value * frac)
        return self.value

    def sell_price(self, unit, item):
        if item.uses:
            frac = item.data['uses'] / item.data['starting_uses']
            return int(self.value * frac // 2)
        return self.value // 2

class Accessory(ItemComponent):
    nid = 'accessory'
    desc = "Item is an accessory"
    tag = 'base'

    def is_accessory(self, unit, item) -> bool:
        return True
