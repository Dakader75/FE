from app.data.item_components import ItemComponent
from app.data.components import Type

from app.utilities import utils
from app.engine import target_system, skill_system
from app.engine.game_state import game 

class BlastAOE(ItemComponent):
    nid = 'blast_aoe'
    desc = "Gives Blast AOE"
    tag = 'aoe'

    expose = Type.Int  # Radius
    value = 1

    def _get_power(self, unit) -> int:
        empowered_splash = skill_system.empower_splash(unit)
        return self.value + 1 + empowered_splash

    def splash(self, unit, item, position) -> tuple:
        ranges = set(range(self._get_power(unit)))
        splash = target_system.find_manhattan_spheres(ranges, position[0], position[1])
        splash = {pos for pos in splash if game.tilemap.check_bounds(pos)}
        from app.engine import item_system
        if item_system.is_spell(unit, item):
            # spell blast
            splash = [game.board.get_unit(s) for s in splash]
            splash = [s.position for s in splash if s]
            return None, splash
        else:
            # regular blast
            splash = [game.board.get_unit(s) for s in splash if s != position]
            splash = [s.position for s in splash if s]
            return position if game.board.get_unit(position) else None, splash

    def splash_positions(self, unit, item, position) -> set:
        ranges = set(range(self._get_power(unit)))
        splash = target_system.find_manhattan_spheres(ranges, position[0], position[1])
        splash = {pos for pos in splash if game.tilemap.check_bounds(pos)}
        return splash

class EnemyBlastAOE(BlastAOE, ItemComponent):
    nid = 'enemy_blast_aoe'
    desc = "Gives Blast AOE that only hits enemies"
    tag = 'aoe'

    def splash(self, unit, item, position) -> tuple:
        ranges = set(range(self._get_power(unit)))
        splash = target_system.find_manhattan_spheres(ranges, position[0], position[1])
        splash = {pos for pos in splash if 0 <= pos[0] < game.tilemap.width and 0 <= pos[1] < game.tilemap.height}
        from app.engine import item_system, skill_system
        if item_system.is_spell(unit, item):
            # spell blast
            splash = [game.board.get_unit(s) for s in splash]
            splash = [s.position for s in splash if s and skill_system.check_enemy(unit, s)]
            return None, splash
        else:
            # regular blast
            splash = [game.board.get_unit(s) for s in splash if s != position]
            splash = [s.position for s in splash if s and skill_system.check_enemy(unit)]
            return position if game.board.get_unit(position) else None, splash

    def splash_positions(self, unit, item, position) -> set:
        from app.engine import skill_system
        ranges = set(range(self._get_power(unit)))
        splash = target_system.find_manhattan_spheres(ranges, position[0], position[1])
        splash = {pos for pos in splash if game.tilemap.check_bounds(pos)}
        # Doesn't highlight allies positions
        splash = {pos for pos in splash if not game.board.get_unit(pos) or skill_system.check_enemy(unit, game.board.get_unit(pos))}
        return splash

class AllyBlastAOE(BlastAOE, ItemComponent):
    nid = 'ally_blast_aoe'
    desc = "Gives Blast AOE that only hits allies"
    tag = 'aoe'

    def splash(self, unit, item, position) -> tuple:
        ranges = set(range(self._get_power(unit)))
        splash = target_system.find_manhattan_spheres(ranges, position[0], position[1])
        splash = {pos for pos in splash if game.tilemap.check_bounds(pos)}
        from app.engine import skill_system
        splash = [game.board.get_unit(s) for s in splash]
        splash = [s.position for s in splash if s and skill_system.check_ally(unit, s)]
        return None, splash

class EquationBlastAOE(BlastAOE, ItemComponent):
    nid = 'equation_blast_aoe'
    desc = "Gives Equation-Sized Blast AOE"
    tag = 'aoe'

    expose = Type.Equation  # Radius
    value = None

    def _get_power(self, unit) -> int:
        from app.engine import equations
        value = equations.parser.get(self.value, unit)
        empowered_splash = skill_system.empower_splash(unit)
        return value + 1 + empowered_splash

