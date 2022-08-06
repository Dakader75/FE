from __future__ import annotations
from app.sprites import SPRITES
import re
from typing import Dict, TYPE_CHECKING, List

from functools import lru_cache
from typing import List, Tuple

from app.data.database import DB
from app.events import event_commands
from app.resources.resources import RESOURCES
from app.utilities import str_utils
from app.utilities.typing import NID, Point


class Validator():
    desc = ""

    def validate(self, text, level):
        return text

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        """Return a list of all known valid options for this validator
        in tuple (name, nid) format.

        Returns:
            List[Tuple[str, NID]]: A list of (name, nid) tuples that are valid for this type.
        """
        return []

    def convert(self, text: str):
        return text

class OptionValidator(Validator):
    valid = []

    @property
    def desc(self) -> str:
        return "must be one of (`%s`)" % '`, `'.join(self.valid)

    def validate(self, text, level):
        if text.lower() in self.valid:
            return text
        return None

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        valids = [(None, option) for option in self.valid]
        return valids

class EventFunction(Validator):
    desc = "must be a valid event function"

    def validate(self, text, level):
        command_nids = [command.nid for command in event_commands.get_commands()]
        if text in command_nids:
            return text
        return None

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        valids = [(None, command.nid) for command in event_commands.get_commands()]
        return valids

class Condition(Validator):
    desc = "must be a valid Python expression to evaluate."

class Nid(Validator):
    """
    Any nid will do, because we cannot know what
    objects will have been created
    """
    pass

class Integer(Validator):
    def validate(self, text, level):
        if str_utils.is_int(text):
            return int(text)
        return None

class Float(Validator):
    desc = "Any number with a decimal"
    def validate(self, text, level):
        if str_utils.is_float(text):
            return float(text)
        return None

    def convert(self, text: str):
        return float(text)

class PositiveInteger(Validator):
    desc = "must be a positive whole number"

    def validate(self, text, level):
        if str_utils.is_int(text) and int(text) > 0:
            return int(text)
        return None

class String(Validator):
    """
    Any string will do
    """
    pass

class Time(Validator):
    def validate(self, text, level):
        if str_utils.is_int(text):
            return int(text)
        return None

class Music(Validator):
    def validate(self, text, level):
        if text in RESOURCES.music.keys():
            return text
        elif text == 'None':
            return text
        return None

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        valids = [(None, music.nid) for music in RESOURCES.music.values()]
        return valids

class Sound(Validator):
    def validate(self, text, level):
        if text in RESOURCES.sfx.keys():
            return text
        return None

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        valids = [(None, sfx.nid) for sfx in RESOURCES.sfx.values()]
        return valids

class PhaseMusic(OptionValidator):
    valid = ['player_phase', 'enemy_phase', 'other_phase', 'enemy2_phase',
             'player_battle', 'enemy_battle', 'other_battle', 'enemy2_battle']

class Volume(Validator):
    desc = "A number between 0 and 1 (0 is muted, 1 is highest volume)"

    def validate(self, text, level):
        if str_utils.is_float(text) and float(text) >= 0:
            return float(text)
        return None

class PortraitNid(Validator):
    def validate(self, text, level):
        if text in RESOURCES.portraits.keys():
            return text
        return None

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        valids = [(None, portrait.nid) for portrait in RESOURCES.portraits.values()]
        return valids

class Portrait(Validator):
    desc = "can be a unit's nid, a portrait's nid, or one of (`{unit}`, `{unit1}`, `{unit2}`)."

    def validate(self, text, level):
        if text in DB.units.keys():
            return text
        elif text in RESOURCES.portraits.keys():
            return text
        elif text in ('{unit}', '{unit1}', '{unit2}'):
            return text
        return None

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        valids = [(None, portrait.nid) for portrait in RESOURCES.portraits.values()]
        other_valids = [(unit.name, unit.nid) for unit in DB.units.values()]
        valids.append((None, "{unit}"))
        valids.append((None, "{unit1}"))
        valids.append((None, "{unit2}"))
        return valids + other_valids

