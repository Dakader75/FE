from __future__ import annotations
from app.sprites import SPRITES
import logging
import re
from typing import Callable, Dict, List, Tuple

import app.engine.config as cf
import app.engine.graphics.ui_framework as uif
from app.constants import WINHEIGHT, WINWIDTH
from app.data.database import DB
from app.data.level_units import GenericUnit, UniqueUnit
from app.engine import (action, background, banner, dialog, engine, evaluate,
                        icons, image_mods, item_funcs, item_system,
                        skill_system, static_random, target_system, unit_funcs)
from app.engine.animations import MapAnimation
from app.engine.combat import interaction
from app.engine.game_state import game
from app.engine.graphics.dialog.narration_dialogue import NarrationDialogue
from app.engine.objects.item import ItemObject
from app.engine.objects.overworld import OverworldNodeObject
from app.engine.objects.tilemap import TileMapObject
from app.engine.objects.unit import UnitObject
from app.engine.overworld.overworld_actions import OverworldMove
from app.engine.overworld.overworld_map_view import OverworldMapView
from app.engine.overworld.overworld_movement_manager import \
    OverworldMovementManager
from app.engine.sound import SOUNDTHREAD
from app.engine.game_state import game
from app.events import event_commands, regions
from app.events.event_portrait import EventPortrait
from app.resources.resources import RESOURCES
from app.utilities import str_utils, utils
from app.utilities.algorithms.interpolation import cubic_easing, tcubic_easing
from app.utilities.typing import NID, Point

screen_positions = {'OffscreenLeft': -96,
                    'FarLeft': -24,
                    'Left': 0,
                    'MidLeft': 24,
                    'CenterLeft': 24,
                    'CenterRight': 120,
                    'MidRight': 120,
                    'LevelUpRight': 140,
                    'Right': 144,
                    'FarRight': 168,
                    'OffscreenRight': 240}

vertical_screen_positions = {'Top': 0,
                             'Middle': 40,
                             'Bottom': 80}

