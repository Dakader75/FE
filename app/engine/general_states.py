from collections import OrderedDict

from app.constants import TILEWIDTH, TILEHEIGHT, WINWIDTH, WINHEIGHT, TILEX
from app.data.database import DB

from app.engine.sprites import SPRITES
from app.engine.fonts import FONT
from app.engine.sound import SOUNDTHREAD
from app.engine.state import State, MapState
import app.engine.config as cf
from app.engine.game_state import game
from app.engine import engine, action, menus, image_mods, \
    banner, save, phase, skill_system, target_system, item_system, \
    item_funcs, ui_view, info_menu, base_surf, gui, background, dialog, \
    text_funcs, equations, evaluate, supports
from app.engine.combat import interaction
from app.engine.selection_helper import SelectionHelper
from app.engine.abilities import ABILITIES, PRIMARY_ABILITIES, OTHER_ABILITIES
from app.engine.input_manager import INPUT
from app.engine.fluid_scroll import FluidScroll

import logging

class TurnChangeState(MapState):
    name = 'turn_change'

    def begin(self):
        # handle end turn supports
        if DB.constants.value('initiative') and game.initiative.get_current_unit().team == 'player':
            supports.increment_unit_end_turn_supports(game.initiative.get_current_unit())
            game.memory['previous_cursor_position'] = game.cursor.position
        elif game.phase.get_current() == 'player':
            supports.increment_team_end_turn_supports('player')
            game.memory['previous_cursor_position'] = game.cursor.position

        # Clear all previous states in state machine except me
        game.state.refresh()
        game.state.back()  # Turn Change should only last 1 frame
        return 'repeat'

    def end(self):
        if DB.constants.value('initiative'):
            action.do(action.IncInitiativeTurn())
            game.state.change('initiative_upkeep')
            if game.initiative.at_start():
                action.do(action.IncrementTurn())
                game.events.trigger('turn_change')
                if game.turncount - 1 <= 0:  # Beginning of the level
                    for unit in game.get_all_units_in_party():
                        # Give out fatigue statuses if necessary at the beginning of the level
                        action.do(action.ChangeFatigue(unit, 0))
                    game.events.trigger('level_start')
        else:
            game.phase.next()  # Go to next phase
            # If entering player phase
            if game.phase.get_current() == 'player':
                action.do(action.IncrementTurn())
                action.do(action.UpdateRecords('turn', None))
                game.state.change('free')
                game.state.change('status_upkeep')
                game.state.change('phase_change')
                # EVENTS TRIGGER HERE
                game.events.trigger('turn_change')
                if game.turncount - 1 <= 0:  # Beginning of the level
                    for unit in game.get_all_units_in_party():
                        # Give out fatigue statuses if necessary at the beginning of the level
                        action.do(action.ChangeFatigue(unit, 0))
                    game.events.trigger('level_start')
            else:
                game.state.change('ai')
                game.state.change('status_upkeep')
                game.state.change('phase_change')
                # EVENTS TRIGGER HERE
                if game.phase.get_current() == 'enemy':
                    game.events.trigger('enemy_turn_change')
                elif game.phase.get_current() == 'enemy2':
                    game.events.trigger('enemy2_turn_change')
                elif game.phase.get_current() == 'other':
                    game.events.trigger('other_turn_change')

    def take_input(self, event):
        return 'repeat'

class InitiativeUpkeep(MapState):
    name = 'initiative_upkeep'

    def begin(self):
        game.state.back()
        return 'repeat'

    def end(self):
        game.phase.next()
        if game.initiative.get_current_unit().team == 'player':
            game.state.change('free')
        else:
            game.state.change('ai')
        game.state.change('status_upkeep')
        game.state.change('phase_change')

    def take_input(self, event):
        return 'repeat'

class PhaseChangeState(MapState):
    name = 'phase_change'

    def refresh_fatigue(self):
        refresh_these = [unit for unit in game.get_all_units_in_party() if not unit.position]
        for unit in refresh_these:
            action.do(action.ChangeFatigue(unit, -unit.get_fatigue()))

    def begin(self):
        self.save_state()
        logging.info("Phase Change Start")
        # These are done here instead of in turnchange because
        # introScript and other event scripts will have to go on the stack
        # in between this and turn change
        # And they technically happen before I want the player to have the turnwheel locked
        # units reset, etc.
        phase.fade_out_phase_music()
        action.do(action.LockTurnwheel(game.phase.get_current() != 'player'))
        if DB.constants.value('fatigue') and game.turncount == 1 and game.phase.get_current() == 'player':
            self.refresh_fatigue()
        action.do(action.ResetAll([unit for unit in game.units if not unit.dead]))
        game.cursor.hide()
        game.phase.slide_in()

        if DB.constants.value('initiative'):
            unit = game.initiative.get_current_unit()
            if unit.position:
                game.cursor.set_pos(unit.position)

    def update(self):
        super().update()
        done = game.phase.update()
        if done:
            game.state.back()

    def draw(self, surf):
        surf = super().draw(surf)
        surf = game.phase.draw(surf)
        return surf

    def end(self):
        logging.info("Phase Change End")
        phase.fade_in_phase_music()

    def save_state(self):
        GAME_NID = str(DB.constants.value('game_nid'))
        if game.phase.get_current() == 'player':
            logging.info("Saving as we enter player phase!")
            name = GAME_NID + '-turn_change-' + game.level.nid + '-' + str(game.turncount)
            save.suspend_game(game, 'turn_change', name=name)
        elif game.phase.get_current() == 'enemy':
            logging.info("Saving as we enter enemy phase!")
            name = GAME_NID + '-enemy_turn_change-' + game.level.nid + '-' + str(game.turncount)
            save.suspend_game(game, 'enemy_turn_change', name=name)

class FreeState(MapState):
    name = 'free'

    def begin(self):
        if game.level.roam and game.level.roam_unit:
            game.state.change('free_roam')
            return 'repeat'

        game.cursor.show()
        game.boundary.show()
        # The turnwheel will not be able to go before this moment
        phase.fade_in_phase_music()
        if game.turncount == 1:
            game.action_log.set_first_free_action()

    def take_input(self, event):
        game.cursor.set_speed_state(INPUT.is_pressed('BACK'))
        game.cursor.take_input()

        if event == 'INFO':
            info_menu.handle_info()

        elif event == 'AUX':
            info_menu.handle_aux()

        elif event == 'SELECT':
            cur_pos = game.cursor.position
            cur_unit = game.board.get_unit(cur_pos)
            if cur_unit and not cur_unit.finished and 'Tile' not in cur_unit.tags and game.board.in_vision(cur_unit.position):
                if skill_system.can_select(cur_unit) and (not DB.constants.value('initiative') or game.initiative.get_current_unit() is cur_unit):
                    game.cursor.cur_unit = cur_unit
                    SOUNDTHREAD.play_sfx('Select 3')
                    game.state.change('move')
                    game.cursor.place_arrows()
                    game.events.trigger('unit_select', cur_unit, position=cur_unit.position)
                else:
                    if cur_unit.team == 'enemy' or cur_unit.team == 'enemy2':
                        SOUNDTHREAD.play_sfx('Select 3')
                        game.boundary.toggle_unit(cur_unit)
                    else:
                        SOUNDTHREAD.play_sfx('Error')
            else:
                game.state.change('option_menu')

        elif event == 'BACK':
            pass

        elif event == 'START':
            SOUNDTHREAD.play_sfx('Select 5')
            if DB.constants.value('initiative'):
                game.initiative.toggle_draw()
            else:
                game.state.change('minimap')

    def update(self):
        super().update()
        game.highlight.handle_hover()

        # Auto-end turn
        autoend_turn = False
        # Check to see if all ally units have completed their turns and no unit is active and the game is in the free state.
        if cf.SETTINGS['autoend_turn'] and any(unit.position for unit in game.units) and \
                (all(unit.finished for unit in game.units if unit.position and unit.team == 'player')):
            autoend_turn = True
        if DB.constants.value('initiative') and game.initiative.get_current_unit().finished:
            autoend_turn = True

        if autoend_turn:
            # End the turn
            logging.info('Autoending turn.')
            game.state.change('turn_change')
            game.state.change('status_endstep')
            game.state.change('ai')
            return 'repeat'

    def end(self):
        game.cursor.set_speed_state(False)
        game.highlight.remove_highlights()

