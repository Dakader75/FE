import math

from app.data.database import DB

from app.engine.sprites import SPRITES
from app.engine.fonts import FONT
from app.engine import engine, image_mods, icons, help_menu, text_funcs, item_system, item_funcs
from app.engine.game_state import game

class EmptyOption():
    def __init__(self, idx):
        self.idx = idx
        self.help_box = None
        self.color = None
        self.ignore = True
        self._width = 104

    def get(self):
        return None

    def set_text(self):
        pass

    def width(self):
        return self._width

    def height(self):
        return 16

    def draw(self, surf, x, y):
        pass

    def draw_highlight(self, surf, x, y, menu_width):
        highlight_surf = SPRITES.get('menu_highlight')
        width = highlight_surf.get_width()
        for slot in range((menu_width - 10)//width):
            left = x + 5 + slot*width
            top = y + 9
            surf.blit(highlight_surf, (left, top))
        return surf

class BasicOption():
    def __init__(self, idx, text):
        self.idx = idx
        self.text = text
        self.display_text = text_funcs.translate(text)
        self.help_box = None
        self.color = 'text-white'
        self.ignore = False

    def get(self):
        return self.text

    def set_text(self, text):
        self.text = text
        self.display_text = text_funcs.translate(text)

    def width(self):
        return FONT[self.color].width(self.display_text) + 24

    def height(self):
        return 16

    def get_color(self):
        if self.ignore:
            return 'text-grey'
        return self.color

    def draw(self, surf, x, y):
        font = FONT[self.get_color()]
        font.blit(self.display_text, surf, (x + 5, y))

    def draw_highlight(self, surf, x, y, menu_width):
        highlight_surf = SPRITES.get('menu_highlight')
        width = highlight_surf.get_width()
        for slot in range((menu_width - 10)//width):
            left = x + 5 + slot*width
            top = y + 9
            surf.blit(highlight_surf, (left, top))
        self.draw(surf, x, y)
        return surf

class HorizOption(BasicOption):
    def width(self):
        return FONT[self.color].width(self.display_text)

class TitleOption():
    def __init__(self, idx, text, option_bg_name):
        self.idx = idx
        self.text = text
        self.display_text = text_funcs.translate(text)
        self.option_bg_name = option_bg_name

        self.color = 'chapter-grey'
        self.ignore = False

    def get(self):
        return self.text

    def set_text(self, text):
        self.text = text
        self.display_text = text_funcs.translate(text)

    def width(self):
        return SPRITES.get(self.option_bg_name).get_width()

    def height(self):
        return SPRITES.get(self.option_bg_name).get_height()

    def draw_text(self, surf, x, y):
        font = FONT[self.color]

        text = self.display_text
        text_size = font.size(text)
        position = (x - text_size[0]//2, y - text_size[1]//2)

        # Handle outline
        t = math.sin(math.radians((engine.get_time()//10) % 180))
        color_transition = image_mods.blend_colors((192, 248, 248), (56, 48, 40), t)
        outline_surf = engine.create_surface((text_size[0] + 4, text_size[1] + 2), transparent=True)
        font.blit(text, outline_surf, (1, 0))
        font.blit(text, outline_surf, (0, 1))
        font.blit(text, outline_surf, (1, 2))
        font.blit(text, outline_surf, (2, 1))
        outline_surf = image_mods.change_color(outline_surf, color_transition)

        surf.blit(outline_surf, (position[0] - 1, position[1] - 1))
        font.blit(text, surf, position)

    def draw(self, surf, x, y):
        left = x - self.width()//2
        surf.blit(SPRITES.get(self.option_bg_name), (left, y))

        self.draw_text(surf, left + self.width()//2, y + self.height()//2 + 1)

    def draw_highlight(self, surf, x, y):
        left = x - self.width()//2
        surf.blit(SPRITES.get(self.option_bg_name + '_highlight'), (left, y))

        self.draw_text(surf, left + self.width()//2, y + self.height()//2 + 1)

class ChapterSelectOption(TitleOption):
    def __init__(self, idx, text, option_bg_name, bg_color):
        self.idx = idx
        self.text = text
        self.display_text = text_funcs.translate(text)
        self.bg_color = bg_color
        self.option_bg_name = option_bg_name + '_' + bg_color

        self.color = 'chapter-grey'
        self.ignore = False

    def draw_flicker(self, surf, x, y):
        left = x - self.width()//2
        surf.blit(SPRITES.get(self.option_bg_name + '_flicker'), (left, y))

        self.draw_text(surf, left + self.width()//2, y + self.height()//2 + 1)

class ModeOption(TitleOption):
    def __init__(self, idx, text):
        self.idx = idx
        self.text = text
        self.display_text = text_funcs.translate(text)

        self.color = 'chapter-grey'
        self.ignore = False
        self.option_bg_name = 'mode_bg'

    def draw_text(self, surf, x, y):
        if self.ignore:
            color = 'chapter-black'
        else:
            color = 'chapter-grey'

        font = FONT[color]

        text = self.display_text
        text_size = font.size(text)
        position = (x - text_size[0]//2, y - text_size[1]//2)

        # Handle outline
        font.blit(text, surf, position)

class ItemOption(BasicOption):
    def __init__(self, idx, item):
        self.idx = idx
        self.item = item
        self.help_box = None
        self.color = item_system.text_color(None, item)
        self.ignore = False

    def get(self):
        return self.item

    def set_text(self, text):
        pass

    def set_item(self, item):
        self.item = item

    def width(self):
        return 104

    def height(self):
        return 16

    def get_color(self):
        owner = game.get_unit(self.item.owner_nid)
        main_font = 'text-grey'
        uses_font = 'text-grey'
        if self.ignore:
            pass
        elif self.color:
            main_font = self.color
            if owner and not item_funcs.available(owner, self.item):
                pass
            else:
                uses_font = 'text-blue'
        elif self.item.droppable:
            main_font = 'text-green'
            uses_font = 'text-green'
        elif not owner or item_funcs.available(owner, self.item):
            main_font = 'text-white'
            uses_font = 'text-blue'
        return main_font, uses_font

    def get_help_box(self):
        owner = game.get_unit(self.item.owner_nid)
        if item_system.is_weapon(owner, self.item) or item_system.is_spell(owner, self.item):
            return help_menu.ItemHelpDialog(self.item)
        else:
            return help_menu.HelpDialog(self.item.desc)

    def draw(self, surf, x, y):
        icon = icons.get_icon(self.item)
        if icon:
            surf.blit(icon, (x + 2, y))
        main_font, uses_font = self.get_color()
        if FONT[main_font].width(self.item.name) > 60:
            main_font = main_font.replace('text', 'narrow')
        FONT[main_font].blit(self.item.name, surf, (x + 20, y))
        uses_string = '--'
        if self.item.uses:
            uses_string = str(self.item.data['uses'])
        elif self.item.c_uses:
            uses_string = str(self.item.data['c_uses'])
        elif self.item.cooldown:
            uses_string = str(self.item.data['cooldown'])
        left = x + 99
        FONT[uses_font].blit_right(uses_string, surf, (left, y))

class ConvoyItemOption(ItemOption):
    def __init__(self, idx, item, owner):
        super().__init__(idx, item)
        self.owner = owner

    def width(self):
        return 112

    def get_color(self):
        main_font = 'text-grey'
        uses_font = 'text-grey'
        if self.ignore:
            pass
        elif self.color:
            main_font = self.color
            uses_font = 'text-blue'
        elif item_funcs.available(self.owner, self.item):
            main_font = 'text-white'
            uses_font = 'text-blue'
        return main_font, uses_font

class FullItemOption(ItemOption):
    def width(self):
        return 120

    def draw(self, surf, x, y):
        icon = icons.get_icon(self.item)
        if icon:
            surf.blit(icon, (x + 2, y))
        main_font, uses_font = self.get_color()
        width = FONT[main_font].width(self.item.name)
        if width > 60:
            main_font = main_font.replace('text', 'narrow')
        FONT[main_font].blit(self.item.name, surf, (x + 20, y))

        uses_string_a = '--'
        uses_string_b = '--'
        if self.item.data.get('uses') is not None:
            uses_string_a = str(self.item.data['uses'])
            uses_string_b = str(self.item.data['starting_uses'])
        elif self.item.data.get('c_uses') is not None:
            uses_string_a = str(self.item.data['c_uses'])
            uses_string_b = str(self.item.data['starting_c_uses'])
        elif self.item.data.get('cooldown') is not None:
            uses_string_a = str(self.item.data['cooldown'])
            uses_string_b = str(self.item.data['starting_cooldown'])
        FONT[uses_font].blit_right(uses_string_a, surf, (x + 96, y))
        FONT['text-white'].blit("/", surf, (x + 98, y))
        FONT[uses_font].blit_right(uses_string_b, surf, (x + 120, y))

class ValueItemOption(ItemOption):
    def __init__(self, idx, item, disp_value):
        super().__init__(idx, item)
        self.disp_value = disp_value

    def width(self):
        return 152

    def draw(self, surf, x, y):
        icon = icons.get_icon(self.item)
        if icon:
            surf.blit(icon, (x + 2, y))
        main_font, uses_font = self.get_color()
        width = FONT[main_font].width(self.item.name)
        if width > 60:
            main_font = main_font.replace('text', 'narrow')
        FONT[main_font].blit(self.item.name, surf, (x + 20, y))

        uses_string = '--'
        if self.item.data.get('uses') is not None:
            uses_string = str(self.item.data['uses'])
        elif self.item.c_uses is not None:
            uses_string = str(self.item.data['c_uses'])
        elif self.item.cooldown is not None:
            uses_string = str(self.item.data['cooldown'])
        FONT[uses_font].blit_right(uses_string, surf, (x + 100, y))

        value_font = 'text-grey'
        value_string = '--'
        owner = game.get_unit(self.item.owner_nid)
        if self.disp_value == 'buy':
            value = item_funcs.buy_price(owner, self.item)
            if value:
                value_string = str(value)
                if value <= game.get_money():
                    value_font = 'text-blue'
            else:
                value_string = '--'
        elif self.disp_value == 'sell':
            value = item_funcs.sell_price(owner, self.item)
            if value:
                value_string = str(value)
                value_font = 'text-blue'
            else:
                value_string = '--'
        FONT[value_font].blit_right(value_string, surf, (x + self.width() - 10, y))

class UnitOption(BasicOption):
    def __init__(self, idx, unit):
        self.idx = idx
        self.unit = unit
        self.help_box = None
        self.color = None
        self.ignore = False
        self.mode = None

    def get(self):
        return self.unit

    def set_text(self, text):
        pass

    def set_unit(self, unit):
        self.unit = unit

    def set_mode(self, mode):
        self.mode = mode

    def width(self):
        return 64

    def height(self):
        return 16

    def get_color(self):
        font = 'text-white'
        if self.ignore:
            font = 'text-grey'
        elif self.color:
            font = self.color
        elif self.mode == 'position':
            if 'Blacklist' in self.unit.tags:
                font = 'text-red'
            elif DB.constants.value('fatigue') and game.game_vars.get('_fatigue') and \
                    self.unit.get_fatigue() >= self.unit.get_max_fatigue():
                font = 'text-red'
            elif not self.unit.position:
                font = 'text-grey'
            elif self.unit.position and not game.check_for_region(self.unit.position, 'formation'):
                font = 'text-green'
            else:
                font = 'text-white'
        return font

    def get_help_box(self):
        return None

    def draw_map_sprite(self, surf, x, y, highlight=False):
        map_sprite = self.unit.sprite.create_image('passive')
        if self.mode == 'position' and not self.unit.position:
            map_sprite = self.unit.sprite.create_image('gray')
        elif highlight:
            map_sprite = self.unit.sprite.create_image('active')
        surf.blit(map_sprite, (x - 20, y - 24 - 1))

    def draw_text(self, surf, x, y):
        font = self.get_color()
        if FONT[font].width(self.unit.name) > 44:
            font = font.replace('text', 'narrow')
        FONT[font].blit(self.unit.name, surf, (x + 20, y))

    def draw(self, surf, x, y):
        self.draw_map_sprite(surf, x, y)
        self.draw_text(surf, x, y)

    def draw_highlight(self, surf, x, y, menu_width=None):
        # Draw actual highlight surf
        highlight_surf = SPRITES.get('menu_highlight')
        width = highlight_surf.get_width()
        for slot in range((self.width() - 10)//width):
            left = x + 5 + slot*width
            top = y + 9
            surf.blit(highlight_surf, (left, top))

        self.draw_map_sprite(surf, x, y, highlight=True)
        self.draw_text(surf, x, y)

class LoreOption(BasicOption):
    def __init__(self, idx, lore):
        self.idx = idx
        self.lore = lore
        self.text = lore.name
        self.display_text = text_funcs.translate(self.text)
        self.help_box = None
        self.color = 'text-white'
        self.ignore = False

    def get(self):
        return self.lore

    def set_text(self, text):
        pass

    def set_lore(self, lore):
        self.lore = lore
        self.text = lore.name
        self.display_text = text_funcs.translate(self.text)

    def width(self):
        return 84

    def height(self):
        return 16

    def get_color(self):
        if self.ignore:
            return 'text-yellow'
        return self.color

    def draw(self, surf, x, y):
        main_font = self.get_color()
        if self.ignore:
            s = self.lore.category
        else:
            s = self.display_text
        width = FONT[main_font].width(s)
        if width > 78:
            main_font = main_font.replace('text', 'narrow')
        font = FONT[main_font]
        font.blit(s, surf, (x + 6, y))
