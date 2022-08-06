from app.constants import TILEWIDTH, TILEHEIGHT, WINWIDTH, WINHEIGHT

from app.engine import engine
from app.engine.game_state import game

class MapView():
    def __init__(self):
        self._unit_surf = engine.create_surface((WINWIDTH, WINHEIGHT), transparent=True)

    def draw_units(self, surf, cull_rect, subsurface_rect=None):
        # Surf is always 240x160 WxH
        unit_surf = engine.copy_surface(self._unit_surf)

        # Update all units except the cur unit
        update_units = [unit for unit in game.units if (unit.position or unit.sprite.fake_position)]
        for unit in update_units:
            unit.sprite.update()
            unit.sound.update()

        pos_units = [unit for unit in update_units if unit is not game.cursor.cur_unit and (unit.position or unit.sprite.fake_position)]
        # Only draw units within 2 tiles of cull_rect
        culled_units = [unit for unit in pos_units if unit.sprite.draw_anyway() or
                        (cull_rect[0] - TILEWIDTH*2 < (unit.position or unit.sprite.fake_position)[0] * TILEWIDTH < cull_rect[0] + cull_rect[2] + TILEWIDTH*2 and
                         cull_rect[1] - TILEHEIGHT*2 < (unit.position or unit.sprite.fake_position)[1] * TILEHEIGHT < cull_rect[1] + cull_rect[3] + TILEHEIGHT*2)]
        if game.level_vars.get('_fog_of_war'):
            culled_units = [unit for unit in culled_units if game.board.in_vision(unit.position or unit.sprite.fake_position)]
        draw_units = sorted(culled_units, key=lambda unit: unit.position[1] if unit.position else unit.sprite.fake_position[1])

        topleft = cull_rect[0], cull_rect[1]

        for unit in draw_units:
            unit.sprite.draw(unit_surf, topleft)
            if 'event' not in game.state.state_names():
                unit.sprite.draw_hp(unit_surf, topleft)
        for unit in draw_units:
            unit.sprite.draw_markers(unit_surf, topleft)

        # Draw the movement arrows
        game.cursor.draw_arrows(unit_surf, topleft)

        # Draw the main unit
        cur_unit = game.cursor.cur_unit
        if cur_unit and (cur_unit.position or cur_unit.sprite.fake_position):
            cur_unit.sprite.draw(unit_surf, topleft)
            if 'event' not in game.state.state_names():
                cur_unit.sprite.draw_hp(unit_surf, topleft)
                cur_unit.sprite.draw_markers(unit_surf, topleft)

        if subsurface_rect:
            left, top = (subsurface_rect[0] - cull_rect[0], subsurface_rect[1] - cull_rect[1])
            unit_surf = engine.subsurface(unit_surf, (left, top, subsurface_rect[2], subsurface_rect[3]))
            surf.blit(unit_surf, (left, top))
        else:
            surf.blit(unit_surf, (0, 0))

    def draw(self, camera_cull=None, subsurface_cull=None):
        game.tilemap.update()
        # Camera Cull
        cull_rect = camera_cull
        full_size = game.tilemap.width * TILEWIDTH, game.tilemap.height * TILEHEIGHT

        map_image = game.tilemap.get_full_image(cull_rect)

        surf = engine.copy_surface(map_image)
        surf = surf.convert_alpha()

        surf = game.boundary.draw(surf, full_size, cull_rect)
        surf = game.boundary.draw_fog_of_war(surf, full_size, cull_rect)
        surf = game.highlight.draw(surf, cull_rect)

        game.tilemap.animations = [anim for anim in game.tilemap.animations if not anim.update()]
        for anim in game.tilemap.animations:
            anim.draw(surf, offset=(-game.camera.get_x(), -game.camera.get_y()))

        if subsurface_cull:  # Forced smaller cull rect from animation combat black background
            # Make sure it has a width
            # Make the cull rect even smaller
            if subsurface_cull[2] > 0:
                subsurface_rect = cull_rect[0] + subsurface_cull[0], cull_rect[1] + subsurface_cull[1], subsurface_cull[2], subsurface_cull[3]
                self.draw_units(surf, cull_rect, subsurface_rect)
            else:
                pass # Don't draw units
        else:
            self.draw_units(surf, cull_rect)

        surf = game.cursor.draw(surf, cull_rect)

        for weather in game.tilemap.weather:
            weather.update()
            weather.draw(surf, cull_rect[0], cull_rect[1])

        surf = game.ui_view.draw(surf)
        return surf
