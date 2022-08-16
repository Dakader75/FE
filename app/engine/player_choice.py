import logging

from app.data.database import DB
from app.engine import action
from app.engine.game_menus.menu_components.generic_menu.choice_table_wrapper import ChoiceMenuUI
from app.engine.game_state import game
from app.engine.sound import get_sound_thread
from app.engine.state import MapState
from app.utilities.enums import Orientation

class PlayerChoiceState(MapState):
    name = 'player_choice'
    transparent = True

    def start(self):
        self.nid, self.header, options_list, self.row_width, self.orientation, \
            self.data_type, self.should_persist, self.alignment, self.bg, self.event_on_choose, \
            self.size, self.no_cursor, self.arrows, self.scroll_bar, self.text_align, self.backable, self.event_context = \
            game.memory['player_choice']
        self.tsize = [0, 0]
        if self.size:
            rows, ncols = self.size
        else:
            if callable(options_list):
                data = options_list()
            else:
                data = options_list
            if self.orientation == 'horizontal':
                ncols = len(data)
                self.size = (1, ncols)
                rows, ncols = self.size
            else:
                nrows = len(data)
                self.size = (nrows, 1)
                rows, ncols = self.size
        self.menu = ChoiceMenuUI(options_list, data_type=self.data_type, rows=rows, row_width=self.row_width,
                                 title=self.header, cols=ncols, alignment=self.alignment, bg=self.bg,
                                 orientation=Orientation(self.orientation), text_align=self.text_align)
        self.menu.set_scrollbar(self.scroll_bar)
        self.menu.set_arrows(self.arrows)

        self.made_choice = False

    def choose(self, selection):
        action.do(action.SetGameVar(self.nid, selection))
        action.do(action.SetGameVar('_last_choice', selection))
        self.made_choice = True

    def unchoose(self):
        self.made_choice = False

    def take_input(self, event):
        if (event == 'RIGHT' and (self.orientation == 'horizontal' or self.size[0] > 1)):
            get_sound_thread().play_sfx('Select 6')
            self.menu.move_right()
        elif (event == 'DOWN' and (self.orientation == 'vertical' or self.size[1] > 1)):
            get_sound_thread().play_sfx('Select 6')
            self.menu.move_down()
        elif (event == 'LEFT' and (self.orientation == 'horizontal' or self.size[0] > 1)):
            get_sound_thread().play_sfx('Select 6')
            self.menu.move_left()
        elif(event == 'UP' and (self.orientation == 'vertical' or self.size[1] > 1)):
            get_sound_thread().play_sfx('Select 6')
            self.menu.move_up()
        elif event == 'BACK':
            if self.should_persist or self.backable:
                if self.backable:
                    action.do(action.SetGameVar(self.nid, "BACK"))
                # this is the only way to exit a persistent state
                game.state.back()
            else:
                get_sound_thread().play_sfx('Error')
        elif event == 'SELECT':
            get_sound_thread().play_sfx('Select 1')
            selection = self.menu.get_selected()
            self.choose(selection)
            if self.event_on_choose:
                valid_events = DB.events.get_by_nid_or_name(self.event_on_choose, game.level.nid)
                for event_prefab in valid_events:
                    game.events.trigger_specific_event(event_prefab.nid, **self.event_context)
                    game.memory[self.nid + '_unchoice'] = self.unchoose
                if not valid_events:
                    logging.error("Couldn't find any valid events matching name %s" % self.event_on_choose)
            return 'repeat'
        selection = self.menu.get_selected()
        game.game_vars[self.nid + '_choice_hover'] = selection

    def update(self):
        if self.made_choice and not self.should_persist:
            game.state.back()
            return 'repeat'

    def draw(self, surf):
        self.menu.update()
        focus = 0
        if not self.no_cursor:
            focus = 1 if game.state.current_state() == self else 2
        self.menu.draw(surf, focus)
        return surf
