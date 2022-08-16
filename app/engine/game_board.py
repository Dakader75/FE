from app.data.database import DB

from app.engine import target_system, line_of_sight
from app.engine.game_state import game

class Node():
    __slots__ = ['reachable', 'cost', 'x', 'y', 'parent', 'g', 'h', 'f', 'true_f']

    def __init__(self, x: int, y: int, reachable: bool, cost: float):
        """
        Initialize new cell
        reachable - is cell reachable? is not a wall?
        cost - how many movement points to reach
        """
        self.reachable = reachable
        self.cost = cost
        self.x = x
        self.y = y
        self.reset()

    def reset(self):
        self.parent = None
        self.g = 0
        self.h = 0
        self.f = 0
        self.true_f = 0

    def __gt__(self, n):
        return self.cost > n

    def __lt__(self, n):
        return self.cost < n

    def __repr__(self):
        return "Node(%d, %d): cost=%d, g=%d, h=%d, f=%f, %s" % (self.x, self.y, self.cost, self.g, self.h, self.f, self.reachable)

class GameBoard(object):
    # __slots__ = ['width', 'height', 'grids', 'team_grid', 'unit_grid',
    #              'aura_grid', 'known_auras']

    def __init__(self, tilemap):
        self.width = tilemap.width
        self.height = tilemap.height
        self.bounds = (0, 0, self.width - 1, self.height - 1)
        self.mcost_grids = {}

        self.reset_grid(tilemap)

        # Keeps track of what team occupies which tile
        self.team_grid = self.init_unit_grid()
        # Keeps track of which unit occupies which tile
        self.unit_grid = self.init_unit_grid()

        # Fog of War -- one for each team
        self.fog_of_war_grids = {}
        for team in DB.teams:
            self.fog_of_war_grids[team] = self.init_aura_grid()
        self.fow_vantage_point = {}  # Unit: Position where the unit is that's looking

        # For Auras
        self.aura_grid = self.init_aura_grid()
        # Key: Aura Skill Uid, Value: Set of positions
        self.known_auras = {}

        # For opacity
        self.opacity_grid = self.init_opacity_grid(tilemap)

    def set_bounds(self, min_x, min_y, max_x, max_y):
        self.bounds = (min_x, min_y, max_x, max_y)

    def check_bounds(self, pos):
        return self.bounds[0] <= pos[0] <= self.bounds[2] and self.bounds[1] <= pos[1] <= self.bounds[3]

    def reset_grid(self, tilemap):
        # For each movement type
        for idx, mode in enumerate(DB.mcost.unit_types):
            self.mcost_grids[mode] = self.init_grid(mode, tilemap)
        self.opacity_grid = self.init_opacity_grid(tilemap)

    # For movement
    def init_grid(self, movement_group, tilemap):
        cells = []
        for x in range(self.width):
            for y in range(self.height):
                terrain_nid = tilemap.get_terrain((x, y))
                if DB.terrain:
                    terrain = DB.terrain.get(terrain_nid)
                    if not terrain:
                        terrain = DB.terrain[0]
                    tile_cost = DB.mcost.get_mcost(movement_group, terrain.mtype)
                else:
                    tile_cost = 1
                cells.append(Node(x, y, tile_cost < 99, tile_cost))

        return cells

    def get_grid(self, movement_group):
        return self.mcost_grids[movement_group]

    def init_unit_grid(self):
        cells = []
        for x in range(self.width):
            for y in range(self.height):
                cells.append([])
        return cells

    def set_unit(self, pos, unit):
        idx = pos[0] * self.height + pos[1]
        self.unit_grid[idx].append(unit)
        self.team_grid[idx].append(unit.team)

    def remove_unit(self, pos, unit):
        idx = pos[0] * self.height + pos[1]
        if unit in self.unit_grid[idx]:
            self.unit_grid[idx].remove(unit)
            self.team_grid[idx].remove(unit.team)

    def get_unit(self, pos):
        if not pos:
            return None
        idx = pos[0] * self.height + pos[1]
        if self.unit_grid[idx]:
            return self.unit_grid[idx][0]
        return None

    def rationalize_pos(self, pos: tuple):
        """Similar to in roam_state, except
        does not force the unit into a particular position"""
        return (int(round(pos[0])), int(round(pos[1])))

    def get_team(self, pos):
        if not pos:
            return None
        idx = pos[0] * self.height + pos[1]
        if self.team_grid[idx]:
            return self.team_grid[idx][0]
        return None

    # Fog of war
    def update_fow(self, pos, unit, sight_range: int):
        grid = self.fog_of_war_grids[unit.team]
        # Remove the old vision
        self.fow_vantage_point[unit.nid] = None
        for cell in grid:
            cell.discard(unit.nid)
        # Add new vision
        if pos:
            self.fow_vantage_point[unit.nid] = pos
            positions = target_system.find_manhattan_spheres(range(sight_range + 1), pos[0], pos[1])
            positions = {pos for pos in positions if 0 <= pos[0] < self.width and 0 <= pos[1] < self.height}
            for position in positions:
                idx = position[0] * self.height + position[1]
                grid[idx].add(unit.nid)

    def in_vision(self, pos, team='player') -> bool:
        if not game.level_vars.get('_fog_of_war'):
            return True  # Always in vision if not in fog of war
        idx = pos[0] * self.height + pos[1]
        if team == 'player':
            if DB.constants.value('fog_los'):
                fog_of_war_radius = game.level_vars.get('_fog_of_war_radius', 0)
                valid = line_of_sight.simple_check(pos, 'player', fog_of_war_radius) or line_of_sight.simple_check(pos, 'other', fog_of_war_radius)
                if not valid:
                    return False
            player_grid = self.fog_of_war_grids['player']
            if player_grid[idx]:
                return True
            other_grid = self.fog_of_war_grids['other']
            if other_grid[idx]:
                return True
        else:
            if DB.constants.value('fog_los'):
                fog_of_war_radius = self.get_fog_of_war_radius(team)
                valid = line_of_sight.simple_check(pos, team, fog_of_war_radius)
                if not valid:
                    return False
            grid = self.fog_of_war_grids[team]
            if grid[idx]:
                return True
        return False

    def get_fog_of_war_radius(self, team: str) -> int:
        ai_fog_of_war_radius = game.level_vars.get('_ai_fog_of_war_radius', game.level_vars.get('_fog_of_war_radius', 0))
        if team == 'player':
            fog_of_war_radius = game.level_vars.get('_fog_of_war_radius', 0)
        elif team == 'other':
            fog_of_war_radius = game.level_vars.get('_other_fog_of_war_radius', ai_fog_of_war_radius)
        else:
            fog_of_war_radius = ai_fog_of_war_radius
        return fog_of_war_radius

    # Line of sight
    def init_opacity_grid(self, tilemap):
        cells = []
        for x in range(self.width):
            for y in range(self.height):
                terrain = tilemap.get_terrain((x, y))
                t = DB.terrain.get(terrain)
                if t:
                    cells.append(t.opaque)
                else:
                    cells.append(False)
        return cells

    def get_opacity(self, pos) -> bool:
        if not pos:
            return False
        idx = pos[0] * self.height + pos[1]
        return self.opacity_grid[idx]

    # Auras
    def init_aura_grid(self):
        cells = []
        for x in range(self.width):
            for y in range(self.height):
                cells.append(set())
        return cells

    def reset_aura(self, child_skill):
        if child_skill.uid in self.known_auras:
            self.known_auras[child_skill.uid].clear()

    def add_aura(self, pos, unit, child_skill, target):
        idx = pos[0] * self.height + pos[1]
        self.aura_grid[idx].add((child_skill.uid, target))
        if child_skill.uid not in self.known_auras:
            self.known_auras[child_skill.uid] = set()
        self.known_auras[child_skill.uid].add(pos)

    def remove_aura(self, pos, child_skill):
        idx = pos[0] * self.height + pos[1]
        for aura_data in list(self.aura_grid[idx]):
            if aura_data[0] == child_skill.uid:
                self.aura_grid[idx].discard(aura_data)
        if child_skill.uid in self.known_auras:
            self.known_auras[child_skill.uid].discard(pos)

    def get_auras(self, pos):
        idx = pos[0] * self.height + pos[1]
        return self.aura_grid[idx]

    def get_aura_positions(self, child_skill) -> set:
        return self.known_auras.get(child_skill.uid, set())