class AI(Validator):
    def validate(self, text, level):
        if text in DB.ai.keys():
            return text
        return None

class Team(Validator):
    def validate(self, text, level):
        if text in DB.teams:
            return text
        return None

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        valids = [(None, team_nid) for team_nid in DB.teams]
        return valids

class Tag(Validator):
    def validate(self, text, level):
        if text in DB.tags.keys():
            return text
        return None

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        valids = [(None, tag.nid) for tag in DB.tags.values()]
        return valids

class ScreenPosition(Validator):
    valid_positions = ["OffscreenLeft", "FarLeft", "Left", "MidLeft", "CenterLeft", "CenterRight", "MidRight", "LevelUpRight", "Right", "FarRight", "OffscreenRight"]

    desc = ("determines where to add the portrait to the screen."
            "Available options are (`OffscreenLeft`, `FarLeft`, "
            "`Left`, `MidLeft`, `MidRight`, `Right`, `FarRight`, "
            "`OffscreenRight`). Alternatively, specify a position in "
            "pixels (`x,y`) for the topleft of the portrait. If the portrait"
            "is placed on the left side of the screen to start, it will be facing "
            "right, and vice versa.")

    def validate(self, text, level):
        if text in self.valid_positions:
            return text
        elif str_utils.is_int(text):
            return text
        elif ',' in text and len(text.split(',')) == 2 and all(str_utils.is_int(t) for t in text.split(',')):
            return text
        return None

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        valids = [(None, option) for option in self.valid_positions]
        return valids

class VerticalScreenPosition(Validator):
    valid_positions = ["Bottom", "Middle", "Top"]

    desc = ("determines what height to add the portrait to the screen."
            "Available options are (`Bottom`, `Middle`, `Top`). By default,"
            "dialog portraits are displayed along the bottom.")

    def validate(self, text, level):
        if text in self.valid_positions:
            return text
        return None

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        valids = [(None, option) for option in self.valid_positions]
        return valids


class Slide(OptionValidator):
    valid = ["normal", "left", "right"]

class Direction(OptionValidator):
    valid = ["open", "close"]

class Orientation(OptionValidator):
    valid = ["h", "horiz", "horizontal", "v", "vert", "vertical"]

class ExpressionList(Validator):
    valid_expressions = ["NoSmile", "Smile", "NormalBlink", "CloseEyes", "HalfCloseEyes", "OpenEyes"]
    desc = "expects a comma-delimited list of expressions. Valid expressions are: (`NoSmile`, `Smile`, `NormalBlink`, `CloseEyes`, `HalfCloseEyes`, `OpenEyes`). Example: `Smile,CloseEyes`"

    def validate(self, text, level):
        text = text.split(',')
        for t in text:
            if t not in self.valid_expressions:
                return None
        return text

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        valids = [(None, option) for option in self.valid_expressions]
        return valids

class DialogVariant(OptionValidator):
    valid = ["thought_bubble", "noir", "hint", "narration", "narration_top", "cinematic"]

class StringList(Validator):
    desc = "must be delimited by commas. For example: `Water,Earth,Fire,Air`"

    def validate(self, text, level):
        text = text.split(',')
        return text

class DashList(Validator):
    desc = "similar to a StringList, but delimited by dashes. For example: `Water-Earth-Fire-Air`"

    def validate(self, text, level):
        try:
            self.convert(text)
            return text
        except:
            pass
        return None

    def convert(self, text: str) -> List:
        return text.split('-')

class PointList(Validator):
    desc = "A list of points separated by dashes. E.g. (1, 1)-(3.5, 3)-(24,-6)"
    decimal_converter = re.compile(r'[^\d.]+')

    def validate(self, value, level):
        if isinstance(value, list):
            if all([isinstance(p, tuple) for p in value]):
                return value
        return None

    def convert(self, text: str) -> List[Point]:
        try:
            text.replace(' ', '')
            tlist = text.split(')-(')
            parsed_list = []
            for pstring in tlist:
                coords = pstring.split(',')
                x = float(self.decimal_converter.sub('', coords[0]))
                y = float(self.decimal_converter.sub('', coords[1]))
                parsed_list.append((x, y))
            return parsed_list
        except:
            return text

