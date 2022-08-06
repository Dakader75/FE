from app.engine.fonts import NORMAL_FONT_COLORS
from app.data.item_components import ItemComponent
from app.data.components import Type

class MapHitAddBlend(ItemComponent):
    nid = 'map_hit_add_blend'
    desc = "Changes the color that appears on the unit when hit -- Use to make brighter"
    tag = 'aesthetic'

    expose = Type.Color3
    value = (255, 255, 255)

    def on_hit(self, actions, playback, unit, item, target, target_pos, mode, attack_info):
        playback.append(('unit_tint_add', target, self.value))

class MapHitSubBlend(ItemComponent):
    nid = 'map_hit_sub_blend'
    desc = "Changes the color that appears on the unit when hit -- Use to make darker"
    tag = 'aesthetic'

    expose = Type.Color3
    value = (0, 0, 0)

    def on_hit(self, actions, playback, unit, item, target, target_pos, mode, attack_info):
        playback.append(('unit_tint_sub', target, self.value))

class MapHitSFX(ItemComponent):
    nid = 'map_hit_sfx'
    desc = "Changes the sound the item will make on hit"
    tag = 'aesthetic'

    expose = Type.Sound
    value = 'Attack Hit 1'

    def on_hit(self, actions, playback, unit, item, target, target_pos, mode, attack_info):
        playback.append(('hit_sound', self.value))

class MapCastSFX(ItemComponent):
    nid = 'map_cast_sfx'
    desc = "Adds a sound to the item on cast"
    tag = 'aesthetic'

    expose = Type.Sound
    value = 'Attack Hit 1'

    def on_hit(self, actions, playback, unit, item, target, target_pos, mode, attack_info):
        playback.append(('cast_sound', self.value))

    def on_miss(self, actions, playback, unit, item, target, target_pos, mode, attack_info):
        playback.append(('cast_sound', self.value))

class MapCastAnim(ItemComponent):
    nid = 'map_cast_anim'
    desc = "Adds a map animation to the item on cast"
    tag = 'aesthetic'

    expose = Type.MapAnimation

    def on_hit(self, actions, playback, unit, item, target, target_pos, mode, attack_info):
        playback.append(('cast_anim', self.value))

    def on_miss(self, actions, playback, unit, item, target, target_pos, mode, attack_info):
        playback.append(('cast_anim', self.value))

class BattleCastAnim(ItemComponent):
    nid = 'battle_cast_anim'
    desc = "Set a specific effect animation to the item in battle"
    tag = 'aesthetic'

    expose = Type.EffectAnimation

    def effect_animation(self, unit, item):
        return self.value

class BattleAnimationMusic(ItemComponent):
    nid = 'battle_animation_music'
    desc = "Uses custom battle music"
    tag = 'aesthetic'

    expose = Type.Music
    value = None

    def battle_music(self, unit, item, target, mode):
        return self.value

class PreCombatEffect(ItemComponent):
    nid = 'pre_combat_effect'
    desc = "Item plays a combat effect right before combat."
    tag = 'aesthetic'

    expose = Type.EffectAnimation

    def combat_effect(self, unit, item, target, mode):
        return self.value

class Warning(ItemComponent):
    nid = 'warning'
    desc = "Yellow warning sign appears above wielder's head"
    tag = 'aesthetic'

    def warning(self, unit, item, target) -> bool:
        return True

class EvalWarning(ItemComponent):
    nid = 'eval_warning'
    desc = "Yellow warning sign appears above wielder's head if current unit meets eval"
    tag = 'aesthetic'

    expose = Type.String
    value = 'True'

    def warning(self, unit, item, target) -> bool:
        from app.engine import evaluate
        try:
            val = evaluate.evaluate(self.value, unit, target, item)
            return bool(val)
        except Exception as e:
            print("Could not evaluate %s (%s)" % (self.value, e))
            return False

class TextColor(ItemComponent):
    nid = 'text_color'
    desc = 'Special color for item text.'
    tag = 'aesthetic'

    expose = (Type.MultipleChoice, NORMAL_FONT_COLORS)
    value = 'white'

    def text_color(self, unit, item):
        if self.value not in NORMAL_FONT_COLORS:
            return 'text-white'
        return 'text-' + self.value