class EnemyCleaveAOE(ItemComponent):
    nid = 'enemy_cleave_aoe'
    desc = "Gives Enemy Cleave AOE"
    tag = 'aoe'

    def splash(self, unit, item, position) -> tuple:
        from app.engine import skill_system
        pos = unit.position
        all_positions = {(pos[0] - 1, pos[1] - 1),
                         (pos[0], pos[1] - 1),
                         (pos[0] + 1, pos[1] - 1),
                         (pos[0] - 1, pos[1]),
                         (pos[0] + 1, pos[1]),
                         (pos[0] - 1, pos[1] + 1),
                         (pos[0], pos[1] + 1),
                         (pos[0] + 1, pos[1] + 1)}
        
        all_positions = {pos for pos in all_positions if game.tilemap.check_bounds(pos)}
        all_positions.discard(position)
        splash = all_positions
        splash = [game.board.get_unit(pos) for pos in splash]
        splash = [s.position for s in splash if s and skill_system.check_enemy(unit, s)]
        main_target = position if game.board.get_unit(position) else None
        return main_target, splash

    def splash_positions(self, unit, item, position) -> set:
        from app.engine import skill_system
        pos = unit.position
        all_positions = {(pos[0] - 1, pos[1] - 1),
                         (pos[0], pos[1] - 1),
                         (pos[0] + 1, pos[1] - 1),
                         (pos[0] - 1, pos[1]),
                         (pos[0] + 1, pos[1]),
                         (pos[0] - 1, pos[1] + 1),
                         (pos[0], pos[1] + 1),
                         (pos[0] + 1, pos[1] + 1)}

        all_positions = {pos for pos in all_positions if game.tilemap.check_bounds(pos)}
        all_positions.discard(position)
        splash = all_positions
        # Doesn't highlight allies positions
        splash = {pos for pos in splash if not game.board.get_unit(pos) or skill_system.check_enemy(unit, game.board.get_unit(pos))}
        return splash

class AllAlliesAOE(ItemComponent):
    nid = 'all_allies_aoe'
    desc = "Item affects all allies on the map including self"
    tag = 'aoe'

    def splash(self, unit, item, position) -> tuple:
        from app.engine import skill_system
        splash = [u.position for u in game.units if u.position and skill_system.check_ally(unit, u)]
        return None, splash

    def splash_positions(self, unit, item, position) -> set:
        # All positions
        splash = [(x, y) for x in range(game.tilemap.width) for y in range(game.tilemap.height)]
        return splash

class AllAlliesExceptSelfAOE(ItemComponent):
    nid = 'all_allies_except_self_aoe'
    desc = "Item affects all allies on the map except user"
    tag = 'aoe'

    def splash(self, unit, item, position) -> tuple:
        from app.engine import skill_system
        splash = [u.position for u in game.units if u.position and skill_system.check_ally(unit, u) and u is not unit]
        return None, splash

    def splash_positions(self, unit, item, position) -> set:
        # All positions
        splash = [(x, y) for x in range(game.tilemap.width) for y in range(game.tilemap.height)]
        return splash

class AllEnemiesAOE(ItemComponent):
    nid = 'all_enemies_aoe'
    desc = "Item affects all enemies on the map"
    tag = 'aoe'

    def splash(self, unit, item, position) -> tuple:
        from app.engine import skill_system
        splash = [u.position for u in game.units if u.position and skill_system.check_enemy(unit, u)]
        return None, splash

    def splash_positions(self, unit, item, position) -> set:
        from app.engine import skill_system
        # All positions
        splash = {(x, y) for x in range(game.tilemap.width) for y in range(game.tilemap.height)}
        # Doesn't highlight allies positions
        splash = {pos for pos in splash if not game.board.get_unit(pos) or skill_system.check_enemy(unit, game.board.get_unit(pos))}
        return splash

class LineAOE(ItemComponent):
    nid = 'line_aoe'
    desc = "Gives Line AOE"
    tag = 'aoe'

    def splash(self, unit, item, position) -> tuple:
        splash = set(utils.raytrace(unit.position, position))
        splash.discard(unit.position)
        splash = [game.board.get_unit(s) for s in splash]
        splash = [s.position for s in splash if s]
        return None, splash

    def splash_positions(self, unit, item, position) -> set:
        splash = set(utils.raytrace(unit.position, position))
        splash.discard(unit.position)
        return splash
