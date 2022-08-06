from app.constants import WINWIDTH, WINHEIGHT
from app.engine.sound import SOUNDTHREAD
from app.engine.fonts import FONT
from app.engine.state import MapState

from app.engine import menus, action, base_surf
from app.engine.game_state import game

class PlayerChoiceState(MapState):
    name = 'player_choice'
    transparent = True

    def start(self):
        self.nid, self.header, options_list, self.orientation = \
            game.memory['player_choice']
        self.menu = menus.Choice(None, options_list, 'center', None)
        self.bg_surf, self.topleft = self.create_bg_surf()
        self.menu.topleft = (self.topleft[0], self.topleft[1] + FONT['text-white'].height)
        if self.orientation == 'horizontal':
            self.menu.set_horizontal(True)
            width = sum(option.width() + 8 for option in self.menu.options)
            self.menu.topleft = (self.topleft[0] + self.bg_surf.get_width()//2 - width//2 - 4,
                                 self.topleft[1] + FONT['text-white'].height)

    def create_bg_surf(self):
        width_of_header = FONT['text-white'].width(self.header) + 16
        menu_width = self.menu.get_menu_width()
        width = max(width_of_header, menu_width)
        menu_height = self.menu.get_menu_height() if self.orientation == 'vertical' else FONT['text-white'].height + 8
        height = menu_height + FONT['text-white'].height
        bg_surf = base_surf.create_base_surf(width, height, 'menu_bg_base')
        topleft = (WINWIDTH//2 - width//2, WINHEIGHT//2 - height//2)
        return bg_surf, topleft

    def take_input(self, event):
        self.menu.handle_mouse()
        if (event == 'RIGHT' and self.orientation == 'horizontal') or \
                (event == 'DOWN' and self.orientation == 'vertical'):
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_down()
        elif (event == 'LEFT' and self.orientation == 'horizontal') or \
                (event == 'UP' and self.orientation == 'vertical'):
            SOUNDTHREAD.play_sfx('Select 6')
            self.menu.move_up()

        elif event == 'BACK':
            SOUNDTHREAD.play_sfx('Error')

        elif event == 'SELECT':
            SOUNDTHREAD.play_sfx('Select 1')
            selection = self.menu.get_current()
            action.do(action.SetGameVar(self.nid, selection))
            action.do(action.SetGameVar('_last_choice', selection))
            game.state.back()

    def update(self):
        self.menu.update()

    def draw(self, surf):
        surf.blit(self.bg_surf, self.topleft)
        FONT['text-white'].blit(self.header, surf, (self.topleft[0] + 4, self.topleft[1] + 4))

        # Place Menu on background
        self.menu.draw(surf)
        return surf