class Speaker(Validator):
    pass  # Any text will do

class Text(Validator):
    pass  # Any text will do

class Panorama(Validator):
    def validate(self, text, level):
        if text in RESOURCES.panoramas.keys():
            return text
        return None

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        valids = [(None, pan.nid) for pan in RESOURCES.panoramas.values()]
        return valids

class Width(Validator):
    desc = "is measured in pixels"

    def validate(self, text, level):
        if str_utils.is_int(text):
            return 8 * round(int(text) / 8)
        return None

class Speed(Validator):
    desc = "is measured in milliseconds"

    def validate(self, text, level):
        if str_utils.is_int(text) and int(text) > 0:
            return text
        return None

class Color3(Validator):
    desc = "uses 0-255 for color channels. Example: `128,160,136`"

    def validate(self, text, level):
        if ',' not in text:
            return None
        text = text.split(',')
        if len(text) != 3:
            return None
        if all(str_utils.is_int(t) and 0 <= int(t) <= 255 for t in text):
            return text
        return None

class Bool(OptionValidator):
    valid = ['t', 'true', '1', 'y', 'yes', 'f', 'false', '0', 'n', 'no']

class ShopFlavor(OptionValidator):
    valid = ['armory', 'vendor']

class Position(Validator):
    desc = "accepts a valid `(x, y)` position. You use a unit's nid to use their position. Alternatively, you can use one of (`{unit}`, `{unit1}`, `{unit2}`, `{position}`)"

    def validate(self, text, level):
        text = text.split(',')
        if len(text) == 1:
            text = text[0]
            if level and text in level.units.keys():
                return text
            elif text in ('{unit}', '{unit1}', '{unit2}', '{position}'):
                return text
            elif text in self.valid_overworld_nids().values():
                return text
            return None
        if len(text) > 2:
            return None
        if not all(str_utils.is_int(t) for t in text):
            return None
        if level and level.tilemap:
            tilemap = RESOURCES.tilemaps.get(level.tilemap)
            x, y = text
            x = int(x)
            y = int(y)
            if 0 <= x < tilemap.width and 0 <= y < tilemap.height:
                return text
            return None
        else:
            return text

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        level_prefab = DB.levels.get(level)
        if level_prefab:
            valids = [(unit.name, unit.nid) for unit in level_prefab.units.values()]
            valids.append((None, "{unit}"))
            valids.append((None, "{unit1}"))
            valids.append((None, "{unit2}"))
            valids.append((None, "{position}"))
            for pair in self.valid_overworld_nids().items():
                valids.append(pair)
            return valids
        else:
            valids = []
            for pair in self.valid_overworld_nids().items():
                valids.append(pair)
            return valids

    def valid_overworld_nids(self) -> Dict[str, NID]:
        # list of all valid nids in overworld
        nids = {}
        for overworld in DB.overworlds.values():
            node_nids = {node.name: node.nid for node in overworld.overworld_nodes.values()}
            nids.update(node_nids)
        party_nids = {party.name: party.nid for party in DB.parties.values()}
        nids.update(party_nids)
        return nids

class FloatPosition(Position, Validator):
    desc = """accepts a valid `(x, y)` position, but also allows fractional positions,
    such as (1.5, 2.6). You use a unit's nid to use their position.
    Alternatively, you can use one of (`{unit}`, `{unit1}`, `{unit2}`, `{position}`)"""

    def validate(self, text, level):
        text = text.split(',')
        if len(text) == 1:
            text = text[0]
            if level and text in level.units.keys():
                return text
            elif text in ('{unit}', '{unit1}', '{unit2}', '{position}'):
                return text
            elif text in self.valid_overworld_nids().values():
                return text
            return None
        if len(text) > 2:
            return None
        if not all(str_utils.is_float(t) for t in text):
            return None
        if level and level.tilemap:
            tilemap = RESOURCES.tilemaps.get(level.tilemap)
            x, y = text
            x = float(x)
            y = float(y)
            if 0 <= x < tilemap.width and 0 <= y < tilemap.height:
                return text
            return None
        else:
            return text

