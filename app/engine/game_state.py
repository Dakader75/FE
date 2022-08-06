from __future__ import annotations

import random
import time
from collections import Counter
from typing import TYPE_CHECKING, Dict, List, Tuple

if TYPE_CHECKING:
    from app.engine import (ai_controller, death,
        game_board, highlight, map_view, movement, phase,
        promotion, ui_view, banner, boundary, camera, cursor,
        initiative, records, save, supports, turnwheel, unit_sprite)
    from app.engine.combat.simple_combat import SimpleCombat
    from app.engine.overworld.overworld_movement_manager import \
        OverworldMovementManager
    from app.engine.overworld.overworld_manager import OverworldManager
    from app.engine.objects.difficulty_mode import DifficultyModeObject
    from app.engine.objects.item import ItemObject
    from app.engine.objects.level import LevelObject
    from app.engine.objects.overworld import OverworldObject
    from app.engine.objects.party import PartyObject
    from app.engine.objects.skill import SkillObject
    from app.engine.objects.unit import UnitObject
    from app.engine.dialog_log import DialogLog
    from app.events.event_manager import EventManager
    from app.events.regions import Region
    from app.utilities.typing import NID

from app.constants import VERSION
from app.data.database import DB
from app.data.difficulty_modes import GrowthOption, PermadeathOption
from app.engine import config as cf
from app.engine import state_machine, static_random
from app.resources.resources import RESOURCES

import logging

