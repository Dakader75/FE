from app.resources.resources import RESOURCES
from app.data.database import DB
from app.engine.sound import SOUNDTHREAD
from app.engine.state import MapState
from app.engine.game_state import game
from app.engine import engine, action, skill_system, \
    health_bar, animations, item_system, item_funcs

import logging

class StatusUpkeepState(MapState):
    name = 'status_upkeep'

    def start(self):
        game.cursor.hide()
        if DB.constants.value('initiative'):
            self.units = [game.initiative.get_current_unit()]
        else:
            self.units = [unit for unit in game.units if
                          unit.position and
                          unit.team == game.phase.get_current() and
                          not unit.dead]
        self.cur_unit = None

        self.health_bar = None
        self.animations = []
        self.state = 'processing'
        self.last_update = 0
        self.time_for_change = 0

        self.actions, self.playback = [], []

    def update(self):
        super().update()

        if self.health_bar:
            self.health_bar.update()

        if self.state == 'processing':
            if (not self.cur_unit or not self.cur_unit.position) and self.units:
                self.cur_unit = self.units.pop()

            if self.cur_unit:
                self.actions.clear()
                self.playback.clear()
                if self.cur_unit.traveler and not self.cur_unit.built_guard:
                    action.do(action.IncGauge(self.cur_unit, -self.cur_unit.get_gauge_inc()))
                if self.cur_unit.built_guard:
                    action.do(action.BuiltGuard(self.cur_unit))
                if self.name == 'status_endstep':
                    skill_system.on_endstep(self.actions, self.playback, self.cur_unit)
                    for item in item_funcs.get_all_items(self.cur_unit):
                        item_system.on_endstep(self.actions, self.playback, self.cur_unit, item)
                else:
                    skill_system.on_upkeep(self.actions, self.playback, self.cur_unit)
                    for item in item_funcs.get_all_items(self.cur_unit):
                        item_system.on_upkeep(self.actions, self.playback, self.cur_unit, item)
                if self.playback and self.cur_unit.position:
                    game.cursor.set_pos(self.cur_unit.position)
                    game.state.change('move_camera')
                    self.cur_unit.sprite.change_state('selected')
                    self.health_bar = health_bar.MapCombatInfo('splash', self.cur_unit, None, None, None)
                    self.state = 'start'
                    self.last_update = engine.get_time()
                elif self.actions and self.cur_unit.position:
                    for act in self.actions:
                        action.do(act)
                    self.check_death()
                    self.cur_unit = None
                else:
                    self.cur_unit = None
                    return 'repeat'

            else:
                # About to begin the real phase
                if self.name == 'status_upkeep':
                    action.do(action.MarkPhase(game.phase.get_current()))
                game.state.back()
                return 'repeat'

        elif self.state == 'start':
            if engine.get_time() > self.last_update + 400:
                self.handle_playback(self.playback)
                for act in self.actions:
                    action.do(act)
                self.health_bar.update()  # Force update to get time for change
                self.state = 'running'
                self.last_update = engine.get_time()
                self.time_for_change = self.health_bar.get_time_for_change() + 800

        elif self.state == 'running':
            if engine.get_time() > self.last_update + self.time_for_change:
                self.check_death()
                self.state = 'processing'
                self.cur_unit = None

    def handle_playback(self, playback):
        for brush in playback:
            if brush[0] == 'unit_tint_add':
                color = brush[2]
                brush[1].sprite.begin_flicker(333, color, 'add')
            elif brush[0] == 'unit_tint_sub':
                color = brush[2]
                brush[1].sprite.begin_flicker(333, color, 'sub')
            elif brush[0] == 'cast_sound':
                SOUNDTHREAD.play_sfx(brush[1])
            elif brush[0] == 'hit_sound':
                SOUNDTHREAD.play_sfx(brush[1])
            elif brush[0] == 'cast_anim':
                anim = RESOURCES.animations.get(brush[1])
                pos = game.cursor.position
                if anim:
                    anim = animations.MapAnimation(anim, pos)
                    self.animations.append(anim)

    def check_death(self):
        if self.cur_unit.get_hp() <= 0:
            # Handle death
            game.death.should_die(self.cur_unit)
            game.state.change('dying')
            game.events.trigger('unit_death', self.cur_unit, position=self.cur_unit.position)
            skill_system.on_death(self.cur_unit)
        else:
            self.cur_unit.sprite.change_state('normal')

    def draw(self, surf):
        surf = super().draw(surf)

        self.animations = [anim for anim in self.animations if not anim.update()]
        for anim in self.animations:
            anim.draw(surf, offset=(-game.camera.get_x(), -game.camera.get_y()))

        if self.health_bar:
            self.health_bar.draw(surf)

        return surf
