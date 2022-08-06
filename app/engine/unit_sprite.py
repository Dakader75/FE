from app.engine.game_counters import ANIMATION_COUNTERS
import math

from app.constants import TILEWIDTH, TILEHEIGHT, COLORKEY
from app.data.palettes import gray_colors, enemy_colors, other_colors, enemy2_colors, black_colors, \
    player_dark_colors, enemy_dark_colors, gray_dark_colors

from app.resources.resources import RESOURCES
from app.data.database import DB

from app.utilities import utils

from app.engine.sprites import SPRITES
from app.engine.sound import SOUNDTHREAD
from app.engine import engine, image_mods, health_bar, equations
from app.engine import item_funcs, item_system, skill_system, particles
import app.engine.config as cf
from app.engine.animations import Animation
from app.engine.game_state import game

class MapSprite():
    def __init__(self, map_sprite, team):
        self.nid = map_sprite.nid
        self.team = team
        self.resource = map_sprite
        if not map_sprite.standing_image:
            map_sprite.standing_image = engine.image_load(map_sprite.stand_full_path)
        gray_stand = map_sprite.standing_image.copy()
        if not map_sprite.moving_image:
            map_sprite.moving_image = engine.image_load(map_sprite.move_full_path)
        stand, move = self.convert_to_team_colors(map_sprite)
        engine.set_colorkey(stand, COLORKEY, rleaccel=True)
        engine.set_colorkey(move, COLORKEY, rleaccel=True)
        self.passive = [engine.subsurface(stand, (num*64, 0, 64, 48)) for num in range(3)]
        self.gray = self.create_gray([engine.subsurface(gray_stand, (num*64, 0, 64, 48)) for num in range(3)])
        self.active = [engine.subsurface(stand, (num*64, 96, 64, 48)) for num in range(3)]
        self.down = [engine.subsurface(move, (num*48, 0, 48, 40)) for num in range(4)]
        self.left = [engine.subsurface(move, (num*48, 40, 48, 40)) for num in range(4)]
        self.right = [engine.subsurface(move, (num*48, 80, 48, 40)) for num in range(4)]
        self.up = [engine.subsurface(move, (num*48, 120, 48, 40)) for num in range(4)]

    def convert_to_team_colors(self, map_sprite):
        if self.team == 'player':
            if DB.constants.value('dark_sprites'):
                conversion_dict = player_dark_colors
            else:
                return map_sprite.standing_image, map_sprite.moving_image
        elif self.team == 'enemy':
            if DB.constants.value('dark_sprites'):
                conversion_dict = enemy_dark_colors
            else:
                conversion_dict = enemy_colors
        elif self.team == 'enemy2':
            conversion_dict = enemy2_colors
        elif self.team == 'other':
            conversion_dict = other_colors
        elif self.team == 'black':
            conversion_dict = black_colors

        return image_mods.color_convert(map_sprite.standing_image, conversion_dict), \
            image_mods.color_convert(map_sprite.moving_image, conversion_dict)

    def create_gray(self, imgs):
        if DB.constants.value('dark_sprites'):
            color = gray_dark_colors
        else:
            color = gray_colors
        imgs = [image_mods.color_convert(img, color) for img in imgs]
        for img in imgs:
            engine.set_colorkey(img, COLORKEY, rleaccel=True)
        return imgs

def load_map_sprite(unit, team='player'):
    klass = DB.classes.get(unit.klass)
    nid = klass.map_sprite_nid
    if unit.variant:
        nid += unit.variant
    res = RESOURCES.map_sprites.get(nid)
    if not res:  # Try without unit variant
        res = RESOURCES.map_sprites.get(klass.map_sprite_nid)
    if not res:
        return None

    map_sprite = game.map_sprite_registry.get(res.nid + '_' + team)
    if not map_sprite:
        map_sprite = MapSprite(res, team)
        game.map_sprite_registry[map_sprite.nid + '_' + team] = map_sprite
    return map_sprite