def suspend():
    game.state.back()
    game.state.process_temp_state()
    logging.info('Suspending game...')
    save.suspend_game(game, 'suspend')
    logging.debug("Suspend state: %s", game.state.state_names())
    logging.debug("Suspend temp state: %s", game.state.temp_state)
    game.state.clear()
    game.state.change('title_start')

def battle_save():
    game.state.back()
    logging.info('Creating battle save...')
    game.memory['save_kind'] = 'battle'
    game.state.change('in_chapter_save')
    game.state.change('transition_out')

class OptionMenuState(MapState):
    name = 'option_menu'

    def start(self):
        game.cursor.hide()
        options = ['Unit', 'Objective', 'Options']
        info_desc = ['Unit_desc', 'Objective_desc', 'Options_desc']
        ignore = [False, False, False]
        if game.current_mode.permadeath:
            options.append('Suspend')
            info_desc.append('Suspend_desc')
            ignore.append(False)
        else:
            options.append('Save')
            info_desc.append('Save_desc')
            ignore.append(False)
        if not game.level or not game.level.roam:
            options.append('End')
            info_desc.append('End_desc')
        ignore.append(False)
        unlocked_lore = [lore for lore in DB.lore if lore.nid in game.unlocked_lore and lore.category == 'Guide']
        if unlocked_lore:
            options.insert(2, 'Guide')
            info_desc.insert(2, 'Guide_desc')
            ignore.insert(2, False)
        if DB.constants.get('turnwheel').value and (not game.level or not game.level.roam):
            options.insert(1, 'Turnwheel')
            info_desc.insert(1, 'Turnwheel_desc')
            ignore.insert(1, False)
        if cf.SETTINGS['debug']:
            options.insert(0, 'Debug')
            info_desc.insert(0, 'Debug_desc')
            ignore.insert(0, False)
        self.menu = menus.Choice(None, options, info=info_desc)
        self.menu.set_ignore(ignore)

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        self.menu.handle_mouse()
        if 'DOWN' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_down(first_push)
        elif 'UP' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_up(first_push)

        if event == 'BACK':
            SOUNDTHREAD.play_sfx('Select 4')
            game.state.back()

        elif event == 'SELECT':
            SOUNDTHREAD.play_sfx('Select 1')
            selection = self.menu.get_current()
            if selection == 'End':
                if cf.SETTINGS['confirm_end']:
                    game.memory['option_owner'] = selection
                    game.memory['option_menu'] = self.menu
                    game.state.change('option_child')
                else:
                    game.state.back()
                    game.state.change('turn_change')
                    game.state.change('status_endstep')
                    game.state.change('ai')
                    game.ui_view.remove_unit_display()
                    return 'repeat'
            elif selection == 'Suspend' or selection == 'Save':
                if cf.SETTINGS['confirm_end']:
                    game.memory['option_owner'] = selection
                    game.memory['option_menu'] = self.menu
                    game.state.change('option_child')
                else:
                    if selection == 'Suspend':
                        suspend()
                    elif selection == 'Save':
                        battle_save()
            elif selection == 'Unit':
                game.memory['next_state'] = 'unit_menu'
                game.state.change('transition_to')
            elif selection == 'Objective':
                game.memory['next_state'] = 'objective_menu'
                game.state.change('transition_to')
            elif selection == 'Guide':
                game.memory['next_state'] = 'base_guide'
                game.state.change('transition_to')
            elif selection == 'Options':
                game.memory['next_state'] = 'settings_menu'
                game.state.change('transition_to')
            elif selection == 'Turnwheel':
                if cf.SETTINGS['debug'] or game.game_vars.get('_current_turnwheel_uses', 1) > 0:
                    game.state.change('turnwheel')
                else:
                    alert = banner.Custom("Turnwheel_empty")
                    # Add banner sound
                    game.alerts.append(alert)
                    game.state.change('alert')
            elif selection == 'Debug':
                game.state.change('debug')

        elif event == 'INFO':
            self.menu.toggle_info()

    def update(self):
        super().update()
        self.menu.update()

    def draw(self, surf):
        surf = super().draw(surf)
        self.menu.draw(surf)
        return surf

class OptionChildState(State):
    name = 'option_child'
    transparent = True

    def begin(self):
        if 'option_owner' in game.memory:
            selection = game.memory['option_owner']
            topleft = game.memory['option_menu']
        else:
            selection = None
            topleft = None
        options = ['Yes', 'No']
        self.menu = menus.Choice(selection, options, topleft)

    def take_input(self, event):
        self.menu.handle_mouse()
        if event == 'DOWN':
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_down()
        elif event == 'UP':
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_up()

        elif event == 'BACK':
            SOUNDTHREAD.play_sfx('Select 4')
            game.state.back()

        elif event == 'SELECT':
            selection = self.menu.get_current()
            if selection == 'Yes':
                SOUNDTHREAD.play_sfx('Select 1')
                if self.menu.owner == 'End':
                    game.state.back()
                    game.state.back()
                    game.state.change('turn_change')
                    game.state.change('status_endstep')
                    game.state.change('ai')
                    game.ui_view.remove_unit_display()
                    return 'repeat'
                elif self.menu.owner == 'Suspend':
                    game.state.back()
                    suspend()
                elif self.menu.owner == 'Save':
                    game.state.back()
                    battle_save()
                elif self.menu.owner == 'Discard' or self.menu.owner == 'Storage':
                    item = game.memory['option_item']
                    cur_unit = game.memory['option_unit']
                    if item in cur_unit.items:
                        if self.menu.owner == 'Discard':
                            action.do(action.RemoveItem(cur_unit, item))
                        elif self.menu.owner == 'Storage':
                            action.do(action.StoreItem(cur_unit, item))
                    if item_funcs.too_much_in_inventory(cur_unit):
                        game.state.back()
                    elif cur_unit.items:
                        game.state.back()
                        game.state.back()
                    else:  # If the unit has no more items, head all the way back to menu
                        game.state.back()
                        game.state.back()
                        game.state.back()
            else:
                SOUNDTHREAD.play_sfx('Select 4')
                game.state.back()

    def update(self):
        self.menu.update()

    def draw(self, surf):
        self.menu.draw(surf)
        return surf

class MoveState(MapState):
    name = 'move'

    def begin(self):
        game.cursor.show()
        cur_unit = game.cursor.cur_unit
        cur_unit.sprite.change_state('selected')

        # Reset their previous position
        if cur_unit.previous_position != cur_unit.position:
            action.do(action.SetPreviousPosition(cur_unit))

        # To keep track of for swapping
        if cur_unit.traveler:
            cur_unit.lead_unit = True

        if cur_unit.has_traded:
            self.valid_moves = target_system.get_valid_moves(cur_unit)
            game.highlight.display_moves(self.valid_moves, light=False)
        else:
            self.valid_moves = game.highlight.display_highlights(cur_unit)
        game.highlight.display_aura_highlights(cur_unit)

        game.cursor.show_arrows()

    def take_input(self, event):
        game.cursor.take_input()
        cur_unit = game.cursor.cur_unit

        if event == 'INFO':
            pass
        elif event == 'AUX':
            pass

        elif event == 'BACK':
            SOUNDTHREAD.play_sfx('Select 4')
            game.cursor.set_pos(cur_unit.position)
            game.state.clear()
            game.state.change('free')
            if cur_unit.has_attacked or cur_unit.has_traded:
                if not cur_unit.finished:
                    cur_unit.wait()
            else:
                cur_unit.sprite.change_state('normal')

        elif event == 'SELECT':
            if game.cursor.position == cur_unit.position:
                SOUNDTHREAD.play_sfx('Select 2')
                if cur_unit.has_attacked or cur_unit.has_traded:
                    game.state.clear()
                    game.state.change('free')
                    if not cur_unit.finished:
                        cur_unit.wait()
                else:
                    # Just move in place
                    cur_unit.current_move = action.Move(cur_unit, game.cursor.position)
                    action.execute(cur_unit.current_move)
                    game.state.change('menu')

            elif game.cursor.position in self.valid_moves:
                if game.board.in_vision(game.cursor.position) and game.board.get_unit(game.cursor.position):
                    SOUNDTHREAD.play_sfx('Error')
                else:
                    witch_warp = set(skill_system.witch_warp(cur_unit))
                    if cur_unit.has_attacked or cur_unit.has_traded:
                        cur_unit.current_move = action.CantoMove(cur_unit, game.cursor.position)
                        game.state.change('canto_wait')
                    elif game.cursor.position in witch_warp:
                        cur_unit.current_move = action.Warp(cur_unit, game.cursor.position)
                        game.state.change('menu')
                    else:
                        cur_unit.current_move = action.Move(cur_unit, game.cursor.position)
                        game.state.change('menu')
                    game.state.change('movement')
                    action.do(cur_unit.current_move)
            else:
                SOUNDTHREAD.play_sfx('Error')

    def end(self):
        game.cursor.remove_arrows()
        game.highlight.remove_highlights()

