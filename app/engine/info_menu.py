from dataclasses import dataclass

from app.constants import WINWIDTH, WINHEIGHT
from app.utilities import utils

from app.resources.resources import RESOURCES
from app.data.database import DB

from app.engine.sprites import SPRITES
from app.engine.fonts import FONT
from app.engine.sound import SOUNDTHREAD
from app.engine.input_manager import INPUT
from app.engine.state import State
from app.engine import engine, background, menu_options, help_menu, gui, \
    icons, image_mods, item_funcs, equations, \
    combat_calcs, menus, skill_system, text_funcs
from app.engine.game_state import game
from app.engine.fluid_scroll import FluidScroll

def handle_info():
    if game.cursor.get_hover():
        SOUNDTHREAD.play_sfx('Select 1')
        game.memory['next_state'] = 'info_menu'
        game.memory['current_unit'] = game.cursor.get_hover()
        game.state.change('transition_to')
    else:
        SOUNDTHREAD.play_sfx('Select 3')
        game.boundary.toggle_all_enemy_attacks()

def handle_aux():
    avail_units = [
        u for u in game.units
        if u.team == 'player' and
        u.position and
        not u.finished and
        skill_system.can_select(u) and
        'Tile' not in u.tags]

    if avail_units:
        cur_unit = game.cursor.get_hover()
        if not cur_unit or cur_unit not in avail_units:
            cur_unit = game.memory.get('aux_unit')
        if not cur_unit or cur_unit not in avail_units:
            cur_unit = avail_units[0]

        if cur_unit in avail_units:
            idx = avail_units.index(cur_unit)
            idx = (idx + 1) % len(avail_units)
            new_pos = avail_units[idx].position
            game.memory['aux_unit'] = cur_unit
            SOUNDTHREAD.play_sfx('Select 4')
            game.cursor.set_pos(new_pos)

@dataclass
class BoundingBox():
    idx: int = 0
    aabb: tuple = None
    help_box: help_menu.HelpDialog = None
    state: str = None
    first: bool = False

info_states = ('personal_data', 'equipment', 'support_skills', 'notes')

class InfoGraph():
    def __init__(self):
        self.registry = {state: [] for state in info_states}
        self.registry.update({'growths': []})
        self.current_bb = None
        self.last_bb = None
        self.current_state = None
        self.cursor = menus.Cursor()
        self.first_bb = None

    def clear(self):
        self.registry = {state: [] for state in info_states}
        self.registry.update({'growths': []})
        self.current_bb = None
        self.last_bb = None
        self.first_bb = None

    def set_current_state(self, state):
        self.current_state = state

    def register(self, aabb, help_box, state, first=False):
        if isinstance(help_box, str):
            help_box = help_menu.HelpDialog(help_box)

        if state == 'all':
            for s in self.registry:
                idx = len(self.registry[s])
                self.registry[s].append(BoundingBox(idx, aabb, help_box, s, first))
        else:
            idx = len(self.registry[state])
            self.registry[state].append(BoundingBox(idx, aabb, help_box, state, first))

    def set_transition_in(self):
        if self.last_bb and self.last_bb.state == self.current_state:
            self.current_bb = self.last_bb
            self.current_bb.help_box.set_transition_in()
        elif self.registry:
            for bb in self.registry[self.current_state]:
                if bb.first:
                    self.current_bb = bb
                    self.current_bb.help_box.set_transition_in()
                    break
            else:
                # For now, just use first help dialog
                self.current_bb = self.registry[self.current_state][0]
                self.current_bb.help_box.set_transition_in()

    def set_transition_out(self):
        if self.current_bb:
            self.current_bb.help_box.set_transition_out()
        self.last_bb = self.current_bb
        self.current_bb = None

    def _move(self, boxes, horiz=False):
        if not boxes:
            return
        if self.current_bb:
            center_point = (self.current_bb.aabb[0] + self.current_bb.aabb[2]/2,
                            self.current_bb.aabb[1] + self.current_bb.aabb[3]/2)
            closest_box = None
            max_distance = 1e6
            # First try to find a close box by moving in the right direction
            for bb in boxes:
                if horiz:
                    a, b = self.current_bb.aabb[1], self.current_bb.aabb[1] + self.current_bb.aabb[3]
                    bb_center = (bb.aabb[0] + bb.aabb[2]/2, bb.aabb[1] + bb.aabb[3]/2)
                    if a < bb_center[1] < b:
                        distance = (center_point[0] - bb_center[0])**2 + (center_point[1] - bb_center[1])**2
                        if distance < max_distance:
                            max_distance = distance
                            closest_box = bb
                else:
                    a, b = self.current_bb.aabb[0], self.current_bb.aabb[0] + self.current_bb.aabb[2]
                    bb_center = (bb.aabb[0] + bb.aabb[2]/2, bb.aabb[1] + bb.aabb[3]/2)
                    if a < bb_center[0] < b:
                        distance = (center_point[0] - bb_center[0])**2 + (center_point[1] - bb_center[1])**2
                        if distance < max_distance:
                            max_distance = distance
                            closest_box = bb
            # Find the closest box from boxes by comparing center points
            if not closest_box:
                for bb in boxes:
                    bb_center = (bb.aabb[0] + bb.aabb[2]/2, bb.aabb[1] + bb.aabb[3]/2)
                    distance = (center_point[0] - bb_center[0])**2 + (center_point[1] - bb_center[1])**2
                    if distance < max_distance:
                        max_distance = distance
                        closest_box = bb
            self.current_bb = closest_box

    def move_left(self):
        boxes = [bb for bb in self.registry[self.current_state] if bb.aabb[0] < self.current_bb.aabb[0]]
        self._move(boxes, horiz=True)

    def move_right(self):
        boxes = [bb for bb in self.registry[self.current_state] if bb.aabb[0] > self.current_bb.aabb[0]]
        self._move(boxes, horiz=True)

    def move_up(self):
        boxes = [bb for bb in self.registry[self.current_state] if bb.aabb[1] < self.current_bb.aabb[1]]
        self._move(boxes)

    def move_down(self):
        boxes = [bb for bb in self.registry[self.current_state] if bb.aabb[1] > self.current_bb.aabb[1]]
        self._move(boxes)

    def handle_mouse(self, mouse_position):
        x, y = mouse_position
        for bb in self.registry[self.current_state]:
            if bb.aabb[0] <= x < bb.aabb[0] + bb.aabb[2] and \
                    bb.aabb[1] <= y < bb.aabb[1] + bb.aabb[3]:
                self.current_bb = bb

    def draw(self, surf):
        # for bb in self.registry[self.current_state]:
        #     s = engine.create_surface((bb.aabb[2], bb.aabb[3]), transparent=True)
        #     engine.fill(s, (10 * bb.idx, 10 * bb.idx, 0, 128))
        #     surf.blit(s, (bb.aabb[0], bb.aabb[1]))
        if self.current_bb:
            # right = self.current_bb.aabb[0] >= int(0.75 * WINWIDTH)
            right = False
            pos = (max(0, self.current_bb.aabb[0] - 32), self.current_bb.aabb[1] + 13)
            self.current_bb.help_box.draw(surf, pos, right)

            cursor_pos = (max(0, self.current_bb.aabb[0] - 4), self.current_bb.aabb[1])
            self.cursor.update()
            self.cursor.draw(surf, *cursor_pos)