class Event():
    _transition_speed = 250
    _transition_color = (0, 0, 0)

    true_vals = ('t', 'true', '1', 'y', 'yes')

    skippable = {"speak", "wait", "bop_portrait",
                 "sound", "location_card", "credits", "ending"}

    def __init__(self, nid, commands, unit=None, unit2=None, item=None, position=None, region=None):
        self.nid = nid
        self.commands = commands.copy()
        self.command_idx = 0

        self.background = None

        self.unit = unit
        self.unit2 = unit2
        self.item = item
        self.position = position
        self.region = region

        self.portraits: Dict[str, EventPortrait] = {}
        self.text_boxes = []
        self.other_boxes = []
        self.overlay_ui = uif.UIComponent.create_base_component()

        self.prev_state = None
        self.state = 'processing'

        self.turnwheel_flag = 0  # Whether to enter the turnwheel state after this event is finished
        self.battle_save_flag = 0  # Whether to enter the battle save state after this event is finished

        self.wait_time: int = 0

        # Handles keeping the order that unit sprites should be drawn
        self.priority_counter = 1
        self.do_skip = False
        self.super_skip = False

        self.if_stack = [] # Keeps track of how many ifs we've encountered while searching for the bad ifs 'end'.
        self.parse_stack = [] # Keeps track of whether we've encountered a truth this level or not

        # For transition
        self.transition_state = None
        self.transition_progress = 0
        self.transition_update = 0
        self.transition_speed = self._transition_speed
        self.transition_color = self._transition_color

        # For map animations
        self.animations = []

        # a way of passing key input events down to individual events
        # map between name of listener, and listener function
        self.functions_listening_for_input: Dict[str, Callable[[str]]] = {}

        # a way for any arbitrary event to block state processing until an arbitrary condition is fulfilled
        self.should_remain_blocked: List[Callable[[], bool]] = []

        # a method of queueing unblocked actions that require updating (e.g. movement)
        # update functions should return False once they are finished (so they can be removed from the queue)
        # they should receive an argument that represents whether or not we're in skip mode to facilitate skipping
        # and avoid infinite loops.
        # maps name to function
        self.should_update: Dict[str, Callable[[bool], bool]] = {}

    @property
    def unit1(self):
        return self.unit

    def save(self):
        ser_dict = {}
        ser_dict['nid'] = self.nid
        ser_dict['commands'] = self.commands
        ser_dict['command_idx'] = self.command_idx
        ser_dict['unit1'] = self.unit.nid if self.unit else None
        ser_dict['unit2'] = self.unit2.nid if self.unit2 else None
        ser_dict['region'] = self.region.nid if self.region else None
        ser_dict['item'] = self.item.uid if self.item else None
        ser_dict['position'] = self.position
        ser_dict['if_stack'] = self.if_stack
        ser_dict['parse_stack'] = self.parse_stack
        return ser_dict

    @classmethod
    def restore(cls, ser_dict):
        unit = game.get_unit(ser_dict['unit1'])
        unit2 = game.get_unit(ser_dict['unit2'])
        region = game.get_region(ser_dict['region'])
        item = game.get_item(ser_dict.get('item'))
        position = ser_dict['position']
        commands = ser_dict['commands']
        nid = ser_dict['nid']
        self = cls(nid, commands, unit, unit2, item, position, region)
        self.command_idx = ser_dict['command_idx']
        self.if_stack = ser_dict['if_stack']
        self.parse_stack = ser_dict['parse_stack']
        return self

    def update(self):
        current_time = engine.get_time()
        # update all internal updates, remove the ones that are finished
        self.should_update = {name: to_update for name, to_update in self.should_update.items() if not to_update(self.do_skip)}

        # Update movement so that no_block works correctly
        game.movement.update()

        # Can move through its own internal state up to 5 times in a frame
        counter = 0
        while counter < 5:
            counter += 1
            if self.state != self.prev_state:
                self.prev_state = self.state
                logging.debug("Event State: %s", self.state)

            if self.state == 'waiting':
                if current_time > self.wait_time:
                    self.state = 'processing'
                else:
                    break

            elif self.state == 'processing':
                if self.command_idx >= len(self.commands):
                    self.end()
                else:
                    self.process()
                if self.state == 'paused':
                    break  # Necessary so we don't go right back to processing

            elif self.state == 'dialog':
                if self.text_boxes:
                    if self.text_boxes[-1].is_done():
                        action.do(action.LogDialog(self.text_boxes[-1]))
                        self.state = 'processing'
                else:
                    self.state = 'processing'

            elif self.state == 'paused':
                self.state = 'processing'

            elif self.state == 'complete':
                break

            elif self.state == 'blocked':
                # state is blocked; try to unblock
                should_still_be_blocked = False
                for check_still_blocked in self.should_remain_blocked:
                    if check_still_blocked(): # we haven't fulfilled unblock conditions
                        should_still_be_blocked = True
                        break
                if should_still_be_blocked:
                    break
                else:
                    # resume execution and clear blockers
                    self.should_remain_blocked.clear()
                    self.state = 'processing'

        # Handle transition
        if self.transition_state:
            perc = (current_time - self.transition_update) / self.transition_speed
            if self.transition_state == 'open':
                perc = 1 - perc
            self.transition_progress = utils.clamp(perc, 0, 1)
            if perc < 0:
                self.transition_state = None

    def take_input(self, event):
        if event == 'START' or event == 'BACK':
            SOUNDTHREAD.play_sfx('Select 4')
            self.skip(event == 'START')

        elif event == 'SELECT' or event == 'RIGHT' or event == 'DOWN':
            if self.state == 'dialog':
                if not cf.SETTINGS['talk_boop']:
                    SOUNDTHREAD.play_sfx('Select 1')
                self.hurry_up()

        for listener in self.functions_listening_for_input.values():
            listener(event)

    def draw(self, surf):
        self.animations = [anim for anim in self.animations if not anim.update()]
        for anim in self.animations:
            anim.draw(surf, offset=(-game.camera.get_x(), -game.camera.get_y()))

        if self.background:
            self.background.draw(surf)

        delete = [key for key, portrait in self.portraits.items() if portrait.update()]
        for key in delete:
            del self.portraits[key]

        # draw all uiframework elements
        ui_surf = self.overlay_ui.to_surf()
        surf.blit(ui_surf, (0, 0))

        sorted_portraits = sorted(self.portraits.values(), key=lambda x: x.priority)
        for portrait in sorted_portraits:
            portrait.draw(surf)

        # Draw other boxes
        self.other_boxes = [box for box in self.other_boxes if box.update()]
        for box in self.other_boxes:
            box.draw(surf)

        # Draw text/dialog boxes
        # if self.state == 'dialog':
        if not self.do_skip:
            to_draw = []
            for dialog_box in reversed(self.text_boxes):
                if not dialog_box.is_complete():
                    to_draw.insert(0, dialog_box)
                if dialog_box.solo_flag:
                    break
            for dialog_box in to_draw:
                dialog_box.update()
                dialog_box.draw(surf)

        # Fade to black
        if self.transition_state:
            s = engine.create_surface((WINWIDTH, WINHEIGHT), transparent=True)
            s.fill((*self.transition_color, int(255 * self.transition_progress)))
            surf.blit(s, (0, 0))

        return surf

    def end(self):
        self.state = 'complete'

    def process(self):
        while self.command_idx < len(self.commands) and self.state == 'processing':
            command = self.commands[self.command_idx]
            try:
                if self.handle_conditional(command):
                    if self.do_skip and command.nid in self.skippable:
                        pass
                    else:
                        self.run_command(command)
                self.command_idx += 1
            except Exception as e:
                raise Exception("Event execution failed with error in command %s" % command) from e

    def handle_conditional(self, command) -> bool:
        """
        Returns true if the processor should be processing this command
        """
        if command.nid == 'if':
            logging.info('%s: %s', command.nid, command.values)
            if not self.if_stack or self.if_stack[-1]:
                try:
                    truth = bool(evaluate.evaluate(command.values[0], self.unit, self.unit2, self.item, self.position, self.region))
                except Exception as e:
                    logging.error("%s: Could not evaluate {%s}" % (e, command.values[0]))
                    truth = False
                logging.info("Result: %s" % truth)
                self.if_stack.append(truth)
                self.parse_stack.append(truth)
            else:
                self.if_stack.append(False)
                self.parse_stack.append(True)
            return False
        elif command.nid == 'elif':
            logging.info('%s: %s', command.nid, command.values)
            if not self.if_stack:
                logging.error("Syntax Error somewhere in script. 'elif' needs to be after if statement.")
                return False
            # If we haven't encountered a truth yet
            if not self.parse_stack[-1]:
                try:
                    truth = bool(evaluate.evaluate(command.values[0], self.unit, self.unit2, self.item, self.position, self.region))
                except Exception as e:
                    logging.error("Could not evaluate {%s}" % command.values[0])
                    truth = False
                self.if_stack[-1] = truth
                self.parse_stack[-1] = truth
                logging.info("Result: %s" % truth)
            else:
                self.if_stack[-1] = False
            return False
        elif command.nid == 'else':
            logging.info('%s: %s', command.nid, command.values)
            if not self.if_stack:
                logging.error("Syntax Error somewhere in script. 'else' needs to be after if statement.")
                return False
            # If the most recent is False but the rest below are non-existent or true
            if not self.parse_stack[-1]:
                self.if_stack[-1] = True
                self.parse_stack[-1] = True
            else:
                self.if_stack[-1] = False
            return False
        elif command.nid == 'end':
            logging.info('%s: %s', command.nid, command.values)
            if self.if_stack:
                self.if_stack.pop()
            if self.parse_stack:
                self.parse_stack.pop()
            return False

        if self.if_stack and not self.if_stack[-1]:
            return False
        return True

    def skip(self, super_skip=False):
        self.do_skip = True
        self.super_skip = super_skip
        if self.state != 'paused':
            self.state = 'processing'
        self.transition_state = None
        self.hurry_up()
        self.text_boxes.clear()
        self.other_boxes.clear()
        self.should_remain_blocked.clear()
        while self.should_update:
            self.should_update = {name: to_update for name, to_update in self.should_update.items() if not to_update(self.do_skip)}

    def hurry_up(self):
        if self.text_boxes:
            self.text_boxes[-1].hurry_up()

    def run_command(self, command: event_commands.EventCommand):
        logging.info('%s: %s', command.nid, command.values)
        current_time = engine.get_time()

        if command.nid == 'break':
            self.end()

        elif command.nid == 'wait':
            self.wait_time = current_time + int(command.values[0])
            self.state = 'waiting'

        elif command.nid == 'end_skip':
            if not self.super_skip:
                self.do_skip = False

        elif command.nid == 'music':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            music = command.values[0]
            fade = 400
            if len(command.values) > 1 and command.values[1]:
                fade = int(command.values[1])
            if self.do_skip:
                fade = 0
            if music == 'None':
                SOUNDTHREAD.fade_to_pause(fade_out=fade)
            else:
                SOUNDTHREAD.fade_in(music, fade_in=fade)

        elif command.nid == 'music_clear':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            fade = 0
            if len(command.values) > 0 and command.values[0]:
                fade = int(command.values[0])
            if self.do_skip:
                fade = 0
            if fade > 0:
                SOUNDTHREAD.fade_clear(fade)
            else:
                SOUNDTHREAD.clear()

        elif command.nid == 'sound':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            sound = command.values[0]
            volume = 1
            if len(command.values) > 1 and command.values[1]:
                volume = float(command.values[1])
            SOUNDTHREAD.play_sfx(sound, volume=volume)

        elif command.nid == 'change_music':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            phase = command.values[0]
            music = command.values[1]
            if music == 'None':
                action.do(action.ChangePhaseMusic(phase, None))
            else:
                action.do(action.ChangePhaseMusic(phase, music))

        elif command.nid == 'change_background':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            if len(values) > 0 and values[0]:
                panorama = values[0]
                panorama = RESOURCES.panoramas.get(panorama)
                if not panorama:
                    return
                self.background = background.PanoramaBackground(panorama)
            else:
                self.background = None
            if 'keep_portraits' in flags:
                pass
            else:
                self.portraits.clear()

        elif command.nid == 'transition':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            if len(values) > 0 and values[0]:
                self.transition_state = values[0].lower()
            elif self.transition_state == 'close':
                self.transition_state = 'open'
            else:
                self.transition_state = 'close'
            if len(values) > 1 and values[1]:
                self.transition_speed = max(1, int(values[1]))
            else:
                self.transition_speed = self._transition_speed
            if len(values) > 2 and values[2]:
                self.transition_color = tuple(int(_) for _ in values[2].split(','))
            else:
                self.transition_color = self._transition_color
                
            if not self.do_skip:
                self.transition_update = current_time
                self.wait_time = current_time + int(self.transition_speed * 1.33)
                self.state = 'waiting'

        elif command.nid == 'speak':
            self.speak(command)

        elif command.nid == 'add_portrait':
            self.add_portrait(command)

        elif command.nid == 'multi_add_portrait':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            commands = []
            for idx in range(len(values)//2):
                portrait = values[idx*2]
                if idx*2 + 1 < len(values):
                    position = values[idx*2 + 1]
                else:
                    logging.error('No Portrait position given')
                    break
                if idx >= len(values)//2 - 1:  # If last command, don't need no_block flag
                    add_portrait_command = event_commands.AddPortrait([portrait, position])
                else:
                    add_portrait_command = event_commands.AddPortrait([portrait, position, 'no_block'])
                commands.append(add_portrait_command)
            for command in reversed(commands):
                # Done backwards to preserve order upon insertion
                self.commands.insert(self.command_idx + 1, command)

        elif command.nid == 'remove_portrait':
            self.remove_portrait(command)

        elif command.nid == 'multi_remove_portrait':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            commands = []
            for idx, portrait in enumerate(values):
                if idx >= len(values) - 1:
                    remove_portrait_command = event_commands.RemovePortrait([portrait])
                else:
                    remove_portrait_command = event_commands.RemovePortrait([portrait, 'no_block'])
                commands.append(remove_portrait_command)
            for command in reversed(commands):
                # Done backwards to preserve order upon insertion
                self.commands.insert(self.command_idx + 1, command)

        elif command.nid == 'move_portrait':
            self.move_portrait(command)

        elif command.nid == 'bop_portrait':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            name = values[0]
            portrait = self.portraits.get(name)
            if not portrait:
                return False
            portrait.bop()
            if 'no_block' in flags:
                pass
            else:
                self.wait_time = engine.get_time() + 666
                self.state = 'waiting'

        elif command.nid == 'expression':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            name = values[0]
            portrait = self.portraits.get(name)
            if not portrait:
                return False
            expression_list = values[1].split(',')
            portrait.set_expression(expression_list)

        elif command.nid == 'disp_cursor':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            b = command.values[0]
            if b.lower() in self.true_vals:
                game.cursor.show()
            else:
                game.cursor.hide()

        elif command.nid == 'move_cursor':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            position = self.parse_pos(values[0])
            if not position:
                logging.error("Could not determine position from %s" % values[0])
                return

            game.cursor.set_pos(position)
            if 'immediate' in flags or self.do_skip:
                game.camera.force_xy(*position)
            else:
                if len(values) > 1:
                    # we are using a custom camera speed
                    duration = int(values[1])
                    game.camera.do_slow_pan(duration)
                game.camera.set_xy(*position)
                game.state.change('move_camera')
                self.state = 'paused'  # So that the message will leave the update loop

        elif command.nid == 'center_cursor':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            position = self.parse_pos(values[0])
            if not position:
                logging.error("Could not determine position from %s" % values[0])
                return

            game.cursor.set_pos(position)
            if 'immediate' in flags or self.do_skip:
                game.camera.force_center(*position)
            else:
                if len(values) > 1:
                    # we are using a custom camera speed
                    duration = int(values[1])
                    game.camera.do_slow_pan(duration)
                    game.camera.set_center(*position)
                game.state.change('move_camera')
                self.state = 'paused'  # So that the message will leave the update loop

        elif command.nid == 'flicker_cursor':
            # This is a macro that just adds new commands to command list
            move_cursor_command = event_commands.MoveCursor(command.values)
            disp_cursor_command1 = event_commands.DispCursor(['1'])
            wait_command = event_commands.Wait(['1000'])
            disp_cursor_command2 = event_commands.DispCursor(['0'])
            # Done backwards to presever order upon insertion
            self.commands.insert(self.command_idx + 1, disp_cursor_command2)
            self.commands.insert(self.command_idx + 1, wait_command)
            self.commands.insert(self.command_idx + 1, disp_cursor_command1)
            self.commands.insert(self.command_idx + 1, move_cursor_command)

        elif command.nid == 'game_var':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            nid = values[0]
            to_eval = values[1]
            try:
                val = evaluate.evaluate(to_eval, self.unit, self.unit2, self.item, self.position, self.region)
                action.do(action.SetGameVar(nid, val))
            except:
                logging.error("Could not evaluate {%s}" % to_eval)

        elif command.nid == 'inc_game_var':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            nid = values[0]
            if len(values) > 1 and values[1]:
                to_eval = values[1]
                try:
                    val = evaluate.evaluate(to_eval, self.unit, self.unit2, self.item, self.position, self.region)
                    action.do(action.SetGameVar(nid, game.game_vars.get(nid, 0) + val))
                except:
                    logging.error("Could not evaluate {%s}" % to_eval)
            else:
                action.do(action.SetGameVar(nid, game.game_vars.get(nid, 0) + 1))

        elif command.nid == 'level_var':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            nid = values[0]
            to_eval = values[1]
            try:
                val = evaluate.evaluate(to_eval, self.unit, self.unit2, self.item, self.position, self.region)
                action.do(action.SetLevelVar(nid, val))
            except:
                logging.error("Could not evaluate {%s}" % to_eval)
                return
            # Need to update fog of war when we change it
            if nid in ('_fog_of_war', '_fog_of_war_radius', '_ai_fog_of_war_radius'):
                for unit in game.units:
                    if unit.position:
                        action.do(action.UpdateFogOfWar(unit))

        elif command.nid == 'inc_level_var':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            nid = values[0]
            if len(values) > 1 and values[1]:
                to_eval = values[1]
                try:
                    val = evaluate.evaluate(to_eval, self.unit, self.unit2, self.item, self.position, self.region)
                    action.do(action.SetLevelVar(nid, game.level_vars.get(nid, 0) + val))
                except:
                    logging.error("Could not evaluate {%s}" % to_eval)
            else:
                action.do(action.SetLevelVar(nid, game.level_vars.get(nid, 0) + 1))

        elif command.nid == 'win_game':
            game.level_vars['_win_game'] = True

        elif command.nid == 'lose_game':
            game.level_vars['_lose_game'] = True

        elif command.nid == 'activate_turnwheel':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            if len(values) > 0 and values[0] and values[0].lower() not in self.true_vals:
                self.turnwheel_flag = 1
            else:
                self.turnwheel_flag = 2

        elif command.nid == 'battle_save':
            self.battle_save_flag = True

        elif command.nid == 'change_tilemap':
            self.change_tilemap(command)

        elif command.nid == 'load_unit':
            self.load_unit(command)

        elif command.nid == 'make_generic':
            self.make_generic(command)

        elif command.nid == 'create_unit':
            self.create_unit(command)

        elif command.nid == 'add_unit':
            self.add_unit(command)

        elif command.nid == 'remove_unit':
            self.remove_unit(command)

        elif command.nid == 'kill_unit':
            self.kill_unit(command)

        elif command.nid == 'remove_all_units':
            for unit in game.units:
                if unit.position:
                    action.do(action.LeaveMap(unit))

        elif command.nid == 'remove_all_enemies':
            for unit in game.units:
                if unit.position and unit.team.startswith('enemy'):
                    action.do(action.FadeOut(unit))

        elif command.nid == 'move_unit':
            self.move_unit(command)

        elif command.nid == 'interact_unit':
            self.interact_unit(command)

        elif command.nid == 'add_group':
            self.add_group(command)

        elif command.nid == 'spawn_group':
            self.spawn_group(command)

        elif command.nid == 'move_group':
            self.move_group(command)

        elif command.nid == 'remove_group':
            self.remove_group(command)

        elif command.nid == 'give_item':
            self.give_item(command)

        elif command.nid == 'remove_item':
            self.remove_item(command)

        elif command.nid == 'change_item_name':
            self.change_item_name(command)

        elif command.nid == 'change_item_desc':
            self.change_item_desc(command)

        elif command.nid == 'add_item_to_multiitem':
            self.add_item_to_multiitem(command)

        elif command.nid == 'remove_item_from_multiitem':
            self.remove_item_from_multiitem(command)

        elif command.nid == 'give_money':
            self.give_money(command)

        elif command.nid == 'give_bexp':
            self.give_bexp(command)

        elif command.nid == 'give_exp':
            self.give_exp(command)

        elif command.nid == 'set_exp':
            self.set_exp(command)

        elif command.nid == 'give_wexp':
            self.give_wexp(command)

        elif command.nid == 'give_skill':
            self.give_skill(command)

        elif command.nid == 'remove_skill':
            self.remove_skill(command)

        elif command.nid == 'change_ai':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            unit = self.get_unit(values[0])
            if not unit:
                logging.error("Couldn't find unit %s" % values[0])
                return
            if values[1] in DB.ai.keys():
                action.do(action.ChangeAI(unit, values[1]))
            else:
                logging.error("Couldn't find AI %s" % values[1])
                return

        elif command.nid == 'change_party':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            unit = self.get_unit(values[0])
            if not unit:
                logging.error("Couldn't find unit %s" % values[0])
                return
            if values[1] in DB.parties.keys():
                action.do(action.ChangeParty(unit, values[1]))
            else:
                logging.error("Couldn't find Party %s" % values[1])
                return

        elif command.nid == 'change_team':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            unit = self.get_unit(values[0])
            if not unit:
                logging.error("Couldn't find unit %s" % values[0])
                return
            if values[1] in DB.teams:
                action.do(action.ChangeTeam(unit, values[1]))
                if unit.position:
                    action.do(action.UpdateFogOfWar(unit))
            else:
                logging.error("Not a valid team: %s" % values[1])
                return

        elif command.nid == 'change_portrait':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            unit = self.get_unit(values[0])
            if not unit:
                logging.error("Couldn't find unit %s" % values[0])
                return
            portrait = RESOURCES.portraits.get(values[1])
            if not portrait:
                logging.error("Couldn't find portrait %s" % values[1])
                return
            action.do(action.ChangePortrait(unit, values[1]))

        elif command.nid == 'change_stats':
            self.change_stats(command)

        elif command.nid == 'set_stats':
            self.set_stats(command)

        elif command.nid == 'autolevel_to':
            self.autolevel_to(command)

        elif command.nid == 'set_mode_autolevels':
            self.set_mode_autolevels(command)

        elif command.nid == 'promote':
            self.promote(command)

        elif command.nid == 'change_class':
            self.class_change(command)

        elif command.nid == 'add_tag':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            unit = self.get_unit(values[0])
            if not unit:
                logging.error("Couldn't find unit %s" % values[0])
                return
            if values[1] in DB.tags.keys():
                action.do(action.AddTag(unit, values[1]))

        elif command.nid == 'remove_tag':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            unit = self.get_unit(values[0])
            if not unit:
                logging.error("Couldn't find unit %s" % values[0])
                return
            if values[1] in DB.tags.keys():
                action.do(action.RemoveTag(unit, values[1]))

        elif command.nid == 'set_current_hp':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            unit = self.get_unit(values[0])
            if not unit:
                logging.error("Couldn't find unit %s" % values[0])
                return
            hp = int(values[1])
            action.do(action.SetHP(unit, hp))

        elif command.nid == 'set_current_mana':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            unit = self.get_unit(values[0])
            if not unit:
                logging.error("Couldn't find unit %s" % values[0])
                return
            mana = int(values[1])
            action.do(action.SetMana(unit, mana))

        elif command.nid == 'add_fatigue':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            unit = self.get_unit(values[0])
            if not unit:
                logging.error("Couldn't find unit %s" % values[0])
                return
            fatigue = int(values[1])
            action.do(action.ChangeFatigue(unit, fatigue))

        elif command.nid == 'set_unit_field':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            unit = self.get_unit(values[0])
            if not unit:
                logging.error("Couldn't find unit %s" % values[0])
                return
            key = values[1]
            try:
                value = evaluate.evaluate(values[2])
            except:
                logging.error("Could not evaluate {%s}" % values[2])
                return
            should_increment = False
            if 'increment_mode' in flags:
                should_increment = True
            action.do(action.ChangeField(unit, key, value, should_increment))

        elif command.nid == 'resurrect':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            unit = self.get_unit(values[0])
            if not unit:
                logging.error("Couldn't find unit %s" % values[0])
                return
            if unit.dead:
                action.do(action.Resurrect(unit))
            action.do(action.Reset(unit))
            action.do(action.SetHP(unit, 1000))

        elif command.nid == 'reset':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            unit = self.get_unit(values[0])
            if not unit:
                logging.error("Couldn't find unit %s" % values[0])
                return
            action.do(action.Reset(unit))

        elif command.nid == 'has_attacked':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            unit = self.get_unit(values[0])
            if not unit:
                logging.error("Couldn't find unit %s" % values[0])
                return
            action.do(action.HasAttacked(unit))

        elif command.nid == 'has_traded':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            unit = self.get_unit(values[0])
            if not unit:
                logging.error("Couldn't find unit %s" % values[0])
                return
            action.do(action.HasTraded(unit))

        elif command.nid == 'add_talk':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            action.do(action.AddTalk(values[0], values[1]))

        elif command.nid == 'remove_talk':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            action.do(action.RemoveTalk(values[0], values[1]))

        elif command.nid == 'add_lore':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            action.do(action.AddLore(values[0]))

        elif command.nid == 'remove_lore':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            action.do(action.RemoveLore(values[0]))

        elif command.nid == 'add_base_convo':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            game.base_convos[values[0]] = False

        elif command.nid == 'remove_base_convo':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            if values[0] in game.base_convos:
                del game.base_convos[values[0]]

        elif command.nid == 'ignore_base_convo':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            if values[0] in game.base_convos:
                game.base_convos[values[0]] = True

        elif command.nid == 'increment_support_points':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            unit1 = self.get_unit(values[0])
            if not unit1:
                unit1 = DB.units.get(values[0])
            if not unit1:
                logging.error("Couldn't find unit %s" % values[0])
                return
            unit2 = self.get_unit(values[1])
            if not unit2:
                unit2 = DB.units.get(values[1])
            if not unit2:
                logging.error("Couldn't find unit %s" % values[1])
                return
            inc = int(values[2])
            prefabs = DB.support_pairs.get_pairs(unit1.nid, unit2.nid)
            if prefabs:
                prefab = prefabs[0]
                action.do(action.IncrementSupportPoints(prefab.nid, inc))
            else:
                logging.error("Couldn't find prefab for units %s and %s" % (unit1.nid, unit2.nid))
                return

        elif command.nid == 'unlock_support_rank':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            unit1 = self.get_unit(values[0])
            if not unit1:
                unit1 = DB.units.get(values[0])
            if not unit1:
                logging.error("Couldn't find unit %s" % values[0])
                return
            unit2 = self.get_unit(values[1])
            if not unit2:
                unit2 = DB.units.get(values[1])
            if not unit2:
                logging.error("Couldn't find unit %s" % values[1])
                return
            rank = values[2]
            if rank not in DB.support_ranks.keys():
                logging.error("Support rank %s not a valid rank!" % rank)
                return
            prefabs = DB.support_pairs.get_pairs(unit1.nid, unit2.nid)
            if prefabs:
                prefab = prefabs[0]
                action.do(action.UnlockSupportRank(prefab.nid, rank))
            else:
                logging.error("Couldn't find prefab for units %s and %s" % (unit1.nid, unit2.nid))
                return

        elif command.nid == 'add_market_item':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            item = values[0]
            if item in DB.items.keys():
                game.market_items.add(item)
            else:
                logging.warning("%s is not a legal item nid", item)

        elif command.nid == 'remove_market_item':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            item = values[0]
            game.market_items.discard(item)

        elif command.nid == 'add_region':
            self.add_region(command)

        elif command.nid == 'region_condition':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            nid = values[0]
            if nid in game.level.regions.keys():
                region = game.level.regions.get(nid)
                action.do(action.ChangeRegionCondition(region, values[1]))
            else:
                logging.error("Couldn't find Region %s" % nid)

        elif command.nid == 'remove_region':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            nid = values[0]
            if nid in game.level.regions.keys():
                region = game.level.regions.get(nid)
                action.do(action.RemoveRegion(region))
            else:
                logging.error("Couldn't find Region %s" % nid)

        elif command.nid == 'show_layer':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            nid = values[0]
            if nid not in game.level.tilemap.layers.keys():
                logging.error("Could not find layer %s in tilemap" % nid)
                return
            if len(values) > 1 and values[1]:
                transition = values[1]
            else:
                transition = 'fade'

            action.do(action.ShowLayer(nid, transition))

        elif command.nid == 'hide_layer':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            nid = values[0]
            if nid not in game.level.tilemap.layers.keys():
                logging.error("Could not find layer %s in tilemap" % nid)
                return
            if len(values) > 1 and values[1]:
                transition = values[1]
            else:
                transition = 'fade'

            action.do(action.HideLayer(nid, transition))

        elif command.nid == 'add_weather':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            nid = values[0].lower()
            action.do(action.AddWeather(nid))

        elif command.nid == 'remove_weather':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            nid = values[0].lower()
            action.do(action.RemoveWeather(nid))

        elif command.nid == 'change_objective_simple':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            action.do(action.ChangeObjective('simple', values[0]))

        elif command.nid == 'change_objective_win':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            action.do(action.ChangeObjective('win', values[0]))

        elif command.nid == 'change_objective_loss':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            action.do(action.ChangeObjective('loss', values[0]))

        elif command.nid == 'set_position':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            pos = self.parse_pos(values[0])
            self.position = pos

        elif command.nid == 'map_anim':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            nid = values[0]
            if nid not in RESOURCES.animations.keys():
                logging.error("Could not find map animation %s" % nid)
                return
            pos = self.parse_pos(values[1], True)
            if len(values) > 2:
                speed_mult = int(values[2])
            else:
                speed_mult = 1
            if 'permanent' in flags:
                action.do(action.AddMapAnim(nid, pos, speed_mult, 'blend' in flags))
            else:
                anim = RESOURCES.animations.get(nid)
                anim = MapAnimation(anim, pos, speed_adj=speed_mult)
                anim.set_tint('blend' in flags)
                self.animations.append(anim)

            if 'no_block' in flags or self.do_skip or 'permanent' in flags:
                pass
            else:
                self.wait_time = engine.get_time() + anim.get_wait()
                self.state = 'waiting'

        elif command.nid == 'remove_map_anim':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            nid = values[0]
            pos = self.parse_pos(values[1])
            action.do(action.RemoveMapAnim(nid, pos))

        elif command.nid == 'merge_parties':
            self.merge_parties(command)

        elif command.nid == 'arrange_formation':
            self.arrange_formation()

        elif command.nid == 'prep':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            if values and values[0].lower() in self.true_vals:
                b = True
            else:
                b = False
            action.do(action.SetLevelVar('_prep_pick', b))
            if len(values) > 1 and values[1]:
                action.do(action.SetGameVar('_prep_music', values[1]))
            game.state.change('prep_main')
            self.state = 'paused'  # So that the message will leave the update loop

        elif command.nid == 'base':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            panorama_nid = values[0]
            action.do(action.SetGameVar('_base_bg_name', panorama_nid))
            if len(values) > 1 and values[1]:
                action.do(action.SetGameVar('_base_music', values[1]))
            if 'show_map' in flags:
                action.do(action.SetGameVar('_base_transparent', True))
            else:
                action.do(action.SetGameVar('_base_transparent', False))
            game.state.change('base_main')
            self.state = 'paused'

        elif command.nid == 'shop':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            unit = self.get_unit(values[0])
            if not unit:
                logging.error("Must have a unit visit the shop!")
                return
            game.memory['current_unit'] = unit
            item_list = values[1].split(',')
            shop_items = item_funcs.create_items(unit, item_list)
            game.memory['shop_items'] = shop_items

            if len(values) > 2 and values[2]:
                game.memory['shop_flavor'] = values[2].lower()
            else:
                game.memory['shop_flavor'] = 'armory'
            game.state.change('shop')
            self.state = 'paused'

        elif command.nid == 'choice':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            nid = values[0]
            header = values[1]
            options_list = values[2].split(',')

            orientation = 'vertical'
            if len(values) > 3 and values[3]:
                if values[3].lower() in ('h', 'horiz', 'horizontal'):
                    orientation = 'horizontal'

            game.memory['player_choice'] = (nid, header, options_list, orientation)
            game.state.change('player_choice')
            self.state = 'paused'

        elif command.nid == 'chapter_title':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            if len(values) > 0 and values[0]:
                music = values[0]
            else:
                music = None
            if len(values) > 1 and values[1]:
                custom_string = values[1]
            else:
                custom_string = None
            game.memory['chapter_title_music'] = music
            game.memory['chapter_title_title'] = custom_string
            # End the skip here
            self.do_skip = False
            self.super_skip = False
            game.state.change('chapter_title')
            self.state = 'paused'

        elif command.nid == 'alert':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            custom_string = values[0]
            game.alerts.append(banner.Custom(custom_string))
            game.state.change('alert')
            self.state = 'paused'

        elif command.nid == 'alert_item':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            custom_string = values[0]
            custom_item_nid = values[1]
            if custom_item_nid in DB.items.keys():
                custom_item = DB.items.get(custom_item_nid)
            else:
                logging.error("Couldn't find item with nid %s" % custom_item_nid)
                return
            game.alerts.append(banner.CustomIcon(custom_string, custom_item))
            game.state.change('alert')
            self.state = 'paused'

        elif command.nid == 'alert_skill':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            custom_string = values[0]
            custom_skill_nid = values[1]
            if custom_skill_nid in DB.skills.keys():
                custom_skill = DB.skills.get(custom_skill_nid)
            else:
                logging.error("Couldn't find skill with nid %s" % custom_skill_nid)
                return
            game.alerts.append(banner.CustomIcon(custom_string, custom_skill))
            game.state.change('alert')
            self.state = 'paused'

        elif command.nid == 'victory_screen':
            game.state.change('victory')
            self.state = 'paused'

        elif command.nid == 'records_screen':
            game.state.change('base_records')
            self.state = 'paused'

        elif command.nid == 'location_card':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            custom_string = values[0]

            new_location_card = dialog.LocationCard(custom_string)
            self.other_boxes.append(new_location_card)

            self.wait_time = engine.get_time() + new_location_card.exist_time
            self.state = 'waiting'

        elif command.nid == 'credits':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            title = values[0]
            credits = values[1].split(',') if 'no_split' not in flags else [values[1]]
            wait = 'wait' in flags
            center = 'center' in flags

            new_credits = dialog.Credits(title, credits, wait, center)
            self.other_boxes.append(new_credits)

            self.wait_time = engine.get_time() + new_credits.wait_time()
            self.state = 'waiting'

        elif command.nid == 'ending':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            name = values[0]
            unit = self.get_unit(name)
            if unit and unit.portrait_nid:
                portrait = icons.get_portrait(unit)
                portrait = portrait.convert_alpha()
                portrait = image_mods.make_translucent(portrait, 0.2)
            else:
                logging.error("Couldn't find unit or portrait %s" % name)
                return False
            title = values[1]
            text = values[2]

            new_ending = dialog.Ending(portrait, title, text, unit)
            self.text_boxes.append(new_ending)
            self.state = 'dialog'

        elif command.nid == 'pop_dialog':
            self.text_boxes.pop()

        elif command.nid == 'unlock':
            # This is a macro that just adds new commands to command list
            find_unlock_command = event_commands.FindUnlock(command.values)
            spend_unlock_command = event_commands.SpendUnlock(command.values)
            # Done backwards to presever order upon insertion
            self.commands.insert(self.command_idx + 1, spend_unlock_command)
            self.commands.insert(self.command_idx + 1, find_unlock_command)

        elif command.nid == 'find_unlock':
            self.find_unlock(command)

        elif command.nid == 'spend_unlock':
            self.spend_unlock(command)

        elif command.nid == 'trigger_script':
            self.trigger_script(command)

        elif command.nid == 'loop_units':
            self.loop_units(command)

        elif command.nid == 'change_roaming':
            self.change_roaming(command)

        elif command.nid == 'change_roaming_unit':
            self.change_roaming_unit(command)

        elif command.nid == 'overworld_cinematic':
            self.start_overworld_cinematic(command)

        elif command.nid == 'set_overworld_position':
            values, flags = event_commands.convert_parse(command)
            self.set_overworld_position(*values, flags=flags)

        elif command.nid == 'reveal_overworld_node':
            self.reveal_overworld_node(command)

        elif command.nid == 'reveal_overworld_road':
            self.reveal_overworld_road(command)

        elif command.nid == 'disable_overworld_entity':
            self.disable_overworld_entity(command)

        elif command.nid == 'overworld_move_unit':
            values, flags = event_commands.convert_parse(command)
            self.overworld_move_unit(*values, flags=flags)

        elif command.nid == 'toggle_narration_mode':
            self.toggle_narration(command)

        elif command.nid == 'narrate':
            self.overworld_speak(command)

        elif command.nid == 'create_overworld_entity':
            self.create_overworld_entity(command)

        elif command.nid == 'clean_up_roaming':
            self.clean_up_roaming(command)

        elif command.nid == 'add_to_initiative':
            self.add_to_initiative(command)

        elif command.nid == 'move_in_initiative':
            self.move_in_initiative(command)

        elif command.nid == 'pair_up':
            self.pair_up(command)

        elif command.nid == 'separate':
            self.separate(command)

        elif command.nid == 'draw_overlay_sprite':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            name = values[0]
            sprite_nid = values[1]
            z = 0
            pos = (0, 0)
            if len(values) > 2:
                pos = eval(values[2])  # Why do we eval this instead of just reading position like we do elsewhere?
            if len(values) > 3:
                z = eval(values[3])  # Why do we eval this also?
            sprite = SPRITES.get(sprite_nid)
            self.overlay_ui.add_surf(sprite, pos, z, name)

        elif command.nid == 'remove_overlay_sprite':
            values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
            name = values[0]
            self.overlay_ui.remove_surf(name)

    def add_portrait(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        name = values[0]
        unit = self.get_unit(name)
        if unit and unit.portrait_nid:
            portrait = RESOURCES.portraits.get(unit.portrait_nid)
        elif name in DB.units.keys():
            portrait = RESOURCES.portraits.get(DB.units.get(name).portrait_nid)
        else:
            portrait = RESOURCES.portraits.get(name)
        if not portrait:
            logging.error("Couldn't find portrait %s" % name)
            return False
        # If already present, don't add
        if name in self.portraits and not self.portraits[name].remove:
            return False

        pos = values[1]
        if len(values) > 4 and values[4]: # there's a vertical position as well
            vert_pos = values[4]
        else:
            vert_pos = 'Bottom'
        if pos in screen_positions:
            position = [screen_positions[pos], vertical_screen_positions[vert_pos]]
            mirror = 'Left' in pos
        else:
            position = [int(p) for p in pos.split(',')]
            mirror = False

        priority = self.priority_counter
        if 'low_priority' in flags:
            priority -= 1000
        self.priority_counter += 1

        if 'mirror' in flags:
            mirror = not mirror

        transition = True
        if 'immediate' in flags or self.do_skip:
            transition = False

        slide = None
        if len(values) > 2 and values[2]:
            slide = values[2]

        new_portrait = EventPortrait(portrait, position, priority, transition, slide, mirror)
        self.portraits[name] = new_portrait

        if len(values) > 3 and values[3]:
            expression_list = values[3].split(',')
            new_portrait.set_expression(expression_list)

        if 'immediate' in flags or 'no_block' in flags or self.do_skip:
            pass
        else:
            self.wait_time = engine.get_time() + new_portrait.transition_speed + 33  # 16 frames
            self.state = 'waiting'

        return True

    def remove_portrait(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        name = values[0]
        if name not in self.portraits:
            return False

        if 'immediate' in flags or self.do_skip:
            portrait = self.portraits.pop(name)
        else:
            portrait = self.portraits[name]
            portrait.end()

        if 'immediate' in flags or 'no_block' in flags or self.do_skip:
            pass
        else:
            self.wait_time = engine.get_time() + portrait.transition_speed + 33
            self.state = 'waiting'

    def move_portrait(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        name = values[0]
        portrait = self.portraits.get(name)
        if not portrait:
            return False

        pos = values[1]
        if pos in screen_positions:
            position = [screen_positions[pos], 80]
        else:
            position = [int(p) for p in pos.split(',')]

        if 'immediate' in flags or self.do_skip:
            portrait.quick_move(position)
        else:
            portrait.move(position)

        if 'immediate' in flags or 'no_block' in flags or self.do_skip:
            pass
        else:
            self.wait_time = engine.get_time() + portrait.travel_time + 66
            self.state = 'waiting'

    def _evaluate_evals(self, text) -> str:
        # Set up variables so evals work well
        to_evaluate = re.findall(r'\{eval:[^{}]*\}', text)
        evaluated = []
        for to_eval in to_evaluate:
            try:
                val = evaluate.evaluate(to_eval[6:-1], self.unit, self.unit2, self.item, self.position, self.region)
                evaluated.append(str(val))
            except Exception as e:
                logging.error("Could not evaluate %s (%s)" % (to_eval[6:-1], e))
                evaluated.append('??')
        for idx in range(len(to_evaluate)):
            text = text.replace(to_evaluate[idx], evaluated[idx])
        return text

    def _evaluate_vars(self, text) -> str:
        to_evaluate = re.findall(r'\{var:[^{}]*\}', text)
        evaluated = []
        for to_eval in to_evaluate:
            key = to_eval[5:-1]
            if key in game.level_vars:
                val = str(game.level_vars[key])
            elif key in game.game_vars:
                val = str(game.game_vars[key])
            else:
                logging.error("Could not find var {%s} in game.level_vars or game.game_vars" % key)
                val = '??'
            evaluated.append(val)
        for idx in range(len(to_evaluate)):
            text = text.replace(to_evaluate[idx], evaluated[idx])
        return text

    def speak(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)

        speaker = values[0]
        text = values[1]

        if len(values) > 2 and values[2]:
            position = self.parse_pos(values[2])
        else:
            position = None
        if len(values) > 3 and values[3]:
            width = int(values[3])
        else:
            width = None
        if len(values) > 4 and values[4]:
            variant = values[4]
        else:
            variant = None

        portrait = self.portraits.get(speaker)
        bg = 'message_bg_base'
        if variant == 'noir':
            bg = 'menu_bg_dark'
        elif variant == 'cinematic':
            bg = None
            if not position:
                position = 'center'
        elif variant == 'hint':
            bg = 'menu_bg_parchment'
            if not position:
                position = 'center'
            if not width:
                width = WINWIDTH//2 + 8
        elif variant == 'narration':
            bg = 'menu_bg_base'
            if not position:
                position = (4, 110)
            if not width:
                width = WINWIDTH - 8
        elif variant == 'narration_top':
            bg = 'menu_bg_base'
            if not position:
                position = (4, 2)
            if not width:
                width = WINWIDTH - 8

        new_dialog = dialog.Dialog(text, portrait, bg, position, width, speaker=speaker, variant=variant)
        self.text_boxes.append(new_dialog)
        self.state = 'dialog'
        # Bring portrait to forefront
        if portrait and 'low_priority' not in flags:
            portrait.priority = self.priority_counter
            self.priority_counter += 1

    def _place_unit(self, unit, position, entry_type):
        if self.do_skip:
            action.do(action.ArriveOnMap(unit, position))
        elif entry_type == 'warp':
            action.do(action.WarpIn(unit, position))
        elif entry_type == 'swoosh':
            action.do(action.SwooshIn(unit, position))
        elif entry_type == 'fade':
            action.do(action.FadeIn(unit, position))
        else:  # immediate
            action.do(action.ArriveOnMap(unit, position))

    def add_unit(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        unit = self.get_unit(values[0])
        if not unit:
            logging.error("Couldn't find unit %s" % values[0])
            return
        if unit.position:
            logging.error("Unit already on map!")
            return
        if unit.dead:
            logging.error("Unit is dead!")
            return
        if len(values) > 1 and values[1]:
            position = self.parse_pos(values[1])
        else:
            position = unit.starting_position
        if not position:
            logging.error("No position found!")
            return
        if len(values) > 2 and values[2]:
            entry_type = values[2]
        else:
            entry_type = 'fade'
        if len(values) > 3 and values[3]:
            placement = values[3]
        else:
            placement = 'giveup'
        position = self.check_placement(unit, position, placement)
        if not position:
            return None
        if DB.constants.value('initiative'):
            action.do(action.InsertInitiative(unit))
        self._place_unit(unit, position, entry_type)

    def move_unit(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        unit = self.get_unit(values[0])
        if not unit:
            logging.error("Couldn't find unit %s" % values[0])
            return
        if not unit.position:
            logging.error("Unit not on map!")
            return

        if len(values) > 1 and values[1]:
            position = self.parse_pos(values[1])
        else:
            position = unit.starting_position
        if not position:
            logging.error("No position found!")
            return

        if len(values) > 2 and values[2]:
            movement_type = values[2]
        else:
            movement_type = 'normal'
        if len(values) > 3 and values[3]:
            placement = values[3]
        else:
            placement = 'giveup'
        follow = 'no_follow' not in flags

        position = self.check_placement(unit, position, placement)
        if not position:
            logging.error("Couldn't get a good position %s %s %s" % (position, movement_type, placement))
            return None

        if movement_type == 'immediate' or self.do_skip:
            action.do(action.Teleport(unit, position))
        elif movement_type == 'warp':
            action.do(action.Warp(unit, position))
        elif movement_type == 'swoosh':
            action.do(action.Swoosh(unit, position))
        elif movement_type == 'fade':
            action.do(action.FadeMove(unit, position))
        elif movement_type == 'normal':
            path = target_system.get_path(unit, position)
            action.do(action.Move(unit, position, path, event=True, follow=follow))

        if 'no_block' in flags or self.do_skip:
            pass
        else:
            self.state = 'paused'
            game.state.change('movement')

    def remove_unit(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        unit = self.get_unit(values[0])
        if not unit:
            logging.error("Couldn't find unit %s" % values[0])
            return
        if not unit.position:
            logging.error("Unit not on map!")
            return
        if len(values) > 1 and values[1]:
            remove_type = values[1]
        else:
            remove_type = 'fade'
        if DB.constants.value('initiative'):
            action.do(action.RemoveInitiative(unit))
        if self.do_skip:
            action.do(action.LeaveMap(unit))
        elif remove_type == 'warp':
            action.do(action.WarpOut(unit))
        elif remove_type == 'swoosh':
            action.do(action.SwooshOut(unit))
        elif remove_type == 'fade':
            action.do(action.FadeOut(unit))
        else:  # immediate
            action.do(action.LeaveMap(unit))

    def kill_unit(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        unit = self.get_unit(values[0])
        if not unit:
            logging.error("Couldn't find unit %s" % values[0])
            return

        if DB.constants.value('initiative'):
            action.do(action.RemoveInitiative(unit))

        if not unit.position:
            unit.dead = True
        elif 'immediate' in flags:
            unit.dead = True
            action.do(action.LeaveMap(unit))
        else:
            game.death.should_die(unit)
            game.state.change('dying')
        game.events.trigger('unit_death', unit, position=unit.position)
        skill_system.on_death(unit)
        self.state = 'paused'

    def interact_unit(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        unit1 = self.get_unit(values[0])
        unit2 = self.get_unit(values[1])
        if not unit1 or not unit1.position:
            logging.error("Couldn't find %s" % unit1)
            return
        if not unit2 or not unit2.position:
            logging.error("Couldn't find %s" % unit2)
            return

        if len(values) > 2 and values[2]:
            script = values[2].split(',')
        else:
            script = None

        items = item_funcs.get_all_items(unit1)
        item = None
        # Get item
        if len(values) > 3 and values[3]:
            item_nid = values[3]
            for i in items:
                if item_nid == i.nid:
                    item = i
                    break
            else:  # Create item on the fly
                item_prefab = DB.items.get(values[3])
                if not item_prefab:
                    logging.error("Couldn't find item with nid %s" % values[3])
                    return
                # Create item
                item = ItemObject.from_prefab(item_prefab)
                item_system.init(item)
                game.register_item(item)
        else:
            if items:
                item = items[0]
            else:
                logging.error("Unit does not have item!")
                return

        interaction.start_combat(unit1, unit2.position, item, event_combat=True, script=script)
        self.state = "paused"

    def add_group(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        group = game.level.unit_groups.get(values[0])
        if not group:
            logging.error("Couldn't find group %s" % values[0])
            return
        if len(values) > 1 and values[1]:
            next_pos = values[1]
        else:
            next_pos = None
        if len(values) > 2 and values[2]:
            entry_type = values[2]
        else:
            entry_type = 'fade'
        if len(values) > 3 and values[3]:
            placement = values[3]
        else:
            placement = 'giveup'
        create = 'create' in flags
        for unit_nid in group.units:
            unit = game.get_unit(unit_nid)
            if create:
                unit = self._copy_unit(unit_nid)
                if not unit:
                    continue
            elif unit.position or unit.dead:
                continue
            position = self._get_position(next_pos, unit, group, unit_nid)
            if not position:
                continue
            position = tuple(position)
            position = self.check_placement(unit, position, placement)
            if not position:
                logging.warning("Couldn't determine valid position for %s?", unit.nid)
                continue
            if DB.constants.value('initiative'):
                action.do(action.InsertInitiative(unit))
            self._place_unit(unit, position, entry_type)

    def _move_unit(self, movement_type, placement, follow, unit, position):
        position = tuple(position)
        position = self.check_placement(unit, position, placement)
        if not position:
            logging.warning("Couldn't determine valid position for %s?", unit.nid)
            return
        if movement_type == 'immediate' or self.do_skip:
            action.do(action.Teleport(unit, position))
        elif movement_type == 'warp':
            action.do(action.Warp(unit, position))
        elif movement_type == 'fade':
            action.do(action.FadeMove(unit, position))
        elif movement_type == 'normal':
            path = target_system.get_path(unit, position)
            action.do(action.Move(unit, position, path, event=True, follow=follow))

    def _add_unit_from_direction(self, unit, position, direction, placement) -> bool:
        offsets = [-1, 1, -2, 2, -3, 3, -4, 4, -5, 5, -6, 6, -7, 7]
        final_pos = None

        if direction == 'west':
            test_pos = (0, position[1])
            for x in offsets:
                if game.movement.check_traversable(unit, test_pos):
                    final_pos = test_pos
                    break
                else:
                    test_pos = (0, position[1] + x)
        elif direction == 'east':
            test_pos = (game.tilemap.width - 1, position[1])
            for x in offsets:
                if game.movement.check_traversable(unit, test_pos):
                    final_pos = test_pos
                    break
                else:
                    test_pos = (game.tilemap.width - 1, position[1] + x)
        elif direction == 'north':
            test_pos = (position[0], 0)
            for x in offsets:
                if game.movement.check_traversable(unit, test_pos):
                    final_pos = test_pos
                    break
                else:
                    test_pos = (position[0] + x, 0)
        elif direction == 'south':
            test_pos = (position[0], game.tilemap.height - 1)
            for x in offsets:
                if game.movement.check_traversable(unit, test_pos):
                    final_pos = test_pos
                    break
                else:
                    test_pos = (position[1] + x, game.tilemap.height - 1)
        if final_pos:
            final_pos = self.check_placement(unit, final_pos, placement)
        if final_pos:
            action.do(action.ArriveOnMap(unit, final_pos))
            return True
        return False

    def _get_position(self, next_pos, unit, group, unit_nid=None):
        if unit_nid is None:
            unit_nid = unit.nid
        if not next_pos:
            position = group.positions.get(unit_nid)
        elif next_pos.lower() == 'starting':
            position = unit.starting_position
        elif ',' in next_pos:
            position = self.parse_pos(next_pos)
        else:
            other_group = game.level.unit_groups.get(next_pos)
            position = other_group.positions.get(unit_nid)
        return position

    def spawn_group(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        group = game.level.unit_groups.get(values[0])
        if not group:
            logging.error("Couldn't find group %s", values[0])
            return
        cardinal_direction = values[1].lower()
        if cardinal_direction not in ('east', 'west', 'north', 'south'):
            logging.error("%s not a legal cardinal direction", cardinal_direction)
            return
        next_pos = values[2]
        if len(values) > 3 and values[3]:
            movement_type = values[3]
        else:
            movement_type = 'normal'
        if len(values) > 4 and values[4]:
            placement = values[4]
        else:
            placement = 'giveup'
        create = 'create' in flags
        follow = 'no_follow' not in flags

        for unit_nid in group.units:
            unit = game.get_unit(unit_nid)
            if create:
                unit = self._copy_unit(unit_nid)
                if not unit:
                    continue
            elif unit.position or unit.dead:
                logging.warning("Unit %s in group %s already on map or dead", unit.nid, group.nid)
                continue
            position = self._get_position(next_pos, unit, group, unit_nid)
            if not position:
                continue

            if self._add_unit_from_direction(unit, position, cardinal_direction, placement):
                if DB.constants.value('initiative'):
                    action.do(action.InsertInitiative(unit))
                self._move_unit(movement_type, placement, follow, unit, position)
            else:
                logging.error("Couldn't add unit %s to position %s" % (unit.nid, position))

        if 'no_block' in flags or self.do_skip:
            pass
        else:
            self.state = 'paused'
            game.state.change('movement')

    def move_group(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        group = game.level.unit_groups.get(values[0])
        if not group:
            logging.error("Couldn't find group %s" % values[0])
            return
        next_pos = values[1]
        if len(values) > 2 and values[2]:
            movement_type = values[2]
        else:
            movement_type = 'normal'
        if len(values) > 3 and values[3]:
            placement = values[3]
        else:
            placement = 'giveup'
        follow = 'no_follow' not in flags

        for unit_nid in group.units:
            unit = game.get_unit(unit_nid)
            if not unit.position:
                continue
            position = self._get_position(next_pos, unit, group)
            if not position:
                continue
            self._move_unit(movement_type, placement, follow, unit, position)

        if 'no_block' in flags or self.do_skip:
            pass
        else:
            self.state = 'paused'
            game.state.change('movement')

    def remove_group(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        group = game.level.unit_groups.get(values[0])
        if not group:
            logging.error("Couldn't find group %s" % values[0])
            return
        if len(values) > 1 and values[1]:
            remove_type = values[1]
        else:
            remove_type = 'fade'
        for unit_nid in group.units:
            unit = game.get_unit(unit_nid)
            if DB.constants.value('initiative'):
                action.do(action.RemoveInitiative(unit))
            if unit.position:
                if self.do_skip:
                    action.do(action.LeaveMap(unit))
                elif remove_type == 'warp':
                    action.do(action.WarpOut(unit))
                elif remove_type == 'fade':
                    action.do(action.FadeOut(unit))
                else:  # immediate
                    action.do(action.LeaveMap(unit))

    def check_placement(self, unit, position, placement):
        current_occupant = game.board.get_unit(position)
        if current_occupant:
            if placement == 'giveup':
                logging.warning("Check placement (giveup): Unit already present on tile %s", position)
                return None
            elif placement == 'stack':
                return position
            elif placement == 'closest':
                position = target_system.get_nearest_open_tile(unit, position)
                if not position:
                    logging.warning("Somehow wasn't able to find a nearby open tile")
                    return None
                return position
            elif placement == 'push':
                new_pos = target_system.get_nearest_open_tile(current_occupant, position)
                action.do(action.ForcedMovement(current_occupant, new_pos))
                return position
        else:
            return position

    def change_tilemap(self, command):
        """
        Cannot be turnwheeled
        """
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)

        reload_map = 'reload' in flags
        if reload_map and game.is_displaying_overworld(): # just go back to the level
            from app.engine import level_cursor, map_view, movement
            game.cursor = level_cursor.LevelCursor(game)
            game.movement = movement.MovementManager()
            game.map_view = map_view.MapView()
            game.boundary = self.prev_game_boundary
            game.board = self.prev_board
            return

        if not len(values) > 0:
            return
        tilemap_nid = values[0]
        tilemap_prefab = RESOURCES.tilemaps.get(tilemap_nid)
        if not tilemap_prefab:
            logging.error("Couldn't find tilemap %s" % tilemap_nid)
            return

        if len(values) > 1 and values[1]:
            position_offset = tuple(str_utils.intify(values[1]))
        else:
            position_offset = (0, 0)
        if len(values) > 2 and values[2]:
            reload_map_nid = values[2]
        else:
            reload_map_nid = tilemap_nid

        # Reset cursor position
        game.cursor.set_pos((0, 0))

        # Remove all units from the map
        # But remember their original positions for later
        previous_unit_pos = {}
        for unit in game.units:
            if unit.position:
                previous_unit_pos[unit.nid] = unit.position
                act = action.LeaveMap(unit)
                act.execute()
        current_tilemap_nid = game.level.tilemap.nid
        game.level_vars['_prev_pos_%s' % current_tilemap_nid] = previous_unit_pos

        tilemap = TileMapObject.from_prefab(tilemap_prefab)
        game.level.tilemap = tilemap
        if game.is_displaying_overworld():
            # we were in the overworld before this, so we should probably reset cursor and such
            from app.engine import level_cursor, map_view, movement
            game.cursor = level_cursor.LevelCursor(game)
            game.movement = movement.MovementManager()
            game.map_view = map_view.MapView()
        game.set_up_game_board(game.level.tilemap)

        # If we're reloading the map
        if reload_map and game.level_vars.get('_prev_pos_%s' % reload_map_nid):
            for unit_nid, pos in game.level_vars['_prev_pos_%s' % reload_map_nid].items():
                # Reload unit's position with position offset
                final_pos = pos[0] + position_offset[0], pos[1] + position_offset[1]
                if game.tilemap.check_bounds(final_pos):
                    unit = game.get_unit(unit_nid)
                    act = action.ArriveOnMap(unit, final_pos)
                    act.execute()

        # Can't use turnwheel to go any further back
        game.action_log.set_first_free_action()

    def _copy_unit(self, unit_nid):
        level_prefab = DB.levels.get(game.level.nid)
        level_unit_prefab = level_prefab.units.get(unit_nid)
        if not level_unit_prefab:
            logging.warning("Could not find level unit prefab for unit with nid: %s", unit_nid)
            return None
        new_nid = str_utils.get_next_int(level_unit_prefab.nid, game.unit_registry.keys())
        level_unit_prefab.nid = new_nid
        new_unit = UnitObject.from_prefab(level_unit_prefab)
        level_unit_prefab.nid = unit_nid  # Set back to old nid
        new_unit.position = None
        new_unit.dead = False
        new_unit.party = game.current_party
        game.full_register(new_unit)
        return new_unit

    def load_unit(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        unit_nid = values[0]
        if game.get_unit(unit_nid):
            logging.error("Unit with NID %s already exists!" % unit_nid)
            return
        unit_prefab = DB.units.get(unit_nid)
        if not unit_prefab:
            logging.error("Could not find unit %s in database" % unit_nid)
            return
        if len(values) > 1 and values[1]:
            team = values[1]
        else:
            team = 'player'
        if len(values) > 2 and values[2]:
            ai_nid = values[2]
        else:
            ai_nid = 'None'
        level_unit_prefab = UniqueUnit(unit_nid, team, ai_nid, None)
        new_unit = UnitObject.from_prefab(level_unit_prefab)
        new_unit.party = game.current_party
        game.full_register(new_unit)

    def make_generic(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        assign_unit = False
        # Get input
        unit_nid = values[0]
        if not unit_nid:
            unit_nid = str_utils.get_next_int('201', [unit.nid for unit in game.units])
            assign_unit = True
        elif game.get_unit(unit_nid):
            logging.error("Unit with NID %s already exists!" % unit_nid)
            return

        klass = values[1]
        if klass not in DB.classes.keys():
            logging.error("Class %s doesn't exist in database " % klass)
            return
        # Level
        try:
            level = int(evaluate.evaluate(values[2], self.unit, self.unit2, self.item, self.position, self.region))
        except:
            logging.error("Could not evaluate {%s}" % values[2])
            return
        team = values[3]
        if len(values) > 4 and values[4]:
            ai_nid = values[4]
        else:
            ai_nid = 'None'
        if len(values) > 5 and values[5]:
            faction = values[5]
        else:
            faction = DB.factions[0].nid
        if len(values) > 6 and values[6]:
            variant = values[6]
        else:
            variant = None
        if len(values) > 7 and values[7]:
            starting_items = values[7].split(',')
        else:
            starting_items = []

        level_unit_prefab = GenericUnit(unit_nid, variant, level, klass, faction, starting_items, team, ai_nid)
        new_unit = UnitObject.from_prefab(level_unit_prefab)
        new_unit.party = game.current_party
        game.full_register(new_unit)
        if assign_unit:
            self.unit = new_unit

    def create_unit(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        unit = self.get_unit(values[0])
        if not unit:
            logging.error("Couldn't find unit %s" % values[0])
            return
        # Get input
        assign_unit = False
        unit_nid = None
        if len(values) > 1 and values[1]:
            unit_nid = values[1]
        if not unit_nid:
            unit_nid = str_utils.get_next_int('201', [unit.nid for unit in game.units])
            assign_unit = True
        elif game.get_unit(unit_nid):
            logging.error("Unit with NID %s already exists!" % unit_nid)
            return

        if len(values) > 2 and values[2]:
            try:
                level = int(evaluate.evaluate(values[2], self.unit, self.unit2, self.item, self.position, self.region))
            except:
                logging.error("Could not evaluate {%s}" % values[2])
                return
        else:
            level = unit.level
        if len(values) > 3 and values[3]:
            position = self.parse_pos(values[3])
        else:
            position = unit.starting_position
        if not position:
            logging.error("No position found!")
            return
        if len(values) > 4 and values[4]:
            entry_type = values[4]
        else:
            entry_type = 'fade'
        if len(values) > 5 and values[5]:
            placement = values[5]
        else:
            placement = 'giveup'

        level_unit_prefab = GenericUnit(
            unit_nid, unit.variant, level, unit.klass, unit.faction, [item.nid for item in unit.items], unit.team, unit.ai)
        new_unit = UnitObject.from_prefab(level_unit_prefab)
        position = self.check_placement(new_unit, position, placement)
        if not position:
            return None
        new_unit.party = game.current_party
        game.full_register(new_unit)
        if assign_unit:
            self.unit = new_unit
        if DB.constants.value('initiative'):
            action.do(action.InsertInitiative(unit))

        self._place_unit(new_unit, position, entry_type)

    def give_item(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        if values[0].lower() == 'convoy':
            unit = None
        else:
            unit = self.get_unit(values[0])
            if not unit:
                logging.error("Couldn't find unit with nid %s" % values[0])
                return
        item_nid = values[1]
        if item_nid in DB.items.keys():
            item = item_funcs.create_item(None, item_nid)
            game.register_item(item)
        else:
            logging.error("Couldn't find item with nid %s" % item_nid)
            return
        if 'no_banner' in flags:
            banner_flag = False
        else:
            banner_flag = True
        if 'droppable' in flags:
            item.droppable = True

        if unit:
            if item_funcs.inventory_full(unit, item):
                if 'no_choice' in flags:
                    action.do(action.PutItemInConvoy(item))
                    if banner_flag:
                        game.alerts.append(banner.SentToConvoy(item))
                        game.state.change('alert')
                        self.state = 'paused'
                else:
                    action.do(action.GiveItem(unit, item))
                    game.cursor.cur_unit = unit
                    game.state.change('item_discard')
                    self.state = 'paused'
                    if banner_flag:
                        game.alerts.append(banner.AcquiredItem(unit, item))
                        game.state.change('alert')
            else:
                action.do(action.GiveItem(unit, item))
                if banner_flag:
                    game.alerts.append(banner.AcquiredItem(unit, item))
                    game.state.change('alert')
                    self.state = 'paused'
        else:
            action.do(action.PutItemInConvoy(item))
            if banner_flag:
                game.alerts.append(banner.SentToConvoy(item))
                game.state.change('alert')
                self.state = 'paused'

    def get_item_in_inventory(self, values):
        unit = self.get_unit(values[0])
        if not unit:
            logging.error("Couldn't find unit with nid %s" % values[0])
            return None, None
        item_nid = values[1]
        if item_nid not in [item.nid for item in unit.items]:
            logging.error("Couldn't find item with nid %s" % values[1])
            return None, None
        item = [item for item in unit.items if item.nid == item_nid][0]
        return unit, item

    def remove_item(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        unit, item = self.get_item_in_inventory(values)
        if not unit or not item:
            return
        banner_flag = 'no_banner' not in flags

        action.do(action.RemoveItem(unit, item))
        if banner_flag:
            item = DB.items.get(item.nid)
            b = banner.TakeItem(unit, item)
            game.alerts.append(b)
            game.state.change('alert')
            self.state = 'paused'

    def change_item_name(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        unit, item = self.get_item_in_inventory(values)
        if not unit or not item:
            return
        name = values[2]

        action.do(action.ChangeItemName(item, name))

    def change_item_desc(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        unit, item = self.get_item_in_inventory(values)
        if not unit or not item:
            return
        desc = values[2]

        action.do(action.ChangeItemDesc(item, desc))

    def add_item_to_multiitem(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        unit, item = self.get_item_in_inventory(values)
        if not unit or not item:
            return
        if not item.multi_item:
            logging.error("Item %s is not a multi-item!" % item.nid)
            return
        subitem_prefab = DB.items.get(values[2])
        if not subitem_prefab:
            logging.error("Couldn't find item with nid %s" % values[2])
            return
        # Create subitem
        subitem = ItemObject.from_prefab(subitem_prefab)
        for component in subitem.components:
            component.item = item
        item_system.init(subitem)
        game.register_item(subitem)
        action.do(action.AddItemToMultiItem(unit, item, subitem))

    def remove_item_from_multiitem(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        unit, item = self.get_item_in_inventory(values)
        if not unit or not item:
            return
        if not item.multi_item:
            logging.error("Item %s is not a multi-item!" % item.nid)
            return
        # Check if item in multiitem
        subitem_nids = [subitem.nid for subitem in item.subitems]
        if values[2] not in subitem_nids:
            logging.error("Couldn't find subitem with nid %s" % values[2])
            return
        subitem = [subitem for subitem in item.subitems if subitem.nid == values[2]][0]
        action.do(action.RemoveItemFromMultiItem(unit, item, subitem))

    def give_money(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        money = int(values[0])
        if len(values) > 1 and values[1]:
            party_nid = values[1]
        else:
            party_nid = game.current_party
        banner_flag = 'no_banner' not in flags

        action.do(action.GainMoney(party_nid, money))
        if banner_flag:
            if money >= 0:
                b = banner.Advanced(['Got ', str(money), ' gold.'], ['text-white', 'text-blue', 'text-white'], 'Item')
            else:
                b = banner.Advanced(['Lost ', str(money), ' gold.'], ['text-white', 'text-blue', 'text-white'], 'ItemBreak')
            game.alerts.append(b)
            game.state.change('alert')
            self.state = 'paused'

    def give_bexp(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        # bexp = int(values[0])
        val = 0
        if len(values) > 1 and values[1]:
            party_nid = values[1]
        else:
            party_nid = game.current_party
        to_eval = values[0]
        try:
            val = evaluate.evaluate(to_eval, self.unit, self.unit2, self.item, self.position, self.region)
            action.do(action.GiveBexp(party_nid, val))
        except:
            logging.error("Could not evaluate {%s}" % to_eval)
            return
        banner_flag = 'no_banner' not in flags

        # action.do(action.GiveBexp(party_nid, bexp))
        if banner_flag:
            if len(values) > 2 and values[2]:
                b = banner.Advanced([values[2], ": ", str(val), " BEXP."], ['text-blue', 'text-white', 'text-blue', "text-white"], 'Item')
            else:
                b = banner.Advanced(['Got ', str(val), ' BEXP.'], ['text-white', 'text-blue', 'text-white'], 'Item')
            game.alerts.append(b)
            game.state.change('alert')
            self.state = 'paused'

    def give_exp(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        unit = self.get_unit(values[0])
        if not unit:
            logging.error("Couldn't find unit with nid %s" % values[0])
            return
        exp = utils.clamp(int(values[1]), 0, 100)
        game.exp_instance.append((unit, exp, None, 'init'))
        game.state.change('exp')
        self.state = 'paused'

    def set_exp(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        unit = self.get_unit(values[0])
        if not unit:
            logging.error("Couldn't find unit with nid %s" % values[0])
            return
        exp = utils.clamp(int(values[1]), 0, 100)
        action.do(action.SetExp(unit, exp))

    def give_wexp(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        unit = self.get_unit(values[0])
        if not unit:
            logging.error("Couldn't find unit with nid %s" % values[0])
            return
        weapon_type = values[1]
        wexp = int(values[2])
        if 'no_banner' in flags:
            action.execute(action.AddWexp(unit, weapon_type, wexp))
        else:
            action.do(action.AddWexp(unit, weapon_type, wexp))

    def give_skill(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        unit = self.get_unit(values[0])
        if not unit:
            logging.error("Couldn't find unit with nid %s" % values[0])
            return
        skill_nid = values[1]
        if skill_nid not in DB.skills.keys():
            logging.error("Couldn't find skill with nid %s" % values[1])
            return
        banner_flag = 'no_banner' not in flags
        action.do(action.AddSkill(unit, skill_nid))
        if banner_flag:
            skill = DB.skills.get(skill_nid)
            b = banner.GiveSkill(unit, skill)
            game.alerts.append(b)
            game.state.change('alert')
            self.state = 'paused'

    def remove_skill(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        unit = self.get_unit(values[0])
        if not unit:
            logging.error("Couldn't find unit with nid %s" % values[0])
            return
        skill_nid = values[1]
        if skill_nid not in [skill.nid for skill in unit.skills]:
            logging.error("Couldn't find skill with nid %s" % values[1])
            return
        banner_flag = 'no_banner' not in flags

        action.do(action.RemoveSkill(unit, skill_nid))
        if banner_flag:
            skill = DB.skills.get(skill_nid)
            b = banner.TakeSkill(unit, skill)
            game.alerts.append(b)
            game.state.change('alert')
            self.state = 'paused'

    def _apply_stat_changes(self, unit, stat_changes, flags):
        klass = DB.classes.get(unit.klass)
        # clamp stat changes
        stat_changes = {k: utils.clamp(v, -unit.stats[k], klass.max_stats.get(k) - unit.stats[k]) for k, v in stat_changes.items()}

        immediate = 'immediate' in flags

        action.do(action.ApplyStatChanges(unit, stat_changes))
        if not immediate:
            game.memory['stat_changes'] = stat_changes
            game.exp_instance.append((unit, 0, None, 'stat_booster'))
            game.state.change('exp')
            self.state = 'paused'

    def change_stats(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        unit = self.get_unit(values[0])
        if not unit:
            logging.error("Couldn't find unit %s" % values[0])
            return

        s_list = values[1].split(',')
        stat_changes = {}
        for idx in range(len(s_list)//2):
            stat_nid = s_list[idx*2]
            stat_value = int(s_list[idx*2 + 1])
            stat_changes[stat_nid] = stat_value

        self._apply_stat_changes(unit, stat_changes, flags)

    def set_stats(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        unit = self.get_unit(values[0])
        if not unit:
            logging.error("Couldn't find unit %s" % values[0])
            return

        s_list = values[1].split(',')
        stat_changes = {}
        for idx in range(len(s_list)//2):
            stat_nid = s_list[idx*2]
            stat_value = int(s_list[idx*2 + 1])
            if stat_nid in unit.stats:
                current = unit.stats[stat_nid]
                stat_changes[stat_nid] = stat_value - current

        self._apply_stat_changes(unit, stat_changes, flags)

    def autolevel_to(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        unit = self.get_unit(values[0])
        if not unit:
            logging.error("Couldn't find unit %s" % values[0])
            return
        try:
            final_level = int(evaluate.evaluate(values[1], self.unit, self.unit2, self.item, self.position, self.region))
        except:
            logging.error("Could not evaluate {%s}" % values[1])
            return
        current_level = unit.level
        diff = max(0, final_level - current_level)
        if diff <= 0:
            return

        action.do(action.AutoLevel(unit, diff))
        if 'hidden' in flags:
            pass
        else:
            action.do(action.SetLevel(unit, final_level))
        if not unit.generic and DB.units.get(unit.nid):
            unit_prefab = DB.units.get(unit.nid)
            personal_skills = unit_funcs.get_personal_skills(unit, unit_prefab)
            for personal_skill in personal_skills:
                action.do(action.AddSkill(unit, personal_skill))
        class_skills = unit_funcs.get_starting_skills(unit)
        for class_skill in class_skills:
            action.do(action.AddSkill(unit, class_skill))

    def set_mode_autolevels(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        try:
            autolevel = int(evaluate.evaluate(values[1], self.unit, self.unit2, self.item, self.position, self.region))
        except:
            logging.error("Could not evaluate {%s}" % values[1])
            return
        if 'hidden' in flags:
            game.current_mode.enemy_autolevels = autolevel
        else:
            game.current_mode.enemy_truelevels = autolevel

    def promote(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        unit = self.get_unit(values[0])
        if not unit:
            logging.error("Couldn't find unit %s" % values[0])
            return
        new_klass = None
        if len(values) > 1 and values[1]:
            new_klass = values[1]
        else:
            klass = DB.classes.get(unit.klass)
            if len(klass.turns_into) == 0:
                logging.error("No available promotions for %s" % klass)
                return
            elif len(klass.turns_into) == 1:
                new_klass = klass.turns_into[0]
            else:
                new_klass = None

        game.memory['current_unit'] = unit
        if new_klass:
            game.memory['next_class'] = new_klass
            game.state.change('promotion')
            game.state.change('transition_out')
            self.state = 'paused'
        else:
            game.state.change('promotion_choice')
            game.state.change('transition_out')
            self.state = 'paused'

    def class_change(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        unit = self.get_unit(values[0])
        if not unit:
            logging.error("Couldn't find unit %s" % values[0])
            return
        new_klass = None
        if len(values) > 1 and values[1]:
            new_klass = values[1]
        elif not unit.generic:
            unit_prefab = DB.units.get(unit.nid)
            if not unit_prefab.alternate_classes:
                logging.error("No available alternate classes for %s" % unit)
                return
            elif len(unit_prefab.alternate_classes) == 1:
                new_klass = unit_prefab.alternate_classes[0]
            else:
                new_klass = None

        if new_klass == unit.klass:
            logging.error("No need to change classes")
            return

        game.memory['current_unit'] = unit
        silent = 'silent' in flags
        if silent and new_klass:
            swap_class = action.ClassChange(unit, new_klass)
            action.do(swap_class)
            _, new_wexp = swap_class.get_data()
            # check for weapon experience gain
            if new_wexp:
                for weapon_nid, value in new_wexp.items():
                    action.do(action.AddWexp(unit, weapon_nid, value))
            action.do(action.UpdateRecords('level_gain', (unit.nid, unit.level, unit.klass)))
        elif new_klass:
            game.memory['next_class'] = new_klass
            game.state.change('class_change')
            game.state.change('transition_out')
            self.state = 'paused'
        else:
            game.state.change('class_change_choice')
            game.state.change('transition_out')
            self.state = 'paused'

    def add_region(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        nid = values[0]
        if nid in game.level.regions.keys():
            logging.error("Region nid %s already present!" % nid)
            return
        position = self.parse_pos(values[1])
        size = self.parse_pos(values[2])
        if not size:
            size = (1, 1)
        region_type = values[3].lower()
        if len(values) > 4 and values[4]:
            sub_region_type = values[4]
        else:
            sub_region_type = None

        new_region = regions.Region(nid)
        new_region.region_type = region_type
        new_region.position = position
        new_region.size = size
        new_region.sub_nid = sub_region_type

        if 'only_once' in flags:
            new_region.only_once = True

        action.do(action.AddRegion(new_region))

    def merge_parties(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        host, guest = values[0], values[1]
        if host not in DB.parties.keys():
            logging.error("Could not locate party %s" % host)
            return
        if guest not in DB.parties.keys():
            logging.error("Could not locate party %s" % guest)
            return
        guest_party = game.get_party(guest)
        # Merge units
        for unit in game.units:
            if unit.party == guest:
                action.do(action.ChangeParty(unit, host))
        # Merge items
        for item in guest_party.convoy:
            action.do(action.RemoveItemFromConvoy(item, guest))
            action.do(action.PutItemInConvoy(item, host))
        # Merge money
        # host.money += guest.money
        action.do(action.GainMoney(host, guest_party.money))
        # guest.money -= guest.money
        action.do(action.GainMoney(guest, -guest_party.money))
        # Merge bexp
        # host.bexp += guest.bexp
        action.do(action.GiveBexp(host, guest_party.bexp))
        # guest.bexp -= guest.bexp
        action.do(action.GiveBexp(guest, -guest_party.bexp))

    def arrange_formation(self):
        """
        # Takes all the units that can be placed on a formation spot that aren't already
        # and places them on an open formation spot
        """
        player_units = game.get_units_in_party()
        stuck_units = [unit for unit in player_units if unit.position and not game.check_for_region(unit.position, 'formation')]
        unstuck_units = [unit for unit in player_units if unit not in stuck_units and not game.check_for_region(unit.position, 'formation')]
        unstuck_units = [unit for unit in unstuck_units if 'Blacklist' not in unit.tags]
        if DB.constants.value('fatigue') and game.game_vars.get('_fatigue') == 1:
            unstuck_units = [unit for unit in unstuck_units if unit.get_fatigue() < unit.get_max_fatigue()]
        num_slots = game.level_vars.get('_prep_slots')
        all_formation_spots = game.get_open_formation_spots()
        if num_slots is None:
            num_slots = len(all_formation_spots)
        assign_these = unstuck_units[:num_slots]
        for idx, unit in enumerate(assign_these):
            position = all_formation_spots[idx]
            action.execute(action.ArriveOnMap(unit, position))
            action.execute(action.Reset(unit))

    def find_unlock(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        unit = self.get_unit(values[0])
        if not unit:
            logging.error("Couldn't find unit with nid %s" % values[0])
            return
        if not self.region:
            logging.error("Can only find_unlock within a region's event script")
            return
        if skill_system.can_unlock(unit, self.region):
            game.memory['unlock_item'] = None
            return  # We're done here

        all_items = []
        for item in item_funcs.get_all_items(unit):
            if item_funcs.available(unit, item) and \
                    item_system.can_unlock(unit, item, self.region):
                all_items.append(item)

        if len(all_items) > 1:
            game.memory['current_unit'] = unit
            game.memory['all_unlock_items'] = all_items
            game.state.change('unlock_select')
            self.state = 'paused'
        elif len(all_items) == 1:
            game.memory['unlock_item'] = all_items[0]
        else:
            logging.debug("Somehow unlocked event without being able to")
            game.memory['unlock_item'] = None

    def spend_unlock(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        unit = self.get_unit(values[0])
        if not unit:
            logging.error("Couldn't find unit with nid %s" % values[0])
            return

        chosen_item = game.memory.get('unlock_item')
        game.memory['unlock_item'] = None
        if not chosen_item:
            return

        actions, playback = [], []
        # In order to proc uses, c_uses etc.
        item_system.start_combat(playback, unit, chosen_item, None, None)
        item_system.on_hit(actions, playback, unit, chosen_item, None, self.position, None, (0, 0), True)
        for act in actions:
            action.do(act)
        item_system.end_combat(playback, unit, chosen_item, None, None)

        if unit.get_hp() <= 0:
            # Force can't die unlocking stuff, because I don't want to deal with that nonsense
            action.do(action.SetHP(unit, 1))

        # Check to see if we broke the item we were using
        if item_system.is_broken(unit, chosen_item):
            alert = item_system.on_broken(unit, chosen_item)
            if alert and unit.team == 'player':
                game.alerts.append(banner.BrokenItem(unit, chosen_item))
                game.state.change('alert')
                self.state = 'paused'

    def trigger_script(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        trigger_script = values[0]
        if len(values) > 1 and values[1]:
            unit = self.get_unit(values[1])
        else:
            unit = self.unit
        if len(values) > 2 and values[2]:
            unit2 = self.get_unit(values[2])
        else:
            unit2 = self.unit2

        valid_events = [event_prefab for event_prefab in DB.events.values() if event_prefab.name == trigger_script and (not event_prefab.level_nid or (game.level and event_prefab.level_nid == game.level.nid))]
        for event_prefab in valid_events:
            game.events.add_event(event_prefab.nid, event_prefab.commands, unit, unit2, position=self.position, region=self.region)
            self.state = 'paused'
            if event_prefab.only_once:
                action.do(action.OnlyOnceEvent(event_prefab.nid))

        if not valid_events:
            logging.error("Couldn't find any valid events matching name %s" % trigger_script)
            return

    def loop_units(self, command):
        unit_list_str = command.values[0]
        try:
            unit_list = evaluate.evaluate(unit_list_str)
        except Exception as e:
            logging.error("%s: Could not evalute {%s}" % (e, unit_list_str))
            return
        if not unit_list:
            logging.warning("No units returned for list: %s" % (unit_list_str))
            return
        if not all((isinstance(unit_nid, str) or isinstance(unit_nid, UnitObject)) for unit_nid in unit_list):
            logging.error("%s: could not evaluate to NID list {%s}" % ('loop_units', unit_list_str))
            return
        for unit_nid in reversed(unit_list):
            if not isinstance(unit_nid, str):
                unit_nid = unit_nid.nid  # Try this!
            macro_command = event_commands.TriggerScript([command.values[1], unit_nid])
            self.commands.insert(self.command_idx + 1, macro_command)

    def change_roaming(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        val = values[0].lower()
        if game.level:
            if val in self.true_vals:
                game.level.roam = True
            else:
                game.level.roam = False

    def change_roaming_unit(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        if game.level:
            unit = self.get_unit(values[0])
            if unit:
                game.level.roam_unit = values[0]
            else:
                game.level.roam_unit = None

    def start_overworld_cinematic(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        if values:
            overworld_nid = values[0]
        else:
            if DB.overworlds.values():
                overworld_nid = DB.overworlds.values()[0].nid
            else:
                logging.error('No overworlds in the DB - why are you calling the overworld command?')
                return
        # save level state
        self.prev_game_boundary = game.boundary
        self.prev_board = game.board
        from app.engine.overworld.overworld_states import OverworldState
        OverworldState.set_up_overworld_game_state(overworld_nid)

    def set_overworld_position(self, entity_nid: NID, location: NID | Tuple[float, float], flags={}):
        if isinstance(location, tuple): # setting to a direct coordinate
            display_pos = location
            overworld = game.overworld_controller
            entity = overworld.entities[entity_nid]
            if entity is None:
                logging.error('{}: Party with NID {} not found.'.format('set_overworld_position', entity_nid))
                return
            entity.display_position = display_pos
        else: # setting position to node
            overworld_node_nid: NID = location
            overworld = game.overworld_controller
            entity = overworld.entities[entity_nid]
            node = overworld.nodes[overworld_node_nid]
            if entity is None or node is None:
                if entity is None:
                    logging.error('{}: Party with NID {} not found.'.format('set_overworld_position', entity_nid))
                if node is None:
                    logging.error('{}: Node with NID {} not found.'.format('set_overworld_position', overworld_node_nid))
                return
            # both node and entity exist
            if overworld_node_nid not in overworld.revealed_node_nids:
                # node isn't enabled yet
                logging.error('{}: Node {} exists, but is not yet enabled in overworld {}.'.format('set_overworld_position', overworld_node_nid, overworld._overworld.nid))
                return
            else:
                # both exist and node is enabled
                # move the entity
                entity.on_node = node.nid
        if not 'no_animate' in flags:
            entity.sprite.set_transition('fade_in')

    def reveal_overworld_node(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        overworld_node_nid: NID = values[0]
        if len(values) > 1:
            force = values[1]
        else:
            force = False
        overworld = game.overworld_controller
        node = overworld.nodes[overworld_node_nid]
        if not node:
            logging.error('{}: Node with NID {} not found'.format('reveal_overworld_node', overworld_node_nid))
            return
        overworld.enable_node(overworld_node_nid)
        if not force and not self.do_skip:
            node.sprite.set_transition('fade_in')
            self.wait_time = engine.get_time() + node.sprite.transition_time
            self.state = 'waiting'

    def reveal_overworld_road(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        node_1_nid: NID = values[0]
        node_2_nid: NID = values[1]
        if len(values) > 2:
            force = values[2]
        else:
            force = False
        overworld = game.overworld_controller
        # both nodes should be enabled
        if node_1_nid not in overworld.revealed_node_nids or node_2_nid not in overworld.revealed_node_nids:
            return
        # both nodes should be neighbors
        if node_2_nid not in overworld.connected_nodes(node_1_nid, force=True):
            return

        road = overworld.get_road(node_1_nid, node_2_nid, True)
        if not road:
            logging.error('{}: Road between nodes {} and {} not found'.format('reveal_overworld_road', node_1_nid, node_2_nid))
            return
        overworld.enable_road(road.nid)
        if not force and not self.do_skip:
            road.sprite.set_transition('fade_in')
            self.wait_time = engine.get_time() + road.sprite.transition_time
            self.state = 'waiting'

    def disable_overworld_entity(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        entity = game.overworld_controller.entities.get(values[0], None)
        if not entity:
            logging.error("%s: No such entity exists with nid %s", "disable_overworld_entity", values[0])
            return
        if not 'no_animate' in flags:
            entity.sprite.set_transition('fade_out')
        entity.on_node = None
        entity.display_position = None

    def overworld_move_unit(self, entity_nid: NID, target_location: Tuple[int, int] | NID,
                            speed_adj: float, path: List[Point], flags={}):
        # default values
        if speed_adj is None: speed_adj = 5

        # function
        entity = game.overworld_controller.entities.get(entity_nid, None)
        if not entity.display_position:
            logging.error("%s: Attempting to move entity %s with no position - is it on the overworld?", 'overworld_move_unit', entity_nid)
            return

        follow = 'no_follow' not in flags
        block = 'no_block' not in flags
        disable_after = 'disable_after' in flags
        mute = 'no_sound' in flags

        if disable_after:
            def disable_func():
                entity.sprite.set_transition('fade_out')
                entity.on_node = None
                entity.display_position = None
        else:
            def disable_func():
                pass

        if not entity:
            logging.error("%s: Couldn't find entity %s", "overworld_move_unit", entity_nid)
            return
        if not entity.display_position:
            logging.error("Unit not on map!")
            return
        if path:
            # i'm disabling linger for arbitrary paths as a default, because i think it makes more sense that way
            movement = OverworldMove(entity, None, game.overworld_controller, event=True, follow=follow, speed_adj=speed_adj, path=path, linger=0, after_move_callback=disable_func, mute=mute)
            if self.do_skip: # we are skipping; resolve this instantly
                entity.display_position = path[-1]
                return
        elif isinstance(target_location, NID):
            target_node: OverworldNodeObject = game.overworld_controller.nodes.get(target_location, None)
            if entity.on_node: # we're pathfinding to a node
                entity_node = game.overworld_controller.nodes[entity.on_node]
                if game.overworld_controller.any_path(entity_node, target_node): # if there is a path from the unit to this node
                    if self.do_skip: # we are skipping; resolve this instantly
                        entity.on_node = target_node.nid
                        return
            movement = OverworldMove(entity, target_node, game.overworld_controller, event=True, follow=follow, speed_adj=speed_adj, after_move_callback=disable_func, mute=mute)
        elif isinstance(target_location, Tuple):
            path = [target_location]
            movement = OverworldMove(entity, None, game.overworld_controller, event=True, follow=follow, speed_adj=speed_adj, path=path, linger=0, after_move_callback=disable_func, mute=mute)
            if self.do_skip: # we are skipping; resolve this instantly
                entity.display_position = path[-1]
                return
        else:
            logging.error("%s: No valid path or target location specified: path: %s | target_location: %s", "overworld_move_unit", str(path), str(target_location))
            return

        if block:
            movement.queue(game.movement)
            self.state = 'paused'
            game.state.change('overworld_movement')
            return
        # else switch internal state
        if not hasattr(self, 'overworld_movement_manager'):
            self.overworld_movement_manager = OverworldMovementManager(game.overworld_controller)
        movement.queue(self.overworld_movement_manager)
        if follow:
            game.camera.do_slow_pan(1000)
            game.camera.set_center(entity.display_position[0], entity.display_position[1])
        if 'overworld_movement' not in self.should_update.keys(): # queue continuous update function if not exists
            def update_movement(should_skip: bool):
                if should_skip:
                    self.overworld_movement_manager.finish_all_movement()
                    return True
                # make sure the camera is centered first
                if not game.camera.at_rest():
                    return False
                self.overworld_movement_manager.update()
                focal_unit_nid = self.overworld_movement_manager.get_following_unit()
                if focal_unit_nid:
                    focal_unit = game.overworld_controller.entities[focal_unit_nid]
                    unit_position = focal_unit.display_position
                    game.cursor.set_pos((round(unit_position[0]), round(unit_position[1])))
                    game.camera.set_center(*unit_position)
                if len(self.overworld_movement_manager) <= 0:
                    return True
                return False
            self.should_update['overworld_movement'] = update_movement

    def toggle_narration(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        toggle_which = values[0].lower()
        if len(values) > 1:
            anim_duration = int(values[1])
        else:
            anim_duration = 1000
        # initialize if the component doesn't exist
        if not self.overlay_ui.has_child('event_narration'):
            narration_component = NarrationDialogue('event_narration', self.overlay_ui, anim_duration)
            self.overlay_ui.add_child(narration_component)
            narration_component.disable()
        else:
            narration_component: NarrationDialogue = self.overlay_ui.get_child('event_narration')

        # animate in or out
        if not self.do_skip:
            if toggle_which == 'open':

                narration_component.enter()
                self.wait_time = engine.get_time() + anim_duration
                self.state = 'waiting'
            else:
                narration_component: NarrationDialogue = self.overlay_ui.get_child('event_narration')
                narration_component.exit()
                self.wait_time = engine.get_time() + anim_duration
                self.state = 'waiting'

    def overworld_speak(self, command):
        if not self.overlay_ui.has_child('event_narration'):
            logging.error("%s: Not currently in overworld narration mode", "overworld_speak")
            return

        narration_component: NarrationDialogue = self.overlay_ui.get_child('event_narration')

        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        narrator = values[0]
        dialogue = values[1]

        # add the hurry up handler if it doesn't already exist
        if 'event_narration_listener' not in self.functions_listening_for_input:
            def handle_input(event):
                narration_component.hurry_up(event)
            self.functions_listening_for_input['event_narration_listener'] = handle_input

        narration_component.push_text(narrator, dialogue)
        if 'no_block' in flags or self.do_skip:
            pass
        else:
            # block state execution while dialogue resolves
            def should_block():
                return not narration_component.finished()
            self.should_remain_blocked.append(should_block)
            self.state = 'blocked'

    def create_overworld_entity(self, command):
        from app.engine.objects.overworld import OverworldEntityObject
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        entity_nid = values[0]
        if 'delete' in flags:
            game.overworld_controller.delete_entity(entity_nid)
            return
        if entity_nid in game.overworld_controller.entities.keys():
            logging.error('%s: Entity with nid %s already exists', 'create_overworld_entity', entity_nid)
            return
        if len(values) > 1 and values[1]:
            unit_nid = values[1]
            if not unit_nid in DB.units.keys():
                logging.error('%s: No such unit with nid %s', 'create_overworld_entity', unit_nid)
            new_entity = OverworldEntityObject.from_unit_prefab(entity_nid, None, unit_nid)
            game.overworld_controller.add_entity(new_entity)

    def clean_up_roaming(self, command):
        # WARNING: Not currently turnwheel combatible
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        for unit in game.units:
            if unit.position and not unit == game.level.roam_unit:
                action.do(action.FadeOut(unit))
        if DB.constants.value('initiative'):
            game.initiative.clear()
            game.initiative.insert_unit(game.level.roam_unit)

    def add_to_initiative(self, command):
        # WARNING: Not currently turnwheel combatible
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        unit = self.get_unit(values[0])
        pos = int(values[1])
        if DB.constants.value('initiative'):
            game.initiative.remove_unit(unit)
            game.initiative.insert_at(unit, game.initiative.current_idx + pos)

    def move_in_initiative(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        unit = self.get_unit(values[0])
        offset = int(values[1])
        action.do(action.MoveInInitiative(unit, offset))

    def pair_up(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        unit = self.get_unit(values[0])
        unit2 = self.get_unit(values[1])
        action.do(action.PairUp(unit, unit2))

    def separate(self, command):
        values, flags = event_commands.parse(command, self._evaluate_evals, self._evaluate_vars)
        unit = self.get_unit(values[0])
        action.do(action.RemovePartner(unit))

    def parse_pos(self, text, is_float=False):
        position = None
        if ',' in text:
            if is_float:
                position = tuple(float(_) for _ in text.split(','))
            else:
                position = tuple(int(_) for _ in text.split(','))
        elif text == '{position}':
            position = self.position
        elif not game.is_displaying_overworld() and self.get_unit(text):
            position = self.get_unit(text).position
        elif game.is_displaying_overworld() and self.get_overworld_location_of_object(text):
            position = self.get_overworld_location_of_object(text).position
        else:
            valid_regions = \
                [tuple(region.position) for region in game.level.regions
                 if text == region.sub_nid and region.position and
                 not game.board.get_unit(region.position)]
            if valid_regions:
                position = static_random.shuffle(valid_regions)[0]
        return position

    def get_unit(self, text) -> UnitObject:
        if text in ('{unit}', '{unit1}'):
            return self.unit
        elif text == '{unit2}':
            return self.unit2
        else:
            return game.get_unit(text)

    def get_overworld_location_of_object(self, text, entity_only=False, node_only=False) -> OverworldNodeObject:
        if game.overworld_controller:
            if not node_only and text in game.overworld_controller.entities:
                entity_at_nid = game.overworld_controller.entities[text]
                if entity_at_nid:
                    return entity_at_nid.node

            if not entity_only and text in game.overworld_controller.nodes:
                node_at_nid = game.overworld_controller.nodes[text]
                if node_at_nid:
                    return node_at_nid
        return None