class PositionOffset(Validator):
    desc = "accepts a valid `(x, y)` position offset."

    def validate(self, text, level):
        text = text.split(',')
        if len(text) != 2:
            return None
        if not all(str_utils.is_int(t) for t in text):
            return None
        return text

class Size(Validator):
    desc = "must be in the format `x,y`. Example: `64,32`"

    def validate(self, text, level):
        text = text.split(',')
        if len(text) > 2:
            return None
        if not all(str_utils.is_int(t) and int(t) > 0 for t in text):
            return None
        return text

class Unit(Validator):
    desc = "accepts a unit's nid. Alternatively, you can use one of (`{unit}`, `{unit1}`, `{unit2}`)."

    def validate(self, text, level):
        if not level:
            return text
        nids = [u.nid for u in level.units]
        if text in nids:
            return text
        elif text in ('{unit}', '{unit1}', '{unit2}'):
            return True
        return None

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        level_prefab = DB.levels.get(level)
        if not level_prefab:
            return []
        valids = [(unit.name, unit.nid) for unit in level_prefab.units]
        valids.append((None, "{unit}"))
        valids.append((None, "{unit1}"))
        valids.append((None, "{unit2}"))
        return valids

class Group(Validator):
    def validate(self, text, level):
        if not level:
            return None
        nids = [g.nid for g in level.unit_groups]
        if text in nids:
            return text
        return None

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        level_prefab = DB.levels.get(level)
        if level_prefab:
            valids = [(None, group.nid) for group in level_prefab.unit_groups.values()]
        else:
            valids = []
        return valids

class StartingGroup(Validator):
    desc = "accepts a unit group's nid. Alternatively, can be `starting` to use the unit's starting positions in the level."

    def validate(self, text, level):
        if not level:
            return None
        if ',' in text and len(text.split(',')) == 2:
            if all(str_utils.is_int(t) for t in text.split(',')):
                return text
            else:
                return None
        if text.lower() == 'starting':
            return text
        nids = [g.nid for g in level.unit_groups]
        if text in nids:
            return text
        return None

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        level_prefab = DB.levels.get(level)
        if level_prefab:
            valids = [(None, group.nid) for group in level_prefab.unit_groups.values()]
            valids.append((None, "starting"))
            return valids
        else:
            return []

class UniqueUnit(Validator):
    def validate(self, text, level):
        if text in DB.units.keys():
            return text
        return None

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        valids = [(unit.name, unit.nid) for unit in DB.units.values()]
        return valids

class GlobalUnit(Validator):
    desc = "accepts a unit's nid. Alternatively, you can use one of (`{unit}`, `{unit1}`, `{unit2}`) or `convoy` where appropriate."

    def validate(self, text, level):
        if level:
            nids = [u.nid for u in level.units]
            if text in nids:
                return text
        if text.lower() == 'convoy':
            return text
        elif text in DB.units.keys():
            return text
        elif text in ('{unit}', '{unit1}', '{unit2}'):
            return True
        return None

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        valids = [(unit.name, unit.nid) for unit in DB.units.values()]
        valids.append((None, "{unit}"))
        valids.append((None, "{unit1}"))
        valids.append((None, "{unit2}"))
        valids.append((None, "convoy"))
        return valids

class CardinalDirection(OptionValidator):
    valid = ['north', 'east', 'west', 'south']

class EntryType(OptionValidator):
    valid = ['fade', 'immediate', 'warp', 'swoosh']

class Placement(OptionValidator):
    valid = ['giveup', 'stack', 'closest', 'push']

class MovementType(OptionValidator):
    valid = ['normal', 'fade', 'immediate', 'warp', 'swoosh']

class RemoveType(OptionValidator):
    valid = ['fade', 'immediate', 'warp', 'swoosh']

class RegionType(OptionValidator):
    valid = ['normal', 'event', 'status', 'formation']

class Weather(OptionValidator):
    valid = ["rain", "sand", "snow", "fire", "light", "dark", "smoke"]

