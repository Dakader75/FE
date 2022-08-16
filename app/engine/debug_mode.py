from app.constants import WINHEIGHT
from app.engine.sprites import SPRITES
from app.engine.fonts import FONT
from app.engine.sound import get_sound_thread

from app.events import event_commands
from app.events.event import Event
from app.engine.input_manager import get_input_manager

from app.engine.state import MapState
from app.engine.game_state import game
from app.engine import engine, config

class DebugState(MapState):
    num_back = 4
    commands = config.get_debug_commands()
    bg = SPRITES.get('debug_bg').convert_alpha()
    quit_commands = ['q', 'exit', '']

    def begin(self):
        game.cursor.show()
        self.current_command = ''
        self.buffer_count = 0

        self.quit_commands += engine.get_key_name(get_input_manager().key_map['BACK'])

    def take_input(self, event):
        game.cursor.take_input()

        for event in engine.events:
            if event.type == engine.KEYDOWN:
                if event.key == engine.key_map['enter']:
                    self.parse_command(self.current_command)
                    if self.current_command not in self.quit_commands:
                        self.commands.append(self.current_command)
                    self.current_command = ''
                    self.buffer_count = 0
                elif event.key == engine.key_map['backspace']:
                    self.current_command = self.current_command[:-1]
                elif event.key == engine.key_map['pageup'] and self.commands:
                    self.buffer_count += 1
                    if self.buffer_count >= len(self.commands):
                        self.buffer_count = 0
                    self.current_command = self.commands[-self.buffer_count]
                else:
                    self.current_command += event.unicode

    def parse_command(self, command):
        if command in self.quit_commands:
            get_sound_thread().play_sfx('Select 4')
            game.state.back()
            return

        event_command, error_loc = event_commands.parse_text_to_command(command)
        if not event_command:
            return
        game.events._add_event('debug_console', [event_command], unit=game.cursor.get_hover(), position=game.cursor.position)

    def draw(self, surf):
        surf = super().draw(surf)
        surf.blit(self.bg, (0, WINHEIGHT - (5 * 16)))
        for idx, command in enumerate(reversed(self.commands[-self.num_back:])):
            FONT['text'].blit(command, surf, (0, WINHEIGHT - idx * 16 - 32))
        FONT['text'].blit(self.current_command, surf, (0, WINHEIGHT - 16))
        return surf

    def end(self):
        game.cursor.hide()
        config.save_debug_commands(self.commands[-20:])
