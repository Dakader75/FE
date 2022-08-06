from app.constants import TILEWIDTH, TILEHEIGHT
from app.utilities import utils

from app.data.database import DB
from app.engine.sprites import SPRITES
from app.engine import engine, target_system, equations
from app.engine.game_state import game

class BoundaryInterface():
    draw_order = ('all_spell', 'all_attack', 'spell', 'attack')
    enemy_teams = ('enemy', 'enemy2')
    fog_of_war_tile1 = SPRITES.get('bg_fow_tile')
    fog_of_war_tile2 = SPRITES.get('bg_black_tile')

    def __init__(self, width, height):
        self.modes = {'attack': SPRITES.get('boundary_red'),
                      'all_attack': SPRITES.get('boundary_purple'),
                      'spell': SPRITES.get('boundary_green'),
                      'all_spell': SPRITES.get('boundary_blue')}

        self.width = width
        self.height = height

        # grid of sets. Each set contains the unit nids that are capable
        # of attacking that spot
        # The movement portion -- unit's have an area of influence
        # If they move, they affect all other units in their area of influence
        self.grids = {'attack': self.init_grid(),
                      'spell': self.init_grid(),
                      'movement': self.init_grid()}
        # Key: Unit NID, Value: list of positions where the unit is capable
        # of attacking
        self.dictionaries = {'attack': {},
                             'spell': {},
                             'movement': {}}

        self.draw_flag = False
        self.all_on_flag = False

        self.displaying_units = set()

        self.surf = None
        self.fog_of_war_surf = None

    def init_grid(self):
        cells = []
        for x in range(self.width):
            for y in range(self.height):
                cells.append(set())
        return cells

    def show(self):
        self.draw_flag = True

    def hide(self):
        self.draw_flag = False

    def check_bounds(self, pos):
        return 0 <= pos[0] < self.width and 0 <= pos[1] < self.height

    def toggle_unit(self, unit):
        if unit.nid in self.displaying_units:
            self.displaying_units.discard(unit.nid)
        else:
            self.displaying_units.add(unit.nid)
        self.surf = None

    def reset_unit(self, unit):
        if unit.nid in self.displaying_units:
            self.displaying_units.discard(unit.nid)
            self.surf = None

    def reset_fog_of_war(self):
        self.fog_of_war_surf = None

    def _set(self, positions, mode, nid):
        grid = self.grids[mode]
        self.dictionaries[mode][nid] = set()
        for pos in positions:
            grid[pos[0] * self.height + pos[1]].add(nid)
            self.dictionaries[mode][nid].add(pos)

    def clear(self, mode=None):
        if mode:
            modes = [mode]
        else:
            modes = list(self.grids.keys())
        for m in modes:
            for x in range(self.width):
                for y in range(self.height):
                    self.grids[m][x * self.height + y].clear()
        self.surf = None
        self.fog_of_war_surf = None

    def _add_unit(self, unit):
        valid_moves = target_system.get_valid_moves(unit, force=True)

        if DB.constants.value('zero_move') and unit.get_ai() and not unit.ai_group_active:
            ai_prefab = DB.ai.get(unit.get_ai())
            guard = ai_prefab.guard_ai()
            if guard:
                valid_moves = {unit.position}

        valid_attacks = target_system.get_possible_attacks(unit, valid_moves)
        valid_spells = target_system.get_possible_spell_attacks(unit, valid_moves)
        self._set(valid_attacks, 'attack', unit.nid)
        self._set(valid_spells, 'spell', unit.nid)

        area_of_influence = target_system.find_manhattan_spheres(set(range(1, equations.parser.movement(unit) + 1)), *unit.position)
        area_of_influence = {pos for pos in area_of_influence if self.check_bounds(pos)}
        self._set(area_of_influence, 'movement', unit.nid)

        self.surf = None

    def _remove_unit(self, unit):
        for mode, grid in self.grids.items():
            if unit.nid in self.dictionaries[mode]:
                for (x, y) in self.dictionaries[mode][unit.nid]:
                    grid[x * self.height + y].discard(unit.nid)
                # del self.dictionaries[mode][unit.nid]
        self.surf = None

    def recalculate_unit(self, unit):
        if unit.team in self.enemy_teams:
            self._remove_unit(unit)
            if unit.position:
                self._add_unit(unit)

    def leave(self, unit):
        if unit.team in self.enemy_teams:
            self._remove_unit(unit)

        # Update ranges of other units that might be affected by my leaving
        if unit.position:
            x, y = unit.position
            other_units = {game.get_unit(nid) for nid in self.grids['movement'][x * self.height + y]}
            other_units = {other_unit for other_unit in other_units if not utils.compare_teams(unit.team, other_unit.team)}

            for other_unit in other_units:
                self._remove_unit(other_unit)
            for other_unit in other_units:
                if other_unit.position:
                    self._add_unit(other_unit)

    def arrive(self, unit):
        if unit.position:
            if unit.team in self.enemy_teams:
                self._add_unit(unit)

            # Update ranges of other units that might be affected by my arrival
            x, y = unit.position
            # print(self.grids['movement'][x * self.height + y])
            other_units = {game.get_unit(nid) for nid in self.grids['movement'][x * self.height + y]}
            other_units = {other_unit for other_unit in other_units if not utils.compare_teams(unit.team, other_unit.team)}

            for other_unit in other_units:
                self._remove_unit(other_unit)
            for other_unit in other_units:
                if other_unit.position:
                    self._add_unit(other_unit)

    # Called when map changes
    def reset(self):
        self.clear()
        for unit in game.units:
            if unit.position and unit.team in self.enemy_teams:
                self._add_unit(unit)

    def toggle_all_enemy_attacks(self):
        if self.all_on_flag:
            self.clear_all_enemy_attacks()
        else:
            self.show_all_enemy_attacks()

    def show_all_enemy_attacks(self):
        self.all_on_flag = True
        self.surf = None

    def clear_all_enemy_attacks(self):
        self.all_on_flag = False
        self.surf = None

    def draw(self, surf, full_size, cull_rect):
        if not self.draw_flag:
            return surf

        if not self.surf:
            self.surf = engine.create_surface(full_size, transparent=True)

            for grid_name in self.draw_order:
                # Check whether we can skip this boundary interface
                if grid_name == 'attack' and not self.displaying_units:
                    continue
                elif grid_name == 'spell' and not self.displaying_units:
                    continue
                elif grid_name == 'all_attack' and not self.all_on_flag:
                    continue
                elif grid_name == 'all_spell' and not self.all_on_flag:
                    continue

                if grid_name == 'all_attack' or grid_name == 'attack':
                    grid = self.grids['attack']
                else:
                    grid = self.grids['spell']

                # Remove all units that we shouldn't be able to see from the boundary
                # Fog of War application
                if game.level_vars.get('_fog_of_war'):
                    new_grid = []
                    for cell in grid:
                        new_grid.append({nid for nid in cell if game.board.in_vision(game.get_unit(nid).position)})
                else:
                    new_grid = grid

                for y in range(self.height):
                    for x in range(self.width):
                        cell = new_grid[x * self.height + y]
                        if cell:
                            # Determine whether this tile should have a red display
                            red_display = False
                            for nid in cell:
                                if nid in self.displaying_units:
                                    red_display = True
                                    break

                            if grid_name == 'all_attack' and red_display:
                                continue
                            if grid_name == 'all_spell' and red_display:
                                continue

                            if grid_name == 'attack' and not red_display:
                                continue
                            if grid_name == 'spell' and not red_display:
                                continue

                            image = self.create_image(new_grid, x, y, grid_name)
                            self.surf.blit(image, (x * TILEWIDTH, y * TILEHEIGHT))

        im = engine.subsurface(self.surf, cull_rect)
        surf.blit(im, (0, 0))
        return surf

    def create_image(self, grid, x, y, grid_name):
        top_pos = (x, y - 1)
        left_pos = (x - 1, y)
        right_pos = (x + 1, y)
        bottom_pos = (x, y + 1)

        top = False
        bottom = False
        left = False
        right = False

        if grid_name == 'all_attack' or grid_name == 'all_spell':
            if self.check_bounds(top_pos) and grid[x * self.height + y - 1]:
                top = True
            if self.check_bounds(bottom_pos) and grid[x * self.height + y + 1]:
                bottom = True
            if self.check_bounds(left_pos) and grid[(x - 1) * self.height + y]:
                left = True
            if self.check_bounds(right_pos) and grid[(x + 1) * self.height + y]:
                right = True
        else:
            top = any(nid in self.displaying_units for nid in grid[x * self.height + y - 1]) if self.check_bounds(top_pos) else False
            left = any(nid in self.displaying_units for nid in grid[(x - 1) * self.height + y]) if self.check_bounds(left_pos) else False
            right = any(nid in self.displaying_units for nid in grid[(x + 1) * self.height + y]) if self.check_bounds(right_pos) else False
            bottom = any(nid in self.displaying_units for nid in grid[x * self.height + y + 1]) if self.check_bounds(bottom_pos) else False
        idx = top*8 + left*4 + right*2 + bottom  # Binary logis to get correct index
        return engine.subsurface(self.modes[grid_name], (idx * TILEWIDTH, 0, TILEWIDTH, TILEHEIGHT))

    def draw_fog_of_war(self, surf, full_size, cull_rect):
        if game.level_vars['_fog_of_war']:
            if not self.fog_of_war_surf:
                self.fog_of_war_surf = engine.create_surface(full_size, transparent=True)
                for y in range(self.height):
                    for x in range(self.width):
                        if not game.board.in_vision((x, y)):
                            if game.level_vars['_fog_of_war'] == 2:
                                image = self.fog_of_war_tile2
                            else:
                                image = self.fog_of_war_tile1
                            self.fog_of_war_surf.blit(image, (x * TILEWIDTH, y * TILEHEIGHT))

            im = engine.subsurface(self.fog_of_war_surf, cull_rect)
            surf.blit(im, (0, 0))
        return surf

    def print_grid(self, mode):
        for y in range(self.height):
            print("%02d|" % y, end="")
            for x in range(self.width):
                cell = self.grids[mode][x * self.height + y]
                if cell:
                    print(' %s |' % ','.join(cell), end="")
                else:
                    print('  -  |', end="")
            print('\n', end=""),