class CombatScript(Validator):
    valid_commands = ['hit1', 'hit2', 'crit1', 'crit2', 'miss1', 'miss2', '--', 'end']
    desc = "specifies the order and type of actions in combat. Valid actions: (`hit1`, `hit2`, `crit1`, `crit2`, `miss1`, `miss2`, `--`, `end`)."

    def validate(self, text, level):
        commands = text.split(',')
        if all(command.lower() in self.valid_commands for command in commands):
            return text
        return None

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        valids = [(None, option) for option in self.valid_commands]
        return valids

class Ability(Validator):
    def validate(self, text, level):
        if text in DB.items.keys():
            return text
        elif text in DB.skills.keys():
            return text
        return None

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        valids = [(item.name, item.nid) for item in DB.items.values()]
        svalids = [(skill.name, skill.nid) for skill in DB.skills.values()]
        return valids + svalids

class Item(Validator):
    def validate(self, text, level):
        if text in DB.items.keys():
            return text
        return None

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        valids = [(item.name, item.nid) for item in DB.items.values()]
        return valids

class ItemList(Validator):
    desc = "accepts a comma-delimited list of item nids. Example: `Iron Sword,Iron Lance,Iron Bow`"

    def validate(self, text, level):
        items = text.split(',')
        if all(item in DB.items.keys() for item in items):
            return text
        return None

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        valids = [(item.name, item.nid) for item in DB.items.values()]
        return valids

