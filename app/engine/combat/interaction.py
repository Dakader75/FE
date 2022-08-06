from app.utilities import utils

from app.engine import item_system, skill_system, battle_animation
from app.engine.game_state import game
from app.engine.input_manager import INPUT

from app.engine.combat.simple_combat import SimpleCombat
from app.engine.combat.map_combat import MapCombat
from app.engine.combat.base_combat import BaseCombat
from app.engine.combat.animation_combat import AnimationCombat
from app.engine import config as cf

from app.engine.objects.unit import UnitObject
from app.engine.objects.item import ItemObject

def has_animation(attacker: UnitObject, item: ItemObject, main_target: tuple) -> bool:
    defender: UnitObject = game.board.get_unit(main_target)
    if not defender:
        return False

    def animation_wanted(attacker: UnitObject, defender: UnitObject) -> bool:
        return cf.SETTINGS['animation'] == 'Always' or \
            (cf.SETTINGS['animation'] == 'Your Turn' and attacker.team == 'player') or \
            (cf.SETTINGS['animation'] == 'Combat Only' and skill_system.check_enemy(attacker, defender))

    toggle_anim = INPUT.is_pressed('START')
    if attacker is not defender and animation_wanted(attacker, defender) != toggle_anim:
        if attacker.position and defender.position:
            distance = utils.calculate_distance(attacker.position, defender.position)
        else:
            distance = 1
        attacker_anim = battle_animation.get_battle_anim(attacker, item, distance)
        def_item = defender.get_weapon()
        defender_anim = battle_animation.get_battle_anim(defender, def_item, distance)
        return bool(attacker_anim and defender_anim)

    return False

def engage(attacker: UnitObject, positions: list, main_item: ItemObject, skip: bool = False, script: list = None):
    """
    Builds the correct combat controller for this interaction

    Targets each of the positions in "positions" with the item
    Determines what kind of combat (Simple, Map, or Animation), should be used for this kind of interaction
    "positions" is a list. The subelements of positions can also be a list, if the item is a multitargeting item
    """
    target_positions = []
    main_targets = []
    splashes = []
    if main_item.sequence_item:
        items = main_item.subitems
    else:
        items = [main_item]
    for idx, position in enumerate(positions):
        item = items[idx]
        splash = set()
        if isinstance(position, list):
            for pos in position:
                main_target, s = item_system.splash(attacker, item, pos)
                if main_target:
                    splash.add(main_target)
                splash |= set(s)
            main_target = None
            target_positions.append(position[0])
        else:
            main_target, splash = item_system.splash(attacker, item, position)
            target_positions.append(position)
        main_targets.append(main_target)
        splashes.append(splash)

    if target_positions[0] is None:
        # If we are targeting None, (which means we're in base using an item)
        combat = BaseCombat(attacker, main_item, attacker, script)
    elif skip:
        # If we are skipping
        combat = SimpleCombat(attacker, main_item, items, target_positions, main_targets, splashes, script)
        game.highlight.remove_highlights()
    # If more than one target position or more than one item being used, cannot use animation combat
    elif len(positions) > 1 or len(items) > 1:
        combat = MapCombat(attacker, main_item, items, target_positions, main_targets, splashes, script)
    # If affecting more than one target, cannot use animation combat
    elif not main_targets[0] or splashes[0]:
        combat = MapCombat(attacker, main_item, items, target_positions, main_targets, splashes, script)
    elif has_animation(attacker, item, main_target):
        defender = game.board.get_unit(main_target)
        def_item = defender.get_weapon()
        combat = AnimationCombat(attacker, item, defender, def_item, script)
    else:
        combat = MapCombat(attacker, main_item, items, target_positions, main_targets, splashes, script)
    return combat

def start_combat(unit: UnitObject, target: tuple, item: ItemObject, skip: bool = False,
                 ai_combat: bool = False, event_combat: bool = False, script: list = None):
    """
    Target is a position tuple
    """
    # Set up the target positions
    if item.sequence_item:
        targets = []
        for subitem in item.subitems:
            num_targets = item_system.num_targets(unit, subitem)
            if num_targets > 1:
                targets.append([target] * num_targets)
            else:
                targets.append(target)
    else:
        num_targets = item_system.num_targets(unit, item)
        if num_targets > 1:
            targets = [[target] * num_targets]
        else:
            targets = [target]

    combat = engage(unit, targets, item, skip=skip, script=script)
    combat.ai_combat = ai_combat # Must mark this so we can come back!
    combat.event_combat = event_combat # Must mark this so we can come back!
    game.combat_instance.append(combat)
    game.state.change('combat')