class MovementState(MapState):
    # Responsible for moving units that need to be moved
    name = 'movement'

    def begin(self):
        game.cursor.hide()

    def update(self):
        super().update()
        game.movement.update()
        if len(game.movement) <= 0:
            if game.movement.surprised:
                game.movement.surprised = False
                game.state.clear()
                game.state.change('free')
            else:
                game.state.back()
            return 'repeat'

class WaitState(MapState):
    """
    State that forces all units that should have waited to wait
    """
    name = 'wait'

    def update(self):
        super().update()
        game.state.back()
        for unit in game.units:
            if unit.has_attacked and not unit.finished:
                unit.wait()
        return 'repeat'

class CantoWaitState(MapState):
    name = 'canto_wait'

    def start(self):
        self.cur_unit = game.cursor.cur_unit
        self.menu = menus.Choice(self.cur_unit, ['Wait'])

    def begin(self):
        self.cur_unit.sprite.change_state('selected')

    def take_input(self, event):
        if event == 'INFO':
            pass

        elif event == 'SELECT':
            game.state.clear()
            game.state.change('free')
            self.cur_unit.wait()

        elif event == 'BACK':
            if self.cur_unit.current_move:
                action.reverse(self.cur_unit.current_move)
                self.cur_unit.current_move = None
                game.cursor.set_pos(self.cur_unit.position)
            game.state.back()

    def update(self):
        super().update()
        self.menu.update()

    def draw(self, surf):
        surf = super().draw(surf)
        surf = self.menu.draw(surf)
        return surf

class MoveCameraState(MapState):
    name = 'move_camera'

    def update(self):
        super().update()
        if game.camera.at_rest():
            game.state.back()
            return 'repeat'

class MenuState(MapState):
    name = 'menu'
    menu = None
    normal_options = {'Item', 'Wait', 'Take', 'Give', 'Rescue', 'Trade', 'Drop', 'Visit', 'Armory', 'Vendor', 'Spells', 'Attack', 'Steal', 'Shove', 'Pair Up', 'Swap', 'Separate', 'Transfer'}

    def begin(self):
        # Play this here because there's a gap in sound while unit is moving
        SOUNDTHREAD.play_sfx('Select 2')
        game.cursor.hide()
        self.cur_unit = game.cursor.cur_unit
        if not self.cur_unit or not self.cur_unit.position:
            # Could happen if unit escaped
            game.state.clear()
            game.state.change('free')
            return 'repeat'

        skill_system.deactivate_all_combat_arts(self.cur_unit)

        if not self.cur_unit.has_attacked:
            self.cur_unit.sprite.change_state('menu')
        else:
            self.cur_unit.sprite.change_state('selected')
        game.cursor.set_pos(self.cur_unit.position)

        options = []

        # Handle primary ability options (attack, spell, talk)
        self.target_dict = OrderedDict()
        for ability in PRIMARY_ABILITIES:
            t = ability.targets(self.cur_unit)
            self.target_dict[ability.name] = ability
            if t:
                options.append(ability.name)

        # Handle region event options
        self.valid_regions = []
        for region in game.level.regions:
            if region.region_type == 'event' and region.contains(self.cur_unit.position):
                try:
                    truth = evaluate.evaluate(region.condition, self.cur_unit, region=region)
                    logging.debug("Testing region: %s %s", region.condition, truth)
                    # No duplicates
                    if truth and region.sub_nid not in options:
                        options.append(region.sub_nid)
                        self.valid_regions.append(region)
                except:
                    logging.error("Region condition {%s} could not be evaluated" % region.condition)

        # Handle regular ability options (give, drop, rescue, take, item, supply, trade, etc...)
        for ability in OTHER_ABILITIES:
            t = ability.targets(self.cur_unit)
            self.target_dict[ability.name] = ability
            if t:
                options.append(ability.name)

        options.append("Wait")

        # Handle extra ability options
        self.extra_abilities = skill_system.get_extra_abilities(self.cur_unit)
        if 'Spells' in options:
            start_index = options.index('Spells') + 1
        elif 'Attack' in options:
            start_index = options.index('Attack') + 1
        else:
            start_index = len(self.valid_regions)
        for ability_name, ability in self.extra_abilities.items():
            if target_system.get_valid_targets(self.cur_unit, ability):
                options.insert(start_index, ability_name)

        # Handle combat art options
        self.combat_arts = skill_system.get_combat_arts(self.cur_unit)
        if 'Attack' in options:
            start_index = options.index('Attack') + 1
        else:
            start_index = len(self.valid_regions)
        for ability_name in self.combat_arts:
            options.insert(start_index, ability_name)

        # Draw highlights
        for ability in ABILITIES:
            if ability.name in options:
                # Only draw one set of highlights
                if ability.highlights(self.cur_unit):
                    break
        if skill_system.has_canto(self.cur_unit, self.cur_unit):
            # Shows the canto moves in the menu
            moves = target_system.get_valid_moves(self.cur_unit)
            game.highlight.display_moves(moves)
        game.highlight.display_aura_highlights(self.cur_unit)

        self.menu = menus.Choice(self.cur_unit, options)
        self.menu.set_limit(8)
        self.menu.set_color(['text-green' if option not in self.normal_options else 'text-white' for option in options])

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        self.menu.handle_mouse()
        if 'DOWN' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_down(first_push)
        elif 'UP' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_up(first_push)

        # Back, put unit back to where he/she started
        if event == 'BACK':
            SOUNDTHREAD.play_sfx('Select 4')
            if self.cur_unit.has_traded:
                if skill_system.has_canto(self.cur_unit, self.cur_unit):
                    game.cursor.set_pos(self.cur_unit.position)
                    game.state.change('move')
                    game.cursor.place_arrows()
                else:
                    print(1)
                    game.state.clear()
                    game.state.change('free')
                    self.cur_unit.wait()
            else:
                # Reverse Swap here
                if not self.cur_unit.lead_unit and self.cur_unit.traveler:
                    self.cur_unit.lead_unit = False
                    u = game.get_unit(self.cur_unit.traveler)
                    act = action.SwapPaired(self.cur_unit, u)
                    act.execute()
                    self.cur_unit = u
                    game.cursor.cur_unit = u
                else:
                    if self.cur_unit.current_move:
                        action.reverse(self.cur_unit.current_move)
                        self.cur_unit.current_move = None
                    # game.cursor.set_pos(self.cur_unit.position)
                    game.state.change('move')
                    game.cursor.construct_arrows(game.cursor.path[::-1])

        elif event == 'INFO':
            pass

        elif event == 'SELECT':
            SOUNDTHREAD.play_sfx('Select 1')
            selection = self.menu.get_current()
            logging.info("Player selected %s", selection)
            game.highlight.remove_highlights()

            if selection == 'Item':
                game.state.change('item')
            elif selection == 'Attack':
                game.memory['targets'] = self.target_dict[selection].targets(self.cur_unit)
                game.memory['ability'] = 'Attack'
                game.state.change('weapon_choice')
            elif selection == 'Spells':
                game.memory['targets'] = self.target_dict[selection].targets(self.cur_unit)
                game.memory['ability'] = 'Spells'
                game.state.change('spell_choice')
            elif selection == 'Supply':
                game.memory['current_unit'] = self.cur_unit
                game.memory['next_state'] = 'supply_items'
                game.state.change('transition_to')
            elif selection == 'Wait':
                game.state.clear()
                game.state.change('free')
                self.cur_unit.wait()
            # A region event
            elif selection in [region.sub_nid for region in self.valid_regions]:
                for region in self.valid_regions:
                    if region.sub_nid == selection:
                        did_trigger = game.events.trigger(selection, self.cur_unit, position=self.cur_unit.position, region=region)
                        if did_trigger:
                            self.menu = None  # Remove menu for a little (Don't worry, it will come back)
                        if did_trigger and region.only_once:
                            action.do(action.RemoveRegion(region))
                        # if did_trigger:
                            # action.do(action.HasTraded(self.cur_unit))
            # An extra ability
            elif selection in self.extra_abilities:
                item = self.extra_abilities[selection]
                targets = target_system.get_valid_targets(self.cur_unit, item)
                game.memory['targets'] = targets
                game.memory['ability'] = selection
                game.memory['item'] = item
                game.state.change('combat_targeting')
            # A combat art
            elif selection in self.combat_arts:
                skill = self.combat_arts[selection][0]
                game.memory['ability'] = 'Combat Art'
                game.memory['valid_weapons'] = self.combat_arts[selection][1]
                skill_system.activate_combat_art(self.cur_unit, skill)
                game.state.change('weapon_choice')
            else:  # Selection is one of the other abilities
                game.memory['ability'] = self.target_dict[selection]
                game.state.change('targeting')
                if selection in ('Talk', 'Support'):
                    self.menu = None  # So it's not shown during the event

    def update(self):
        super().update()
        if self.menu:
            self.menu.update()

    def draw(self, surf):
        surf = super().draw(surf)
        if self.menu:
            surf = self.menu.draw(surf)
        return surf

    def end(self):
        game.highlight.remove_highlights()

