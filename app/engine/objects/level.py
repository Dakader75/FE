from app.utilities.data import Data

from app.engine.objects.unit import UnitObject
from app.engine.objects.tilemap import TileMapObject
from app.events.regions import Region
from app.data.level_units import UnitGroup

# Main Level Object used by engine
class LevelObject():
    def __init__(self):
        self.nid: str = None
        self.name: str = None
        self.tilemap: TileMapObject = None  # Actually the tilemap, not a nid
        self.party: str = None  # Party Nid
        self.roam: bool = False
        self.roam_unit: str = None  # Unit Nid

        self.music = {}
        self.objective = {}

        self.units: Data[UnitObject] = Data()
        self.regions = Data()
        self.unit_groups = Data()

    @classmethod
    def from_prefab(cls, prefab, tilemap, unit_registry):
        level = cls()
        level.nid = prefab.nid
        level.name = prefab.name
        level.tilemap = tilemap
        level.party = prefab.party
        level.roam = prefab.roam
        level.roam_unit = prefab.roam_unit

        level.music = {k: v for k, v in prefab.music.items()}
        level.objective = {k: v for k, v in prefab.objective.items()}

        # Load in units
        level.units = Data()
        for unit_prefab in prefab.units:
            if unit_prefab.nid in unit_registry:
                unit = unit_registry[unit_prefab.nid]
                unit.starting_position = tuple(unit_prefab.starting_position) if unit_prefab.starting_position else None
                if not unit.dead:
                    unit.position = unit.starting_position
                else:
                    unit.position = None
                level.units.append(unit)
            else:
                new_unit = UnitObject.from_prefab(unit_prefab)
                level.units.append(new_unit)

        level.regions = Data([p for p in prefab.regions])
        level.unit_groups = Data([UnitGroup.from_prefab(p) for p in prefab.unit_groups])

        return level

    def save(self):
        s_dict = {'nid': self.nid,
                  'name': self.name,
                  'tilemap': self.tilemap.save(),
                  'party': self.party,
                  'roam': self.roam,
                  'roam_unit': self.roam_unit,
                  'music': self.music,
                  'objective': self.objective,
                  'units': [unit.nid for unit in self.units],
                  'regions': [region.save() for region in self.regions],
                  'unit_groups': [unit_group.save() for unit_group in self.unit_groups],
                  }
        return s_dict

    @classmethod
    def restore(cls, s_dict, game):
        level = cls()
        level.nid = s_dict['nid']
        level.name = s_dict['name']
        level.tilemap = TileMapObject.restore(s_dict['tilemap'])
        level.party = s_dict['party']
        level.roam = s_dict.get('roam', False)
        level.roam_unit = s_dict.get('roam_unit')

        level.music = s_dict['music']
        level.objective = s_dict['objective']

        level.units = Data([game.get_unit(unit_nid) for unit_nid in s_dict['units']])
        level.regions = Data([Region.restore(region) for region in s_dict['regions']])
        level.unit_groups = Data([UnitGroup.restore(unit_group) for unit_group in s_dict['unit_groups']])

        return level