class GameState():
    def __init__(self):
        # define all GameState properties
        self.memory: Dict = {}

        self.state: state_machine.StateMachine = state_machine.StateMachine()

        self.alerts: List[banner.Banner] = []

        self.current_mode: DifficultyModeObject = None

        # global variable stores
        self.game_vars: Counter = None
        self.level_vars: Counter = None
        self.playtime: int = 0
        self.current_save_slot: save.SaveSlot = None

        # global registries
        self.unit_registry: Dict[NID, UnitObject] = {}
        self.item_registry: Dict[NID, ItemObject] = {}
        self.skill_registry: Dict[NID, SkillObject] = {}
        self.terrain_status_registry: Dict[NID, NID] = {}
        self.region_registry: Dict[NID, Region] = {}
        self.overworld_registry: Dict[NID, OverworldObject] = {}
        self.parties: Dict[NID, PartyObject] = {}
        self.unlocked_lore: List[NID] = []
        self.dialog_log: DialogLog = None
        self.already_triggered_events: List[NID] = []
        self.market_items: set = []

        # global controllers
        self.supports: supports.SupportController = None
        self.records: records.Recordkeeper = None

        # 'current' state information, typically varies by level
        self.current_level: LevelObject = None
        self._current_party: NID = None
        self.turncount: int = 0
        self.talk_options: List[Tuple[NID, NID]] = []
        self.base_convos: Dict[NID, bool] = {}
        self.action_log: turnwheel.ActionLog = None
        self.events: EventManager = None
        self.map_sprite_registry: Dict[NID, unit_sprite.MapSprite] = {}

        # current-level controllers and game objects
        self.board: game_board.GameBoard = None
        self.cursor: cursor.BaseCursor = None
        self.camera: camera.Camera = None
        self.boundary: boundary.BoundaryInterface = None
        self.phase: phase.PhaseController = None
        self.highlight: highlight.HighlightController = None
        self.initiative: initiative.InitiativeTracker = None
        self.map_view: map_view.MapView = None
        self.movement: movement.MovementManager | OverworldMovementManager = None
        self.death: death.DeathManager = None
        self.ui_view: ui_view.UIView = None
        self.combat_instance: List[SimpleCombat] = []
        self.exp_instance: List[Tuple[UnitObject, int, promotion.PromotionState, str]] = []
        self.mana_instance = []
        self.ai: ai_controller.AIController = None
        self.overworld_controller: OverworldManager = None

        self.clear()

    def is_displaying_overworld(self) -> bool:
        from app.engine.overworld.overworld_map_view import OverworldMapView
        return isinstance(self.map_view, OverworldMapView)

    def clear(self):
        self.game_vars = Counter()
        self.memory = {}

        self.state = state_machine.StateMachine()

        self.playtime = 0

        self.alerts = []
        self.cursor = None
        self.camera = None
        self.boundary = None

        self.current_save_slot = None
        self.current_level = None

    def load_states(self, starting_states):
        self.state.load_states(starting_states)

    # Start a new game
    # When the player clicks "New Game"
    def build_new(self):
        from app.engine import records, supports
        logging.info("Building New Game")
        self.playtime = 0

        self.unit_registry = {}
        self.item_registry = {}
        self.skill_registry = {}
        self.terrain_status_registry = {}
        self.region_registry = {}

        self.current_mode = self.default_mode()

        self.parties = {}
        self.current_party = None
        self.current_level = None
        self.game_vars.clear()

        # Set up random seed
        if cf.SETTINGS['random_seed'] >= 0:
            random_seed = int(cf.SETTINGS['random_seed'])
        else:
            random_seed = random.randint(0, 1023)
        static_random.set_seed(random_seed)
        self.game_vars['_random_seed'] = random_seed

        # initialize all parties
        from app.engine.objects.party import PartyObject
        for party_prefab in DB.parties.values():
            nid, name, leader = party_prefab.nid, party_prefab.name, party_prefab.leader
            self.parties[nid] = PartyObject(nid, name, leader)

        # Initialize all overworlds and enter them into the registry
        from app.engine.objects.overworld import OverworldObject
        for overworld in DB.overworlds.values():
            self.overworld_registry[overworld.nid] = OverworldObject.from_prefab(overworld, self.parties, self.unit_registry)
        self.supports = supports.SupportController()
        self.records = records.Recordkeeper()
        self.market_items = set()
        self.unlocked_lore = []
        from app.engine.dialog_log import DialogLog
        self.dialog_log = DialogLog()
        self.already_triggered_events = []
        self.sweep()
        self.generic()

    def sweep(self):
        """
        Cleans up variables that need to be reset at the end of each level
        """
        from app.engine import turnwheel
        from app.events import event_manager
        self.level_vars = Counter()
        self.turncount = 0
        self.talk_options = []
        self.base_convos = {}
        self.action_log = turnwheel.ActionLog()
        self.events = event_manager.EventManager()
        self.dialog_log.clear()

    def generic(self):
        """
        Done on loading a level, whether from overworld, last level, save_state, etc.
        """
        from app.engine import (ai_controller, camera, death, highlight,
                                map_view, movement, phase, ui_view)

        # Systems
        self.camera = camera.Camera(self)
        self.phase = phase.PhaseController()
        self.highlight = highlight.HighlightController()
        self.map_view = map_view.MapView()
        self.movement = movement.MovementManager()
        self.death = death.DeathManager()
        self.ui_view = ui_view.UIView()
        self.combat_instance = []
        self.exp_instance = []
        self.mana_instance = []
        self.ai = ai_controller.AIController()

        self.alerts.clear()

        # Build registries
        self.map_sprite_registry = {}

    def start_level(self, level_nid, with_party=None):
        """
        Done at the beginning of a new level to start the level up
        """
        self.boundary = None
        self.generic()
        logging.debug("Starting Level %s", level_nid)

        from app.engine.initiative import InitiativeTracker
        from app.engine.level_cursor import LevelCursor
        from app.engine.objects.level import LevelObject
        from app.engine.objects.tilemap import TileMapObject

        level_nid = str(level_nid)
        level_prefab = DB.levels.get(level_nid)
        tilemap_nid = level_prefab.tilemap
        tilemap_prefab = RESOURCES.tilemaps.get(tilemap_nid)
        tilemap = TileMapObject.from_prefab(tilemap_prefab)
        self.cursor = LevelCursor(self)
        self.current_level = LevelObject.from_prefab(level_prefab, tilemap, self.unit_registry)
        if with_party:
            self.current_party = with_party
        else:
            self.current_party = self.current_level.party

        # Build party object for new parties
        if self.current_party not in self.parties:
            self.build_party(self.current_party)

        # Assign every unit the levels party if they don't already have one
        for unit in self.current_level.units:
            if not unit.party:
                unit.party = self.current_party
        self.set_up_game_board(self.current_level.tilemap)

        for region in self.current_level.regions:
            self.register_region(region)

        for unit in self.current_level.units:
            self.full_register(unit)
        for unit in self.current_level.units:
            self.arrive(unit)

        # Handle initiative
        if DB.constants.value('initiative'):
            self.initiative = InitiativeTracker()
            self.initiative.start(self.get_all_units())

    def full_register(self, unit):
        self.register_unit(unit)
        for item in unit.items:
            self.register_item(item)
        for skill in unit.skills:
            self.register_skill(skill)

    def set_up_game_board(self, tilemap):
        from app.engine import boundary, game_board
        self.board = game_board.GameBoard(tilemap)
        self.boundary = boundary.BoundaryInterface(tilemap.width, tilemap.height)

    def save(self):
        self.action_log.record = False

        s_dict = {'units': [unit.save() for unit in self.unit_registry.values()],
                  'items': [item.save() for item in self.item_registry.values()],
                  'skills': [skill.save() for skill in self.skill_registry.values()],
                  'terrain_status_registry': self.terrain_status_registry,
                  'regions': [region.save() for region in self.region_registry.values()],
                  'level': self.current_level.save() if self.current_level else None,
                  'overworlds': [overworld.save() for overworld in self.overworld_registry.values()],
                  'turncount': self.turncount,
                  'playtime': self.playtime,
                  'game_vars': self.game_vars,
                  'level_vars': self.level_vars,
                  'current_mode': self.current_mode.save(),
                  'parties': [party.save() for party in self.parties.values()],
                  'current_party': self.current_party,
                  'state': self.state.save(),
                  'action_log': self.action_log.save(),
                  'events': self.events.save(),
                  'supports': self.supports.save(),
                  'records': self.records.save(),
                  'market_items': self.market_items,  # Item nids
                  'unlocked_lore': self.unlocked_lore,
                  'dialog_log': self.dialog_log.save(),
                  'already_triggered_events': self.already_triggered_events,
                  'talk_options': self.talk_options,
                  'base_convos': self.base_convos,
                  'current_random_state': static_random.get_combat_random_state(),
                  }
        meta_dict = {'playtime': self.playtime,
                     'realtime': time.time(),
                     'version': VERSION,
                     'title': DB.constants.value('title'),
                     'mode': self.current_mode.nid,
                     }
        if self.current_level:
            meta_dict['level_title'] = self.current_level.name
            meta_dict['level_nid'] = self.current_level.nid
        elif self.game_vars.get('_next_level_nid'):
            fake_level = DB.levels.get(self.game_vars.get('_next_level_nid'))
            meta_dict['level_title'] = fake_level.name
            meta_dict['level_nid'] = fake_level.nid
        else:
            meta_dict['level_title'] = 'Overworld'
            meta_dict['level_nid'] = None

        self.action_log.record = True
        return s_dict, meta_dict

    def load(self, s_dict):
        from app.engine import action, records, save, supports, turnwheel, dialog_log
        from app.engine.objects.difficulty_mode import DifficultyModeObject
        from app.engine.objects.item import ItemObject
        from app.engine.objects.level import LevelObject
        from app.engine.objects.overworld import OverworldObject
        from app.engine.objects.party import PartyObject
        from app.engine.objects.skill import SkillObject
        from app.engine.objects.unit import UnitObject
        from app.events import event_manager
        from app.events.regions import Region

        logging.info("Loading Game...")
        self.game_vars = Counter(s_dict.get('game_vars', {}))
        static_random.set_seed(self.game_vars.get('_random_seed', 0))
        self.level_vars = Counter(s_dict.get('level_vars', {}))
        mode_dict = s_dict.get('current_mode')
        if mode_dict:
            self.current_mode = DifficultyModeObject.restore(mode_dict)
        else:
            self.current_mode = self.default_mode()
        self.playtime = float(s_dict['playtime'])
        self.current_party = s_dict['current_party']
        self.turncount = int(s_dict['turncount'])

        self.state.load_states(s_dict['state'][0], s_dict['state'][1])

        self.item_registry = {item['uid']: ItemObject.restore(item) for item in s_dict['items']}
        self.skill_registry = {skill['uid']: SkillObject.restore(skill) for skill in s_dict['skills']}
        save.set_next_uids(self)
        self.terrain_status_registry = s_dict.get('terrain_status_registry', {})
        self.region_registry = {region['nid']: Region.restore(region) for region in s_dict.get('regions', [])}
        self.unit_registry = {unit['nid']: UnitObject.restore(unit) for unit in s_dict['units']}

        # Handle subitems
        for item in self.item_registry.values():
            for subitem_uid in item.subitem_uids:
                subitem = self.item_registry.get(subitem_uid)
                item.subitems.append(subitem)
                subitem.parent_item = item
        # Handle subskill
        for skill in self.skill_registry.values():
            if skill.subskill_uid is not None:
                subskill = self.skill_registry.get(skill.subskill_uid)
                skill.subskill = subskill
                subskill.parent_skill = skill

        self.parties = {party_data['nid']: PartyObject.restore(party_data) for party_data in s_dict['parties']}
        self.market_items = s_dict.get('market_items', set())
        self.unlocked_lore = s_dict.get('unlocked_lore', [])
        self.dialog_log = dialog_log.DialogLog.restore(s_dict.get('dialog_log', []))

        self.already_triggered_events = s_dict.get('already_triggered_events', [])
        self.talk_options = s_dict.get('talk_options', [])
        self.base_convos = s_dict.get('base_convos', {})

        # load all overworlds, or initialize them
        if 'overworlds' in s_dict:
            for overworld in s_dict['overworlds']:
                overworld_obj = OverworldObject.restore(overworld, self)
                self.overworld_registry[overworld_obj.nid] = overworld_obj
        for overworld in DB.overworlds.values():
            if overworld.nid not in self.overworld_registry:
                self.overworld_registry[overworld.nid] = OverworldObject.from_prefab(overworld, self.parties, self.unit_registry)

        self.action_log = turnwheel.ActionLog.restore(s_dict['action_log'])
        if s_dict.get('supports'):
            self.supports = supports.SupportController.restore(s_dict['supports'])
        else:
            self.supports = supports.SupportController()
        if s_dict.get('records'):
            self.records = records.Recordkeeper.restore(s_dict['records'])
        else:
            self.records = records.Recordkeeper()

        if 'current_random_state' in s_dict:
            static_random.set_combat_random_state(s_dict['current_random_state'])

        if s_dict['level']:
            logging.info("Loading Level...")
            self.current_level = LevelObject.restore(s_dict['level'], self)
            self.set_up_game_board(self.current_level.tilemap)

            self.generic()
            from app.engine.level_cursor import LevelCursor
            self.cursor = LevelCursor(self)

            # Now have units actually arrive on map
            for unit in self.units:
                if unit.position:
                    self.board.set_unit(unit.position, unit)
                    self.boundary.arrive(unit)
                    action.UpdateFogOfWar(unit).execute()

            self.cursor.autocursor(True)

        self.events = event_manager.EventManager.restore(s_dict.get('events'))

    def clean_up(self):
        from app.engine import (action, item_funcs, item_system, skill_system,
                                supports)

        supports.increment_end_chapter_supports()

        self.game_vars['_current_turnwheel_uses'] = \
            self.game_vars.get('_max_turnwheel_uses', -1)

        for unit in self.unit_registry.values():
            self.leave(unit)
        for unit in self.unit_registry.values():
            # Unit cleanup
            if unit.traveler:
                unit.traveler = None
                action.execute(action.RemoveSkill(unit, 'Rescue'))
            unit.set_hp(1000)  # Set to full health
            if DB.constants.value('reset_mana'):
                unit.set_mana(1000)  # Set to full mana
            unit.position = None
            unit.sprite.change_state('normal')
            unit.reset()

        for item in self.item_registry.values():
            unit = None
            if item.owner_nid:
                unit = self.get_unit(item.owner_nid)
            item_system.on_end_chapter(unit, item)

        for skill in self.skill_registry.values():
            unit = None
            if skill.owner_nid:
                unit = self.get_unit(skill.owner_nid)
                if unit:
                    skill_system.on_end_chapter(unit, skill)
                else:
                    logging.error("Unable to find owner %s in unit_registry", skill.owner_nid)

        self.terrain_status_registry.clear()
        self.region_registry.clear()

        # Remove all generics
        self.unit_registry = {k: v for (k, v) in self.unit_registry.items() if not v.generic}

        # Remove any skill that's not on a unit and does not have a parent_skill
        for k, v in list(self.skill_registry.items()):
            if v.parent_skill:
                if v.parent_skill.owner_nid:
                    if v.parent_skill.owner_nid not in self.unit_registry:
                        del self.skill_registry[k]
                else:
                    del self.skill_registry[k]
            elif v.owner_nid:  # Remove skills from units that no longer exist
                if v.owner_nid not in self.unit_registry:
                    del self.skill_registry[k]
            else:
                del self.skill_registry[k]

        # Remove any item that's not on a unit or in the convoy
        for k, v in list(self.item_registry.items()):
            if v.owner_nid:  # Remove items from units that no longer exist
                if v.owner_nid not in self.unit_registry:
                    del self.item_registry[k]
            else:
                for party in self.parties.values():
                    if v in party.convoy or (v.parent_item and v.parent_item in party.convoy):
                        break
                else:  # No party ever found
                    del self.item_registry[k]

        # Handle player death
        for unit in self.unit_registry.values():
            if unit.dead:
                action.do(action.ChangeFatigue(unit, -unit.get_fatigue()))  # Reset fatigue
            if unit.dead and unit.team == 'player':
                if not game.current_mode.permadeath:
                    unit.dead = False  # Resurrect unit
                elif DB.constants.value('convoy_on_death'):
                    for item in item_funcs.get_all_tradeable_items(unit):
                        unit.remove_item(item)
                        # Put the item in the unit's party's convoy
                        self.parties[unit.party].convoy.append(item)

        # Remove unnecessary information between levels
        self.sweep()
        self.current_level = None

    @property
    def level(self):
        return self.current_level

    @property
    def current_party(self):
        if self.is_displaying_overworld() and self.overworld_controller.selected_entity.nid:
            self._current_party = self.overworld_controller.selected_entity.nid
        return self._current_party

    @current_party.setter
    def current_party(self, party_nid: NID):
        self._current_party = party_nid
        if self.overworld_controller and party_nid:
            self.overworld_controller.select_entity(self._current_party)

    @property
    def tilemap(self):
        if self.is_displaying_overworld():
            return self.overworld_controller.tilemap
        elif self.current_level:
            return self.current_level.tilemap
        else:
            return None

    @property
    def mode(self):
        return DB.difficulty_modes.get(self.current_mode.nid)

    def default_mode(self):
        from app.engine.objects.difficulty_mode import DifficultyModeObject
        first_mode = DB.difficulty_modes[0]
        if first_mode.permadeath_choice == PermadeathOption.PLAYER_CHOICE:
            permadeath = False
        else:
            permadeath = first_mode.permadeath_choice == PermadeathOption.CLASSIC
        if first_mode.growths_choice == GrowthOption.PLAYER_CHOICE:
            growths = GrowthOption.FIXED
        else:
            growths = first_mode.growths_choice
        return DifficultyModeObject(first_mode.nid, permadeath, growths)

    @property
    def party(self):
        return self.parties[self.current_party]

    def get_party(self, party_nid: str = None):
        if not party_nid:
            party_nid = self.current_party
        if party_nid not in self.parties:
            self.build_party(party_nid)
        return self.parties[party_nid]

    def build_party(self, party_nid):
        from app.engine.objects.party import PartyObject
        party_prefab = DB.parties.get(party_nid)
        if not party_prefab:
            party_prefab = DB.parties[0]
        nid, name, leader = party_prefab.nid, party_prefab.name, party_prefab.leader
        self.parties[self.current_party] = PartyObject(nid, name, leader)

    @property
    def units(self):
        return list(self.unit_registry.values())

    def register_unit(self, unit):
        logging.debug("Registering unit %s as %s", unit, unit.nid)
        self.unit_registry[unit.nid] = unit

    def register_item(self, item):
        logging.debug("Registering item %s as %s", item, item.uid)
        self.item_registry[item.uid] = item
        # For multi-items
        for subitem in item.subitems:
            self.item_registry[subitem.uid] = subitem

    def register_skill(self, skill):
        logging.debug("Registering skill %s as %s", skill, skill.uid)
        self.skill_registry[skill.uid] = skill
        # For aura skills
        if skill.subskill:
            self.skill_registry[skill.subskill.uid] = skill.subskill

    def register_terrain_status(self, key, skill_uid):
        logging.debug("Registering terrain status %s", skill_uid)
        self.terrain_status_registry[key] = skill_uid

    def register_region(self, region):
        logging.debug("Registering region %s", region.nid)
        self.region_registry[region.nid] = region

    def get_unit(self, unit_nid):
        """
        Can get units not just in the current level
        Could be used to get units in overworld, base,
        etc.
        """
        unit = self.unit_registry.get(unit_nid)
        return unit

    def get_item(self, item_uid):
        item = self.item_registry.get(item_uid)
        return item

    def get_skill(self, skill_uid):
        skill = self.skill_registry.get(skill_uid)
        return skill

    def get_terrain_status(self, key):
        skill_uid = self.terrain_status_registry.get(key)
        return skill_uid

    def get_region(self, region_nid):
        region = self.region_registry.get(region_nid)
        return region

    def get_all_units(self) -> List[UnitObject]:
        return [unit for unit in self.units if unit.position and not unit.dead and not unit.is_dying and 'Tile' not in unit.tags]

    def get_player_units(self) -> List[UnitObject]:
        return [unit for unit in self.get_all_units() if unit.team == 'player']

    def get_enemy_units(self) -> List[UnitObject]:
        return [unit for unit in self.get_all_units() if unit.team.startswith('enemy')]

    def get_all_units_in_party(self, party=None) -> List[UnitObject]:
        if party is None:
            party = self.current_party
        return [unit for unit in self.units if unit.team == 'player' and not unit.generic and unit.party == party]

    def get_units_in_party(self, party=None) -> List[UnitObject]:
        if party is None:
            party = self.current_party
        return [unit for unit in self.get_all_units_in_party() if not unit.dead]

    def check_dead(self, nid):
        unit = self.get_unit(nid)
        if unit and (unit.dead or unit.is_dying):
            return True
        return False

    def check_alive(self, nid):
        unit = self.get_unit(nid)
        if unit and not (unit.dead or unit.is_dying):
            return True
        return False

    def leave(self, unit, test=False):
        """
        # Removes a unit from the map
        # This function should always be called BEFORE changing the unit's position
        # Handles:
        # 1. removing the unit from the boundary manager
        # 2. Removes any auras from the unit's skill list, since they will no longer be on the map
        # 3. Removes any of the unit's own auras from the map
        # 4. Removes any status/skills that the terrain or regions on the map are giving
        # the unit
        #
        # If "test" is True, some of these are skipped, such as removing the unit from
        # the boundary manager and registering these actions with the action_log
        # Set "test" to True when you are just testing what would happen by moving
        # to a position (generally used for AI)
        """
        from app.engine import action, aura_funcs
        if unit.position:
            logging.debug("Leave %s %s", unit.nid, unit.position)
            # Auras
            for aura_data in game.board.get_auras(unit.position):
                child_aura_uid, target = aura_data
                child_skill = self.get_skill(child_aura_uid)
                aura_funcs.remove_aura(unit, child_skill, test)
            if not test:
                for skill in unit.skills:
                    if skill.aura:
                        aura_funcs.release_aura(unit, skill, self)
            # Regions
            for region in game.level.regions:
                if region.region_type == 'status' and region.contains(unit.position):
                    skill_uid = self.get_terrain_status(region.nid)
                    skill_obj = self.get_skill(skill_uid)
                    if skill_obj and skill_obj in unit.skills:
                        if test:
                            unit.skills.remove(skill_obj)
                        else:
                            act = action.RemoveSkill(unit, skill_obj)
                            action.do(act)
            # Tiles
            layer = self.tilemap.get_layer(unit.position)
            terrain_key = (*unit.position, layer)  # Terrain position and layer
            skill_uid = self.get_terrain_status(terrain_key)
            skill_obj = self.get_skill(skill_uid)
            if skill_obj and skill_obj in unit.skills:
                if test:
                    unit.skills.remove(skill_obj)
                else:
                    act = action.RemoveSkill(unit, skill_obj)
                    action.do(act)
            # Boundary
            if not test:
                self.boundary.leave(unit)
            # Board
            if not test:
                self.board.remove_unit(unit.position, unit)

    def arrive(self, unit, test=False):
        """
        # Adds a unit to the map
        # This function should always be called AFTER changing the unit's position
        # Handles:
        # 1. adding the unit to the boundary manager
        # 2. adding any auras from that the unit should be affected by to the the unit's skill list
        # 3. Adding any of the unit's own auras to other units
        # 4. Adding any status/skills that the terrain or regions on the map are giving
        #
        # If "test" is True, some of these are skipped, such as adding the unit to
        # the boundary manager and registering these actions with the action_log
        # Set "test" to True when you are just testing what would happen by moving
        # to a position (generally used for AI)
        """
        from app.engine import aura_funcs, skill_system
        if unit.position:
            logging.debug("Arrive %s %s", unit.nid, unit.position)
            if not test:
                self.board.set_unit(unit.position, unit)
            # Tiles
            if not skill_system.ignore_terrain(unit):
                self.add_terrain_status(unit, test)
            # Regions
            if not skill_system.ignore_region_status(unit):
                for region in game.level.regions:
                    if region.region_type == 'status' and region.contains(unit.position):
                        self.add_region_status(unit, region, test)
            # Auras
            aura_funcs.pull_auras(unit, self, test)
            if not test:
                for skill in unit.skills:
                    if skill.aura:
                        aura_funcs.propagate_aura(unit, skill, self)
            # Boundary
            if not test:
                self.boundary.arrive(unit)

    def add_terrain_status(self, unit, test):
        from app.engine import action, item_funcs
        layer = self.tilemap.get_layer(unit.position)
        terrain_key = (*unit.position, layer)  # Terrain position and layer
        skill_uid = self.get_terrain_status(terrain_key)
        skill_obj = self.get_skill(skill_uid)

        if not skill_obj:
            terrain_nid = self.tilemap.get_terrain(unit.position)
            terrain = DB.terrain.get(terrain_nid)
            if terrain and terrain.status:
                skill_obj = item_funcs.create_skill(unit, terrain.status)
                if skill_obj:
                    game.register_skill(skill_obj)
                    self.register_terrain_status(terrain_key, skill_obj.uid)
                else:
                    logging.error("Could not create skill with nid: %s" % terrain.status)

        if skill_obj:
            # Only bother adding if not already present
            if skill_obj not in unit.skills:
                if test:
                    # Don't need to use action for test
                    unit.skills.append(skill_obj)
                else:
                    act = action.AddSkill(unit, skill_obj)
                    action.do(act)

    def add_region_status(self, unit, region, test):
        from app.engine import action, item_funcs
        skill_uid = self.get_terrain_status(region.nid)
        skill_obj = self.get_skill(skill_uid)

        if not skill_obj:
            skill_obj = item_funcs.create_skill(unit, region.sub_nid)
            game.register_skill(skill_obj)
            self.register_terrain_status(region.nid, skill_obj.uid)

        if skill_obj:
            # Only bother adding if not already present
            if skill_obj not in unit.skills:
                if test:
                    # Don't need to use action for test
                    unit.skills.append(skill_obj)
                else:
                    act = action.AddSkill(unit, skill_obj)
                    action.do(act)

    def check_for_region(self, position, region_type, sub_nid=None):
        if not position:
            return None
        for region in game.level.regions:
            if region.region_type == region_type and region.contains(position):
                if not sub_nid or region.sub_nid == sub_nid:
                    return region
        return None

    def get_all_formation_spots(self) -> list:
        legal_spots = set()
        for region in game.level.regions:
            if region.region_type == 'formation':
                for x in range(region.size[0]):
                    for y in range(region.size[1]):
                        legal_spots.add((region.position[0] + x, region.position[1] + y))
        return legal_spots

    def get_open_formation_spots(self) -> list:
        all_formation_spots = self.get_all_formation_spots()
        return sorted({pos for pos in all_formation_spots if not self.board.get_unit(pos)})

    def get_next_formation_spot(self) -> tuple:
        legal_spots = self.get_open_formation_spots()
        if legal_spots:
            return legal_spots[0]
        return None

    def get_money(self):
        return self.parties[self.current_party].money

    def set_money(self, val):
        self.parties[self.current_party].money = val

    def get_bexp(self):
        return self.parties[self.current_party].bexp

    def inc_bexp(self, amount):
        self.parties[self.current_party].bexp += amount

    def set_bexp(self, amount):
        self.parties[self.current_party].bexp = amount

game = GameState()

def start_game():
    global game
    if not game:
        game = GameState()
    else:
        game.clear()  # Need to use old game if called twice in a row
    game.load_states(['title_start'])
    return game

def start_level(level_nid):
    global game
    logging.info("Start Level %s" % level_nid)
    if not game:
        game = GameState()
    else:
        game.clear()  # Need to use old game if called twice in a row
    game.load_states(['turn_change'])
    game.build_new()
    game.start_level(level_nid)
    return game

def load_level(level_nid, save_loc):
    global game
    logging.info("Load Level %s" % level_nid)
    if not game:
        game = GameState()
    else:
        game.clear()
    import pickle

    from app.engine import save
    with open(save_loc, 'rb') as fp:
        s_dict = pickle.load(fp)
    game.load_states(['turn_change'])
    game.build_new()
    game.load(s_dict)
    save.set_next_uids(game)
    game.start_level(level_nid)
    return game
