from app.constants import WINWIDTH, WINHEIGHT
from app.engine.sprites import SPRITES
from app.engine.fonts import FONT
from app.engine import engine, base_surf, image_mods, icons, text_funcs, item_system
from app.data import skills, items

class Banner():
    update_flag = False
    time_to_pause = 300
    time_to_wait = 2500
    time_to_start = None
    remove_flag = False
    surf = None

    def __init__(self):
        self.text = []
        self.item = None
        self.font = []
        self.sound = None

    def figure_out_size(self):
        self.length = FONT['text-white'].width(''.join(self.text))
        self.length += 16
        self.length -= self.length%8
        self.length += (16 if self.item else 0)
        self.font_height = 16
        self.size = self.length, 24

    def update(self):
        if not self.update_flag:
            self.update_flag = True
            self.time_to_start = engine.get_time()
            # play sound
            if self.sound:
                from app.engine.sound import SOUNDTHREAD
                SOUNDTHREAD.play_sfx(self.sound)
        if engine.get_time() - self.time_to_start > self.time_to_wait:
            self.remove_flag = True

    def draw_icon(self, surf):
        if self.item:
            icons.draw_item(surf, self.item, (self.size[0] - 20, 8), cooldown=False)

    def draw(self, surf):
        if not self.surf:
            w, h = self.size
            bg_surf = base_surf.create_base_surf(w, h, 'menu_bg_base')
            self.surf = engine.create_surface((w + 2, h + 4), transparent=True)
            self.surf.blit(bg_surf, (2, 4))
            self.surf.blit(SPRITES.get('menu_gem_small'), (0, 0))
            self.surf = image_mods.make_translucent(self.surf, .1)

        bg_surf = self.surf.copy()
        
        left = 6
        
        for idx, word in enumerate(self.text):
            word_width = FONT[self.font[idx]].width(word)
            FONT[self.font[idx]].blit(word, bg_surf, (left, self.size[1]//2 - self.font_height//2 + 3))
            left += word_width

        self.draw_icon(bg_surf)
        
        engine.blit_center(surf, bg_surf)
        return surf

class AcquiredItem(Banner):
    def __init__(self, unit, item):
        super().__init__()
        self.unit = unit
        self.item = item
        article = 'an' if self.item.name.lower()[0] in ('a', 'e', 'i', 'o', 'u') else 'a'
        item_color = item_system.text_color(None, item) if item_system.text_color(None, item) else 'text-blue'
        if "'" in self.item.name:
            # No article for things like Prim's Charm, Ophie's Blade, etc.
            self.text = [unit.name, ' got ', item.name, '.']
            self.font = ['text-blue', 'text-white', item_color, 'text-white']
        else:
            self.text = [unit.name, ' got ', article, ' ', item.name, '.']
            self.font = ['text-blue', 'text-white', 'text-white', 'text-white', item_color, 'text-white']
        self.figure_out_size()
        self.sound = 'Item'

class StoleItem(Banner):
    def __init__(self, unit, item):
        super().__init__()
        self.unit = unit
        self.item = item
        item_color = item_system.text_color(None, item) if item_system.text_color(None, item) else 'text-blue'
        article = 'an' if self.item.name.lower()[0] in ('a', 'e', 'i', 'o', 'u') else 'a'
        if "'" in self.item.name:
            # No article for things like Prim's Charm, Ophie's Blade, etc.
            self.text = [unit.name, ' stole ', item.name, '.']
            self.font = ['text-blue', 'text-white', item_color, 'text-white']
        else:
            self.text = [unit.name, ' stole ', article, ' ', item.name, '.']
            self.font = ['text-blue', 'text-white', 'text-white', 'text-white', item_color, 'text-white']
        self.figure_out_size()
        if self.unit.team in ('player', 'other'):
            self.sound = 'Item'
        else:
            self.sound = 'ItemBreak'

class SentToConvoy(Banner):
    def __init__(self, item):
        super().__init__()
        self.item = item
        item_color = item_system.text_color(None, item) if item_system.text_color(None, item) else 'text-blue'
        self.text = [item.name, ' sent to convoy.']
        self.font = [item_color, 'text-white']
        self.figure_out_size()
        self.sound = 'Item'

class BrokenItem(Banner):
    def __init__(self, unit, item):
        super().__init__()
        self.unit = unit
        self.item = item
        item_color = item_system.text_color(None, item) if item_system.text_color(None, item) else 'text-blue'
        self.text = [unit.name, ' broke ', item.name, '.']
        self.font = ['text-blue', 'text-white', item_color, 'text-blue']
        self.figure_out_size()
        self.sound = 'ItemBreak'

class TakeItem(BrokenItem):
    def __init__(self, unit, item):
        super().__init__(unit, item)
        self.text = [unit.name, ' lost ', item.name, '.']
        self.figure_out_size()

class GainWexp(Banner):
    def __init__(self, unit, weapon_rank, weapon_type):
        super().__init__()
        self.unit = unit
        self.weapon_type = self.item = weapon_type
        self.weapon_rank = weapon_rank
        self.text = [unit.name, ' reached rank ', self.weapon_rank]
        self.font = ['text-blue', 'text-white', 'text-blue']
        self.figure_out_size()
        self.sound = 'Item'

    def draw_icon(self, surf):
        if self.weapon_type:
            icons.draw_weapon(surf, self.item, (self.size[0] - 20, 7))

class GiveSkill(Banner):
    def __init__(self, unit, skill):
        super().__init__()
        self.unit = unit
        self.item = skill
        self.text = [unit.name, ' got ', skill.name]
        self.font = ['text-blue', 'text-white', 'text-blue']
        self.figure_out_size()
        self.sound = 'Item'

    def draw_icon(self, surf):
        if self.item:
            icons.draw_skill(surf, self.item, (self.size[0] - 20, 7), simple=True)

class TakeSkill(GiveSkill):
    def __init__(self, unit, skill):
        super().__init__(unit, skill)
        self.text = [unit.name, ' lost ', skill.name]
        self.figure_out_size()

class Custom(Banner):
    def __init__(self, text, sound=None):
        self.text = [text]
        self.font = ['text-white']
        self.item = None
        self.figure_out_size()
        self.sound = sound

class CustomIcon(Banner):
    def __init__(self, text, icon, sound=None):
        self.text = [text]
        self.font = ['text-white']
        self.item = icon
        self.figure_out_size()
        self.sound = sound
    
    def figure_out_size(self):
        self.length = FONT['text-white'].width(''.join(self.text))
        self.length += 16
        self.length -= self.length%8
        self.length += (10 if self.item else 0)
        self.font_height = 16
        self.size = self.length, 24
    
    def draw_icon(self, surf):
        if self.item:
            if isinstance(self.item, skills.SkillPrefab):
                icons.draw_skill(surf, self.item, (2, 7), simple=True)
            elif isinstance(self.item, items.ItemPrefab):
                icons.draw_item(surf, self.item, (2,7), cooldown=False)
    
    def draw(self, surf):
        if not self.surf:
            w, h = self.size
            bg_surf = base_surf.create_base_surf(w, h, 'menu_bg_base')
            self.surf = engine.create_surface((w + 2, h + 4), transparent=True)
            self.surf.blit(bg_surf, (2, 4))
            self.surf.blit(SPRITES.get('menu_gem_small'), (0, 0))
            self.surf = image_mods.make_translucent(self.surf, .1)

        bg_surf = self.surf.copy()
        
        left = 20
        
        for idx, word in enumerate(self.text):
            word_width = FONT[self.font[idx]].width(word)
            FONT[self.font[idx]].blit(word, bg_surf, (left, self.size[1]//2 - self.font_height//2 + 3))
            left += word_width

        self.draw_icon(bg_surf)
        
        engine.blit_center(surf, bg_surf)
        return surf

class Advanced(Banner):
    def __init__(self, text: list, font: list, sound=None):
        self.text = text
        self.font = font
        self.item = None
        self.figure_out_size()
        self.sound = sound

class Pennant():
    """
    Lower banner that scrolls across bottom of screen
    """

    font = FONT['convo-white']
    bg_surf = SPRITES.get('pennant_bg')

    def __init__(self, text):
        self.change_text(text)

        self.sprite_offset = 32

        self.width = WINWIDTH
        self.height = 16

        self.last_update = engine.get_time()

    def change_text(self, text):
        self.text = text_funcs.translate(text)
        self.text_width = self.font.width(self.text)
        self.text_counter = 0

    def draw(self, surf, draw_on_top=False):
        self.sprite_offset -= 4
        self.sprite_offset = max(0, self.sprite_offset)

        counter = int(-self.text_counter)

        # If cursor is all the way on the bottom of the map
        if draw_on_top:
            surf.blit(engine.flip_vert(self.bg_surf), (0, -self.sprite_offset))
            while counter < self.width:
                self.font.blit(self.text, surf, (counter, -self.sprite_offset))
                counter += self.text_width + 24
        else:
            surf.blit(self.bg_surf, (0, WINHEIGHT - self.height + self.sprite_offset))
            while counter < self.width:
                self.font.blit(self.text, surf, (counter, WINHEIGHT - self.height + self.sprite_offset))
                counter += self.text_width + 24

        self.text_counter += (engine.get_time() - self.last_update)/24
        if self.text_counter >= self.text_width + 24:
            self.text_counter = 0
        self.last_update = engine.get_time()
