from app.utilities import utils

from app.data.item_components import ItemComponent
from app.data.components import Type

from app.engine import skill_system, target_system, item_funcs
from app.engine.game_state import game 

class TargetsAnything(ItemComponent):
    nid = 'target_tile'
    desc = "Item targets any tile"
    tag = 'target'

    def ai_targets(self, unit, item) -> set:
        return {(x, y) for x in range(game.tilemap.width) for y in range(game.tilemap.height)}

    def valid_targets(self, unit, item) -> set:
        rng = item_funcs.get_range(unit, item)
        positions = target_system.find_manhattan_spheres(rng, *unit.position)
        return {pos for pos in positions if game.tilemap.check_bounds(pos)}

class TargetsUnits(ItemComponent):
    nid = 'target_unit'
    desc = "Item targets any unit"
    tag = 'target'

    def ai_targets(self, unit, item):
        return {other.position for other in game.units if other.position}

    def valid_targets(self, unit, item) -> set:
        targets = {other.position for other in game.units if other.position}
        return {t for t in targets if utils.calculate_distance(unit.position, t) in item_funcs.get_range(unit, item)}

class TargetsEnemies(ItemComponent):
    nid = 'target_enemy'
    desc = "Item targets any enemy"
    tag = 'target'

    def ai_targets(self, unit, item):
        return {other.position for other in game.units if other.position and 
                skill_system.check_enemy(unit, other)}

    def valid_targets(self, unit, item) -> set:
        targets = {other.position for other in game.units if other.position and 
                   skill_system.check_enemy(unit, other)}        
        return {t for t in targets if utils.calculate_distance(unit.position, t) in item_funcs.get_range(unit, item)}

class TargetsAllies(ItemComponent):
    nid = 'target_ally'
    desc = "Item targets any ally"
    tag = 'target'

    def ai_targets(self, unit, item):
        return {other.position for other in game.units if other.position and 
                skill_system.check_ally(unit, other)}

    def valid_targets(self, unit, item) -> set:
        targets = {other.position for other in game.units if other.position and 
                   skill_system.check_ally(unit, other)}        
        return {t for t in targets if utils.calculate_distance(unit.position, t) in item_funcs.get_range(unit, item)}

class EvalTargetRestrict(ItemComponent):
    nid = 'eval_target_restrict'
    desc = "Use this to restrict what units can be targeted"
    tag = 'target'

    expose = Type.String
    value = 'True'

    def target_restrict(self, unit, item, def_pos, splash) -> bool:
        from app.engine import evaluate
        try:
            target = game.board.get_unit(def_pos)
            if target and evaluate.evaluate(self.value, target, position=def_pos):
                return True
            for s_pos in splash:
                target = game.board.get_unit(s_pos)
                if evaluate.evaluate(self.value, target, position=s_pos):
                    return True
        except Exception as e:
            print("Could not evaluate %s (%s)" % (self.value, e))
            return True
        return False

class EmptyTileTargetRestrict(ItemComponent):
    nid = 'empty_tile_target_restrict'
    desc = "Item will only target tiles without units on them"
    tag = 'target'

    def target_restrict(self, unit, item, def_pos, splash) -> bool:
        if not game.board.get_unit(def_pos):
            return True
        return False

class MinimumRange(ItemComponent):
    nid = 'min_range'
    desc = "Set the minimum_range of the item to an integer"
    tag = 'target'

    expose = Type.Int
    value = 0

    def minimum_range(self, unit, item) -> int:
        return self.value

class MaximumRange(ItemComponent):
    nid = 'max_range'
    desc = "Set the maximum_range of the item to an integer"
    tag = 'target'

    expose = Type.Int
    value = 0

    def maximum_range(self, unit, item) -> int:
        return self.value

class MaximumEquationRange(ItemComponent):
    nid = 'max_equation_range'
    desc = "Set the maximum_range of the item to an equation"
    tag = 'target'

    expose = Type.Equation

    def maximum_range(self, unit, item) -> int:
        from app.engine import equations
        value = equations.parser.get(self.value, unit)
        return int(value)

class GlobalRange(ItemComponent):
    nid = 'global_range'
    desc = "Item has no maximum range"
    tag = 'target'

    def maximum_range(self, unit, item) -> int:
        return 99
