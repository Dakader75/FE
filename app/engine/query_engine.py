from __future__ import annotations
import logging
from typing import List, Tuple

from app.engine.game_state import GameState
from app.engine.objects.item import ItemObject
from app.engine.objects.skill import SkillObject
from app.engine.objects.unit import UnitObject
from app.events.regions import Region
from app.utilities import utils
from app.utilities.typing import NID


class QueryType():
    UNIT = 'Units'
    SKILL = 'Skills'
    ITEM = 'Items'
    MAP = 'Map Functions'

def categorize(tag):
    def deco(func):
        func.tag = tag
        return func
    return deco

class GameQueryEngine():
    def __init__(self, logger: logging.Logger, game: GameState) -> None:
        self.logger = logger
        self.game = game

    def _resolve_to_nid(self, obj_or_nid) -> NID:
        try:
            return obj_or_nid.uid
        except:
            try:
                return obj_or_nid.nid
            except:
                return obj_or_nid

    def _resolve_to_unit(self, unit_or_nid) -> UnitObject:
        nid = self._resolve_to_nid(unit_or_nid)
        return self.game.get_unit(nid)

    def _resolve_to_region(self, region_or_nid) -> Region:
        nid = self._resolve_to_nid(region_or_nid)
        return self.game.get_region(nid)

    def _resolve_pos(self, has_pos_or_is_pos) -> Tuple[int, int] | None:
        try:
            # possibly a unit?
            has_pos_or_is_pos = self._resolve_to_unit(has_pos_or_is_pos)
            return has_pos_or_is_pos.position
        except:
            return has_pos_or_is_pos

    @categorize(QueryType.ITEM)
    def get_item(self, unit, item) -> ItemObject:
        """Returns a item object by nid.

        Args:
            unit: unit to check
            item: item to check

        Returns:
            ItemObject | None: Item if exists on unit, otherwise None
        """
        item = self._resolve_to_nid(item)
        if unit == 'convoy':
            found_items = [it for it in self.game.get_convoy_inventory() if it.uid == item or it.nid == item]
        else:
            unit = self._resolve_to_unit(unit)
            found_items = [it for it in unit.items if it.uid == item or it.nid == item]
        if found_items:
            return found_items[0]
        return None

    @categorize(QueryType.ITEM)
    def has_item(self, item, nid=None, team=None, tag=None, party=None) -> bool:
        """Check if any unit matching criteria has item.

Example usage:

* `has_item("Iron Sword", team="player")` will check if any player unit is holding an iron sword
* `has_item("Sacred Stone", party='Eirika')` will check if Eirika's party has the item "Sacred Stone"

        Args:
            item: item to check
            nid (optional): use to check specific unit nid
            team (optional): used to match for team. one of 'player', 'enemy', 'enemy2', 'other'
            tag (optional): used to match for tag.
            party (optional): used to match for party

        Returns:
            bool: True if unit has item, else False
        """
        all_units = self.game.get_all_units() if not party else self.game.get_all_units_in_party(party)
        convoy = None
        item = self._resolve_to_nid(item)
        if not nid or nid == 'convoy':
            if nid == 'convoy' or team == 'player':
                convoy = self.game.get_convoy_inventory()
            elif party:
                convoy = self.game.get_convoy_inventory(self.game.get_party(party))
        if convoy and any([citem.nid == item or citem.uid == item for citem in convoy]):
            return True
        for unit in all_units:
            if nid and not nid == unit.nid:
                continue
            if team and not team == unit.team:
                continue
            if tag and not tag in unit.tags:
                continue
            if bool(self.get_item(unit, item)):
                return True
        return False

    @categorize(QueryType.SKILL)
    def get_skill(self, unit, skill) -> SkillObject:
        """Returns a skill object by nid.

        Args:
            unit: unit in question
            skill: nid of skill

        Returns:
            SkillObject | None: Skill, if exists on unit, else None.
        """
        unit = self._resolve_to_unit(unit)
        skill = self._resolve_to_nid(skill)
        for sk in unit.skills:
            if sk.nid == skill:
                return sk
        return None

    @categorize(QueryType.SKILL)
    def has_skill(self, unit, skill) -> bool:
        """checks if unit has skill

        Args:
            unit: unit to check
            skill: skill to check

        Returns:
            bool: True if unit has skill, else false
        """
        return bool(self.get_skill(unit, skill))


    @categorize(QueryType.MAP)
    def get_closest_allies(self, position, num: int = 1) -> List[Tuple[UnitObject, int]]:
        """Return a list containing the closest player units and their distances.

        Args:
            position: position or unit
            num (int, optional): How many allies to search for. Defaults to 1.

        Returns:
            List[Tuple[UnitObject, int]]: Returns `num` pairs of `(unit, distance)` to the position.
            Will return fewer if there are fewer player units than `num`.
        """
        position = self._resolve_pos(position)
        return sorted([(unit, utils.calculate_distance(unit.position, position)) for unit in self.game.get_player_units()],
                      key=lambda pair: pair[1])[:num]

    @categorize(QueryType.MAP)
    def get_allies_within_distance(self, position, dist: int = 1) -> List[Tuple[UnitObject, int]]:
        """Return a list containing all player units within `dist` distance to the specific position.

        Args:
            position: position or unit
            dist (int, optional): How far to search. Defaults to 1.

        Returns:
            List[Tuple[UnitObject, int]]: Returns all pairs of `(unit, distance)`
            within the specified `dist`.
        """
        position = self._resolve_pos(position)
        return [(unit, utils.calculate_distance(unit.position, position)) for unit in self.game.get_player_units() if utils.calculate_distance(unit.position, position) <= dist]

    @categorize(QueryType.MAP)
    def get_units_in_area(self, position_corner_1: Tuple[int, int], position_corner_2: Tuple[int, int]) -> List[UnitObject]:
        """Returns a list of units within a rectangular area.

        Args:
            position_corner_1 (Tuple[int, int]): (x, y) coordinates for one corner of the area
            position_corner_2 (Tuple[int, int]): (x, y) coordinates for the opposite corner

        Returns:
            List[UnitObject]: Returns all units with positions with values between those
            specified by the corners (inclusive), or an empty list if no units exist in that area
        """
        x1, y1 = position_corner_1
        x2, y2 = position_corner_2
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        target_units = []
        for unit in self.game.get_all_units():
            ux, uy = unit.position
            if x1 <= ux <= x2 and y1 <= uy <= y2:
                target_units.append(unit)
        return target_units

    @categorize(QueryType.SKILL)
    def get_debuff_count(self, unit) -> int:
        """Checks how many negative skills the unit has.

        Args:
            unit: Unit in question

        Returns:
            int: Number of unique negative skills on the unit
        """
        unit = self._resolve_to_unit(unit)
        return len([skill for skill in unit.skills if skill.negative])

    @categorize(QueryType.MAP)
    def get_units_in_region(self, region, nid=None, team=None, tag=None) -> List[UnitObject]:
        """returns all units matching the criteria in the given region

Example usage:
* `get_units_in_region('NorthReinforcements', team='player')` will return all player units in the region
* `get_units_in_region('NorthReinforcements', nid='Eirika')` will return Eirika if Eirika is in the region
* `get_units_in_region('NorthReinforcements')` will return all units in the region

        Args:
            region: region in question
            nid (optional): used to match for NID
            team (optional): used to match for team. one of 'player', 'enemy', 'enemy2', 'other'
            tag (optional): used to match for tag.

        Returns:
            List[UnitObject]: all units matching the criteria in the region
        """
        region = self._resolve_to_region(region)
        all_units = []
        for unit in self.game.get_all_units():
            if nid and nid != unit.nid:
                continue
            if team and team != unit.team:
                continue
            if tag and tag not in unit.tags:
                continue
            if region.contains(unit.position):
                all_units.append(unit)
        return all_units

    @categorize(QueryType.MAP)
    def any_unit_in_region(self, region, nid=None, team=None, tag=None) -> List[UnitObject]:
        """checks if any unit matching the criteria is in the region

Example usage:
* `any_unit_in_region('NorthReinforcements', team='player')` will check if any player unit is in the region
* `any_unit_in_region('NorthReinforcements', nid='Eirika')` will check if Eirika is in the region
* `any_unit_in_region('NorthReinforcements')` will check if ANY unit is in the region

        Args:
            region: region in question
            nid (optional): used to match for NID
            team (optional): used to match for team. one of 'player', 'enemy', 'enemy2', 'other'
            tag (optional): used to match for tag.

        Returns:
            bool: if any unit matching criteria is in the region
        """
        return bool(self.get_units_in_region(region, nid, team, tag))

    @categorize(QueryType.UNIT)
    def is_dead(self, unit) -> bool:
        """checks if unit is dead

        Args:
            unit: unit to check

        Returns:
            bool: if the unit has died
        """
        unit = self._resolve_to_unit(unit)
        return self.game.check_dead(unit)