class ItemState(MapState):
    name = 'item'

    def _get_options(self):
        # items = item_funcs.get_all_items(self.cur_unit)
        # items = [item for item in items if (item in self.cur_unit.items or item_funcs.can_use(self.cur_unit, item))]
        items = self.cur_unit.items
        return items

    def start(self):
        self.cur_unit = game.cursor.cur_unit
        options = self._get_options()
        self.menu = menus.Choice(self.cur_unit, options)

    def begin(self):
        game.cursor.hide()
        self.menu.update_options(self._get_options())
        self.item_desc_panel = ui_view.ItemDescriptionPanel(self.cur_unit, self.menu.get_current())

    def _item_desc_update(self):
        current = self.menu.get_current()
        self.item_desc_panel.set_item(current)

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        did_move = self.menu.handle_mouse()
        if did_move:
            self._item_desc_update()

        if 'DOWN' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_down(first_push)
            self._item_desc_update()
            
        elif 'UP' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_up(first_push)
            self._item_desc_update()

        if event == 'BACK':
            if self.menu.info_flag:
                self.menu.toggle_info()
                SOUNDTHREAD.play_sfx('Info Out')
            else:
                SOUNDTHREAD.play_sfx('Select 4')
                game.state.back()

        elif event == 'SELECT':
            if self.menu.info_flag:
                pass
            else:
                SOUNDTHREAD.play_sfx('Select 1')
                game.memory['parent_menu'] = self.menu
                game.state.change('item_child')

        elif event == 'INFO':
            self.menu.toggle_info()
            if self.menu.info_flag:
                SOUNDTHREAD.play_sfx('Info In')
            else:
                SOUNDTHREAD.play_sfx('Info Out')

    def update(self):
        super().update()
        self.menu.update()

    def draw(self, surf):
        surf = super().draw(surf)
        surf = self.item_desc_panel.draw(surf)
        surf = self.menu.draw(surf)
        return surf

class ItemChildState(MapState):
    name = 'item_child'
    transparent = True

    def begin(self):
        parent_menu = game.memory['parent_menu']
        item = parent_menu.get_current()
        self.cur_unit = game.cursor.cur_unit

        options = []
        if item_system.equippable(self.cur_unit, item) and \
                item_funcs.available(self.cur_unit, item) and \
                item in self.cur_unit.items:
            options.append("Equip")
        if item_funcs.can_use(self.cur_unit, item) and not self.cur_unit.has_attacked:
            options.append("Use")
        if not item_system.locked(self.cur_unit, item) and item in self.cur_unit.items:
            if game.game_vars.get('_convoy'):
                options.append('Storage')
            else:
                options.append('Discard')
        if not options:
            options.append('Nothing')

        self.menu = menus.Choice(item, options, parent_menu)
        self.menu.gem = False

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        self.menu.handle_mouse()
        if 'DOWN' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_down(first_push)
        elif 'UP' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_up(first_push)

        if event == 'BACK':
            SOUNDTHREAD.play_sfx('Select 4')
            game.state.back()

        elif event == 'SELECT':
            SOUNDTHREAD.play_sfx('Select 1')
            selection = self.menu.get_current()
            item = self.menu.owner
            if selection == 'Use':
                interaction.start_combat(self.cur_unit, self.cur_unit.position, item)
            elif selection == 'Equip':
                action.do(action.EquipItem(self.cur_unit, item))
                if item in self.cur_unit.items:
                    action.do(action.BringToTopItem(self.cur_unit, item))
                    game.memory['parent_menu'].current_index = 0  # Reset selection
                game.state.back()
            elif selection == 'Storage' or selection == 'Discard':
                game.memory['option_owner'] = selection
                game.memory['option_item'] = item
                game.memory['option_unit'] = self.cur_unit
                game.memory['option_menu'] = self.menu
                game.state.change('option_child')

    def update(self):
        super().update()
        self.menu.update()

    def draw(self, surf):
        surf = self.menu.draw(surf)
        return surf

class ItemDiscardState(MapState):
    name = 'item_discard'
    menu = None
    pennant = None

    def start(self):
        game.cursor.hide()
        self.cur_unit = game.cursor.cur_unit
        options = self.cur_unit.items
        self.menu = menus.Choice(self.cur_unit, options)

        if game.game_vars.get('_convoy'):
            self.pennant = banner.Pennant('Choose item to send to storage')
        else:
            self.pennant = banner.Pennant('Choose item to discard')

    def begin(self):
        self.menu.update_options(self.cur_unit.items)
        # Don't need to do this if we are under items
        if not item_funcs.too_much_in_inventory(self.cur_unit):
            game.state.back()
            return 'repeat'

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        self.menu.handle_mouse()
        if 'DOWN' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_down(first_push)
        elif 'UP' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_up(first_push)

        if event == 'BACK':
            SOUNDTHREAD.play_sfx('Error')

        elif event == 'SELECT':
            SOUNDTHREAD.play_sfx('Select 1')
            selection = self.menu.get_current()
            owner = 'Storage' if game.game_vars.get('_convoy') else 'Discard'
            game.memory['option_owner'] = owner
            game.memory['option_item'] = selection
            game.memory['option_unit'] = self.cur_unit
            game.memory['option_menu'] = self.menu
            game.state.change('option_child')

        elif event == 'INFO':
            self.menu.toggle_info()

    def update(self):
        super().update()
        self.menu.update()

    def draw(self, surf):
        surf = super().draw(surf)
        if self.pennant:
            draw_on_top = game.cursor.position[1] >= game.tilemap.height - 1
            self.pennant.draw(surf, draw_on_top)
        if self.menu:
            surf = self.menu.draw(surf)
        return surf

class WeaponChoiceState(MapState):
    name = 'weapon_choice'

    def get_options(self, unit) -> list:
        if game.memory.get('valid_weapons'):
            options = game.memory['valid_weapons']
        else:
            options = target_system.get_all_weapons(unit)
        # Skill straining
        options = [option for option in options if target_system.get_valid_targets(unit, option)]
        return options

    def disp_attacks(self, unit, item):
        valid_attacks = target_system.get_attacks(unit, item)
        game.highlight.display_possible_attacks(valid_attacks)

    def begin(self):
        game.cursor.hide()
        self.cur_unit = game.cursor.cur_unit
        self.cur_unit.sprite.change_state('chosen')
        options = self.get_options(self.cur_unit)
        self.menu = menus.Choice(self.cur_unit, options)
        self.item_desc_panel = ui_view.ItemDescriptionPanel(self.cur_unit, self.menu.get_current())
        self.disp_attacks(self.cur_unit, self.menu.get_current())

    def _item_desc_update(self):
        current = self.menu.get_current()
        self.item_desc_panel.set_item(current)
        game.highlight.remove_highlights()
        self.disp_attacks(self.cur_unit, current)

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        did_move = self.menu.handle_mouse()
        if did_move:
            self._item_desc_update()

        if 'DOWN' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_down(first_push)
            self._item_desc_update()

        elif 'UP' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_up(first_push)
            self._item_desc_update()

        if event == 'BACK':
            SOUNDTHREAD.play_sfx('Select 4')
            game.memory['valid_weapons'] = None
            game.state.back()

        elif event == 'SELECT':
            SOUNDTHREAD.play_sfx('Select 1')
            selection = self.menu.get_current()
            # Only bother to equip if it's a weapon
            # We don't equip spells
            if item_system.is_weapon(self.cur_unit, selection):
                equip_action = action.EquipItem(self.cur_unit, selection)
                # game.memory['equip_action'] = equip_action
                action.do(equip_action)

            # If the item is in our inventory, bring it to the top
            if selection in self.cur_unit.items:
                action.do(action.BringToTopItem(self.cur_unit, selection))

            game.memory['item'] = selection
            game.state.change('combat_targeting')

        elif event == 'INFO':
            self.menu.toggle_info()

    def update(self):
        super().update()
        self.menu.update()

    def draw(self, surf):
        surf = super().draw(surf)
        surf = self.item_desc_panel.draw(surf)
        surf = self.menu.draw(surf)
        return surf

    def end(self):
        game.highlight.remove_highlights()

