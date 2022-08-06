from app.constants import WINWIDTH, WINHEIGHT
from app.data.database import DB

from app.utilities import utils
from app.engine.sprites import SPRITES
from app.engine.fonts import FONT
import app.engine.config as cf
from app.engine import engine, base_surf, text_funcs, icons, item_system, item_funcs
from app.engine.game_state import game

class HelpDialog():
    help_logo = SPRITES.get('help_logo')
    font = FONT['convo-black']

    def __init__(self, desc, num_lines=2, name=False):
        self.name = name
        self.last_time = self.start_time = 0
        self.transition_in = False
        self.transition_out = 0
        self.num_lines = num_lines

        self.build_lines(desc)

        greater_line_len = max([self.font.width(line) for line in self.lines])
        if self.name:
            greater_line_len = max(greater_line_len, self.font.width(self.name))

        self.width = greater_line_len + 24
        if self.name:
            self.num_lines += 1
        self.height = self.font.height * self.num_lines + 16

        self.help_surf = base_surf.create_base_surf(self.width, self.height, 'message_bg_base') 
        self.h_surf = engine.create_surface((self.width, self.height + 3), transparent=True)

    def get_width(self):
        return self.help_surf.get_width()

    def get_height(self):
        return self.help_surf.get_height()

    def build_lines(self, desc):
        if not desc:
            desc = ''
        desc = text_funcs.translate(desc)
        # Hard set num lines if desc is very short
        if '\n' in desc:
            self.lines = desc.splitlines()
        else:
            if len(desc) < 28:
                self.num_lines = 1
            self.lines = text_funcs.split(self.font, desc, self.num_lines, WINWIDTH - 8)

    def set_transition_in(self):
        self.transition_in = True
        self.transition_out = 0
        self.start_time = engine.get_time()

    def handle_transition_in(self, time, h_surf):
        if self.transition_in:
            progress = utils.clamp((time - self.start_time) / 130., 0, 1)
            if progress >= 1:
                self.transition_in = False
            else:
                h_surf = engine.transform_scale(h_surf, (int(progress * h_surf.get_width()), int(progress * h_surf.get_height())))
        return h_surf

    def set_transition_out(self):
        self.transition_out = engine.get_time()

    def handle_transition_out(self, time, h_surf):
        if self.transition_out:
            progress = 1 - (time - self.transition_out) / 100.
            if progress <= 0.1:
                self.transition_out = 0
                progress = 0.1
            h_surf = engine.transform_scale(h_surf, (int(progress * h_surf.get_width()), int(progress * h_surf.get_height())))
        return h_surf

    def final_draw(self, surf, pos, time, help_surf):
        # Draw help logo
        h_surf = engine.copy_surface(self.h_surf)
        h_surf.blit(help_surf, (0, 3))
        h_surf.blit(self.help_logo, (9, 0))

        if pos[0] + help_surf.get_width() >= WINWIDTH:
            pos = (WINWIDTH - help_surf.get_width() - 8, pos[1])
        if pos[1] + help_surf.get_height() >= WINHEIGHT:
            pos = (pos[0], max(0, pos[1] - help_surf.get_height() - 16))

        if self.transition_in:
            h_surf = self.handle_transition_in(time, h_surf)
        elif self.transition_out:
            h_surf = self.handle_transition_out(time, h_surf)

        surf.blit(h_surf, pos)
        return surf

    def draw(self, surf, pos, right=False):
        time = engine.get_time()
        if time > self.last_time + 1000:  # If it's been at least a second since last update
            self.start_time = time - 16
            self.transition_in = True
            self.transition_out = 0
        self.last_time = time

        help_surf = engine.copy_surface(self.help_surf)
        if self.name:
            self.font.blit(self.name, help_surf, (8, 8))

        if cf.SETTINGS['text_speed'] > 0:
            num_characters = int(2 * (time - self.start_time) / float(cf.SETTINGS['text_speed']))
        else:
            num_characters = 1000
        for idx, line in enumerate(self.lines):
            if num_characters > 0:
                self.font.blit(line[:num_characters], help_surf, (8, self.font.height * idx + 8 + (16 if self.name else 0)))
                num_characters -= len(line)

        if right:
            surf = self.final_draw(surf, (pos[0] - help_surf.get_width(), pos[1]), time, help_surf)
        else:
            surf = self.final_draw(surf, pos, time, help_surf)

        return surf

