from typing import Tuple

from app.resources.map_icons import MapIconCatalog
from app.utilities.data import Data, Prefab


class OverworldNodePrefab(Prefab):
    def __init__(self, nid: str, name: str, pos: str, icon: str = None):
        self.nid: str = nid
        self.name: str = name
        self.pos: Tuple[int, int] = pos             # tuple of location pair
        self.icon: str = icon or MapIconCatalog.DEFAULT()           # icon nid (see map_icons.json for a manifest)
        self.level: str = None          # level associated

    def save_attr(self, name, value):
        value = super().save_attr(name, value)
        return value

    def restore_attr(self, name, value):
        value = super().restore_attr(name, value)
        if(name == 'pos'):
            value = tuple(value)
        return value

    @classmethod
    def default(cls):
        return cls('0', 'Frelia Castle', (0, 0))

class OverworldNodeCatalog(Data[OverworldNodePrefab]):
    datatype = OverworldNodePrefab