def build_groove(surf, topleft, width, fill):
    bg = SPRITES.get('groove_back')
    start = engine.subsurface(bg, (0, 0, 2, 5))
    mid = engine.subsurface(bg, (2, 0, 1, 5))
    end = engine.subsurface(bg, (3, 0, 2, 5))
    fg = SPRITES.get('groove_fill')

    # Build back groove
    surf.blit(start, topleft)
    for idx in range(width - 2):
        mid_pos = (topleft[0] + 2 + idx, topleft[1])
        surf.blit(mid, mid_pos)
    surf.blit(end, (topleft[0] + width, topleft[1]))

    # Build fill groove
    number_needed = int(fill * (width - 1))  # Width of groove minus section for start and end
    for groove in range(number_needed):
        surf.blit(fg, (topleft[0] + 1 + groove, topleft[1] + 1))

class InfoMenuState(State):
    name = 'info_menu'
    in_level = False
    show_map = False

    def create_background(self):
        panorama = RESOURCES.panoramas.get('info_menu_background')
        if not panorama:
            panorama = RESOURCES.panoramas.get('default_background')
        if panorama:
            self.bg = background.PanoramaBackground(panorama)
        else:
            self.bg = None

    def start(self):
        self.mouse_indicator = gui.MouseIndicator()
        self.create_background()

        # Unit to be displayed
        self.unit = game.memory.get('current_unit')
        self.scroll_units = game.memory.get('scroll_units')
        if self.scroll_units is None:
            self.scroll_units = [unit for unit in game.units if not unit.dead and unit.team == self.unit.team and unit.party == self.unit.party]
            if self.unit.position:
                self.scroll_units = [unit for unit in self.scroll_units if unit.position and game.board.in_vision(unit.position)]
        self.scroll_units = [unit for unit in self.scroll_units if 'Tile' not in unit.tags]
        game.memory['scroll_units'] = None

        self.state = game.memory.get('info_menu_state', info_states[0])
        if self.state == 'notes' and not (DB.constants.value('unit_notes') and self.unit.notes):
            self.state = 'personal_data'
        self.growth_flag = False

        self.fluid = FluidScroll(200, 1)

        self.left_arrow = gui.ScrollArrow('left', (103, 3))
        self.right_arrow = gui.ScrollArrow('right', (217, 3), 0.5)

        self.logo = None
        self.switch_logo(self.state)

        self.info_graph = InfoGraph()
        self.info_flag = False
        self.info_graph.set_current_state(self.state)
        self.reset_surfs()

        # For transitions between states
        self.rescuer = None  # Keeps track of the rescuer if we are looking at the traveler
        self.next_unit = None
        self.next_state = None
        self.scroll_offset_x = 0
        self.scroll_offset_y = 0
        self.transition = None
        self.transition_counter = 0
        self.transparency = 0

        game.state.change('transition_in')
        return 'repeat'

    def reset_surfs(self):
        self.info_graph.clear()
        self.portrait_surf = None

        self.personal_data_surf = None
        self.growths_surf = None
        self.wexp_surf = None
        self.equipment_surf = None
        self.support_surf = None
        self.skill_surf = None
        self.class_skill_surf = None
        self.fatigue_surf = None
        self.notes_surf = None

    def switch_logo(self, name):
        if name == 'personal_data':
            image = SPRITES.get('info_title_personal_data')
        elif name == 'equipment':
            image = SPRITES.get('info_title_items')
        elif name == 'support_skills':
            image = SPRITES.get('info_title_weapon')
        elif name == 'notes':
            image = SPRITES.get('info_title_notes')
        else:
            return
        if self.logo:
            self.logo.switch_image(image)
        else:
            self.logo = gui.Logo(image, (164, 10))

    def back(self):
        SOUNDTHREAD.play_sfx('Select 4')
        game.memory['info_menu_state'] = self.state
        game.memory['current_unit'] = self.unit
        if self.unit.position:
            game.cursor.set_pos(self.unit.position)
        game.state.change('transition_pop')

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()

        self.handle_mouse()
        if self.info_flag:
            if event == 'INFO' or event == 'BACK':
                SOUNDTHREAD.play_sfx('Info Out')
                self.info_graph.set_transition_out()
                self.info_flag = False
                return

            if 'RIGHT' in directions:
                SOUNDTHREAD.play_sfx('Select 6')
                self.info_graph.move_right()
            elif 'LEFT' in directions:
                SOUNDTHREAD.play_sfx('Select 6')
                self.info_graph.move_left()
            elif 'UP' in directions:
                SOUNDTHREAD.play_sfx('Select 6')
                self.info_graph.move_up()
            elif 'DOWN' in directions:
                SOUNDTHREAD.play_sfx('Select 6')
                self.info_graph.move_down()

        elif not self.transition:  # Only takes input when not transitioning

            if event == 'INFO':
                SOUNDTHREAD.play_sfx('Info In')
                self.info_graph.set_transition_in()
                self.info_flag = True
            elif event == 'AUX':
                if self.state == 'personal_data' and self.unit.team == 'player' and DB.constants.value('growth_info'):
                    SOUNDTHREAD.play_sfx('Select 3')
                    self.growth_flag = not self.growth_flag
                    if self.growth_flag:
                        self.info_graph.set_current_state('growths')
                    else:
                        self.info_graph.set_current_state('personal_data')
            elif event == 'BACK':
                if self.rescuer:
                    self.move_up()
                else:
                    self.back()
                    return
            elif event == 'SELECT':
                mouse_position = INPUT.get_mouse_position()
                if mouse_position:
                    mouse_x, mouse_y = mouse_position
                    if mouse_x <= 16:
                        self.move_left()
                    elif mouse_x >= WINWIDTH - 16:
                        self.move_right()
                    elif mouse_y <= 16:
                        self.move_up()
                    elif mouse_y >= WINHEIGHT - 16:
                        self.move_down()
                if not self.transition:  # Some of the above move commands could cause transition
                    if self.unit.traveler:
                        self.move_traveler()

            if 'RIGHT' in directions:
                self.move_right()
            elif 'LEFT' in directions:
                self.move_left()
            elif 'DOWN' in directions:
                self.move_down()
            elif 'UP' in directions:
                self.move_up()

    def move_left(self):
        SOUNDTHREAD.play_sfx('Status_Page_Change')
        index = info_states.index(self.state)
        new_index = (index - 1) % len(info_states)
        self.next_state = info_states[new_index]
        if self.next_state == 'notes' and not (DB.constants.value('unit_notes') and self.unit.notes):
            new_index = (new_index - 1) % len(info_states)
            self.next_state = info_states[new_index]
        self.transition = 'LEFT'
        self.left_arrow.pulse()
        self.switch_logo(self.next_state)

    def move_right(self):
        SOUNDTHREAD.play_sfx('Status_Page_Change')
        index = info_states.index(self.state)
        new_index = (index + 1) % len(info_states)
        self.next_state = info_states[new_index]
        if self.next_state == 'notes' and not (DB.constants.value('unit_notes') and self.unit.notes):
            new_index = (new_index + 1) % len(info_states)
            self.next_state = info_states[new_index]
        self.transition = 'RIGHT'
        self.right_arrow.pulse()
        self.switch_logo(self.next_state)

    def move_down(self):
        SOUNDTHREAD.play_sfx('Status_Character')
        if self.scroll_units:
            if self.rescuer:
                new_index = self.scroll_units.index(self.rescuer)
                self.rescuer = None
            else:
                index = self.scroll_units.index(self.unit)
                new_index = (index + 1) % len(self.scroll_units)
            self.next_unit = self.scroll_units[new_index]
            if self.state == 'notes' and not (DB.constants.value('unit_notes') and self.next_unit.notes):
                self.state = 'personal_data'
                self.switch_logo('personal_data')
            self.transition = 'DOWN'

    def move_up(self):
        SOUNDTHREAD.play_sfx('Status_Character')
        if self.scroll_units:
            if self.rescuer:
                new_index = self.scroll_units.index(self.rescuer)
                self.rescuer = None
            else:
                index = self.scroll_units.index(self.unit)
                new_index = (index - 1) % len(self.scroll_units)
            self.next_unit = self.scroll_units[new_index]
            if self.state == 'notes' and not (DB.constants.value('unit_notes') and self.next_unit.notes):
                self.state = 'personal_data'
                self.switch_logo('personal_data')
            self.transition = 'UP'

    def move_traveler(self):
        SOUNDTHREAD.play_sfx('Status_Character')
        self.rescuer = self.unit
        self.next_unit = game.get_unit(self.unit.traveler)
        if self.state == 'notes' and not (DB.constants.value('unit_notes') and self.next_unit.notes):
            self.state = 'personal_data'
            self.switch_logo('personal_data')
        self.transition = 'DOWN'

    def handle_mouse(self):
        mouse_position = INPUT.get_mouse_position()
        if not mouse_position:
            return
        if self.info_flag:
            self.info_graph.handle_mouse(mouse_position)

    def update(self):
        # Up and Down
        if self.next_unit:
            self.transition_counter += 1
            # Transition in
            if self.next_unit == self.unit:
                if self.transition_counter == 1:
                    self.transparency = .75
                    self.scroll_offset_y = -80 if self.transition == 'DOWN' else 80
                elif self.transition_counter == 2:
                    self.transparency = .6
                    self.scroll_offset_y = -32 if self.transition == 'DOWN' else 32
                elif self.transition_counter == 3:
                    self.transparency = .48
                    self.scroll_offset_y = -16 if self.transition == 'DOWN' else 16
                elif self.transition_counter == 4:
                    self.transparency = .15
                    self.scroll_offset_y = -4 if self.transition == 'DOWN' else 4
                elif self.transition_counter == 5:
                    self.scroll_offset_y = 0
                else:
                    self.transition = None
                    self.transparency = 0
                    self.next_unit = None
                    self.transition_counter = 0
            # Transition out
            else:
                if self.transition_counter == 1:
                    self.transparency = .15
                elif self.transition_counter == 2:
                    self.transparency = .48
                elif self.transition_counter == 3:
                    self.transparency = .6
                    self.scroll_offset_y = 8 if self.transition == 'DOWN' else -8
                elif self.transition_counter == 4:
                    self.transparency = .75
                    self.scroll_offset_y = 16 if self.transition == 'DOWN' else -16
                elif self.transition_counter < 8: # (5, 6, 7, 8):  # Pause for a bit
                    self.transparency = 1.
                    self.scroll_offset_y = 160 if self.transition == 'DOWN' else -160
                else:
                    self.unit = self.next_unit  # Now transition in
                    self.reset_surfs()
                    self.transition_counter = 0

        # Left and Right
        elif self.next_state is not None:
            self.transition_counter += 1
            # Transition in
            if self.next_state == self.state:
                if self.transition_counter == 1:
                    self.scroll_offset_x = 104 if self.transition == 'RIGHT' else -104
                elif self.transition_counter == 2:
                    self.scroll_offset_x = 72 if self.transition == 'RIGHT' else -72
                elif self.transition_counter == 3:
                    self.scroll_offset_x = 56 if self.transition == 'RIGHT' else -56
                elif self.transition_counter == 4:
                    self.scroll_offset_x = 40 if self.transition == 'RIGHT' else -40
                elif self.transition_counter == 5:
                    self.scroll_offset_x = 24 if self.transition == 'RIGHT' else -24
                elif self.transition_counter == 6:
                    self.scroll_offset_x = 8 if self.transition == 'RIGHT' else -8
                else:
                    self.transition = None
                    self.scroll_offset_x = 0
                    self.next_state = None
                    self.transition_counter = 0
            else:
                if self.transition_counter == 1:
                    self.scroll_offset_x = -32 if self.transition == 'RIGHT' else 32
                elif self.transition_counter == 2:
                    self.scroll_offset_x = -56 if self.transition == 'RIGHT' else 56
                elif self.transition_counter == 3:
                    self.scroll_offset_x = -80 if self.transition == 'RIGHT' else 80
                elif self.transition_counter == 4:
                    self.scroll_offset_x = -96 if self.transition == 'RIGHT' else 96
                elif self.transition_counter == 5:
                    self.scroll_offset_x = -112 if self.transition == 'RIGHT' else 112
                else:
                    self.scroll_offset_x = -140 if self.transition == 'RIGHT' else 140
                    self.state = self.next_state
                    self.info_graph.set_current_state(self.state)
                    self.transition_counter = 0

    def draw(self, surf):
        if self.bg:
            self.bg.draw(surf)

        # Image flashy thing at the top of the InfoMenu
        num_frames = 8
        # 8 frames long, 8 different frames
        blend_perc = abs(num_frames - ((engine.get_time()/134) % (num_frames * 2))) / float(num_frames)
        sprite = SPRITES.get('info_menu_flash')
        im = image_mods.make_translucent_blend(sprite, 128. * blend_perc)
        surf.blit(im, (98, 0), None, engine.BLEND_RGB_ADD)

        self.draw_portrait(surf)
        self.draw_slide(surf)

        if self.info_graph.current_bb:
            self.info_graph.draw(surf)

        if not self.transition:
            self.mouse_indicator.draw(surf)

        return surf

    def draw_portrait(self, surf):
        # Only create if we don't have one in memory
        if not self.portrait_surf:
            self.portrait_surf = self.create_portrait()

        # Stick it on the surface
        if self.transparency:
            im = image_mods.make_translucent(self.portrait_surf, self.transparency)
            surf.blit(im, (0, self.scroll_offset_y))
        else:
            surf.blit(self.portrait_surf, (0, self.scroll_offset_y))

        # Blit the unit's active/focus map sprite
        if not self.transparency:
            active_sprite = self.unit.sprite.create_image('active')
            x_pos = 81 - active_sprite.get_width()//2
            y_pos = WINHEIGHT - 61
            surf.blit(active_sprite, (x_pos, y_pos + self.scroll_offset_y))

    def create_portrait(self):
        surf = engine.create_surface((96, WINHEIGHT), transparent=True)
        surf.blit(SPRITES.get('info_unit'), (8, 122))

        im = icons.get_portrait(self.unit)
        if im:
            x_pos = (im.get_width() - 80)//2
            portrait_surf = engine.subsurface(im, (x_pos, 0, 80, 72))
            surf.blit(portrait_surf, (8, 8))

        FONT['text-white'].blit_center(self.unit.name, surf, (48, 80))
        self.info_graph.register((24, 80, 52, 24), self.unit.desc, 'all')
        class_obj = DB.classes.get(self.unit.klass)
        FONT['text-white'].blit(class_obj.name, surf, (8, 104))
        self.info_graph.register((8, 104, 72, 16), class_obj.desc, 'all')
        FONT['text-blue'].blit_right(str(self.unit.level), surf, (39, 120))
        self.info_graph.register((8, 120, 30, 16), 'Level_desc', 'all')
        FONT['text-blue'].blit_right(str(self.unit.exp), surf, (63, 120))
        self.info_graph.register((38, 120, 30, 16), 'Exp_desc', 'all')
        FONT['text-blue'].blit_right(str(self.unit.get_hp()), surf, (39, 136))
        self.info_graph.register((8, 136, 72, 16), 'HP_desc', 'all')
        max_hp = equations.parser.hitpoints(self.unit)
        FONT['text-blue'].blit_right(str(max_hp), surf, (63, 136))
        # Blit the white status platform
        surf.blit(SPRITES.get('status_platform'), (66, 131))
        # Blit affinity
        affinity = DB.affinities.get(self.unit.affinity)
        if affinity:
            icons.draw_item(surf, affinity, (78, 81))
            self.info_graph.register((76, 80, 16, 16), affinity.desc, 'all')
        return surf

    def draw_top_arrows(self, surf):
        self.left_arrow.draw(surf)
        self.right_arrow.draw(surf)

    def draw_slide(self, surf):
        top_surf = engine.create_surface((WINWIDTH, WINHEIGHT), transparent=True)
        main_surf = engine.copy_surface(top_surf)

        # Blit title of menu
        top_surf.blit(SPRITES.get('info_title_background'), (112, 8))
        if self.logo:
            self.logo.update()
            self.logo.draw(top_surf)
        page = str(info_states.index(self.state) + 1) + '/' + str(len(info_states))
        FONT['small-white'].blit_right(page, top_surf, (235, 12))

        self.draw_top_arrows(top_surf)

        if self.state == 'personal_data':
            if self.growth_flag:
                if not self.growths_surf:
                    self.growths_surf = self.create_personal_data_surf(growths=True)
                self.draw_growths_surf(main_surf)
            else:
                if not self.personal_data_surf:
                    self.personal_data_surf = self.create_personal_data_surf()
                self.draw_personal_data_surf(main_surf)
            if not self.class_skill_surf:
                self.class_skill_surf = self.create_class_skill_surf()
            self.draw_class_skill_surf(main_surf)
            if DB.constants.value('fatigue') and self.unit.team == 'player' and \
                    game.game_vars.get('_fatigue'):
                if not self.fatigue_surf:
                    self.fatigue_surf = self.create_fatigue_surf()
                self.draw_fatigue_surf(main_surf)

        elif self.state == 'equipment':
            if not self.equipment_surf:
                self.equipment_surf = self.create_equipment_surf()
            self.draw_equipment_surf(main_surf)

        elif self.state == 'support_skills':
            main_surf.blit(SPRITES.get('status_logo'), (100, WINHEIGHT - 42))
            if not self.skill_surf:
                self.skill_surf = self.create_skill_surf()
            self.draw_skill_surf(main_surf)
            if not self.wexp_surf:
                self.wexp_surf = self.create_wexp_surf()
            self.draw_wexp_surf(main_surf)
            if not self.support_surf:
                self.support_surf = self.create_support_surf()
            self.draw_support_surf(main_surf)

        elif self.state == 'notes':
            if not self.notes_surf:
                self.notes_surf = self.create_notes_surf()
            self.draw_notes_surf(main_surf)

        # Now put it in the right place
        offset_x = max(96, 96 - self.scroll_offset_x)
        main_surf = engine.subsurface(main_surf, (offset_x, 0, main_surf.get_width() - offset_x, WINHEIGHT))
        surf.blit(main_surf, (max(96, 96 + self.scroll_offset_x), self.scroll_offset_y))
        if self.transparency:
            top_surf = image_mods.make_translucent(top_surf, self.transparency)
        surf.blit(top_surf, (0, self.scroll_offset_y))

    def create_personal_data_surf(self, growths=False):
        if growths:
            state = 'growths'
        else:
            state = 'personal_data'

        menu_size = WINWIDTH - 96, WINHEIGHT
        surf = engine.create_surface(menu_size, transparent=True)

        class_obj = DB.classes.get(self.unit.klass)
        max_stats = class_obj.max_stats

        left_stats = [stat.nid for stat in DB.stats if stat.position == 'left']
        right_stats = left_stats[6:]  # Only first six get to be on the left
        right_stats += [stat.nid for stat in DB.stats if stat.position == 'right']
        # Make sure we only display up to 6 on each
        left_stats = left_stats[:6]
        right_stats = right_stats[:6]

        for idx, stat_nid in enumerate(left_stats):
            # Value
            if growths:
                icons.draw_growth(surf, stat_nid, self.unit, (47, 16 * idx + 24))
            else:
                highest_stat = DB.stats.get(stat_nid).maximum
                max_stat = max_stats.get(stat_nid, 30)
                if max_stat > 0:
                    total_length = int(max_stat / highest_stat * 44)
                    frac = utils.clamp(self.unit.stats.get(stat_nid) / max_stat, 0, 1)
                    build_groove(surf, (27, 16 * idx + 32), total_length, frac)
                icons.draw_stat(surf, stat_nid, self.unit, (47, 16 * idx + 24))
            # Name
            name = DB.stats.get(stat_nid).name
            FONT['text-yellow'].blit(name, surf, (8, 16 * idx + 24))
            base_value = self.unit.stats.get(stat_nid, 0)
            contribution = self.unit.stat_contribution(stat_nid)
            contribution['Base Value'] = base_value
            help_box = help_menu.StatDialog('%s_desc' % stat_nid, contribution)
            self.info_graph.register((96 + 8, 16 * idx + 24, 64, 16), help_box, state, first=(idx == 0))

        for idx, stat_nid in enumerate(right_stats):
            if growths:
                icons.draw_growth(surf, stat_nid, self.unit, (111, 16 * idx + 24))
            else:
                icons.draw_stat(surf, stat_nid, self.unit, (111, 16 * idx + 24))
            # Name
            name = DB.stats.get(stat_nid).name
            FONT['text-yellow'].blit(name, surf, (72, 16 * idx + 24))
            base_value = self.unit.stats.get(stat_nid, 0)
            contribution = self.unit.stat_contribution(stat_nid)
            contribution['Base Value'] = base_value
            help_box = help_menu.StatDialog('%s_desc' % stat_nid, contribution)
            self.info_graph.register((96 + 72, 16 * idx + 24, 64, 16), help_box, state)

        other_stats = ['TRV', 'AID', 'RAT']
        if self.unit.get_max_mana() > 0:
            other_stats.insert(0, 'MANA')
        if DB.constants.value('pairup'):
            other_stats.insert(2, 'GAUGE')
        other_stats = other_stats[:6 - len(right_stats)]

        for idx, stat in enumerate(other_stats):
            true_idx = idx + len(right_stats)

            if stat == 'TRV':
                if self.unit.traveler:
                    trav = game.get_unit(self.unit.traveler)
                    FONT['text-blue'].blit(trav.name, surf, (96, 16 * true_idx + 24))
                else:
                    FONT['text-blue'].blit('--', surf, (96, 16 * true_idx + 24))
                FONT['text-yellow'].blit('Trv', surf, (72, 16 * true_idx + 24))
                self.info_graph.register((96 + 72, 16 * true_idx + 24, 64, 16), 'Trv_desc', state)

            elif stat == 'AID':
                if growths:
                    icons.draw_growth(surf, 'HP', self.unit, (111, 16 * true_idx + 24))
                    FONT['text-yellow'].blit('HP', surf, (72, 16 * true_idx + 24))
                    self.info_graph.register((96 + 72, 16 * true_idx + 24, 64, 16), 'HP_desc', state)
                else:
                    aid = equations.parser.rescue_aid(self.unit)
                    FONT['text-blue'].blit_right(str(aid), surf, (111, 16 * true_idx + 24))

                    # Mount Symbols
                    if 'Dragon' in self.unit.tags:
                        aid_surf = engine.subsurface(SPRITES.get('aid_icons'), (0, 48, 16, 16))
                    elif 'Flying' in self.unit.tags:
                        aid_surf = engine.subsurface(SPRITES.get('aid_icons'), (0, 32, 16, 16))
                    elif 'Mounted' in self.unit.tags:
                        aid_surf = engine.subsurface(SPRITES.get('aid_icons'), (0, 16, 16, 16))
                    else:
                        aid_surf = engine.subsurface(SPRITES.get('aid_icons'), (0, 0, 16, 16))
                    surf.blit(aid_surf, (112, 16 * true_idx + 24))
                    FONT['text-yellow'].blit('Aid', surf, (72, 16 * true_idx + 24))
                    self.info_graph.register((96 + 72, 16 * true_idx + 24, 64, 16), 'Aid_desc', state)

            elif stat == 'RAT':
                rat = str(equations.parser.rating(self.unit))
                FONT['text-blue'].blit_right(rat, surf, (111, 16 * true_idx + 24))
                FONT['text-yellow'].blit('Rat', surf, (72, 16 * true_idx + 24))
                self.info_graph.register((96 + 72, 16 * true_idx + 24, 64, 16), 'Rating_desc', state)

            elif stat == 'MANA':
                mana = str(self.unit.current_mana)
                FONT['text-blue'].blit_right(mana, surf, (111, 16 * true_idx + 24))
                FONT['text-yellow'].blit(text_funcs.translate('MANA'), surf, (72, 16 * true_idx + 24))
                self.info_graph.register((96 + 72, 16 * true_idx + 24, 64, 16), 'MANA_desc', state)

            elif stat == 'GAUGE':
                gge = str(self.unit.get_guard_gauge()) + '/' + str(self.unit.get_max_guard_gauge())
                FONT['text-blue'].blit_right(gge, surf, (111, 16 * true_idx + 24))
                FONT['text-yellow'].blit(text_funcs.translate('GAUGE'), surf, (72, 16 * true_idx + 24))
                self.info_graph.register((96 + 72, 16 * true_idx + 24, 64, 16), 'GAUGE_desc', state)

            if DB.constants.value('lead'):
                FONT['text-yellow'].blit('Lead', surf, (72, 120))
                self.info_graph.register((96 + 72, 120, 64, 16), 'Lead_desc', state)

                if growths:
                    icons.draw_growth(surf, 'LEAD', self.unit, (111, 120))
                else:
                    icons.draw_stat(surf, 'LEAD', self.unit, (111, 120))
                    lead_surf = engine.subsurface(SPRITES.get('lead_star'), (0, 16, 16, 16))
                    surf.blit(lead_surf, (111, 120))

        return surf

    def draw_personal_data_surf(self, surf):
        surf.blit(self.personal_data_surf, (96, 0))

    def draw_growths_surf(self, surf):
        surf.blit(self.growths_surf, (96, 0))

    def create_wexp_surf(self):
        surf = engine.create_surface((WINWIDTH - 96, 24), transparent=True)

        how_many = len([wexp for wexp in self.unit.wexp.values() if wexp > 0])
        x_pos = (WINWIDTH - 102) // max(how_many, 2)

        class_obj = DB.classes.get(self.unit.klass)
        counter = 0
        for idx, weapon in enumerate(self.unit.wexp.keys()):
            value = self.unit.wexp[weapon]
            if value > 0 and (class_obj.wexp_gain.get(weapon).usable or skill_system.wexp_usable_skill(self.unit, weapon)):
                weapon_rank = DB.weapon_ranks.get_rank_from_wexp(value)
                next_weapon_rank = DB.weapon_ranks.get_next_rank_from_wexp(value)
                if not weapon_rank:
                    perc = 0
                elif not next_weapon_rank:
                    perc = 1
                else:
                    perc = (value - weapon_rank.requirement) / (next_weapon_rank.requirement - weapon_rank.requirement)
                offset = 8 + counter * x_pos
                counter += 1

                icons.draw_weapon(surf, weapon, (offset, 4))

                # Build groove
                build_groove(surf, (offset + 18, 10), x_pos - 24, perc)
                # Add text
                pos = (offset + 7 + x_pos//2, 4)
                FONT['text-blue'].blit_center(weapon_rank.nid, surf, pos)
                self.info_graph.register((96 + pos[0] - x_pos//2 - 8, 24 + pos[1], x_pos, 16), "%s mastery level: %d" % (DB.weapons.get(weapon).name, value), 'support_skills', first=(idx==0))

        return surf

    def draw_wexp_surf(self, surf):
        surf.blit(self.wexp_surf, (96, 24))

    def create_equipment_surf(self):
        surf = engine.create_surface((WINWIDTH - 96, WINHEIGHT), transparent=True)

        weapon = self.unit.get_weapon()
        accessory = self.unit.get_accessory()

        # Blit items
        for idx, item in enumerate(self.unit.nonaccessories):
            if item.multi_item and any(subitem is weapon for subitem in item.subitems):
                surf.blit(SPRITES.get('equipment_highlight'), (8, idx * 16 + 24 + 8))
                for subitem in item.subitems:
                    if subitem is weapon:
                        item_option = menu_options.FullItemOption(idx, subitem)
                        break
                else:  # Shouldn't happen
                    item_option = menu_options.FullItemOption(idx, item)
            else:
                if item is weapon:
                    surf.blit(SPRITES.get('equipment_highlight'), (8, idx * 16 + 24 + 8))
                item_option = menu_options.FullItemOption(idx, item)
            item_option.draw(surf, 8, idx * 16 + 24)
            self.info_graph.register((96 + 8, idx * 16 + 24, 120, 16), item_option.get_help_box(), 'equipment', first=(idx == 0))

        # Blit accessories
        for idx, item in enumerate(self.unit.accessories):
            aidx = item_funcs.get_num_items(self.unit) + idx
            y_pos = aidx * 16 + 24
            if item.multi_item and any(subitem is accessory for subitem in item.subitems):
                surf.blit(SPRITES.get('equipment_highlight'), (8, y_pos + 8))
                for subitem in item.subitems:
                    if subitem is accessory:
                        item_option = menu_options.FullItemOption(aidx, subitem)
                        break
                else:  # Shouldn't happen
                    item_option = menu_options.FullItemOption(aidx, item)
            else:
                if item is accessory:
                    surf.blit(SPRITES.get('equipment_highlight'), (8, y_pos + 8))
                item_option = menu_options.FullItemOption(aidx, item)
            item_option.draw(surf, 8, y_pos)
            first = (idx == 0 and not self.unit.nonaccessories)
            self.info_graph.register((96 + 8, y_pos, 120, 16), item_option.get_help_box(), 'equipment', first=first)

        # Battle stats
        battle_surf = SPRITES.get('battle_info')
        top, left = 104, 12
        surf.blit(battle_surf, (left, top))
        # Populate battle info
        surf.blit(SPRITES.get('equipment_logo'), (14, top + 4))
        FONT['text-yellow'].blit('Rng', surf, (78, top))
        self.info_graph.register((96 + 78, top, 56, 16), 'Rng_desc', 'equipment')
        FONT['text-yellow'].blit('Atk', surf, (22, top + 16))
        self.info_graph.register((96 + 14, top + 16, 64, 16), 'Atk_desc', 'equipment')
        FONT['text-yellow'].blit('Hit', surf, (22, top + 32))
        self.info_graph.register((96 + 14, top + 32, 64, 16), 'Hit_desc', 'equipment')
        if DB.constants.value('crit'):
            FONT['text-yellow'].blit('Crit', surf, (78, top + 16))
            self.info_graph.register((96 + 78, top + 16, 56, 16), 'Crit_desc', 'equipment')
        else:
            FONT['text-yellow'].blit('AS', surf, (78, top + 16))
            self.info_graph.register((96 + 78, top + 16, 56, 16), 'AS_desc', 'equipment')
        FONT['text-yellow'].blit('Avoid', surf, (78, top + 32))
        self.info_graph.register((96 + 78, top + 32, 56, 16), 'Avoid_desc', 'equipment')

        if weapon:
            rng = item_funcs.get_range_string(self.unit, weapon)
            dam = str(combat_calcs.damage(self.unit, weapon))
            acc = str(combat_calcs.accuracy(self.unit, weapon))
            crt = combat_calcs.crit_accuracy(self.unit, weapon)
            if crt is None:
                crt = '--'
            else:
                crt = str(crt)
        else:
            rng, dam, acc, crt = '--', '--', '--', '--'

        avo = str(combat_calcs.avoid(self.unit, weapon))
        attack_speed = str(combat_calcs.attack_speed(self.unit, weapon))
        FONT['text-blue'].blit_right(rng, surf, (127, top))
        FONT['text-blue'].blit_right(dam, surf, (71, top + 16))
        FONT['text-blue'].blit_right(acc, surf, (71, top + 32))
        if DB.constants.value('crit'):
            FONT['text-blue'].blit_right(crt, surf, (127, top + 16))
        else:
            FONT['text-blue'].blit_right(attack_speed, surf, (127, top + 16))
        FONT['text-blue'].blit_right(avo, surf, (127, top + 32))

        return surf

    def draw_equipment_surf(self, surf):
        surf.blit(self.equipment_surf, (96, 0))

    def create_skill_surf(self):
        surf = engine.create_surface((WINWIDTH - 96, 24), transparent=True)
        skills = [skill for skill in self.unit.skills if not (skill.class_skill or skill.hidden)][:6]

        for idx, skill in enumerate(skills):
            left_pos = idx * 24
            icons.draw_skill(surf, skill, (left_pos + 8, 4), compact=False)
            if skill.data.get('total_charge'):
                charge = ' %d / %d' % (skill.data['charge'], skill.data['total_charge'])
            else:
                charge = ''
            self.info_graph.register((96 + left_pos + 8, WINHEIGHT - 28, 16, 16), help_menu.HelpDialog(skill.desc, name=skill.name + charge), 'support_skills')

        return surf

    def draw_skill_surf(self, surf):
        surf.blit(self.skill_surf, (96, WINHEIGHT - 32))

    def create_class_skill_surf(self):
        surf = engine.create_surface((WINWIDTH - 96, 24), transparent=True)
        class_skills = [skill for skill in self.unit.skills if skill.class_skill and not skill.hidden][:6]

        for idx, skill in enumerate(class_skills):
            left_pos = idx * 24
            icons.draw_skill(surf, skill, (left_pos + 8, 4))
            if skill.data.get('total_charge'):
                charge = ' (%d/%d)' % (skill.data['charge'], skill.data['total_charge'])
            else:
                charge = ''
            self.info_graph.register((96 + left_pos + 8, WINHEIGHT - 32, 16, 16), help_menu.HelpDialog(skill.desc, name=skill.name + charge), 'personal_data')
            self.info_graph.register((96 + left_pos + 8, WINHEIGHT - 32, 16, 16), help_menu.HelpDialog(skill.desc, name=skill.name + charge), 'growths')

        return surf

    def draw_class_skill_surf(self, surf):
        surf.blit(self.class_skill_surf, (96, WINHEIGHT - 36))

    def create_support_surf(self):
        surf = engine.create_surface((WINWIDTH - 96, WINHEIGHT), transparent=True)

        if game.game_vars.get('_supports'):
            pairs = game.supports.get_pairs(self.unit.nid)
            pairs = [pair for pair in pairs if pair.unlocked_ranks]
        else:
            pairs = []

        top = 48
        for idx, pair in enumerate(pairs):
            other_unit = None
            if pair.unit1 == self.unit.nid:
                other_unit = game.get_unit(pair.unit2)
            elif pair.unit2 == self.unit.nid:
                other_unit = game.get_unit(pair.unit1)
            if not other_unit:
                continue
            affinity = DB.affinities.get(other_unit.affinity)
            if affinity:
                icons.draw_item(surf, affinity, (16, idx * 16 + top))
                self.info_graph.register((112, idx * 16 + top, WINWIDTH - 120, 16), affinity.desc, 'support_skills')
            FONT['text-white'].blit(other_unit.name, surf, (36, idx * 16 + top))
            highest_rank = pair.unlocked_ranks[-1]
            FONT['text-yellow'].blit_right(highest_rank, surf, (surf.get_width() - 24, idx * 16 + top))
        return surf

    def draw_support_surf(self, surf):
        surf.blit(self.support_surf, (96, 0))

    def create_fatigue_surf(self):
        surf = engine.create_surface((WINWIDTH - 96, WINHEIGHT), transparent=True)
        max_fatigue = max(1, equations.parser.max_fatigue(self.unit))
        fatigue = self.unit.get_fatigue()
        build_groove(surf, (27, WINHEIGHT - 9), 88, utils.clamp(fatigue / max_fatigue, 0, 1))
        x_pos = 27 + 88 // 2
        text = str(fatigue) + '/' + str(max_fatigue)
        x_pos -= FONT['text-blue'].width(text)//2
        FONT['text-blue'].blit(text, surf, (x_pos, WINHEIGHT - 17))
        if fatigue >= max_fatigue:
            FONT['text-red'].blit(str(fatigue), surf, (x_pos, WINHEIGHT - 17))
        FONT['text-yellow'].blit(text_funcs.translate('Ftg'), surf, (8, WINHEIGHT - 17))

        return surf

    def draw_fatigue_surf(self, surf):
        surf.blit(self.fatigue_surf, (96, 0))

    def create_notes_surf(self):
        # Menu background
        menu_surf = engine.create_surface((WINWIDTH - 96, WINHEIGHT), transparent=True)
        font = FONT['text-white']

        my_notes = self.unit.notes

        if my_notes:
            total_height = 24
            help_offset = 0
            for idx, note in enumerate(my_notes):
                category = note[0]
                entries = note[1].split(',')
                FONT['text-blue'].blit(category, menu_surf, (10, total_height))
                for entry in entries:
                    category_length = font.size(category)[0]
                    left_pos = 64 if category_length <= 64 else (category_length + 8)
                    font.blit(entry, menu_surf, (left_pos, total_height))
                    total_height += 16
                self.info_graph.register((96, 16 * help_offset + 24, 64, 16), '%s_desc' % category, 'notes', first=(idx == 0))
                help_offset += len(entries)

        return menu_surf

    def draw_notes_surf(self, surf):
        surf.blit(self.notes_surf, (96, 0))
