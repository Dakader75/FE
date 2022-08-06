from enum import IntEnum

from app.utilities import str_utils
from app.utilities.data import Data

class Type(IntEnum):
    Int = 1
    Float = 2
    String = 3
    WeaponType = 4  # Stored as Nids
    WeaponRank = 5  # Stored as Nids
    Unit = 6  # Stored as Nids
    Class = 7  # Stored as Nids
    Tag = 8
    Color3 = 9
    Color4 = 10
    Item = 12  # Stored as Nids
    Skill = 13  # Stored as Nids
    Stat = 14  # Stored as Nids
    MapAnimation = 15  # Stored as Nids
    Equation = 16  # Stored as Nids
    MovementType = 17  # Stored as Nid
    Sound = 18  # Stored as Nid
    AI = 19  # Stored as Nid
    Music = 20  # Stored as Nid
    CombatAnimation = 21  # Stored as Nid
    EffectAnimation = 22  # Stored as Nid
    Affinity = 23  # Stored as Nid
    Event = 80
    List = 100
    Dict = 101  # Item followed by integer
    FloatDict = 102  # Item followed by floating
    MultipleChoice = 103 # item is a string value from a number of choices

class Component():
    nid: str = None
    desc: str = None
    author: str = 'rainlash'
    expose = None  # Attribute
    paired_with: list = []
    tag = 'extra'
    value = None

    def __init__(self, value=None):
        self.value = value

    @property
    def name(self):
        name = self.__class__.__name__
        return str_utils.camel_case(name)

    @classmethod
    def class_name(cls):
        name = cls.__name__
        return str_utils.camel_case(name)

    def defines(self, function_name):
        return hasattr(self, function_name)

    @classmethod
    def copy(cls, other):
        return cls(other.value)

    def save(self):
        if isinstance(self.value, Data):
            return self.nid, self.value.save()
        elif isinstance(self.value, list):
            return self.nid, self.value.copy()
        else:
            return self.nid, self.value