class SpellChoiceState(WeaponChoiceState):
    name = 'spell_choice'

    def get_options(self, unit) -> list:
        options = target_system.get_all_spells(unit)
        # Skill straining
        options = [option for option in options if target_system.get_valid_targets(unit, option)]
        return options

    def disp_attacks(self, unit, item):
        spell_attacks = target_system.get_attacks(unit, item)
        game.highlight.display_possible_spell_attacks(spell_attacks)

class TargetingState(MapState):
    name = 'targeting'

    def start(self):
        self.cur_unit = game.cursor.cur_unit

        # Should always come with associated ability
        self.ability = game.memory.get('ability')
        good_pos = self.ability.targets(self.cur_unit)

        self.selection = SelectionHelper(good_pos)
        closest_pos = self.selection.get_closest(self.cur_unit.position)
        game.cursor.set_pos(closest_pos)

        self.pennant = banner.Pennant(self.ability.name + '_desc')

        # Only used for Trade ability, to enable trading
        # with rescued units
        self.traveler_mode = False  # Should we be targeting the traveler?

    def begin(self):
        game.cursor.combat_show()
        self.cur_unit.sprite.change_state('chosen')

    def take_input(self, event):
        self.fluid.update()
        directions = self.fluid.get_directions()

        if 'DOWN' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            if self.ability.name == 'Trade':
                current_target = game.cursor.get_hover()
                traveler = current_target.traveler
                if traveler and game.get_unit(traveler).team == self.cur_unit.team:
                    self.traveler_mode = not self.traveler_mode
                else:
                    new_position = self.selection.get_down(game.cursor.position)
                    game.cursor.set_pos(new_position)
            if not self.traveler_mode:
                new_position = self.selection.get_down(game.cursor.position)
                game.cursor.set_pos(new_position)
        elif 'UP' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.traveler_mode = False
            new_position = self.selection.get_up(game.cursor.position)
            game.cursor.set_pos(new_position)
        if 'LEFT' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.traveler_mode = False
            new_position = self.selection.get_left(game.cursor.position)
            game.cursor.set_pos(new_position)
        elif 'RIGHT' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.traveler_mode = False
            new_position = self.selection.get_right(game.cursor.position)
            game.cursor.set_pos(new_position)

        new_position = self.selection.handle_mouse()
        if new_position:
            game.cursor.set_pos(new_position)

        if event == 'BACK':
            SOUNDTHREAD.play_sfx('Select 4')
            game.state.back()

        elif event == 'SELECT':
            SOUNDTHREAD.play_sfx('Select 1')
            unit = game.cursor.get_hover()
            if self.traveler_mode:
                if unit.traveler:
                    game.memory['trade_partner'] = game.get_unit(unit.traveler)
                else:
                    game.memory['trade_partner'] = unit
            else:
                game.memory['trade_partner'] = unit
            self.ability.do(self.cur_unit)

        elif event == 'AUX':
            SOUNDTHREAD.play_sfx('Select 6')
            self.traveler_mode = False
            new_position = self.selection.get_next(game.cursor.position)
            game.cursor.set_pos(new_position)

    def draw_rescue_preview(self, rescuee, surf):
        window = SPRITES.get('rescue_window').copy()
        con = str(equations.parser.rescue_weight(rescuee))
        aid = str(equations.parser.rescue_aid(self.cur_unit))
        FONT['text-blue'].blit_right(con, window, (window.get_width() - 5, 72))
        FONT['text-blue'].blit_right(aid, window, (window.get_width() - 5, 24))
        rescuer_sprite = self.cur_unit.sprite.create_image('passive')
        rescuee_sprite = rescuee.sprite.create_image('passive')
        FONT['text-white'].blit(self.cur_unit.name, window, (32, 8))
        FONT['text-white'].blit(rescuee.name, window, (32, 56))

        if game.cursor.position[0] > TILEX//2 + game.camera.get_x() - 1:
            topleft = (0, 0)
        else:
            topleft = (WINWIDTH - 4 - window.get_width(), 0)
        surf.blit(window, topleft)

        surf.blit(rescuer_sprite, (topleft[0] - 12, topleft[1] - 16))
        surf.blit(rescuee_sprite, (topleft[0] - 12, topleft[1] - 16 + 48))

        return surf

    def draw_give_preview(self, traveler, give_to, surf):
        window = SPRITES.get('give_window').copy()
        con = str(equations.parser.rescue_weight(traveler))
        aid = str(equations.parser.rescue_aid(give_to))
        FONT['text-blue'].blit_right(con, window, (window.get_width() - 5, 24))
        FONT['text-blue'].blit_right(aid, window, (window.get_width() - 5, 72))
        traveler_sprite = traveler.sprite.create_image('passive')
        give_to_sprite = give_to.sprite.create_image('passive')
        FONT['text-white'].blit(traveler.name, window, (32, 8))
        FONT['text-white'].blit(give_to.name, window, (32, 56))

        if game.cursor.position[0] > TILEX//2 + game.camera.get_x() - 1:
            topleft = (0, 0)
        else:
            topleft = (WINWIDTH - 4 - window.get_width(), 0)
        surf.blit(window, topleft)

        surf.blit(traveler_sprite, (topleft[0] - 12, topleft[1] - 16))
        surf.blit(give_to_sprite, (topleft[0] - 12, topleft[1] - 16 + 48))

        return surf

    def draw(self, surf):
        surf = super().draw(surf)
        if self.ability.name == 'Rescue':
            rescuee = game.board.get_unit(game.cursor.position)
            if rescuee:
                self.draw_rescue_preview(rescuee, surf)
        elif self.ability.name == 'Take':
            holder = game.board.get_unit(game.cursor.position)
            if holder and holder.traveler:
                traveler = game.get_unit(holder.traveler)
                if traveler:
                    self.draw_rescue_preview(traveler, surf)
        elif self.ability.name == 'Give':
            if self.cur_unit.traveler:
                give_to = game.board.get_unit(game.cursor.position)
                traveler = game.get_unit(self.cur_unit.traveler)
                if give_to and traveler:
                    self.draw_give_preview(traveler, give_to, surf)
        elif self.ability.name == 'Trade':
            unit = game.cursor.get_hover()
            if self.traveler_mode:
                if unit.traveler:
                    game.ui_view.draw_trade_preview(game.get_unit(unit.traveler), surf)
            else:
                game.ui_view.draw_trade_preview(unit, surf)
        elif self.ability.name == 'Steal':
            unit = game.cursor.get_hover()
            game.ui_view.draw_trade_preview(unit, surf)
        if self.pennant:
            draw_on_top = game.cursor.position[1] >= game.tilemap.height - 1
            self.pennant.draw(surf, draw_on_top)
        return surf