class StatDialog(HelpDialog):
    font_green = FONT['text-green']
    font_red = FONT['text-red']

    def __init__(self, desc, bonuses):
        self.last_time = self.start_time = 0
        self.transition_in = False
        self.transition_out = 0

        self.desc = text_funcs.translate(desc)
        self.bonuses = bonuses
        
        self.lines = text_funcs.line_wrap(self.font, self.desc, 148)
        self.size_y = self.font.height * (len(self.lines) + len(self.bonuses)) + 16

        self.help_surf = base_surf.create_base_surf(160, self.size_y, 'message_bg_base')
        self.h_surf = engine.create_surface((160, self.size_y + 3), transparent=True)

    def draw(self, surf, pos, right=False):
        time = engine.get_time()
        if time > self.last_time + 1000:  # If it's been at least a second since last update
            self.start_time = time - 16
            self.transition_in = True
            self.transition_out = 0
        self.last_time = time

        help_surf = engine.copy_surface(self.help_surf)
        if cf.SETTINGS['text_speed'] > 0:
            num_characters = int(2 * (time - self.start_time) / float(cf.SETTINGS['text_speed']))
        else:
            num_characters = 1000
        
        for idx, line in enumerate(self.lines):
            if num_characters > 0:
                self.font.blit(line[:num_characters], help_surf, (8, self.font.height * idx + 6))
                num_characters -= len(line)

        y_height = len(self.lines) * 16
        bonuses = sorted(self.bonuses.items(), key=lambda x: x[0] != 'Base Value')
        for idx, (bonus, val) in enumerate(bonuses):
            if num_characters > 0:
                top = self.font.height * idx + 6 + y_height
                if idx == 0:
                    self.font.blit(str(val), help_surf, (8, top))
                elif val > 0:
                    self.font_green.blit("+" + str(val), help_surf, (8, top))
                elif val < 0:
                    self.font_red.blit(str(val), help_surf, (8, top))
                else:
                    self.font.blit(str(val), help_surf, (8, top))
                self.font.blit(bonus[:num_characters], help_surf, (32, top))
                num_characters -= len(bonus)

        if right:
            surf = self.final_draw(surf, (pos[0] - help_surf.get_width(), pos[1]), time, help_surf)
        else:
            surf = self.final_draw(surf, pos, time, help_surf)
        return surf


class ItemHelpDialog(HelpDialog):
    font_blue = FONT['text-blue']
    font_yellow = FONT['text-yellow']

    def __init__(self, item):
        self.last_time = self.start_time = 0
        self.transition_in = False
        self.transition_out = 0

        self.item = item
        self.unit = game.get_unit(item.owner_nid) if item.owner_nid else None

        weapon_rank = item_system.weapon_rank(self.unit, self.item)
        if not weapon_rank:
            if item.prf_unit or item.prf_class or item.prf_tag:
                weapon_rank = 'Prf'
            else:
                weapon_rank = '--'

        might = item_system.damage(self.unit, self.item)
        hit = item_system.hit(self.unit, self.item)
        if DB.constants.value('crit'):
            crit = item_system.crit(self.unit, self.item)
        else:
            crit = None
        weight = self.item.weight.value if self.item.weight else None
        # Get range
        rng = item_funcs.get_range_string(self.unit, self.item)

        self.vals = [weapon_rank, rng, weight, might, hit, crit]

        if self.item.desc:
            self.lines = text_funcs.line_wrap(self.font, self.item.desc, 148)
        else:
            self.lines = []

        self.num_present = len([v for v in self.vals if v is not None])

        if self.num_present > 3:
            size_y = 48 + self.font.height * len(self.lines)
        else:
            size_y = 32 + self.font.height * len(self.lines)
        self.help_surf = base_surf.create_base_surf(160, size_y, 'message_bg_base')
        self.h_surf = engine.create_surface((160, size_y + 3), transparent=True)

    def draw(self, surf, pos, right=False):
        time = engine.get_time()
        if time > self.last_time + 1000:  # If it's been at least a second since last update
            self.start_time = time - 16
            self.transition_in = True
            self.transition_out = 0
        self.last_time = time

        help_surf = engine.copy_surface(self.help_surf)
        weapon_type = item_system.weapon_type(self.unit, self.item)
        if weapon_type:
            icons.draw_weapon(help_surf, weapon_type, (8, 6))
        self.font_blue.blit_right(str(self.vals[0]), help_surf, (50, 6))

        name_positions = [(56, 6), (106, 6), (8, 22), (56, 22), (106, 22)]
        name_positions.reverse()
        val_positions = [(100, 6), (144, 6), (50, 22), (100, 22), (144, 22)]
        val_positions.reverse()
        names = ['Rng', 'Wt', 'Mt', 'Hit', 'Crit']
        for v, n in zip(self.vals[1:], names):
            if v is not None:
                name_pos = name_positions.pop()
                self.font_yellow.blit(n, help_surf, name_pos)
                val_pos = val_positions.pop()
                self.font_blue.blit_right(str(v), help_surf, val_pos)

        if cf.SETTINGS['text_speed'] > 0:
            num_characters = int(2 * (time - self.start_time) / float(cf.SETTINGS['text_speed']))
        else:
            num_characters = 1000
        
        y_height = 32 if self.num_present > 3 else 16 
        for idx, line in enumerate(self.lines):
            if num_characters > 0:
                self.font.blit(line[:num_characters], help_surf, (8, self.font.height * idx + 6 + y_height))
                num_characters -= len(line)

        if right:
            surf = self.final_draw(surf, (pos[0] - help_surf.get_width(), pos[1]), time, help_surf)
        else:
            surf = self.final_draw(surf, pos, time, help_surf)
        return surf
