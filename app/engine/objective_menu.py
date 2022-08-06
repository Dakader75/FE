import datetime
from app.constants import WINWIDTH

from app.engine.sprites import SPRITES
from app.engine.fonts import FONT
from app.engine.sound import SOUNDTHREAD
from app.engine.state import State
from app.engine import engine, background, base_surf, text_funcs, evaluate
from app.engine.game_state import game

class ObjectiveMenuState(State):
    name = 'objective_menu'
    bg = None
    surfaces = []

    def start(self):
        self.bg = background.create_background('settings_background')
        self.surfaces = self.get_surfaces()

        game.state.change('transition_in')
        return 'repeat'

    def get_surfaces(self) -> list:
        surfaces = []

        name_back_surf = SPRITES.get('chapter_select_green')
        # Text
        big_font = FONT['chapter-green']
        center = (name_back_surf.get_width()//2, name_back_surf.get_height()//2 - big_font.height//2)
        big_font.blit_center(game.level.name, name_back_surf, center)
        surfaces.append((name_back_surf, (24, 2)))

        # Background
        back_surf = base_surf.create_base_surf(WINWIDTH - 8, 24, 'menu_bg_white')
        surfaces.append((back_surf, (4, 34)))

        # Get words
        golden_words_surf = SPRITES.get('golden_words')

        # Get Turn
        turn_surf = engine.subsurface(golden_words_surf, (0, 17, 26, 10))
        surfaces.append((turn_surf, (10, 42)))
        # Get Funds
        funds_surf = engine.subsurface(golden_words_surf, (0, 33, 32, 10))
        surfaces.append((funds_surf, (WINWIDTH//3 - 8, 42)))
        # Get PlayTime
        playtime_surf = engine.subsurface(golden_words_surf, (32, 15, 17, 13))
        surfaces.append((playtime_surf, (2*WINWIDTH//3 + 6, 39)))
        # Get G
        g_surf = engine.subsurface(golden_words_surf, (40, 47, 9, 12))
        surfaces.append((g_surf, (2*WINWIDTH//3 - 8 - 1, 40)))
        # TurnCountSurf
        turn_count_size = FONT['text-blue'].width(str(game.turncount)) + 1, FONT['text-blue'].height
        turn_count_surf = engine.create_surface(turn_count_size, transparent=True)
        FONT['text-blue'].blit(str(game.turncount), turn_count_surf, (0, 0))
        surfaces.append((turn_count_surf, (WINWIDTH//3 - 16 - turn_count_surf.get_width(), 38)))                    
        # MoneySurf
        money = str(game.get_money())
        money_size = FONT['text-blue'].width(money) + 1, FONT['text-blue'].height
        money_surf = engine.create_surface(money_size, transparent=True)
        FONT['text-blue'].blit(money, money_surf, (0, 0))
        surfaces.append((money_surf, (2*WINWIDTH//3 - 12 - money_surf.get_width(), 38)))

        # Get win and loss conditions
        win_con = game.level.objective['win']
        win_lines = evaluate.eval_string(win_con).split(',') 

        loss_con = game.level.objective['loss']
        loss_lines = evaluate.eval_string(loss_con).split(',')

        hold_surf = base_surf.create_base_surf(WINWIDTH - 16, 40 + 16*len(win_lines) + 16 * len(loss_lines))
        shimmer = SPRITES.get('menu_shimmer2')
        hold_surf.blit(shimmer, (hold_surf.get_width() - 1 - shimmer.get_width(), hold_surf.get_height() - shimmer.get_height() - 5))

        # Win cons
        hold_surf.blit(SPRITES.get('lowlight'), (2, 12))

        FONT['text-yellow'].blit(text_funcs.translate('Win Conditions'), hold_surf, (4, 4))

        for idx, win_con in enumerate(win_lines):
            FONT['text-white'].blit(win_con, hold_surf, (8, 20 + 16*idx))

        hold_surf.blit(SPRITES.get('lowlight'), (2, 28 + 16*len(win_lines)))

        FONT['text-yellow'].blit(text_funcs.translate('Loss Conditions'), hold_surf, (4, 20 + 16*len(win_lines)))

        for idx, loss_con in enumerate(loss_lines):
            FONT['text-white'].blit(loss_con, hold_surf, (8, 36 + 16*len(win_lines) + idx*16))

        surfaces.append((hold_surf, (8, 34 + back_surf.get_height() + 2)))

        seed = str(game.game_vars['_random_seed'])
        seed_surf = engine.create_surface((28, 16), transparent=True)
        FONT['text-numbers'].blit_center(seed, seed_surf, (14, 0))
        surfaces.append((seed_surf, (WINWIDTH - 28, 4)))
            
        return surfaces

    def take_input(self, event):
        if event == 'BACK':
            SOUNDTHREAD.play_sfx('Select 4')
            game.state.change('transition_pop')

    def draw(self, surf):
        if self.bg:
            self.bg.draw(surf)

        # Non moving surfaces
        for surface, pos in self.surfaces:
            surf.blit(surface, pos)

        # Playtime
        time = datetime.timedelta(milliseconds=game.playtime)
        seconds = int(time.total_seconds())
        hours = min(seconds//3600, 99)
        minutes = str((seconds%3600)//60)
        if len(minutes) < 2:
            minutes = '0' + minutes
        seconds = str(seconds%60)
        if len(seconds) < 2:
            seconds = '0' + seconds

        formatted_time = ':'.join([str(hours), minutes, seconds])
        FONT['text-blue'].blit_right(formatted_time, surf, (WINWIDTH - 8, 38))

        return surf