class UnitSprite():
    default_transition_time = 450

    def __init__(self, unit):
        self.unit = unit
        self.state = 'normal'  # What state the image sprite is in
        self.image_state = 'passive'  # What the image looks like
        self.transition_state = 'normal'

        self.transition_counter = 0
        self.transition_time = self.default_transition_time

        self.fake_position = None  # For escape and rescue, etc...
        self.net_position = None
        self.offset = [0, 0]

        self.flicker = []
        self.flicker_tint = []
        self.vibrate = []
        self.vibrate_counter = 0
        self.animations = {}
        self.particles = []
        self.damage_numbers = []

        self.map_sprite = load_map_sprite(self.unit, self.unit.team)

        self.health_bar = health_bar.MapHealthBar(self.unit)

    def load_sprites(self):
        self.map_sprite = load_map_sprite(self.unit, self.unit.team)

    # Normally drawing units is culled to those on the screen
    # Unit sprites matching this will be drawn anyway
    def draw_anyway(self):
        return self.transition_state != 'normal' or self.particles

    def reset(self):
        self.offset = [0, 0]
        ANIMATION_COUNTERS.attack_movement_counter.reset()

    def add_animation(self, animation_nid):
        anim = RESOURCES.animations.get(animation_nid)
        if anim:
            anim = Animation(anim, (-16, -16), loop=True)
            self.animations[animation_nid] = anim

    def remove_animation(self, animation_nid):
        if animation_nid in self.animations:
            del self.animations[animation_nid]

    def add_flicker_tint(self, color, period, width):
        self.flicker_tint.append((color, period, width))

    def remove_flicker_tint(self, color, period, width):
        if (color, period, width) in self.flicker_tint:
            self.flicker_tint.remove((color, period, width))

    def begin_flicker(self, total_time, color, direction='add'):
        self.flicker.append((engine.get_time(), total_time, color, direction, False))

    def start_flicker(self, start_time, total_time, color, direction='add', fade_out=False):
        self.flicker.append((engine.get_time() + start_time, total_time, color, direction, fade_out))

    def start_vibrate(self, start_time, total_time):
        self.vibrate.append((engine.get_time() + start_time, total_time))

    def add_warp_anim(self, nid, reverse=False):
        anim = RESOURCES.animations.get('Warp')
        if anim:
            anim_trans = Animation(anim, (-7, -24), reverse=reverse)
            anim_trans.sprite = image_mods.make_translucent(anim_trans.sprite, .33)
            self.animations[nid] = anim_trans
            anim_blend = Animation(anim, (-7, -24), reverse=reverse)
            anim_blend.set_tint(True)
            self.animations[nid] = anim_blend

    def add_warp_flowers(self, reverse=False):
        ps = particles.ParticleSystem('warp_flower', particles.WarpFlower, -1, (-1, -1, -1, -1), (-1, -1))
        angle_frac = math.pi / 8
        true_pos_x = self.unit.position[0] * TILEWIDTH + TILEWIDTH//2
        true_pos_y = self.unit.position[1] * TILEHEIGHT + TILEHEIGHT//2
        for idx, speed in enumerate((4.5, )):
            for num in range(0, 16):
                angle = num * angle_frac + (angle_frac / 2 if idx == 0 else 0)
                if reverse:
                    new_particle = particles.ReverseWarpFlower((true_pos_x, true_pos_y), speed, angle)
                else:
                    new_particle = particles.WarpFlower((true_pos_x, true_pos_y), speed, angle)
                ps.particles.append(new_particle)
        self.particles.append(ps)

    def add_swoosh_anim(self, reverse=False):
        anim = RESOURCES.animations.get('Swoosh')
        if anim:
            anim = Animation(anim, (-12, -40), reverse=reverse)
        self.animations['swoosh'] = anim

    def set_transition(self, new_state):
        self.transition_state = new_state
        self.transition_counter = self.transition_time  # 400
        if self.state == 'moving':
            self.change_state('normal')
            self.reset()

        if self.transition_state == 'normal':
            self.offset = [0, 0]
            self.fake_position = None
        elif self.transition_state == 'fake_in':
            self.fake_position = None
            self.change_state('fake_transition_in')
        elif self.transition_state in ('fake_out', 'rescue'):
            self.fake_position = self.unit.position
            self.change_state('fake_transition_out')
        elif self.transition_state == 'fade_in':
            self.fake_position = None
        elif self.transition_state == 'fade_out':
            self.fake_position = self.unit.position
        elif self.transition_state == 'fade_move':
            self.fake_position = self.unit.position
        elif self.transition_state == 'warp_in':
            SOUNDTHREAD.play_sfx('WarpEnd')
            self.fake_position = None
            self.add_warp_anim('warp_in')
            self.add_warp_flowers(reverse=True)
        elif self.transition_state == 'warp_out':
            SOUNDTHREAD.play_sfx('Warp')
            self.fake_position = self.unit.position
            self.add_warp_anim('warp_out')
            self.begin_flicker(self.transition_time, (255, 255, 255))
            self.add_warp_flowers()
        elif self.transition_state == 'warp_move':
            SOUNDTHREAD.play_sfx('Warp')
            self.fake_position = self.unit.position
            self.add_warp_anim('warp_move')
            self.begin_flicker(self.transition_time, (255, 255, 255))
            self.add_warp_flowers()
        elif self.transition_state == 'swoosh_in':
            SOUNDTHREAD.play_sfx('Sword Whoosh')
            self.fake_position = None
            self.add_swoosh_anim()
        elif self.transition_state == 'swoosh_out':
            SOUNDTHREAD.play_sfx('Sword Whoosh')
            self.fake_position = self.unit.position
            self.add_swoosh_anim(reverse=True)
        elif self.transition_state == 'swoosh_move':
            SOUNDTHREAD.play_sfx('Sword Whoosh')
            self.fake_position = self.unit.position
            self.add_swoosh_anim(reverse=True)

    def change_state(self, new_state):
        self.state = new_state
        if self.state in ('combat_attacker', 'combat_anim'):
            self.net_position = game.cursor.position[0] - self.unit.position[0], game.cursor.position[1] - self.unit.position[1]
            self.handle_net_position(self.net_position)
            self.reset()
        elif self.state in ('combat_active'):
            self.image_state = 'active'
        elif self.state == 'combat_defender':
            attacker = game.memory['current_combat'].attacker
            self.net_position = attacker.position[0] - self.unit.position[0], attacker.position[1] - self.unit.position[1]
            self.handle_net_position(self.net_position)
        elif self.state == 'combat_counter':
            attacker = game.memory['current_combat'].defender
            self.net_position = attacker.position[0] - self.unit.position[0], attacker.position[1] - self.unit.position[1]
            self.handle_net_position(self.net_position)
        elif self.state == 'fake_transition_in':
            pos = (self.unit.position[0] + utils.clamp(self.offset[0], -1, 1),
                   self.unit.position[1] + utils.clamp(self.offset[1], -1, 1))
            pos = (pos[0] - self.unit.position[0], pos[1] - self.unit.position[1])
            self.net_position = (-pos[0], -pos[1])
            self.handle_net_position(self.net_position)
        elif self.state == 'fake_transition_out':
            pos = (utils.clamp(self.offset[0], -1, 1),
                   utils.clamp(self.offset[1], -1, 1))
            self.net_position = pos
            self.handle_net_position(self.net_position)
        elif self.state == 'selected':
            self.image_state = 'down'

    def handle_net_position(self, pos):
        if abs(pos[0]) >= abs(pos[1]):
            if pos[0] > 0:
                self.image_state = 'right'
            elif pos[0] < 0:
                self.image_state = 'left'
            else:
                self.image_state = 'down'  # default
        else:
            if pos[1] < 0:
                self.image_state = 'up'
            else:
                self.image_state = 'down'

    def update(self):
        self.update_state()
        self.update_transition()
        self.health_bar.update()

    def update_state(self):
        current_time = engine.get_time()
        if self.state == 'normal':
            if self.unit.finished and not self.unit.is_dying:
                self.image_state = 'gray'
            elif DB.constants.value('initiative') and game.initiative.get_current_unit() != self.unit \
                    and not game.level.roam and self.unit.team == 'player':
                self.image_state = 'gray'
            elif game.cursor.draw_state and game.cursor.position == self.unit.position and self.unit.team == 'player':
                self.image_state = 'active'
            elif game.level and game.level.roam and game.level.roam_unit == self.unit.nid:
                self.image_state = 'passive'
            else:
                self.image_state = 'passive'
        elif self.state == 'combat_anim':
            self.offset[0] = utils.clamp(self.net_position[0], -1, 1) * ANIMATION_COUNTERS.attack_movement_counter.value()
            self.offset[1] = utils.clamp(self.net_position[1], -1, 1) * ANIMATION_COUNTERS.attack_movement_counter.value()
        elif self.state == 'chosen':
            self.net_position = game.cursor.position[0] - self.unit.position[0], game.cursor.position[1] - self.unit.position[1]
            self.handle_net_position(self.net_position)
        elif self.state == 'moving':
            next_position = game.movement.get_next_position(self.unit.nid)
            if not next_position:
                self.set_transition('normal')
                return
            self.net_position = (next_position[0] - self.unit.position[0], next_position[1] - self.unit.position[1])
            last_update = game.movement.get_last_update(self.unit.nid)
            dt = current_time - last_update
            self.offset[0] = int(TILEWIDTH * dt / cf.SETTINGS['unit_speed'] * self.net_position[0])
            self.offset[1] = int(TILEHEIGHT * dt / cf.SETTINGS['unit_speed'] * self.net_position[1])
            self.handle_net_position(self.net_position)
        elif self.state == 'fake_transition_in':
            if self.offset[0] > 0:
                self.offset[0] -= 2
            elif self.offset[0] < 0:
                self.offset[0] += 2
            if self.offset[1] > 0:
                self.offset[1] -= 2
            elif self.offset[1] < 0:
                self.offset[1] += 2

            if self.offset[0] == 0 and self.offset[1] == 0:
                self.set_transition('normal')
                self.change_state('normal')
        elif self.state == 'fake_transition_out':
            if self.offset[0] > 0:
                self.offset[0] += 2
            elif self.offset[0] < 0:
                self.offset[0] -= 2
            if self.offset[1] > 0:
                self.offset[1] += 2
            elif self.offset[1] < 0:
                self.offset[1] -= 2

            if abs(self.offset[0]) > TILEWIDTH or abs(self.offset[1]) > TILEHEIGHT:
                self.set_transition('normal')
                self.change_state('normal')

    def update_transition(self):
        self.transition_counter -= engine.get_delta()
        if self.transition_counter < 0:
            self.transition_counter = 0
            self.fake_position = None
            if self.transition_state in ('fade_out', 'warp_out', 'swoosh_out', 'fade_in', 'warp_in', 'swoosh_in'):
                self.set_transition('normal')
            elif self.transition_state == 'fade_move':
                self.set_transition('fade_in')
            elif self.transition_state == 'warp_move':
                self.set_transition('warp_in')
            elif self.transition_state == 'swoosh_move':
                self.set_transition('swoosh_in')

    def select_frame(self, image, state):
        if self.unit.is_dying:
            return image[0].copy()
        elif state == 'passive' or state == 'gray':
            return image[ANIMATION_COUNTERS.passive_sprite_counter.count].copy()
        elif state == 'active':
            return image[ANIMATION_COUNTERS.active_sprite_counter.count].copy()
        elif state == 'combat_anim':
            return image[ANIMATION_COUNTERS.fast_move_sprite_counter.count].copy()
        else:
            return image[ANIMATION_COUNTERS.move_sprite_counter.count].copy()

    def create_image(self, state):
        if not self.map_sprite:  # This shouldn't happen, but if it does...
            res = RESOURCES.map_sprites[0]
            self.map_sprite = MapSprite(res, self.unit.team)
        if self.transition_state == 'swoosh_in':
            state = 'down'
        image = getattr(self.map_sprite, state)
        image = self.select_frame(image, state)
        return image

    def get_topleft(self, cull_rect):
        if self.fake_position:
            x, y = self.fake_position
        elif self.unit.position:
            x, y = self.unit.position
        left = x * TILEWIDTH + self.offset[0] - cull_rect[0]
        top = y * TILEHEIGHT + self.offset[1] - cull_rect[1]
        return left, top

    def draw(self, surf, cull_rect):
        current_time = engine.get_time()
        image = self.create_image(self.image_state)
        left, top = self.get_topleft(cull_rect)

        anim_top = top

        self.vibrate_counter += 1
        for vibrate in self.vibrate[:]:
            starting_time, total_time = vibrate
            if engine.get_time() >= starting_time:
                if engine.get_time() > starting_time + total_time:
                    self.vibrate.remove(vibrate)
                    continue
                left += (1 if self.vibrate_counter % 2 else -1)

        # Handle transitions
        if self.transition_state in ('fade_out', 'warp_out', 'swoosh_out', 'fade_move', 'warp_move', 'swoosh_move'):
            progress = utils.clamp((self.transition_time - self.transition_counter) / self.transition_time, 0, 1)
            # Distort Vertically
            if self.transition_state in ('swoosh_out', 'swoosh_move'):
                cur_width, cur_height = image.get_width(), image.get_height()
                new_width, new_height = cur_width, int(cur_height * (max(0, progress - 0.4) * 3 + 1))
                extra_height = new_height - cur_height
                image = engine.transform_scale(image, (new_width, new_height))
                top -= extra_height
            image = image_mods.make_translucent(image.convert_alpha(), progress)

        elif self.transition_state in ('fade_in', 'warp_in', 'swoosh_in'):
            progress = utils.clamp((self.transition_time - self.transition_counter) / self.transition_time, 0, 1)
            progress = 1 - progress
            if self.transition_state == 'swoosh_in':
                # Distort Vertically
                cur_width, cur_height = image.get_width(), image.get_height()
                new_width, new_height = cur_width, int(cur_height * (max(0, progress - 0.4) * 3 + 1))
                extra_height = new_height - cur_height
                image = engine.transform_scale(image, (new_width, new_height))
                top -= extra_height
            image = image_mods.make_translucent(image.convert_alpha(), progress)

        for flicker in self.flicker[:]:
            starting_time, total_time, color, direction, fade_out = flicker
            if engine.get_time() >= starting_time:
                if engine.get_time() > starting_time + total_time:
                    self.flicker.remove(flicker)
                    continue
                if fade_out:
                    time_passed = engine.get_time() - starting_time
                    color = tuple((total_time - time_passed) * float(c) // total_time for c in color)
                if direction == 'add':
                    image = image_mods.add_tint(image.convert_alpha(), color)
                elif direction == 'sub':
                    image = image_mods.sub_tint(image.convert_alpha(), color)

        if not self.flicker and game.boundary.draw_flag and self.unit.nid in game.boundary.displaying_units:
            image = image_mods.change_color(image.convert_alpha(), (60, 0, 0))

        if game.action_log.hovered_unit is self.unit:
            length = 200
            if not (current_time // length) % 2:
                diff = current_time % length
                if diff > length // 2:
                    diff = length - diff
                diff = utils.clamp(255. * diff / length * 2, 0, 255)
                color = (0, int(diff * .5), 0)  # Tint image green at magnitude depending on diff
                image = image_mods.change_color(image.convert_alpha(), color)

        for flicker_tint in self.flicker_tint:
            color, period, width = flicker_tint
            diff = utils.model_wave(current_time, period, width)
            diff = utils.clamp(diff, 0, 1)
            color = tuple([int(c * diff) for c in color])
            image = image_mods.add_tint(image.convert_alpha(), color)

        # Each image has (self.image.get_width() - 32)//2 buggers on the
        # left and right of it, to handle any off tile spriting
        topleft = left - max(0, (image.get_width() - 16)//2), top - 24

        if DB.constants.value('pairup') and self.unit.traveler:
            partner = game.get_unit(self.unit.traveler)
            partner_image = partner.sprite.create_image(self.image_state)
            partner_image = partner_image.convert_alpha()
            surf.blit(partner_image, (topleft[0] + 3, topleft[1] - 3))
            gray_version = image_mods.make_gray(partner_image)
            translucent_gray = image_mods.make_translucent(gray_version, 0.25)
            surf.blit(translucent_gray, (topleft[0] + 3, topleft[1] - 3))
            surf.blit(image, (topleft[0] - 3, topleft[1] + 3))
        else:
            surf.blit(image, topleft)

        # Draw animations
        self.animations = {k: v for (k, v) in self.animations.items() if not v.update()}
        for animation in self.animations.values():
            animation.draw(surf, (left, anim_top))

        # Draw personal particles
        self.particles = [ps for ps in self.particles if not ps.remove_me_flag]
        for particle_system in self.particles:
            particle_system.update()
            particle_system.draw(surf, cull_rect[0], cull_rect[1])

        # Draw damage numbers
        for damage_num in self.damage_numbers:
            damage_num.update()
            damage_num.draw(surf, (left + 4, anim_top))
        self.damage_numbers = [d for d in self.damage_numbers if not d.done]

        return surf

    def draw_markers(self, surf, cull_rect):
        # Talk Options
        cur_unit = None
        if game.state.current() == 'free':
            cur_unit = game.cursor.get_hover()
        elif game.state.current() in ('move', 'menu', 'item', 'item_child', 'item_discard',
                                      'weapon_choice', 'spell_choice', 'targeting',
                                      'combat_targeting', 'item_targeting'):
            cur_unit = game.cursor.cur_unit
        elif game.state.current() == 'free_roam':
            cur_unit = game.get_unit(game.level.roam_unit)
        if not cur_unit:
            return surf
        map_markers = SPRITES.get('map_markers')

        left, top = self.get_topleft(cull_rect)
        topleft = (left - 2, top - 14)

        frame = (engine.get_time() // 100) % 8
        offset = [0, 0, 0, 1, 2, 2, 2, 1][frame]
        if game.level.roam and game.state.current() == 'free_roam' and game.state.state[-1].can_talk() and \
                (self.unit.nid, cur_unit.nid) in game.talk_options:
            talk_marker = engine.subsurface(map_markers, (0, 0, 24, 16))
            surf.blit(talk_marker, (topleft[0], topleft[1] + offset))
        if (cur_unit.nid, self.unit.nid) in game.talk_options:
            talk_marker = engine.subsurface(map_markers, (0, 0, 24, 16))
            surf.blit(talk_marker, (topleft[0], topleft[1] + offset))
        elif cur_unit.team == 'player' and skill_system.check_enemy(self.unit, cur_unit):
            warning = False
            for item in item_funcs.get_all_items(self.unit):
                if item_system.warning(self.unit, item, cur_unit):
                    warning = True
                    break
            danger = False
            for item in item_funcs.get_all_items(self.unit):
                if item_system.danger(self.unit, item, cur_unit):
                    danger = True
                    break
            steal = False
            if skill_system.steal_icon(cur_unit, self.unit):
                steal = True
            if warning or danger or steal:
                icon_frame = (engine.get_time() // 500) % sum([warning, danger, steal])
                danger_marker = engine.subsurface(map_markers, (0, 16, 16, 16))
                warning_marker = engine.subsurface(map_markers, (16, 16, 16, 16))
                steal_marker = engine.subsurface(map_markers, (32, 16, 16, 16))
                if icon_frame == 0:
                    if warning:
                        surf.blit(warning_marker, (topleft[0] + 2, topleft[1] + offset))
                    elif danger:
                        surf.blit(danger_marker, (topleft[0] + 2, topleft[1] + offset))
                    else:
                        surf.blit(steal_marker, (topleft[0] + 2, topleft[1] + offset))
                elif icon_frame == 1:
                    if warning:
                        surf.blit(danger_marker, (topleft[0] + 2, topleft[1] + offset))
                    else:
                        surf.blit(steal_marker, (topleft[0] + 2, topleft[1] + offset))
                elif icon_frame == 2:
                    surf.blit(steal_marker, (topleft[0] + 2, topleft[1] + offset))
        return surf

    def check_draw_hp(self) -> bool:
        if self.unit.is_dying or self.unit.dead:
            return False
        if (cf.SETTINGS['hp_map_team'] == 'All') or \
           (cf.SETTINGS['hp_map_team'] == 'Ally' and self.unit.team in ('player', 'other')) or \
           (cf.SETTINGS['hp_map_team'] == 'Enemy' and self.unit.team.startswith('enemy')):
            if (cf.SETTINGS['hp_map_cull'] == 'All') or \
               (cf.SETTINGS['hp_map_cull'] == 'Wounded' and self.unit.get_hp() < equations.parser.hitpoints(self.unit)):
                return True
        return False

    def draw_hp(self, surf, cull_rect):
        current_time = engine.get_time()
        left, top = self.get_topleft(cull_rect)

        if self.check_draw_hp():
            self.health_bar.draw(surf, left, top)

        if 'Boss' in self.unit.tags and self.transition_state == 'normal' and not self.unit.is_dying and \
                self.image_state in ('gray', 'passive') and int((current_time%450) // 150) in (1, 2):
            boss_icon = SPRITES.get('boss_icon')
            surf.blit(boss_icon, (left - 8, top - 8))

        if self.unit.traveler and self.transition_state == 'normal' and \
                not self.unit.is_dying and not DB.constants.value('pairup'):
            if game.get_unit(self.unit.traveler).team == 'player':
                rescue_icon = SPRITES.get('rescue_icon_blue')
            else:
                rescue_icon = SPRITES.get('rescue_icon_green')
            topleft = (left - 8, top - 8)
            surf.blit(rescue_icon, topleft)

        return surf
