import re
from app.engine.graphics.text.text_renderer import render_text, rendered_text_width

from app.utilities import utils
from app.constants import WINWIDTH, WINHEIGHT
from app.engine.fonts import FONT
from app.engine.sprites import SPRITES
from app.engine.sound import get_sound_thread
from app.engine.base_surf import create_base_surf
from app.engine import text_funcs, engine, image_mods
from app.engine import config as cf

from app.engine.game_state import game

class Dialog():
    solo_flag = False
    cursor = SPRITES.get('waiting_cursor')
    cursor_offset = [0]*20 + [1]*2 + [2]*8 + [1]*2
    transition_speed = 166  # 10 frames
    pause_time = 150  # 9 frames
    attempt_split: bool = True # Whether we attempt to split big chunks across multiple lines

    aesthetic_commands = ('{red}', '{/red}', '{black}', '{/black}', '{white}', '{/white}', '{green}', '{/green}')

    def __init__(self, text, portrait=None, background=None, position=None, width=None,
                 speaker=None, style_nid=None, autosize=False, speed=1, font_color='black',
                 font_type='convo', num_lines=2, draw_cursor=True, message_tail='message_bg_tail'):
        self.plain_text = text
        self.portrait = portrait
        self.speaker = speaker
        self.style_nid = style_nid
        self.font_type = font_type
        self.font_color = font_color
        self.autosize = autosize
        self.speed = speed
        self.num_lines = num_lines
        self.draw_cursor_flag = draw_cursor
        self.font = FONT[self.font_type]

        if '{sub_break}' in self.plain_text:
            self.attempt_split = False

        # States: process, transition, pause, wait, done, new_line
        self.state = 'transition'

        self.no_wait = False
        self.text_commands = self.format_text(text)
        self.text_lines = []

        # Size
        if width:
            self.width = width
            self.width -= self.width%8
            self.text_width = max(8, self.width - 24)
            self.determine_height()
        elif self.portrait or self.autosize:
            self.determine_size()
        else:
            self.text_width, self.text_height = (WINWIDTH - 24, self.num_lines * 16)
            self.width, self.height = self.text_width + 16, self.text_height + 16

        # Position
        if position:
            if position == 'center':
                pos_x = WINWIDTH//2 - self.width//2
                pos_y = WINHEIGHT//2 - self.height//2
            else:
                pos_x = position[0]
                pos_y = position[1]
        elif self.portrait:
            desired_center = self.determine_desired_center(self.portrait)
            pos_x = utils.clamp(desired_center - self.width//2, 8, WINWIDTH - 8 - self.width)
            if pos_x % 8 != 0:
                pos_x += 4
            if pos_x == 0:
                pos_x = 4
            pos_y = WINHEIGHT - self.height - 80
        else:
            pos_x = 4
            pos_y = WINHEIGHT - self.height - 4
        self.position = pos_x, pos_y

        self.background = None
        self.tail = None

        if background and background not in ('None', 'clear'):
            self.background = self.make_background(background)
            if message_tail and message_tail != 'None':
                self.tail = SPRITES.get(message_tail)

        self.name_tag_surf = create_base_surf(64, 16, 'name_tag')

        # For drawing
        self.cursor_offset_index = 0
        self.text_index = 0
        self.total_num_updates = 0
        self.y_offset = 0 # How much to move lines (for when a new line is spawned)

        # For state transitions
        self.transition_progress = 0
        self.last_update = engine.get_time()

        self.hold = False

        # For sound
        self.last_sound_update = 0

    def format_text(self, text):
        # Pipe character replacement
        text = text.replace('|', '{w}{br}')
        if text.endswith('{no_wait}'):
            text = text[:-len('{no_wait}')]
            self.no_wait = True
        elif not text.endswith('{w}'):
            text += '{w}'
        command = None
        processed_text = []
        for character in text:
            if character == '{' and command is None:
                command = '{'
            elif character == '}' and command is not None:
                command += '}'
                processed_text.append(command)
                command = None
            elif command is not None:
                command += character
            else:
                processed_text.append(character)
        processed_text = [';' if char == '{semicolon}' else char for char in processed_text]
        return processed_text

    def determine_desired_center(self, portrait):
        x = self.portrait.position[0] + self.portrait.get_width()//2
        if x < 48:  # FarLeft
            return 8
        elif x < 72:  # Left
            return 80
        elif x < 104:  # MidLeft
            return 104
        elif x > 192:  # FarRight
            return 232
        elif x > 168:  # Right
            return 152
        elif x > 144:  # MidRight
            return 128
        else:
            return 120

    def determine_width(self):
        width = 0
        current_line = ''
        preceded_by_wait: bool = False
        waiting_cursor = False
        for command in self.text_commands:
            if command in ('{br}', '{break}', '{clear}', '{sub_break}'):
                if not preceded_by_wait or not self.attempt_split:
                    # Force it to be only one line
                    split_lines = self.get_lines_from_block(current_line, 1)
                else:
                    split_lines = self.get_lines_from_block(current_line)
                width = max(width, max(rendered_text_width([self.font_type], [s]) for s in split_lines))
                if len(split_lines) == 1:
                    waiting_cursor = True
                current_line = ''
                preceded_by_wait = False
            elif command in ('{w}', '{wait}'):
                preceded_by_wait = True
            elif command.startswith('{'):
                pass
            else:
                current_line += command
        if current_line:
            if self.attempt_split:
                split_lines = self.get_lines_from_block(current_line)
            else:
                split_lines = self.get_lines_from_block(current_line, 1)
            width = max(width, max(rendered_text_width([self.font_type], [s]) for s in split_lines))
            if len(split_lines) == 1:
                waiting_cursor = True
        if waiting_cursor:
            if len(split_lines) == 1:
                width += 16
        return width

    def determine_height(self):
        self.text_height = self.font.height * self.num_lines
        self.text_height = max(self.text_height, 16)
        self.height = self.text_height + 16

    def determine_size(self):
        self.text_width = self.determine_width()
        self.text_width = utils.clamp(self.text_width, 48, WINWIDTH - 32)
        self.width = self.text_width + 24 - self.text_width%8
        if self.width <= WINWIDTH - 16:
            self.width += 8
        self.determine_height()

    def make_background(self, background):
        surf = create_base_surf(self.width, self.height, background)
        return surf

    def get_lines_from_block(self, block, force_lines=None):
        if force_lines:
            num_lines = force_lines
        else:
            num_lines = self.num_lines
            if len(block) <= 24:
                num_lines = 1
        lines = text_funcs.split(self.font_type, block, num_lines, WINWIDTH - 16)
        return lines

    def _next_line(self):
        # Don't do this for the first line
        if len(self.text_lines) > self.num_lines - 1:
            self.state = 'new_line'
            self.y_offset = 16
        else:
            self.state = 'process'
            if self.portrait:
                self.portrait.talk()
        self.text_lines.append([])

    def _add_letter(self, letter):
        self.text_lines[-1].append(letter)

    def _next_char(self, sound=True):  # Add the next character to the text_lines list
        if self.text_index >= len(self.text_commands):
            self.pause()
            return
        command = self.text_commands[self.text_index]
        if command in ('{br}', '{break}', '{sub_break}'):
            self._next_line()
        elif command == '{w}' or command == '{wait}':
            self.pause()
        elif command == '{clear}':
            self.text_lines.clear()
            self._next_line()
        elif command == ' ':  # Check to see if we should move to next line
            current_line = ''.join(self.text_lines[-1])
            # Remove any commands from line
            current_line = re.sub(r'\{[^}]*\}', '', current_line)
            next_word = self._get_next_word(self.text_index)
            if self.font.width(current_line + ' ' + next_word) > self.text_width:
                self._next_line()
            else:
                self._add_letter(' ')
                if sound:
                    self.play_talk_boop()
        elif command in self.aesthetic_commands:
            self._add_letter(command)
        else:
            self._add_letter(command)
            if sound:
                self.play_talk_boop()
        self.text_index += 1

    def _get_next_word(self, text_index):
        word = ''
        for letter in self.text_commands[self.text_index + 1:]:
            if letter == ' ':
                break
            elif len(letter) > 1:  # Command
                if letter in self.aesthetic_commands:
                    continue
                else:
                    break
            else:
                word += letter
        return word

    def is_complete(self):
        """
        Should no longer be drawn
        """
        return self.state == 'done' and not self.hold

    def is_done(self):
        """
        Can move onto processing other commands
        """
        return self.state == 'done'

    def is_done_or_wait(self):
        return self.state in ('done', 'wait')

    def pause(self):
        if self.portrait:
            self.portrait.stop_talking()
        self.state = 'pause'
        self.last_update = engine.get_time()

    def hurry_up(self):
        if self.state == 'process':
            while self.state == 'process':
                self._next_char(sound=False)
        elif self.state == 'wait':
            if self.text_index >= len(self.text_commands):
                self.state = 'done'
            else:
                self.state = 'process'
                if self.portrait:
                    self.portrait.talk()

    def play_talk_boop(self):
        if cf.SETTINGS['talk_boop'] and engine.get_true_time() - self.last_sound_update > 32:
            self.last_sound_update = engine.get_true_time()
            get_sound_thread().play_sfx('Talk_Boop')

    def update(self):
        current_time = engine.get_time()

        if self.state == 'transition':
            perc = (current_time - self.last_update) / self.transition_speed
            self.transition_progress = utils.clamp(perc, 0, 1)
            if self.transition_progress == 1:
                self._next_line()
        elif self.state == 'process':
            if cf.SETTINGS['text_speed'] > 0:
                num_updates = engine.get_delta() / (float(cf.SETTINGS['text_speed']) * self.speed)
                self.total_num_updates += num_updates
                while self.total_num_updates >= 1 and self.state == 'process':
                    self.total_num_updates -= 1
                    self._next_char(sound=self.total_num_updates < 2)
                    if self.state != 'process':
                        self.total_num_updates = 0
            else:
                while self.state == 'process':
                    self._next_char(sound=False)
                self.play_talk_boop()
        elif self.state == 'pause':
            if current_time - self.last_update > self.pause_time:
                if self.no_wait:
                    self.state = 'done'
                else:
                    self.state = 'wait'
        elif self.state == 'new_line':
            # Update y_offset
            self.y_offset = max(0, self.y_offset - 2)
            if self.y_offset == 0:
                self.state = 'process'
                if self.portrait:
                    self.portrait.talk()

        self.cursor_offset_index = (self.cursor_offset_index + 1) % len(self.cursor_offset)

    def chunkify(self, line: list, current_color: str):
        chunks = []
        current_chunk = ['', current_color]
        for char in line:
            if char in self.aesthetic_commands:
                if char == '{red}':
                    current_color = 'red'
                elif char == '{black}':
                    current_color = 'black'
                elif char == '{white}':
                    current_color = 'white'
                elif char == '{green}':
                    current_color = 'green'
                elif char in ('{/red}', '{/black}', '{/white}', '{/green}'):
                    current_color = self.font_color
                # Create new chunk
                chunks.append(current_chunk)
                current_chunk = ['', current_color]
            else:
                current_chunk[0] += char
        chunks.append(current_chunk)
        return chunks, current_color

    def draw_text(self, surf):
        end_x_pos, end_y_pos = 0, 0
        text_surf = engine.create_surface((self.text_width, self.text_height), transparent=True)

        current_color = self.font_color

        # Draw line that's disappearing
        if self.y_offset and len(self.text_lines) > self.num_lines:
            x_pos = 0
            y_pos = -16 + self.y_offset
            line = self.text_lines[-self.num_lines - 1]

            line_chunks, current_color = self.chunkify(line, current_color)
            for chunk in line_chunks:
                text, color = chunk
                width = rendered_text_width([self.font_type], [text])
                render_text(text_surf, [self.font_type], [text], [color], (x_pos, y_pos))
                x_pos += width

        display_lines = self.text_lines[-self.num_lines:]
        for idx, line in enumerate(display_lines):
            x_pos = 0
            y_pos = 16 * idx
            if len(self.text_lines) > self.num_lines:
                y_set = y_pos + self.y_offset
            else:
                y_set = y_pos

            line_chunks, current_color = self.chunkify(line, current_color)
            for chunk in line_chunks:
                text, color = chunk
                width = rendered_text_width([self.font_type], [text])
                render_text(text_surf, [self.font_type], [text], [color], (x_pos, y_set))
                x_pos += width

            end_x_pos = self.position[0] + 8 + x_pos
            end_y_pos = self.position[1] + 8 + y_pos

        surf.blit(text_surf, (self.position[0] + 8, self.position[1] + 8))

        return end_x_pos, end_y_pos

    def draw_tail(self, surf, portrait):
        portrait_pos = portrait.position[0] + portrait.get_width()//2
        mirror = portrait_pos < WINWIDTH//2
        if mirror:
            tail_surf = engine.flip_horiz(self.tail)
        else:
            tail_surf = self.tail
        y_pos = self.position[1] + self.background.get_height() - 2
        x_pos = portrait_pos + 20 if mirror else portrait_pos - 36
        # If we wouldn't actually be on the dialog box
        if x_pos > self.background.get_width() + self.position[0] - 24:
            x_pos = self.position[0] + self.background.get_width() - 24
        elif x_pos < self.position[0] + 8:
            x_pos = self.position[0] + 8

        tail_surf = image_mods.make_translucent(tail_surf, .05)
        surf.blit(tail_surf, (x_pos, y_pos))

    def draw_nametag(self, surf, name):
        x_pos = self.position[0] - 4
        y_pos = self.position[1] - 10
        if x_pos < 0:
            x_pos = self.position[0] + 16
        name_tag_surf = self.name_tag_surf.copy()
        self.font.blit_center(name, name_tag_surf, (name_tag_surf.get_width()//2, name_tag_surf.get_height()//2 - self.font.height//2), self.font_color)
        surf.blit(name_tag_surf, (x_pos, y_pos))
        return surf

    def draw(self, surf):
        if self.background:
            if self.state == 'transition':
                # bg = image_mods.resize(self.background, (1, .5 + self.transition_progress/2.))
                new_width = max(1, self.background.get_width() - 10 + int(10*self.transition_progress))
                new_height = max(1, self.background.get_height() - 10 + int(10*self.transition_progress))
                bg = engine.transform_scale(self.background, (new_width, new_height))
                bg = image_mods.make_translucent(bg, .05 + .7 * (1 - self.transition_progress))
                surf.blit(bg, (self.position[0], self.position[1] + self.height - bg.get_height()))
            else:
                bg = image_mods.make_translucent(self.background, .05)
                surf.blit(bg, self.position)

        if self.state != 'transition':
            # Draw message tail
            if self.portrait and self.background and self.tail:
                self.draw_tail(surf, self.portrait)
            # Draw nametag
            if not self.portrait and self.speaker and self.speaker != 'Narrator':
                self.draw_nametag(surf, self.speaker)
            # Draw text
            end_pos = self.draw_text(surf)

            if self.state == 'wait' and self.draw_cursor_flag:
                cursor_pos = 4 + end_pos[0], \
                    6 + end_pos[1] + self.cursor_offset[self.cursor_offset_index]
                surf.blit(self.cursor, cursor_pos)

        return surf

class LocationCard():
    exist_time = 2000
    transition_speed = 166  # 10 frames

    def __init__(self, text, background='menu_bg_brown'):
        self.plain_text = text
        self.font = FONT['text']

        self.text_lines = self.format_text(text)
        self.determine_size()
        self.position = (10, 1)

        if background:
            self.background = self.make_background(background)
        else:
            self.background = engine.create_surface((self.width, self.height), transparent=True)

        # For transition
        self.transition = 'start'
        self.transition_progress = 0
        self.transition_update = engine.get_time()
        self.start_time = engine.get_time()

    def format_text(self, text):
        return [text]

    def determine_size(self):
        self.width = max(self.font.width(line) for line in self.text_lines) + 16
        self.height = len(self.text_lines) * self.font.height + 8

    def make_background(self, background):
        surf = create_base_surf(self.width, self.height, background)
        return surf

    def update(self):
        current_time = engine.get_time()

        if self.transition:
            perc = (current_time - self.transition_update) / self.transition_speed
            self.transition_progress = utils.clamp(perc, 0, 1)
            if self.transition_progress == 1:
                if self.transition == 'end':
                    return False
                self.transition = False

        if not self.transition and current_time - self.start_time > self.exist_time:
            self.transition_update = current_time
            self.transition = 'end'
            self.transition_progress = 0

        return True

    def draw(self, surf):
        bg = self.background.copy()
        # Draw text
        for idx, line in enumerate(self.text_lines):
            self.font.blit_center(line, bg, (bg.get_width()//2, idx * self.font.height + 4))

        if self.transition == 'start':
            transparency = 1.1 - self.transition_progress
            bg = image_mods.make_translucent(bg, transparency)
        elif self.transition == 'end':
            transparency = .1 + (self.transition_progress * .9)
            bg = image_mods.make_translucent(bg, transparency)
        else:
            bg = image_mods.make_translucent(bg, .1)
        surf.blit(bg, self.position)

        return surf

class Credits():
    speed = 0.02

    def __init__(self, title, text, wait_flag=False, center_flag=True):
        self.title = title
        self.text = text
        self.title_font = FONT['credit_title-white']
        self.title_font_name = 'credit_title-white'
        self.font = FONT['credit-white']
        self.font_name = 'credit-white'

        self.center_flag = center_flag
        self.wait_flag = wait_flag
        self.waiting = False

        self.make_surf()

        self.position = [0, WINHEIGHT]

        self.pause_update = engine.get_time()
        self.has_paused = False
        self.start_update = engine.get_time()

    def make_surf(self):
        index = 0
        self.parsed_text = []
        for line in self.text:
            x_bound = WINWIDTH - 12 if self.center_flag else WINWIDTH - 88
            lines = text_funcs.line_wrap(self.font_name, line, x_bound)
            for li in lines:
                if self.center_flag:
                    x_pos = WINWIDTH//2 - self.font.width(li)//2
                else:
                    x_pos = 88
                y_pos = self.font.height * index + self.title_font.height
                index += 1
                self.parsed_text.append((li, index, (x_pos, y_pos)))

        self.num_lines = index

        size = (WINWIDTH, self.title_font.height + self.font.height * self.num_lines)
        self.surf = engine.create_surface(size, transparent=True)

        title_pos_x = 32
        self.title_font.blit(self.title, self.surf, (title_pos_x, 0))

        for text, index, pos in self.parsed_text:
            self.font.blit(text, self.surf, pos)

    def wait_time(self) -> int:
        time = int((self.num_lines + 2) * self.font.height * 50)
        if self.wait_flag:
            time += int(self.pause_time() * 2.1)
        return time

    def pause_time(self) -> int:
        return int((self.num_lines + 1) * 1000)

    def update(self):
        current_time = engine.get_time()

        if not self.waiting or current_time - self.pause_update > self.pause_time():
            self.waiting = False
            ms_passed = current_time - self.start_update
            if self.has_paused:
                ms_passed -= self.pause_time()
            self.position[1] = WINHEIGHT - (ms_passed * self.speed)
            # Should we pause?
            if self.wait_flag and WINHEIGHT//2 - self.surf.get_height()//2 >= self.position[1]:
                self.waiting = True
                self.wait_flag = False
                self.pause_update = current_time
                self.has_paused = True
        return True

    def draw(self, surf):
        surf.blit(self.surf, self.position)
        return surf

class Ending():
    """
    Contains a dialog
    """
    solo_flag = True
    wait_time = 5000
    background = SPRITES.get('endings_display')

    def __init__(self, portrait, title, text, unit):
        self.portrait = portrait
        self.title = title
        self.plain_text = text
        self.speaker = None  # Unused attribute to match Dialog
        self.unit = unit
        self.font = FONT['text']

        # Build dialog
        self.dialog = Dialog(text, num_lines=6, draw_cursor=False)
        self.dialog.position = (8, 40)
        self.dialog.text_width = WINWIDTH - 32
        self.dialog.width = self.dialog.text_width + 16
        self.dialog.font = FONT['text']
        self.dialog.font_type = 'text'
        self.dialog.font_color = 'white'

        self.make_background()
        self.x_position = WINWIDTH

        self.wait_update = 0

    def make_background(self):
        size = WINWIDTH, WINHEIGHT
        self.bg = engine.create_surface(size, transparent=True)
        self.bg.blit(self.background, (0, 0))
        self.bg.blit(self.portrait, (136, 57))

        title_pos_x = 68 - self.font.width(self.title)//2
        self.font.blit(self.title, self.bg, (title_pos_x, 24))

        # Stats
        if self.unit:
            kills = game.records.get_kills(self.unit.nid)
            damage = game.records.get_damage(self.unit.nid)
            healing = game.records.get_heal(self.unit.nid)

            FONT['text-yellow'].blit(text_funcs.translate('K'), self.bg, (136, 8))
            FONT['text-yellow'].blit(text_funcs.translate('D'), self.bg, (168, 8))
            FONT['text-yellow'].blit(text_funcs.translate('H'), self.bg, (200, 8))
            FONT['text-blue'].blit(str(kills), self.bg, (144, 8))
            dam = str(damage)
            if damage >= 1000:
                dam = dam[:-3] + '.' + dam[-3] + 'k'
            heal = str(healing)
            if healing >= 1000:
                heal = heal[:-3] + '.' + heal[-3] + 'k'
            FONT['text-blue'].blit(dam, self.bg, (176, 8))
            FONT['text-blue'].blit(heal, self.bg, (208, 8))

        return self.bg

    def is_complete(self):
        """
        Should stop being drawn
        """
        return False

    def is_done(self):
        return self.dialog.is_done()

    def is_done_or_wait(self):
        return self.dialog.is_done_or_wait()

    def hurry_up(self):
        self.dialog.hurry_up()

    def update(self):
        current_time = engine.get_time()

        # Move in
        if self.x_position > 0:
            self.x_position -= 8
            self.x_position = max(0, self.x_position)
        else:
            self.dialog.update()

        # Only wait for so long
        if self.wait_update:
            if current_time - self.wait_update > self.wait_time:
                self.dialog.state = 'done'
        elif self.is_done_or_wait():
            self.wait_update = current_time

        return False

    def draw(self, surf):
        bg = self.bg.copy()
        self.dialog.draw(bg)
        surf.blit(bg, (self.x_position, 0))