class CombatTargetingState(MapState):
    name = 'combat_targeting'

    def start(self):
        self.cur_unit = game.cursor.cur_unit
        self.item = game.memory['item']

        # Support for sequence items
        self.sequence_item_index = game.memory.get('sequence_item_index', 0)
        if self.item.sequence_item:
            self.parent_item = self.item
            # Replaces item with the item we'll be working with here
            self.item = self.parent_item.subitems[self.sequence_item_index]
        else: # For no sequence item, we won't be using this
            self.parent_item = None

        self.num_targets = item_system.num_targets(self.cur_unit, self.item)
        self.current_target_idx = 0
        self.prev_targets = game.memory.get('prev_targets', [])

        positions = target_system.get_valid_targets(self.cur_unit, self.item)

        # Remove previous targets if not allow_same_target
        if self.parent_item:
            allow_same_target = item_system.allow_same_target(self.cur_unit, self.parent_item)
            if not allow_same_target:
                for pos in self.prev_targets:
                    positions.discard(pos)

        self.selection = SelectionHelper(positions)
        self.previous_mouse_pos = None
        closest_pos = self.selection.get_closest(game.cursor.position)
        game.cursor.set_pos(closest_pos)

        # Sets dual strike variables and chooses attacker dual strike
        self.find_strike_partners(closest_pos)

        # Reset these
        game.memory['sequence_item_index'] = 0
        game.memory['prev_targets'] = []

        # This is used to immediately handle the next target
        # after item targeting has occurred
        self._process_next_target_asap = False

        self.ability_name = game.memory.get('ability')
        if self.ability_name == 'Spells':
            game.ui_view.prepare_spell_info()
        else:
            game.ui_view.prepare_attack_info()
        self.display_single_attack()

    def begin(self):
        game.cursor.combat_show()
        if self._process_next_target_asap:
            self._process_next_target_asap = False
            self._get_next_target()

    def find_strike_partners(self, target, atk=True):
        if atk:
            self.attacker_assist = None
        self.defender_assist = None
        attacker = self.cur_unit
        if isinstance(target, tuple):
            defender = game.board.get_unit(target)
        else:
            defender = None
        partners = target_system.find_strike_partners(attacker, defender, self.item)
        atk_result, self.defender_assist = partners
        if self.attacker_assist:
            pass  # Attacker assistant already chosen!
        else:
            self.attacker_assist = atk_result

    def display_single_attack(self):
        game.highlight.remove_highlights()
        splash_positions = item_system.splash_positions(self.cur_unit, self.item, game.cursor.position)
        valid_attacks = target_system.get_attacks(self.cur_unit, self.item)
        if item_system.is_spell(self.cur_unit, self.item):
            game.highlight.display_possible_spell_attacks(valid_attacks, light=True)
            game.highlight.display_possible_spell_attacks(splash_positions)
            game.highlight.display_possible_spell_attacks({game.cursor.position})
        else:
            game.highlight.display_possible_attacks(valid_attacks, light=True)
            game.highlight.display_possible_attacks(splash_positions)
            game.highlight.display_possible_attacks({game.cursor.position})

    def _engage_combat(self):
        if self.parent_item:  # For sequence item
            main_item = self.parent_item
            targets = []
            target_counter = 0
            for item in self.parent_item.subitems:
                num_targets = item_system.num_targets(self.cur_unit, item)
                t = self.prev_targets[target_counter:target_counter + num_targets]
                if num_targets > 1:
                    targets.append(t)
                else:
                    targets.append(t[0])
                target_counter += num_targets
        else: # Guaranteed to be len(1) since it's not a sequence item
            main_item = self.item
            if len(self.prev_targets) > 1:
                targets = [self.prev_targets]
            else:
                targets = self.prev_targets

        # Find strike partner for first target
        self.find_strike_partners(targets[0], atk=False)
        self.cur_unit.strike_partner = self.attacker_assist
        if len(self.prev_targets) == 1:
            defender = game.board.get_unit(targets[0])
            if defender:
                defender.strike_partner = self.defender_assist

        combat = interaction.engage(self.cur_unit, targets, main_item)
        game.combat_instance.append(combat)
        game.state.change('combat')
        game.memory['valid_weapons'] = None

    def _get_next_target(self):
        allow_same_target = item_system.allow_same_target(self.cur_unit, self.item)
        if self.current_target_idx < self.num_targets and \
                (allow_same_target or self.selection.count() > 1):
            if not allow_same_target:
                self.selection.remove_target(game.cursor.position)
                closest_pos = self.selection.get_closest(game.cursor.position)
                game.cursor.set_pos(closest_pos)

            self.begin()
            self.display_single_attack()
        elif self.parent_item and self.sequence_item_index < len(self.parent_item.sequence_item.value) - 1:
            # Pass along the sequence item index to the next combat targeting state
            self.sequence_item_index += 1
            game.memory['sequence_item_index'] = self.sequence_item_index
            game.memory['prev_targets'] = self.prev_targets
            game.state.back()
            game.state.change('combat_targeting')
        else:
            self._engage_combat()

    def take_input(self, event):
        self.fluid.update()
        directions = self.fluid.get_directions()

        if 'DOWN' in directions:
            new_position = self.selection.get_down(game.cursor.position)
            game.cursor.set_pos(new_position)
        elif 'UP' in directions:
            new_position = self.selection.get_up(game.cursor.position)
            game.cursor.set_pos(new_position)
        if 'LEFT' in directions:
            new_position = self.selection.get_left(game.cursor.position)
            game.cursor.set_pos(new_position)
        elif 'RIGHT' in directions:
            new_position = self.selection.get_right(game.cursor.position)
            game.cursor.set_pos(new_position)

        mouse_position = self.selection.handle_mouse()
        if mouse_position:
            game.cursor.set_pos(mouse_position)

        if event == 'AUX':
            adj_allies = target_system.get_adj_allies(self.cur_unit)
            if not DB.constants.value('pairup'):
                new_position = self.selection.get_next(game.cursor.position)
                game.cursor.set_pos(new_position)
                SOUNDTHREAD.play_sfx('Select 6')
                game.ui_view.reset_info()
                self.display_single_attack()
            # Switch chosen pairup with AUX
            elif len(adj_allies) > 1 and self.num_targets == 1:
                i = adj_allies.index(self.attacker_assist)
                # Hardset attacker
                self.attacker_assist = adj_allies[(i + 1) % len(adj_allies)]
                game.ui_view.reset_info()
                self.display_single_attack()

        elif event == 'BACK':
            SOUNDTHREAD.play_sfx('Select 4')
            # Equip Action doesn't need to be reversed
            # equip_action = game.memory.get('equip_action')
            # if equip_action:
            #     action.reverse(equip_action)
            # game.memory['equip_action'] = None
            game.state.back()
            return 'repeat'

        elif event == 'SELECT':
            SOUNDTHREAD.play_sfx('Select 1')
            self.current_target_idx += 1

            self.prev_targets.append(game.cursor.position)

            if item_system.targets_items(self.cur_unit, self.item):
                target = game.board.get_unit(game.cursor.position)
                if target:
                    game.memory['target'] = target
                    game.state.change('item_targeting')
                    self._process_next_target_asap = True
                else:
                    self._get_next_target()
            # If we still have targets to select
            # If we don't allow same target, need to make sure there is still at least one target after this
            else:
                self._get_next_target()

        if directions or (mouse_position and mouse_position != self.previous_mouse_pos):
            if mouse_position:
                self.previous_mouse_pos = mouse_position
            SOUNDTHREAD.play_sfx('Select 6')
            game.ui_view.reset_info()
            self.display_single_attack()

    def draw(self, surf):
        surf = super().draw(surf)
        target_unit = game.board.get_unit(game.cursor.position)
        if self.cur_unit and target_unit:
            if item_system.targets_items(self.cur_unit, self.item):
                game.ui_view.draw_trade_preview(target_unit, surf)
            elif item_system.is_weapon(self.cur_unit, self.item):
                game.ui_view.draw_attack_info(surf, self.cur_unit, self.item, target_unit, self.attacker_assist, self.defender_assist)
            else:
                game.ui_view.draw_spell_info(surf, self.cur_unit, self.item, target_unit)

        return surf

    def end(self):
        game.highlight.remove_highlights()
        game.ui_view.reset_info()

class ItemTargetingState(MapState):
    name = 'item_targeting'

    def start(self):
        self.cur_unit = game.cursor.cur_unit
        self.item = game.memory['item']
        self.target = game.memory['target']

        # Support for sequence items
        self.sequence_item_index = game.memory.get('sequence_item_index', 0)
        if self.item.sequence_item:
            self.parent_item = self.item
            # Replaces item with the item we're actually working with here
            self.item = self.parent_item.subitems[self.sequence_item_index]
        else: # For no sequence item, we won't be using this
            self.parent_item = None

        # Build menu
        options = self.target.items
        ignore = [not item_system.item_restrict(self.cur_unit, self.item, self.target, item) for item in self.target.items]
        self.menu = menus.Choice(self.target, options)
        self.menu.set_ignore(ignore)

    def begin(self):
        game.cursor.hide()

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        self.menu.handle_mouse()
        if 'DOWN' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_down(first_push)
        elif 'UP' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_up(first_push)

        if event == 'BACK':
            if self.menu.info_flag:
                self.menu.toggle_info()
                SOUNDTHREAD.play_sfx('Info Out')
            else:
                SOUNDTHREAD.play_sfx('Select 4')
                game.state.back()
                game.state.back()  # Go back twice to skip over recent combat_targeting state

        elif event == 'SELECT':
            if self.menu.info_flag:
                pass
            else:
                SOUNDTHREAD.play_sfx('Select 1')
                target_item = self.menu.get_current()
                self.item.data['target_item'] = target_item
                game.state.back()
                return 'repeat'

        elif event == 'INFO':
            self.menu.toggle_info()
            if self.menu.info_flag:
                SOUNDTHREAD.play_sfx('Info In')
            else:
                SOUNDTHREAD.play_sfx('Info Out')

    def update(self):
        super().update()
        self.menu.update()

    def draw(self, surf):
        surf = super().draw(surf)
        surf = self.menu.draw(surf)
        return surf

    def end(self):
        game.cursor.show()

