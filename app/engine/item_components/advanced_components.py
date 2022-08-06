from app.data.item_components import ItemComponent
from app.data.components import Type

from app.engine import action
from app.engine import skill_system
from app.engine.game_state import game

class MultiItem(ItemComponent):
    nid = 'multi_item'
    desc = "Item that contains multiple items. Don't abuse!"
    tag = 'advanced'

    expose = (Type.List, Type.Item)

class SequenceItem(ItemComponent):
    nid = 'sequence_item'
    desc = "Item that contains a sequence of items used for targeting"
    tag = 'advanced'

    expose = (Type.List, Type.Item)

class MultiTarget(ItemComponent):
    nid = 'multi_target'
    desc = "Item can target multiple targets."
    tag = 'advanced'

    expose = Type.Int
    value = 2

    def num_targets(self, unit, item) -> int:
        return self.value

class AllowSameTarget(ItemComponent):
    nid = 'allow_same_target'
    desc = "Item can target the same target multiple times"
    tag = 'advanced'

    def allow_same_target(self, unit, item) -> bool:
        return True

class StoreUnit(ItemComponent):
    nid = 'store_unit'
    desc = "Item registers a unit on the map on hit"
    tag = 'advanced'

    def init(self, item):
        self.item.data['stored_unit'] = None

    def on_hit(self, actions, playback, unit, item, target, target_pos, mode, attack_info):
        if not skill_system.ignore_forced_movement(target):
            self.item.data['stored_unit'] = target.nid
            # actions.append(action.WarpOut(target))
            playback.append(('rescue_hit', unit, item, target))

class UnloadUnit(ItemComponent):
    nid = 'unload_unit'
    desc = "Item takes stored unit and warps them to the new location on the map"
    tag = 'advanced'

    def target_restrict(self, unit, item, def_pos, splash) -> bool:
        if not game.board.get_unit(def_pos) and game.movement.check_simple_traversable(def_pos):
            return True
        return False
    
    def on_hit(self, actions, playback, unit, item, target, target_pos, mode, attack_info):
        if self.item.data.get('stored_unit'):
            rescuee = game.get_unit(self.item.data['stored_unit'])
            self.item.data['stored_unit'] = None
            if rescuee:
                actions.append(action.Warp(rescuee, target_pos))
                # Move camera over position
                game.cursor.set_pos(target_pos)
