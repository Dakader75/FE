from app.engine.exp_calculator import ExpCalcType
from app.data.difficulty_modes import GrowthOption
from app.utilities.data import Data


class Constant(object):
    def __init__(self, nid=None, name='', attr=bool, value=False, tag='other'):
        self.nid = nid
        self.name = name
        self.attr = attr
        self.value = value
        self.tag = tag

    def set_value(self, val):
        self.value = val

    def save(self):
        return (self.nid, self.value)

class ConstantCatalog(Data):
    def save(self):
        return [elem.save() for elem in self._list]

    def restore(self, ser_data):
        # Assign each constant with the correct value
        for nid, value in ser_data:
            constant = self.get(nid)
            if constant:
                constant.value = value

    def value(self, val):
        return self.get(val).value

    def total_items(self):
        return self.value('num_items') + self.value('num_accessories')

tags = ['title', 'features', 'inventory', 'line_of_sight', 'leveling', 'ai', 'wexp', 'other', 'hidden']

constants = ConstantCatalog([
    Constant('num_items', "Max number of Items in inventory", int, 5, 'inventory'),
    Constant('num_accessories', "Max number of Accessories in inventory", int, 0, 'inventory'),
    Constant('turnwheel', "Turnwheel", bool, False, 'features'),
    Constant('initiative', "Per Unit Initiative Order", bool, False, 'features'),
    Constant('fatigue', "Fatigue", bool, False, 'features'),
    Constant('reset_fatigue', "Automatically reset fatigue to 0 for benched units", bool, False, 'features'),
    Constant('minimap', "Enable Minimap", bool, True, 'features'),
    Constant('pairup', "Pair Up", bool, False, 'features'),
    Constant('limit_attack_stance', "Limit Attack Stance to first attack only", bool, False, 'features'),
    Constant('attack_stance_only', "Only attack stance allowed", bool, False, 'features'),
    Constant('player_pairup_only', "Only player units can pairup", bool, False, 'features'),
    Constant('lead', "Global Leadership Stars", bool, False, 'features'),
    Constant('bexp', "Bonus Experience", bool, False, 'features'),
    Constant('rd_bexp_lvl', "Always gain 3 stat-ups when using Bonus Exp.", bool, False, 'features'),
    Constant('support', "Supports", bool, False, 'features'),
    Constant('overworld', "Overworld", bool, False, 'features'),
    Constant('unit_notes', "Unit Notes", bool, False, 'features'),
    Constant('crit', "Allow Criticals", bool, True, 'features'),
    Constant('trade', "Can trade items on map", bool, True, 'features'),
    Constant('growth_info', "Can view unit growths in Info Menu", bool, True, 'features'),
    Constant('backpropagate_difficulty_growths', "Apply difficulty bonus growths to past levels", bool, True, 'features'),
    Constant('traveler_time_decrement', "Timed skills applied to traveler units will decrease.", bool, False, 'features'),
    Constant('line_of_sight', "Force items and abilities to obey line of sight rules", bool, False, 'line_of_sight'),
    Constant('aura_los', "Force auras to obey line of sight rules", bool, False, 'line_of_sight'),
    Constant('fog_los', "Fog of War will also be affected by line of sight", bool, False, 'line_of_sight'),
    Constant('ai_fog_of_war', "AI will also be affected by Fog of War", bool, False, 'line_of_sight'),
    Constant('def_double', "Defender can double counterattack", bool, True, 'features'),
    Constant('unit_stats_as_bonus', "Add class stats to non-generic base stats", bool, False, 'leveling'),
    Constant('enemy_leveling', "Method for autoleveling generic units", (*[growth.value for growth in GrowthOption if growth != GrowthOption.PLAYER_CHOICE], "Match"), "Match", 'leveling'),
    Constant('auto_promote', "Units will promote automatically upon reaching max level", bool, False, 'leveling'),
    Constant('promote_level_reset', "Promotion resets level back to 1", bool, True, 'leveling'),
    Constant('class_change_level_reset', "Class Change resets level back to 1", bool, False, 'leveling'),
    Constant('negative_growths', "Negative growth rates will reduce stats", bool, True, 'leveling'),
    Constant('class_change_same_tier', "Class Change only between classes of the same tier", bool, False, 'leveling'),
    Constant('generic_feats', "Generic units will be given random feats when appropriate", bool, False, 'leveling'),
    Constant('min_damage', "Min damage dealt by an attack", int, 0),
    Constant('boss_crit', "Final blow on boss will use critical animation", bool, False, 'aesthetic'),
    Constant('battle_platforms', "Use battle platforms when battle backgrounds are on", bool, True, 'aesthetic'),
    Constant('roam_hide_hp', "Hide hp bars during free roam", bool, False, 'aesthetic'),
    Constant('convoy_on_death', "Items held by dead player units are sent to convoy", bool),
    Constant('repair_shop', "Access the Repair Shop in prep and base", bool, False),
    Constant('sound_room_in_codex', "Can access sound room from Codex menu in base", bool, True),
    Constant('give_and_take', "Units can give a unit after taking a unit", bool),
    Constant('combat_art_category', "Combat Arts get put in their own category in the menu", bool, False),
    Constant('reset_mana', "Mana resets to full for units upon completion of the chapter", bool),
    Constant('double_splash', "When doubling, splash/aoe damage is applied on the second strike as well", bool),
    Constant('num_save_slots', "Number of save slots", int, 3, 'title'),
    Constant('sell_modifier', "Value multiplier when selling an item", float, 0.5, 'inventory'),
    Constant('attack_zero_hit', "Enemy AI attacks even if Hit is 0", bool, True, 'ai'),
    Constant('attack_zero_dam', "Enemy AI attacks even if Damage is 0", bool, True, 'ai'),
    Constant('zero_move', "Show Movement as 0 if AI does not move", bool, False, 'ai'),
    Constant('game_nid', "Game Unique Identifier", str, "LT", 'title'),
    Constant('title', "Game Title", str, "Lex Talionis Game", 'title'),
    Constant('title_particles', "Display particle effect on title screen", bool, True, 'title_screen'),
    Constant('music_main', "Music to play on title screen", 'music', None, 'music'),
    Constant('music_promotion', "Music to play on promotion", 'music', None, 'music'),
    Constant('music_class_change', "Music to play on class change", 'music', None, 'music'),
    Constant('restart_phase_music', "Restart phase music at beginning of new phase", bool, True, 'music'),
    Constant('restart_battle_music', "Restart battle music at beginning of each combat", bool, True, 'music'),
    Constant('kill_wexp', "Kills give double weapon exp", bool, True, 'wexp'),
    Constant('double_wexp', "Each hit when doubling grants weapon exp", bool, True, 'wexp'),
    Constant('miss_wexp', "Gain weapon exp even on miss", bool, True, 'wexp'),
    # Experience constants below
    Constant('exp_curve', "How linear the exp curve is; Higher = less linear", float, 0.035, 'exp'),
    Constant('exp_magnitude', "How much base exp is received for each interaction", float, 10, 'exp'),
    Constant('exp_offset', "Tries to keep player character this many levels above enemies", int, 0, 'exp'),
    Constant('gexp_max', "Maximum exp that can be earned from a hit", float, 30, 'exp'),
    Constant('gexp_min', "Minimum exp that can be earned from a hit", float, 1, 'exp'),
    Constant('gexp_slope', "How sharply exp drops off", float, 0.25, 'exp'),
    Constant('gexp_intercept', "Exp earned by two equal-level units fighting", float, 10, 'exp'),
    Constant('exp_formula', "Which exp formula to use", (calcType.value for calcType in ExpCalcType), ExpCalcType.STANDARD.value, 'exp'),
    Constant('kill_multiplier', "Exp multiplier on kill", float, 3, 'exp'),
    Constant('boss_bonus', "Extra exp for killing a boss", int, 40, 'exp'),
    Constant('min_exp', "Min exp gained in combat", int, 1, 'exp'),
    Constant('default_exp', "Default exp gain", int, 11, 'exp'),
    Constant('heal_curve', "How much to multiply the amount healed by to determine experience gain", float, 0, 'exp'),
    Constant('heal_magnitude', "Added to total exp for healing", int, 0, 'exp'),
    Constant('heal_offset', "Modifies expected healing", int, 11, 'exp'),
    Constant('heal_min', "Min exp gained for healing", int, 11, 'exp'),
    # Hidden constants below
    Constant('dark_sprites', "Use darker map sprites", bool, False, 'hidden'),
    Constant('glancing_hit', "Chance to score a glancing hit", bool, False, 'hidden')])