class CombatState(MapState):
    name = 'combat'
    fuzz_background = image_mods.make_translucent(SPRITES.get('bg_black'), 0.75)

    def start(self):
        game.cursor.hide()
        self.skip = False
        width = game.tilemap.width * TILEWIDTH
        height = game.tilemap.height * TILEHEIGHT
        self.combat = game.combat_instance.pop(0)
        game.memory['current_combat'] = self.combat
        self.unit_surf = engine.create_surface((width, height), transparent=True)
        self.is_animation_combat = isinstance(self.combat, interaction.AnimationCombat)

    def take_input(self, event):
        if event == 'START':
            if self.skip:
                self.skip = False
                self.combat.end_skip()
            else:
                self.skip = True
                self.combat.skip()
        elif event == 'BACK':
            # Arena
            pass

    def update(self):
        super().update()
        done = self.combat.update()
        if self.skip and not self.is_animation_combat:
            while not done:
                done = self.combat.update()
        if done:
            return 'repeat'

    def draw(self, surf):
        if self.is_animation_combat:
            if self.combat.viewbox:
                viewbox = self.combat.viewbox
                viewbox_bg = self.fuzz_background.copy()
                if viewbox[2] > 0:  # Width
                    viewbox_bg.fill((0, 0, 0, 0), viewbox)
                surf = super().draw(surf, culled_rect=viewbox)
                surf.blit(viewbox_bg, (0, 0))
            else:
                surf = super().draw(surf)
        else:
            surf = super().draw(surf)
        self.combat.draw(surf)
        return surf

class DyingState(MapState):
    name = 'dying'

    def begin(self):
        game.cursor.hide()

    def update(self):
        super().update()

        done = game.death.update()
        if done:
            game.state.back()
            return 'repeat'

class AlertState(State):
    name = 'alert'
    transparent = True

    def begin(self):
        if game.cursor:
            game.cursor.hide()

    def back(self):
        game.alerts.pop()
        game.state.back()
        return 'repeat'

    def take_input(self, event):
        if game.alerts:
            alert = game.alerts[-1]

        if event and alert and alert.time_to_start and \
                engine.get_time() - alert.time_to_start > alert.time_to_pause:
            self.back()

    def update(self):
        if game.alerts:
            alert = game.alerts[-1]
            alert.update()
            if alert.remove_flag:
                self.back()

    def draw(self, surf):
        if game.alerts and self.started:
            alert = game.alerts[-1]
            alert.draw(surf)
        return surf

class AIState(MapState):
    name = 'ai'

    def start(self):
        logging.info("Starting AI State")
        game.cursor.hide()

        self.cur_unit = None
        self.cur_group = None

    def get_next_unit(self):
        # Initiative way
        if DB.constants.value('initiative'):
            current_unit = game.initiative.get_current_unit()
            if current_unit.position and not current_unit.finished and not current_unit.has_run_ai:
                return current_unit
            else:
                return None

        # Normal way
        valid_units = [
            unit for unit in game.units if
            unit.position and
            not unit.finished and
            not unit.has_run_ai and
            unit.team == game.phase.get_current()]
        if not valid_units:
            return None
        # Check if any members of group
        if self.cur_group:
            group_units = [unit for unit in valid_units if unit.ai_group == self.cur_group]
            if group_units:
                # Sort by distance to closest enemy (ascending)
                group_units = sorted(group_units, key=lambda unit: target_system.distance_to_closest_enemy(unit))
                # Sort by priority
                group_units = sorted(group_units, key=lambda unit: DB.ai.get(unit.get_ai()).priority, reverse=True)
                group_units.reverse()
                return group_units.pop()
            else:
                self.cur_group = None
        # So default to this
        # Sort by distance to closest enemy (ascending)
        valid_units = sorted(valid_units, key=lambda unit: target_system.distance_to_closest_enemy(unit))
        # Sort by ai priority
        valid_units = sorted(valid_units, key=lambda unit: DB.ai.get(unit.get_ai()).priority, reverse=True)
        # Reverse, because we will be popping them off at the end
        valid_units.reverse()
        return valid_units.pop()

    def take_input(self, event):
        # Skip combats while START is held down
        if not game.ai.do_skip and INPUT.is_pressed('START'):
            game.ai.skip()
        elif game.ai.do_skip and not INPUT.is_pressed('START'):
            game.ai.end_skip()

    def update(self):
        super().update()

        # Don't bother if someone is dying!!!
        if any(unit.is_dying for unit in game.units):
            return

        if (not self.cur_unit or not self.cur_unit.position):
            self.cur_unit = self.get_next_unit()
            # Reset previous position

            if self.cur_unit:
                if self.cur_unit.position and self.cur_unit.previous_position != self.cur_unit.position:
                    action.do(action.SetPreviousPosition(self.cur_unit))
                self.cur_group = self.cur_unit.ai_group
            else:
                self.cur_group = None
            # also resets AI
            game.ai.load_unit(self.cur_unit)

        logging.info("Current AI: %s", self.cur_unit.nid if self.cur_unit else None)

        if self.cur_unit:
            has_already_moved = game.ai.move_ai_complete
            did_something, change = game.ai.act()
            # Center camera on current unit
            if change and self.cur_unit.position:
                game.cursor.set_pos(self.cur_unit.position)
                if game.ai.goal_target:
                    game.camera.set_center2(self.cur_unit.position, game.ai.goal_target)
                elif game.ai.goal_position:
                    game.camera.set_center2(self.cur_unit.position, game.ai.goal_position)
                else:
                    game.camera.set_center(*self.cur_unit.position)  # Actually center the camera
                if has_already_moved and not game.ai.do_skip:
                    # Only do this for non-move actions
                    game.state.change('move_camera')

            if not change and game.ai.is_done():
                logging.info("Current AI %s is done with turn.", self.cur_unit.nid)
                if did_something:  # Don't turn grey if didn't actually do anything
                    self.cur_unit.wait()
                game.ai.reset()
                self.cur_unit.has_run_ai = True
                self.cur_unit = None
        else:
            logging.info("AI Phase complete")
            game.ai.end_skip()
            game.ai.reset()
            self.cur_unit = None
            self.cur_group = None
            game.state.change('turn_change')
            game.state.change('status_endstep')
            self.finish()
            return 'repeat'

    def finish(self):
        logging.info("Finishing AI State")
        for unit in game.units:
            unit.has_run_ai = False