class StatList(Validator):
    desc = "accepts a comma-delimited list of pairs of stat nids and stat changes. For example, `STR,2,SPD,-3` to increase STR by 2 and decrease SPD by 3."

    def validate(self, text, level):
        s_l = text.split(',')
        if len(s_l)%2 != 0:  # Must be divisible by 2
            return None
        for idx in range(len(s_l)//2):
            stat_nid = s_l[idx*2]
            stat_value = s_l[idx*2 + 1]
            if stat_nid not in DB.stats.keys():
                return None
            elif not str_utils.is_int(stat_value):
                return None
        return text

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        valids = [(stat.name, stat.nid) for stat in DB.stats.values()]
        return valids

class Skill(Validator):
    def validate(self, text, level):
        if text in DB.skills.keys():
            return text
        return None

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        svalids = [(skill.name, skill.nid) for skill in DB.skills.values()]
        return svalids

class Party(Validator):
    desc = "accepts the nid of an existing Party"

    def validate(self, text, level):
        if text in DB.parties.keys():
            return text
        return None

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        valids = [(party.name, party.nid) for party in DB.parties.values()]
        return valids

class Faction(Validator):
    def validate(self, text, level):
        if text in DB.factions.keys():
            return text
        return None

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        valids = [(fac.name, fac.nid) for fac in DB.factions.values()]
        return valids

class Klass(Validator):
    def validate(self, text, level):
        if text in DB.classes.keys():
            return text
        return None

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        valids = [(klass.name, klass.nid) for klass in DB.classes.values()]
        return valids

class Lore(Validator):
    def validate(self, text, level):
        if text in DB.lore.keys():
            return text
        return None

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        valids = [(lore.name, lore.nid) for lore in DB.lore.values()]
        return valids

class WeaponType(Validator):
    def validate(self, text, level):
        if text in DB.weapons.keys():
            return text
        return None

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        valids = [(weapon.name, weapon.nid) for weapon in DB.weapons.values()]
        return valids

class SupportRank(Validator):
    def validate(self, text, level):
        if text in DB.support_ranks.keys():
            return text
        return None

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        valids = [(None, rank.nid) for rank in DB.support_ranks.values()]
        return valids

class Layer(Validator):
    def validate(self, text, level):
        tilemap_prefab = RESOURCES.tilemaps.get(level.tilemap)
        if text in tilemap_prefab.layers.keys():
            return text
        return None

class LayerTransition(OptionValidator):
    valid = ['fade', 'immediate']

class MapAnim(Validator):
    def validate(self, text, level):
        if text in RESOURCES.animations.keys():
            return text
        return None

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        valids = [(None, anim.nid) for anim in RESOURCES.animations.values()]
        return valids

class Tilemap(Validator):
    def validate(self, text, level):
        if text in RESOURCES.tilemaps.keys():
            return text
        return None

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        valids = [(None, tilemap.nid) for tilemap in RESOURCES.tilemaps.values()]
        return valids

class Event(Validator):
    desc = "accepts the name of an event. Will run the event appropriate for the level if more than one event with the same name exists."

    def validate(self, text, level):
        for event in DB.events:
            if event.name == text and (not event.level_nid or not level or event.level_nid == level.nid):
                return text
        return None

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        valids = [(event.name, event.nid) for event in DB.events.values() if (level is None or event.level_nid == level or event.level_nid is None)]
        return valids

class OverworldNID(Validator):
    desc = "accepts the nid of a valid overworld"

    def validate(self, text, level):
        if DB.overworlds.get(text) is not None:
            return text
        return None

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        valids = [(overworld.name, overworld.nid) for overworld in DB.overworlds.values()]
        return valids

class OverworldLocation(Validator):
    desc = "accepts the nid of an overworld location/node, or a coordinate x, y"
    decimal_converter = re.compile(r'[^\d.]+')

    def validate(self, text, level):
        try:
            text = self.convert(text)
            if isinstance(text, tuple) and len(text) == 2:
                return text
            for overworld in DB.overworlds.values():
                for node in overworld.overworld_nodes:
                    if node.nid == text:
                        return text
        except:
            pass
        return None

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        valids = []
        for overworld in DB.overworlds.values():
            valids = valids + [(node.name, node.nid) for node in overworld.overworld_nodes.values()]
        return valids

    def convert(self, text: str) -> NID | Tuple[float, float]:
        if len(text.split(',')) == 2: # is coordinate
            try:
                coords = text.split(',')
                x = float(self.decimal_converter.sub('', coords[0]))
                y = float(self.decimal_converter.sub('', coords[1]))
                return (x, y)
            except:
                raise ValueError("Could not parse coordinates from string %s" % text)
        else: # is nid
            return text

class OverworldNodeNID(Validator):
    desc = "accepts the nid of an overworld node only"

    def validate(self, text, level):
        for overworld in DB.overworlds.values():
            for node in overworld.overworld_nodes:
                if node.nid == text:
                    return text
        return None

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        valids = []
        for overworld in DB.overworlds.values():
            valids = valids + [(node.name, node.nid) for node in overworld.overworld_nodes.values()]
        return valids

class OverworldEntity(Validator):
    desc = "accepts the nid of an overworld entity. By default, all parties have associated overworld entities."

    def validate(self, text, level):
        return text

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        valids = [(party.name, party.nid) for party in DB.parties.values()]
        return valids

class Sprite(Validator):
    desc = 'accepts the filename of any sprite resource in the project.'

    def validate(self, text: NID, level: NID):
        if text in SPRITES.keys():
            return text
        return None

    @lru_cache()
    def valid_entries(self, level: NID = None) -> List[Tuple[str, NID]]:
        valids = [(sprite_name, sprite_name) for sprite_name in SPRITES.keys()]
        return valids

validators = {validator.__name__: validator for validator in Validator.__subclasses__()}
option_validators = {validator.__name__: validator for validator in OptionValidator.__subclasses__()}

def validate(var_type, text, level):
    if text and text[0] == '{' and text[-1] == '}': # eval, so assume this is valid
        return text
    validator = validators.get(var_type)
    if validator:
        v = validator()
        return v.validate(text, level)
    validator = option_validators.get(var_type)
    if validator:
        v = validator()
        return v.validate(text, level)
    else:
        return text

def convert(var_type, text):
    if not text:
        return None
    try:
        validator = validators.get(var_type)
        if validator:
            v = validator()
            return v.convert(text)
        validator = option_validators.get(var_type)
        if validator:
            v = validator()
            return v.convert(text)
        else:
            return text
    except:
        return text

def get(keyword) -> Validator:
    if keyword in validators:
        return validators[keyword]
    elif keyword in option_validators:
        return option_validators[keyword]
    return None
