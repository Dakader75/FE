from app.constants import WINWIDTH, WINHEIGHT
from app.resources.resources import RESOURCES
from app.engine import engine, image_mods
from app.engine.sprites import SPRITES
from app.utilities import utils

class SpriteBackground():
    def __init__(self, image, fade=True):
        self.counter = 0
        self.image = image

        if fade:
            self.fade = 100
            self.state = "in"
        else:
            self.fade = 0
            self.state = "normal"

    def draw(self, surf):
        if self.state == "in":
            self.fade -= 4
            if self.fade <= 0:
                self.fade = 0
                self.state = "normal"
            bg_surf = image_mods.make_translucent(self.image, self.fade/100.)
        elif self.state == "out":
            self.fade += 4
            bg_surf = image_mods.make_translucent(self.image, self.fade/100.)
            if self.fade >= 100:
                return True
        else:
            bg_surf = self.image

        engine.blit_center(surf, bg_surf)
        return False

    def fade_out(self):
        self.state = 'out'

class PanoramaBackground():
    def __init__(self, panorama, speed=125, loop=True):
        self.counter = 0
        self.panorama = panorama
        if not self.panorama.images:
            for path in self.panorama.get_all_paths():
                self.panorama.images.append(engine.image_load(path))

        self.speed = speed
        self.loop = loop
        self.fade_state = 'normal'
        self.fade_time = 0
        self.transition = 0
        self.bg_black = SPRITES.get('bg_black').copy()

        self.last_update = engine.get_time()

    def update(self):
        if self.fade_state == 'normal' or self.fade_state == 'off':
            pass
        else:
            self.transition += engine.get_delta() / (self.fade_time * 0.5)
            if self.transition >= 1:
                self.transition = 0
                if self.fade_state == 'to_black':
                    self.fade_state = 'to_image'
                elif self.fade_state == 'to_image':
                    self.fade_state = 'normal'
                elif self.fade_state == 'from_image':
                    self.fade_state = 'from_black'
                elif self.fade_state == 'from_black':
                    self.fade_state = 'off'

        # For procession of frames
        if engine.get_time() - self.last_update > self.speed:
            self.counter += 1
            if self.counter >= self.panorama.num_frames:
                self.counter = 0
            self.last_update = engine.get_time()
            if self.counter == 0 and not self.loop:
                return True
        return False

    def _draw(self, surf, image):
        engine.blit_center(surf, image)

    def draw(self, surf):
        image = self.panorama.images[self.counter]
        if self.fade_state == 'normal':
            if image:
                self._draw(surf, image)
        elif self.fade_state == 'off':
            pass
        elif self.fade_state == 'to_black':
            image = image_mods.make_translucent(self.bg_black, 1 - self.transition)
            engine.blit_center(surf, image)
        elif self.fade_state == 'to_image':
            if image:
                self._draw(surf, image)
                image = image_mods.make_translucent(self.bg_black, self.transition)
                engine.blit_center(surf, image)
        elif self.fade_state == 'from_image':
            if image:
                self._draw(surf, image)
                image = image_mods.make_translucent(self.bg_black, 1 - self.transition)
                engine.blit_center(surf, image)
        elif self.fade_state == 'from_black':
            image = image_mods.make_translucent(self.bg_black, self.transition)
            engine.blit_center(surf, image)

        return self.update()

    def set_off(self):
        self.fade_state = "off"
        self.transition = 0

    def set_normal(self):
        self.fade_state = "normal"
        self.transition = 0

    def fade_in(self, time_ms):
        self.fade_state = 'to_black'
        self.fade_time = time_ms
        self.transition = 0

    def fade_out(self, time_ms):
        self.fade_state = 'from_image'
        self.fade_time = time_ms
        self.transition = 0

class ScrollingBackground(PanoramaBackground):
    scroll_speed = 25

    def __init__(self, panorama, speed=125, loop=True):
        super().__init__(panorama, speed, loop)
        self.x_index = 0
        self.scroll_counter = 0
        self.last_scroll_update = 0

    def _draw(self, surf, image):
        # Handle scroll
        current_time = engine.get_time()
        width = image.get_width()
        self.scroll_counter = (current_time / self.scroll_speed) % width
        x_counter = -self.scroll_counter
        while x_counter < WINWIDTH:
            surf.blit(image, (x_counter, 0))
            x_counter += width

class TransitionBackground():
    speed = 25
    fade_speed = int(50 * 16.66)

    def __init__(self, image, fade=True):
        self.counter = 0
        self.image = image

        self.last_update = engine.get_time()
        self.width = image.get_width()
        self.height = image.get_height()
        self.y_movement = True
        self.fade_update = 0

        if fade:
            self.fade = 1
            self.state = 'in'
        else:
            self.fade = 0
            self.state = 'normal'

    def set_y_movement(self, val):
        self.y_movement = val

    def set_update(self, val):
        self.last_update = val

    def update(self):
        current_time = engine.get_time()
        diff = current_time - self.last_update
        self.counter += diff / self.speed
        self.counter %= self.width
        self.last_update = current_time

        if self.state == 'in':
            if not self.fade_update:
                self.fade_update = current_time
            perc = current_time - self.fade_update
            perc = utils.clamp(perc / self.fade_speed, 0, 1)
            self.fade = 1 - perc
            if self.fade <= 0:
                self.fade = 0
                self.state = 'normal'
        return self.state == 'normal'

    def draw(self, surf):
        xindex = -self.counter
        while xindex < WINWIDTH:
            if self.y_movement:
                yindex = -self.counter
            else:
                yindex = 0
            while yindex < WINHEIGHT:
                image = self.image
                if self.fade:
                    image = image_mods.make_translucent(image, self.fade)
                surf.blit(image, (xindex, yindex))
                yindex += self.height
            xindex += self.width

class Foreground():
    def __init__(self):
        self.foreground = None
        self.foreground_frames = 0
        self.fade_out: bool = False
        self.fade_out_frames = 0

    def flash(self, num_frames, fade_out, color=(248, 248, 248)):
        self.foreground_frames = num_frames
        self.foreground = SPRITES.get('bg_black').copy()
        engine.fill(self.foreground, color)
        self.fade_out_frames = fade_out

    def draw(self, surf, blend=False):
        # Screen Flash
        if self.foreground or self.fade_out_frames:
            foreground = self.foreground
            if self.fade_out:
                alpha = 1 - self.foreground_frames / self.fade_out_frames
                foreground = image_mods.make_translucent_blend(self.foreground, alpha * 255)
            # Always additive blend
            engine.blit(surf, foreground, (0, 0), blend=engine.BLEND_RGB_ADD)
            self.foreground_frames -= 1
            # If done
            if self.foreground_frames <= 0:
                if self.fade_out_frames and not self.fade_out:
                    self.foreground_frames = self.fade_out_frames
                    self.fade_out = True
                else:
                    self.fade_out_frames = 0
                    self.foreground_frames = 0
                    self.foreground = None
                    self.fade_out = False

def create_background(bg_name):
    panorama = RESOURCES.panoramas.get(bg_name)
    if not panorama:
        panorama = RESOURCES.panoramas.get('default_background')
    if panorama:
        if panorama.num_frames > 1:
            return PanoramaBackground(panorama)
        else:
            bg = ScrollingBackground(panorama)
            bg.scroll_speed = 50  # Make it move slower
            return bg
    else:
        return None