class ShopState(State):
    name = 'shop'

    def start(self):
        self.fluid = FluidScroll()

        self.unit = game.memory['current_unit']
        self.flavor = game.memory['shop_flavor']
        if self.flavor == 'vendor':
            self.portrait = SPRITES.get('vendor_portrait')
            self.opening_message = 'vendor_opener'
            self.buy_message = 'vendor_buy'
            self.back_message = 'vendor_back'
            self.leave_message = 'vendor_leave'
        else:
            self.portrait = SPRITES.get('armory_portrait')
            self.opening_message = 'armory_opener'
            self.buy_message = 'armory_buy'
            self.back_message = 'armory_back'
            self.leave_message = 'armory_leave'

        items = game.memory['shop_items']
        my_items = item_funcs.get_all_tradeable_items(self.unit)
        topleft = (44, WINHEIGHT - 16 * 5 - 8 - 4)
        self.sell_menu = menus.Shop(self.unit, my_items, topleft, disp_value='sell')
        self.sell_menu.set_limit(5)
        self.sell_menu.set_hard_limit(True)
        self.sell_menu.gem = True
        self.sell_menu.shimmer = 0
        self.sell_menu.set_takes_input(False)
        self.buy_menu = menus.Shop(self.unit, items, topleft, disp_value='buy')
        self.buy_menu.set_limit(5)
        self.buy_menu.set_hard_limit(True)
        self.buy_menu.gem = True
        self.buy_menu.shimmer = 0
        self.buy_menu.set_takes_input(False)

        self.choice_menu = menus.Choice(self.unit, ["Buy", "Sell"], (120, 32), background=None)
        self.choice_menu.set_horizontal(True)
        self.choice_menu.set_color(['convo-white', 'convo-white'])
        self.choice_menu.set_highlight(False)
        self.menu = None  # For input

        self.state = 'open'
        self.current_msg = self.get_dialog(self.opening_message)

        self.message_bg = base_surf.create_base_surf(WINWIDTH + 8, 48, 'menu_bg_clear')
        self.money_counter_disp = gui.PopUpDisplay((223, 32))

        self.bg = background.create_background('rune_background')

        game.state.change('transition_in')
        return 'repeat'

    def get_dialog(self, text):
        d = dialog.Dialog(text_funcs.translate(text))
        d.position = (60, 8)
        d.text_width = WINWIDTH - 80
        d.width = d.text_width + 16
        d.font = FONT['convo-white']
        d.font_color = 'white'
        return d

    def update_options(self):
        self.sell_menu.update_options(item_funcs.get_all_tradeable_items(self.unit))

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        if self.menu:
            self.menu.handle_mouse()
            if 'DOWN' in directions or 'RIGHT' in directions:
                SOUNDTHREAD.play_sfx('Select 6')
                self.menu.move_down(first_push)
            elif 'UP' in directions or 'LEFT' in directions:
                SOUNDTHREAD.play_sfx('Select 6')
                self.menu.move_up(first_push)

        if event == 'SELECT':
            if self.state == 'open':
                SOUNDTHREAD.play_sfx('Select 1')
                self.current_msg.hurry_up()
                if self.current_msg.is_done_or_wait():
                    self.state = 'choice'
                    self.menu = self.choice_menu

            elif self.state == 'choice':
                SOUNDTHREAD.play_sfx('Select 1')
                current = self.choice_menu.get_current()
                if current == 'Buy':
                    self.menu = self.buy_menu
                    self.state = 'buy'
                    self.current_msg = self.get_dialog(self.buy_message)
                    self.buy_menu.set_takes_input(True)
                elif current == 'Sell' and item_funcs.get_all_tradeable_items(self.unit):
                    self.menu = self.sell_menu
                    self.state = 'sell'
                    self.sell_menu.set_takes_input(True)

            elif self.state == 'buy':
                item = self.buy_menu.get_current()
                if item:
                    value = item_funcs.buy_price(self.unit, item)
                    if game.get_money() - value >= 0:
                        action.do(action.HasTraded(self.unit))
                        SOUNDTHREAD.play_sfx('GoldExchange')
                        action.do(action.GainMoney(game.current_party, -value))
                        self.money_counter_disp.start(-value)
                        new_item = item_funcs.create_item(self.unit, item.nid)
                        game.register_item(new_item)
                        if not item_funcs.inventory_full(self.unit, new_item):
                            action.do(action.GiveItem(self.unit, new_item))
                            self.current_msg = self.get_dialog('shop_buy_again')
                        elif game.game_vars.get('_convoy'):
                            action.do(action.PutItemInConvoy(new_item))
                            self.current_msg = self.get_dialog('shop_convoy')
                        else:
                            self.current_msg = self.get_dialog('shop_max')
                            self.state = 'choice'
                            self.menu = self.choice_menu
                            self.buy_menu.set_takes_input(False)

                        self.update_options()
                    else:
                        # You don't have enough money
                        SOUNDTHREAD.play_sfx('Select 4')
                        self.current_msg = self.get_dialog('shop_no_money')

            elif self.state == 'sell':
                item = self.sell_menu.get_current()
                if item:
                    value = item_funcs.sell_price(self.unit, item)
                    if value:
                        action.do(action.HasTraded(self.unit))
                        SOUNDTHREAD.play_sfx('GoldExchange')
                        action.do(action.GainMoney(game.current_party, value))
                        self.money_counter_disp.start(value)
                        action.do(action.RemoveItem(self.unit, item))
                        self.current_msg = self.get_dialog('shop_sell_again')
                        self.update_options()
                    else:
                        # No value, can't be sold
                        SOUNDTHREAD.play_sfx('Select 4')
                        self.current_msg = self.get_dialog('shop_no_value')
                else:
                    # You didn't choose anything to sell
                    SOUNDTHREAD.play_sfx('Select 4')

            elif self.state == 'close':
                SOUNDTHREAD.play_sfx('Select 1')
                if self.current_msg.is_done_or_wait():
                    if self.unit.has_traded:
                        action.do(action.HasAttacked(self.unit))
                    game.state.change('transition_pop')
                else:
                    self.current_msg.hurry_up()

        elif event == 'BACK':
            if self.state == 'open' or self.state == 'close':
                SOUNDTHREAD.play_sfx('Select 4')
                if self.unit.has_traded:
                    action.do(action.HasAttacked(self.unit))
                game.state.change('transition_pop')
            elif self.state == 'choice':
                SOUNDTHREAD.play_sfx('Select 4')
                self.state = 'close'
                self.current_msg = self.get_dialog(self.leave_message)
            elif self.state == 'buy' or self.state == 'sell':
                if self.menu.info_flag:
                    self.menu.toggle_info()
                    SOUNDTHREAD.play_sfx('Info Out')
                else:
                    SOUNDTHREAD.play_sfx('Select 4')
                    self.state = 'choice'
                    self.menu.set_takes_input(False)
                    self.menu = self.choice_menu
                    self.current_msg = self.get_dialog('shop_again')

        elif event == 'INFO':
            if self.state == 'buy' or self.state == 'sell':
                self.menu.toggle_info()
                if self.menu.info_flag:
                    SOUNDTHREAD.play_sfx('Info In')
                else:
                    SOUNDTHREAD.play_sfx('Info Out')

    def update(self):
        if self.current_msg:
            self.current_msg.update()
        if self.menu:
            self.menu.update()

    def draw(self, surf):
        if self.bg:
            self.bg.draw(surf)
        surf.blit(self.message_bg, (-4, 8))
        if self.current_msg:
            self.current_msg.draw(surf)

        surf.blit(self.portrait, (3, 0))
        
        money_bg = SPRITES.get('money_bg')
        money_bg = image_mods.make_translucent(money_bg, .1)
        surf.blit(money_bg, (172, 48))

        FONT['text-blue'].blit_right(str(game.get_money()), surf, (223, 48))
        self.money_counter_disp.draw(surf)

        if self.state == 'sell':
            self.sell_menu.draw(surf)
        elif self.state == 'choice' and self.choice_menu.get_current() == 'Sell':
            self.sell_menu.draw(surf)
        else:
            self.buy_menu.draw(surf)
        if self.state == 'choice' and self.current_msg.is_done_or_wait():
            self.choice_menu.draw(surf)

        return surf

class UnlockSelectState(MapState):
    name = 'unlock_select'

    def start(self):
        self.cur_unit = game.memory['current_unit']
        options = game.memory['all_unlock_items']
        self.menu = menus.Choice(self.cur_unit, options)

    def begin(self):
        game.cursor.hide()
        self.item_desc_panel = ui_view.ItemDescriptionPanel(self.cur_unit, self.menu.get_current())

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        self.menu.handle_mouse()
        if 'DOWN' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_down(first_push)
            current = self.menu.get_current()
            self.item_desc_panel.set_item(current)
        elif 'UP' in directions:
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_up(first_push)
            current = self.menu.get_current()
            self.item_desc_panel.set_item(current)

        if event == 'BACK':
            if self.menu.info_flag:
                self.menu.toggle_info()
                SOUNDTHREAD.play_sfx('Info Out')
            else:
                SOUNDTHREAD.play_sfx('Error')

        elif event == 'SELECT':
            if self.menu.info_flag:
                pass
            else:
                SOUNDTHREAD.play_sfx('Select 1')
                game.memory['unlock_item'] = self.menu.get_current()
                game.state.back()

        elif event == 'INFO':
            self.menu.toggle_info()
            if self.menu.info_flag:
                SOUNDTHREAD.play_sfx('Info In')
            else:
                SOUNDTHREAD.play_sfx('Info Out')

    def update(self):
        super().update()
        self.menu.update()

    def draw(self, surf):
        surf = super().draw(surf)
        surf = self.item_desc_panel.draw(surf)
        surf = self.menu.draw(surf)
        return surf
