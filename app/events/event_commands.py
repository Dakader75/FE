from enum import Enum
from typing import Callable, List
from app.utilities.data import Prefab

import logging

class Tags(Enum):
    FLOW_CONTROL = 'Flow Control'
    MUSIC_SOUND = 'Music/Sound'
    PORTRAIT = 'Portrait'
    BG_FG = 'Background/Foreground'
    DIALOGUE_TEXT = 'Dialogue/Text'
    CURSOR_CAMERA = 'Cursor/Camera'
    LEVEL_VARS = 'Level-wide Unlocks and Variables'
    GAME_VARS = 'Game-wide Unlocks and Variables'
    TILEMAP = 'Tilemap'
    REGION = 'Region'
    ADD_REMOVE_INTERACT_WITH_UNITS = 'Add/Remove/Interact with Units'
    MODIFY_UNIT_PROPERTIES = 'Modify Unit Properties'
    MODIFY_ITEM_PROPERTIES = 'Modify Item Properties'
    UNIT_GROUPS = 'Unit Groups'
    MISCELLANEOUS = 'Miscellaneous'
    OVERWORLD = 'Overworld'
    HIDDEN = 'Hidden'

class EventCommand(Prefab):
    nid: str = None
    nickname: str = None
    tag: Tags = Tags.HIDDEN
    desc: str = ''

    keyword_names: list = []
    keywords: list = []
    optional_keywords: list = []
    flags: list = []

    values: list = []
    display_values: list = []

    def __init__(self, values: List[str] = None, disp_values: List[str] = None):
        self.values: List[str] = values or []
        self.display_values: List[str] = disp_values or values or []

    def save(self):
        # Don't bother saving display values if they are identical
        if self.display_values == self.values:
            return self.nid, self.values
        else:
            return self.nid, self.values, self.display_values

    def to_plain_text(self) -> str:
        if self.display_values:
            return ';'.join([self.nid] + self.display_values)
        else:
            return ';'.join([self.nid] + self.values)

    def __repr__(self):
        return self.to_plain_text()

class Comment(EventCommand):
    nid = "comment"
    nickname = '#'
    tag = Tags.FLOW_CONTROL
    desc = \
        """
**Lines** starting with '#' will be ignored.
        """
    def to_plain_text(self) -> str:
        if self.values and not self.values[0].startswith('#'):
            self.values[0] = '#' + self.values[0]
        return self.values[0]

class If(EventCommand):
    nid = "if"
    tag = Tags.FLOW_CONTROL
    desc = \
        """
If the *Condition* returns true, the block under this command will be executed.
If it returns false, the script will search for the next **elif**, **else**,
or **end** command before proceeding. If it is not a valid Python expression, the result will be treated as false.

Remember to end your **if** blocks with **end**.

The indentation is not required, but is recommended for organization of the conditional blocks.

Example:

```
if;game.check_dead('Eirika')
    lose_game
elif;game.check_dead('Lyon')
    win_game
else
    u;Eirika
    s;Eirika;Nice!
    r;Eirika
end
```
        """

    keywords = ['Condition']

class Elif(EventCommand):
    nid = "elif"
    tag = Tags.FLOW_CONTROL
    desc = \
        """
Works exactly like the **if** statement, but is called only if the previous **if** or **elif** returned false.

In the following example, the **elif** will only be processed if `if;game.check_dead('Eirika')` return false.

Example:

```
if;game.check_dead('Eirika')
    lose_game
elif;game.check_dead('Lyon')
    win_game
else
    u;Eirika
    s;Eirika;Nice!
    r;Eirika
end
```
        """

    keywords = ['Condition']

class Else(EventCommand):
    nid = "else"
    tag = Tags.FLOW_CONTROL
    desc = \
        """
Defines a block to be executed only if the previous **if** or **elif** returned false.

Example:

```
if;game.check_dead('Eirika')
    lose_game
elif;game.check_dead('Lyon')
    win_game
else
    u;Eirika
    s;Eirika;Nice!
    r;Eirika
end
```
        """

class End(EventCommand):
    nid = "end"
    tag = Tags.FLOW_CONTROL
    desc = \
        """
Ends a conditional block. Refer to the **if** command for more information.
        """

class Break(EventCommand):
    nid = "break"
    tag = Tags.FLOW_CONTROL
    desc = \
        """
Immediately ends the current event.
        """


class Wait(EventCommand):
    nid = "wait"
    tag = Tags.FLOW_CONTROL
    desc = \
        """
Pauses the execution of the script for *Time* milliseconds.

Often used after a scene transition, cursor movement, or reinforcements to give the player a chance to take in the scene.
        """

    keywords = ['Time']

class EndSkip(EventCommand):
    nid = "end_skip"
    tag = Tags.FLOW_CONTROL
    desc = \
        """
If the player was skipping through the event script, stop the skip here.
Used to prevent a single skip from skipping through an entire event.
        """

class Music(EventCommand):
    nid = "music"
    nickname = "m"
    tag = Tags.MUSIC_SOUND
    desc = \
        """
Fades in *Music* over the course of *Time* milliseconds. Fade in defaults to 400 milliseconds.
        """

    keywords = ['Music']
    optional_keywords = ['Time']  # How long to fade in (default 400)

class MusicClear(EventCommand):
    nid = "music_clear"
    tag = Tags.MUSIC_SOUND

    desc = \
        """
Fades out the currently playing song over the course of *Time* milliseconds.
Also clears the entire song stack. Fade out defaults to 400 milliseconds.
        """

    optional_keywords = ['Time']  # How long to fade out

class Sound(EventCommand):
    nid = "sound"
    tag = Tags.MUSIC_SOUND

    desc = \
        """
Plays the *Sound* once.
        """

    keywords = ['Sound']
    optional_keywords = ['Volume']

class ChangeMusic(EventCommand):
    nid = 'change_music'
    tag = Tags.MUSIC_SOUND

    desc = \
        """
Changes the phase theme music. For instance, you could use this command to change the player phase theme halfway through the chapter.
        """

    keywords = ['PhaseMusic', 'Music']

class AddPortrait(EventCommand):
    nid = "add_portrait"
    nickname = "u"
    tag = Tags.PORTRAIT

    desc = \
        """
Adds a portrait to the screen.

Extra flags:

1. *mirror*: Portrait will face opposite expected direction.
2. *low_priority*: Portrait will appear behind all other portraits on the screen.
3. *immediate*: Portrait will not fade in.
4. *no_block*: Portrait will fade in, but will not pause execution of event script while doing so.
        """

    keywords = ['Portrait', 'ScreenPosition']
    optional_keywords = ['Slide', 'ExpressionList', 'VerticalScreenPosition']
    flags = ["mirror", "low_priority", "immediate", "no_block"]

class MultiAddPortrait(EventCommand):
    nid = "multi_add_portrait"
    nickname = "uu"
    tag = Tags.PORTRAIT

    desc = \
        """
Adds more than one portrait to the screen at the same time. Accepts 2-4 portraits and their associated *ScreenPosition* as input.
        """

    keywords = ['Portrait', 'ScreenPosition', 'Portrait', 'ScreenPosition']
    optional_keywords = ['Portrait', 'ScreenPosition', 'Portrait', 'ScreenPosition']

class RemovePortrait(EventCommand):
    nid = "remove_portrait"
    nickname = "r"
    tag = Tags.PORTRAIT

    desc = \
        """
Removes a portrait from the screen.

Extra flags:

1. *immediate*: Portrait will disappear instantly and will not fade out.
2. *no_block*: Portrait will fade out, but will not pause execution of event script while doing so.
        """

    keywords = ['Portrait']
    flags = ["immediate", "no_block"]

class MultiRemovePortrait(EventCommand):
    nid = "multi_remove_portrait"
    nickname = "rr"
    tag = Tags.PORTRAIT

    desc = \
        """
Removes multiple portraits from the screen simultaneously.
        """

    keywords = ['Portrait', 'Portrait']
    optional_keywords = ['Portrait', 'Portrait']

class MovePortrait(EventCommand):
    nid = "move_portrait"
    tag = Tags.PORTRAIT

    desc = \
        """
Causes a portrait to "walk" from one screen position to another.

Extra flags:

1. *immediate*: Portrait will teleport instantly to the new position.
2. *no_block*: Portrait will walk as normal, but will not pause execution of event script while doing so.
        """

    keywords = ['Portrait', 'ScreenPosition']
    flags = ["immediate", "no_block"]

class BopPortrait(EventCommand):
    nid = "bop_portrait"
    nickname = "bop"
    tag = Tags.PORTRAIT

    desc = \
        """
Causes a portrait to briefly bob up and down. Often used to illustrate a surprised or shocked reaction.
If the *no_block* flag is set, portrait bopping will not pause execution of event script.
        """

    keywords = ['Portrait']
    flags = ["no_block"]

class Expression(EventCommand):
    nid = "expression"
    nickname = "e"
    tag = Tags.PORTRAIT

    desc = \
        """
Changes a portrait's facial expression.
        """

    keywords = ['Portrait', 'ExpressionList']

class Speak(EventCommand):
    nid = "speak"
    nickname = "s"
    tag = Tags.DIALOGUE_TEXT

    desc = \
        """
Causes the *Speaker* to speak some *Text*. If *Speaker* is a portrait nid that is currently displayed on screen,
*Text* will appear in a speech bubble from that portrait. If *Speaker* is left blank,
*Text* will appear in a box with no name label. For all other values of *Speaker*,
*Text* will appear in a box with the *Speaker* as the name label.

The pipe | symbol can be used within the *Text* body to insert a line break.

The *DialogVariant* optional keyword changes how the text is displayed graphically:

1. *thought_bubble*: causes the text to be in a cloud-like thought bubble instead of a speech bubble.
2. *noir*: causes the speech bubble to be dark grey with white text.
3. *hint*: causes the text to be displayed in a hint box similar to tutorial information.
4. *narration*: causes the text to be displayed in a blue narration box at the bottom of the screen. No name label will be displayed.
5. *narration_top*: same as *narration* but causes the text box to be displayed at the top of the screen.

Extra flags:

1. *low_priority*: The speaker's portrait will not be moved in front of other overlapping portraits.
        """

    keywords = ['Speaker', 'Text']
    optional_keywords = ['ScreenPosition', 'Width', 'DialogVariant']
    flags = ['low_priority']

class Narrate(EventCommand):
    nid = "narrate"
    tag = Tags.DIALOGUE_TEXT

    desc = \
        """
Causes text to be displayed in the whole-screen narration frame.
Before using this command, the narration frame must be phased in using **toggle_narration_mode**.

Extra flags:

1. *no_block*: The event script will continue to execute while the narration text is being displayed.
        """

    keywords = ['Speaker', 'Text']
    flags = ['no_block']

class Transition(EventCommand):
    nid = "transition"
    nickname = "t"
    tag = Tags.BG_FG

    desc = \
        """
If a scene is currently displayed, it is faded out to a black screen.
The next use of this function will fade the scene back into view.
The optional *Speed* and *Color3* keywords control the speed and color of the transition.
        """

    optional_keywords = ['Direction', 'Speed', 'Color3']

class Background(EventCommand):
    # Also does remove background
    nid = "change_background"
    nickname = "b"
    tag = Tags.BG_FG

    desc = \
        """
Changes the dialogue scene's background image to *Panorama*. If no *Panorama* is specified,
the current background is removed without being replaced.
Displayed portraits are also removed unless the *keep_portraits* flag is set.
        """

    optional_keywords = ['Panorama']
    flags = ["keep_portraits"]

class DispCursor(EventCommand):
    nid = "disp_cursor"
    tag = Tags.CURSOR_CAMERA

    desc = \
        """
Toggles whether the game's cursor is displayed.
        """

    keywords = ["Bool"]

class MoveCursor(EventCommand):
    nid = "move_cursor"
    nickname = "set_cursor"
    tag = Tags.CURSOR_CAMERA

    desc = \
        """
Moves the cursor to the map coordinate given by *Position*. The optional *Speed* keyword changes how fast the cursor moves.

Extra flags:

1. *immediate*: Causes the cursor to immediately jump to the target coordinates.
        """

    keywords = ["Position"]
    optional_keywords = ['Speed']
    flags = ["immediate"]


class CenterCursor(EventCommand):
    nid = "center_cursor"
    tag = Tags.CURSOR_CAMERA

    desc = \
        """
Similar to **move_cursor** except that it attempts to center the screen on the new cursor position to the greatest extent possible.
        """

    keywords = ["Position"]
    optional_keywords = ['Speed']
    flags = ["immediate"]

class FlickerCursor(EventCommand):
    nid = 'flicker_cursor'
    nickname = 'highlight'
    tag = Tags.CURSOR_CAMERA

    desc = \
        """
Causes the cursor to briefly blink on and off at the indicated *Position*.
        """

    keywords = ["Position"]
    flags = ["immediate"]

class GameVar(EventCommand):
    nid = 'game_var'
    tag = Tags.GAME_VARS

    desc = \
        """
Creates a game variable or changes its value. Game variables are preserved between chapters.
The *Nid* is the variable's identifier, and the *Condition* is the value that is given to the variable.
*Condition* can be a number or a Python expression.
        """

    keywords = ["Nid", "Condition"]

class IncGameVar(EventCommand):
    nid = 'inc_game_var'
    tag = Tags.GAME_VARS

    desc = \
        """
Increments a game variable by one, or by a Python expression provided using the *Condition* optional keyword.
        """

    keywords = ["Nid"]
    optional_keywords = ["Condition"]

class LevelVar(EventCommand):
    nid = 'level_var'
    tag = Tags.LEVEL_VARS

    desc = \
        """
Creates a level-specific variable or changes its value.
Level variables are deleted upon completion of a chapter.
The *Nid* is the variable's identifier, and the *Condition* is the
value that is given to the variable. *Condition* can be a number or a Python expression.
        """

    keywords = ["Nid", "Condition"]

class IncLevelVar(EventCommand):
    nid = 'inc_level_var'
    tag = Tags.LEVEL_VARS

    desc = \
        """
Increments a level variable by one, or by a Python expression provided using the *Condition* optional keyword.
        """

    keywords = ["Nid"]
    optional_keywords = ["Condition"]

class WinGame(EventCommand):
    nid = 'win_game'
    tag = Tags.LEVEL_VARS

    desc = \
        """
Ends the current chapter in victory.
        """

class LoseGame(EventCommand):
    nid = 'lose_game'
    tag = Tags.LEVEL_VARS

    desc = \
        """
Ends the current chapter in defeat. The game over screen will be displayed.
        """

class ActivateTurnwheel(EventCommand):
    nid = 'activate_turnwheel'
    tag = Tags.MISCELLANEOUS

    desc = \
        """
Brings up the turnwheel interface to allow the player to roll back turns.
The optional *bool* keyword controls whether the player is forced to turn back time,
or whether it's optional (default = true = forced to).
        """

    # Whether to force the player to move the turnwheel back
    # defaults to true
    optional_keywords = ['Bool']

class BattleSave(EventCommand):
    nid = 'battle_save'
    tag = Tags.MISCELLANEOUS

    desc = \
        """
The player is given the option of saving the game mid-battle.
This can be useful if the player chose Classic Mode,
as he or she would otherwise only be able to suspend and not save mid-battle.
        """

class ChangeTilemap(EventCommand):
    nid = 'change_tilemap'
    tag = Tags.TILEMAP

    desc = \
        """
Changes the current map to a different layout (*Tilemap*).
If the *reload* flag is set, the currently deployed units
will be placed at their same positions on the new tilemap.
If a *PositionOffset* is given, the units will be reloaded but shifted by +x,+y.

Instead of reloading the units from their current positions,
a second *Tilemap* optional keyword can be specified.
In this case, unit deployment will be loaded from that tilemap's data instead of from the current map.

Note that this command cannot be turnwheel'ed.
Players attempting to use the turnwheel will find that
they cannot turn time back past the point when this command was executed.
        """

    # How much to offset placed units by
    # Which tilemap to load the unit positions from
    optional_keywords = ["Tilemap", "PositionOffset", "Tilemap"]
    flags = ["reload"]  # Should place units in previously recorded positions

class LoadUnit(EventCommand):
    nid = 'load_unit'
    tag = Tags.ADD_REMOVE_INTERACT_WITH_UNITS

    desc = \
        """
Loads a unique (non-generic) unit from memory. This does not place the unit on the map. If the unit already exists in the game's memory, this command will do nothing.

Optionally, the loaded unit can be assigned to a *Team* and given an *AI* preset. If not specified, defaults of Player team and no AI script are applied.
        """

    keywords = ["UniqueUnit"]
    optional_keywords = ["Team", "AI"]

class MakeGeneric(EventCommand):
    nid = 'make_generic'
    tag = Tags.ADD_REMOVE_INTERACT_WITH_UNITS

    desc = \
        """
Fabricates a new generic unit from scratch. This does not place instances of the new unit on the map.
The required keywords are in the following order: nid to be given to the unit (*String*),
the unit's class (*Klass*), the unit's level (*String*), and the unit's *Team*.

Several optional keywords can also be provided to further modify the new unit:
*AI* defines an AI preset to be given to the unit, *Faction* assignes the unit
to one of the factions for the chapter, the unit can be given an animation variant
(*String*), and finally the unit can be given an inventory of items (*ItemList*).
        """

    # Nid, class, level, team, ai, faction, anim variant
    keywords = ["String", "Klass", "String", "Team"]
    optional_keywords = ["AI", "Faction", "String", "ItemList"]

class CreateUnit(EventCommand):
    nid = 'create_unit'
    tag = Tags.ADD_REMOVE_INTERACT_WITH_UNITS

    desc = \
        """
Creates a new instance of a unit and, optionally, places it on the map.
*Unit* points to the unit template to be used. A new nid can be assigned using *String* (can be empty: '').

Several optional keywords can be provided to modify the unit and/or place it on the map.

Optional keywords can be specified to place the unit on the map.
The *String* value sets the unit's nid, if a specific nid is desired.
The *Condition* value, if provided, sets the unit's level.
The *Position* value indicates the map coordinates that the unit will be placed at.
*EntryType* defines which placement animation is used.
Finally, *Placement* defines the behavior that occurs if the chosen map position is already occupied.
        """

    # Unit template
    keywords = ["Unit"]
    # New unit nid (which can be ''), Unit level, position, entrytype, placement
    optional_keywords = ["String", "Condition", "Position", "EntryType", "Placement"]

class AddUnit(EventCommand):
    nid = 'add_unit'
    nickname = 'add'
    tag = Tags.ADD_REMOVE_INTERACT_WITH_UNITS

    desc = \
        """
Places *Unit* on the map. The unit must be in the chapter's data or otherwise have been loaded into memory (see **load_unit** or **make_generic**).

The optional keywords define how the unit is placed. *Position* indicates the map coordinates that the unit will be placed at.
*EntryType* defines which placement animation is used. *Placement* defines the behavior that occurs if the chosen map position is already occupied.
If no placement information is provided, the unit will attempt to be placed at its starting location from the chapter data (if any).
        """

    keywords = ["Unit"]
    optional_keywords = ["Position", "EntryType", "Placement"]

class MoveUnit(EventCommand):
    nid = 'move_unit'
    nickname = 'move'
    tag = Tags.ADD_REMOVE_INTERACT_WITH_UNITS

    desc = \
        """
Causes *Unit* to move to a new position on the map.

The optional keywords define how the movement occurs.
*Position* indicates the target map coordinates. *MovementType* selects the method of movement.
*Placement* defines the behavior that occurs if the chosen map position is already occupied.

The *no_block* optional flag causes the event script to continue to execute while the unit is moving.
The *no_follow* flag prevents the camera from tracking the unit as it moves.
        """

    keywords = ["Unit"]
    optional_keywords = ["Position", "MovementType", "Placement"]
    flags = ['no_block', 'no_follow']

class RemoveUnit(EventCommand):
    nid = 'remove_unit'
    nickname = 'remove'
    tag = Tags.ADD_REMOVE_INTERACT_WITH_UNITS

    desc = \
        """
Removes *Unit* from the map. The optional *RemoveType* keyword specifies the method of removal.
        """

    keywords = ["Unit"]
    optional_keywords = ["RemoveType"]

class KillUnit(EventCommand):
    nid = 'kill_unit'
    nickname = 'kill'
    tag = Tags.ADD_REMOVE_INTERACT_WITH_UNITS

    desc = \
        """
Causes *Unit* to be removed from the map and marked as dead.
The *immediate* flag causes this to occur instantly without the normal map death animation.
        """

    keywords = ["Unit"]
    flags = ['immediate']

class RemoveAllUnits(EventCommand):
    nid = 'remove_all_units'
    tag = Tags.ADD_REMOVE_INTERACT_WITH_UNITS

    desc = \
        """
Removes all units from the map.
        """

class RemoveAllEnemies(EventCommand):
    nid = 'remove_all_enemies'
    tag = Tags.ADD_REMOVE_INTERACT_WITH_UNITS

    desc = \
        """
Removes all units in the enemy team from the map.
        """

class InteractUnit(EventCommand):
    nid = 'interact_unit'
    nickname = 'interact'
    tag = Tags.ADD_REMOVE_INTERACT_WITH_UNITS

    desc = \
        """
Initiates a battle between two units.
A *CombatScript* can optionally be provided to ensure a pre-set outcome to the battle.
*Ability* can be used to specify which item or ability the attacker will use.
        """

    keywords = ["Unit", "Unit"]
    optional_keywords = ["CombatScript", "Ability"]

class SetCurrentHP(EventCommand):
    nid = 'set_current_hp'
    tag = Tags.MODIFY_UNIT_PROPERTIES

    desc = \
        """
Sets *Unit*'s hit points to *PositiveInteger*.
        """

    keywords = ["Unit", "PositiveInteger"]

class SetCurrentMana(EventCommand):
    nid = 'set_current_mana'
    tag = Tags.MODIFY_UNIT_PROPERTIES

    desc = \
        """
Sets *Unit*'s mana to *PositiveInteger*.
        """

    keywords = ["Unit", "PositiveInteger"]

class AddFatigue(EventCommand):
    nid = 'add_fatigue'
    tag = Tags.MODIFY_UNIT_PROPERTIES

    desc = \
        """
Modify *Unit*'s current fatigue level by *Integer*.
        """
    keywords = ["Unit", "Integer"]

class SetField(EventCommand):
    nid = 'set_unit_field'
    tag = Tags.MODIFY_UNIT_PROPERTIES

    desc = \
    """
Set arbitrary property on _Unit_. **Note**: This cannot be used to set unit stats; if you try, you will simply set
a property called, for example, "STR", that has nothing to do with the unit's stats. This is for enabling unit-level
vars that are persisted across events.

If the flag `increment_mode` is supplied, this will add the value to the existing value instead instead of setting it.
Please try to avoid using `increment_mode` with non-numerical fields. That would erase your field and then nobody will be happy.
    """
    keyword_names = ['unit_nid', 'key', 'value']
    keywords = ['Unit', 'String', 'String']
    flags = ['increment_mode']

class Resurrect(EventCommand):
    nid = 'resurrect'
    tag = Tags.ADD_REMOVE_INTERACT_WITH_UNITS

    desc = \
        """
Brings a dead unit back to life. This does not place the unit on the map.
        """

    keywords = ["GlobalUnit"]

class Reset(EventCommand):
    nid = 'reset'
    tag = Tags.MODIFY_UNIT_PROPERTIES

    desc = \
        """
Refreshes the unit so that it can act again this turn.
        """

    keywords = ["Unit"]

class HasAttacked(EventCommand):
    nid = 'has_attacked'
    tag = Tags.MODIFY_UNIT_PROPERTIES

    desc = \
        """
Sets the unit's state as having already attacked this turn.
        """

    keywords = ["Unit"]

class HasTraded(EventCommand):
    nid = 'has_traded'
    tag = Tags.MODIFY_UNIT_PROPERTIES

    desc = \
        """
Sets the unit's state as having already traded this turn. The unit can still attack, but can no longer move.
        """

    keywords = ['Unit']

class AddGroup(EventCommand):
    nid = 'add_group'
    tag = Tags.UNIT_GROUPS

    desc = \
        """
Adds a unit group to the map. This will use the group's starting position data in the chapter by default.
Alternatively, a separate unit group nid can be provided as *StartingGroup* to cause the units to be placed at this other group's starting position.
*EntryType* selects the method of placement, and *Placement* defines the behavior that occurs if any of the chosen map positions are already occupied.

If the *create* flag is set, a copy of each unit will be created and deployed instead of using the unit itself.
        """

    keywords = ["Group"]
    optional_keywords = ["StartingGroup", "EntryType", "Placement"]
    flags = ["create"]

class SpawnGroup(EventCommand):
    nid = 'spawn_group'
    tag = Tags.UNIT_GROUPS

    desc = \
        """
Causes a unit *Group* to arrive on the map from one of the *CardinalDirection*s.
*EntryType* selects the method of placement, and *Placement* defines the behavior that occurs if any of the chosen map positions are already occupied.

If the *create* flag is set, a copy of each unit will be created and deployed instead of using the unit itself.
*no_block* causes the script to continue executing while the units appear on the map. *no_follow* prevents the camera from focusing on the point where the units enter the map.
        """

    keywords = ["Group", "CardinalDirection", "StartingGroup"]
    optional_keywords = ["EntryType", "Placement"]
    flags = ["create", "no_block", 'no_follow']

class MoveGroup(EventCommand):
    nid = 'move_group'
    nickname = 'morph_group'
    tag = Tags.UNIT_GROUPS

    desc = \
        """
Causes a unit *Group* to move to a new set of map positions specified using a different group's nid (*StartingGroup*).
*MovementType* selects the method of movement, and *Placement* defines the behavior that occurs if any of the chosen map positions are already occupied.

If the *no_block* flag is set, the script will continue to execute while the units move.
*no_follow* prevents the camera from following the movement of the units.
        """

    keywords = ["Group", "StartingGroup"]
    optional_keywords = ["MovementType", "Placement"]
    flags = ['no_block', 'no_follow']

class RemoveGroup(EventCommand):
    nid = 'remove_group'
    tag = Tags.UNIT_GROUPS

    desc = \
        """
Removes a unit *Group* from the map. *RemoveType* selects the method of removal.
        """

    keywords = ["Group"]
    optional_keywords = ["RemoveType"]

class GiveItem(EventCommand):
    nid = 'give_item'
    tag = Tags.MODIFY_UNIT_PROPERTIES

    desc = \
        """
Gives a new copy of *Item* to *GlobalUnit*. If the *no_banner* flag is set, there will not be a banner announcing that "X unit got a Y item!".

If the unit's inventory is full, the player will be given the option of which item to send to the convoy.
If the *no_choice* flag is set, the new item will be automatically sent to the convoy in this case without prompting the player.
The *droppable* flag determines whether the item is set as a "droppable" item (generally only given to enemy units).
        """

    keywords = ["GlobalUnit", "Item"]
    flags = ['no_banner', 'no_choice', 'droppable']

class RemoveItem(EventCommand):
    nid = 'remove_item'
    tag = Tags.MODIFY_UNIT_PROPERTIES

    desc = \
        """
Removes *Item* from the inventory of *GlobalUnit*.
If the *no_banner* flag is set, there will not be a banner announcing that "X unit lost a Y item!".
        """

    keywords = ["GlobalUnit", "Item"]
    flags = ['no_banner']

class ChangeItemName(EventCommand):
    nid = 'change_item_name'
    tag = Tags.MODIFY_ITEM_PROPERTIES

    desc = \
        """
Changes the name of *Item* in the inventory of *GlobalUnit* to *Text*.
        """

    keywords = ["GlobalUnit", "Item", "Text"]

class ChangeItemDesc(EventCommand):
    nid = 'change_item_desc'
    tag = Tags.MODIFY_ITEM_PROPERTIES

    desc = \
        """
Changes the description of *Item* in the inventory of *GlobalUnit* to *Text*.
        """

    keywords = ["GlobalUnit", "Item", "Text"]

class AddItemToMultiItem(EventCommand):
    nid = 'add_item_to_multiitem'
    tag = Tags.MODIFY_ITEM_PROPERTIES

    desc = \
        """
Adds a new item to an existing multi-item in the inventory of *GlobalUnit*.
The first *Item* specifies the multi-item, and the second *Item* specifies the nid of the item to be added.
        """

    keywords = ["GlobalUnit", "Item", "Item"]

class RemoveItemFromMultiItem(EventCommand):
    nid = 'remove_item_from_multiitem'
    tag = Tags.MODIFY_ITEM_PROPERTIES

    desc = \
        """
Removes an item from an existing multi-item in the inventory of *GlobalUnit*.
The first *Item* specifies the multi-item, and the second *Item* specifies the nid of the item to be removed.
        """

    keywords = ["GlobalUnit", "Item", "Item"]

class GiveMoney(EventCommand):
    nid = 'give_money'
    tag = Tags.GAME_VARS

    desc = \
        """
Gives *Integer* amount of money to the indicated *Party*.
If *Party* is not specified, the player's current party will be used.
If the *no_banner* flag is set, there will not be a banner announcing that the player "received X gold!".
        """

    keywords = ["Integer"]
    optional_keywords = ["Party"]
    flags = ['no_banner']

class GiveBexp(EventCommand):
    nid = 'give_bexp'
    tag = Tags.GAME_VARS

    desc = \
        """
Gives bonus experience of the amount defined by *Condition* (can just be a number) to the indicated *Party*.
If *Party* is not specified, the player's current party will be used.
The optional *Text* keyword specifies what text is shown to the player in the banner.
If *Text* is not specified, the banner will state "Got X BEXP".
If the *no_banner* flag is set, the player will not be informed that the bonus experience was awarded.
        """

    keywords = ["Condition"]
    optional_keywords = ["Party", "Text"]
    flags = ['no_banner']

class GiveExp(EventCommand):
    nid = 'give_exp'
    tag = Tags.MODIFY_UNIT_PROPERTIES

    desc = \
        """
Gives a *PositiveInteger* amount of experience to *GlobalUnit*.
        """

    keywords = ["GlobalUnit", "PositiveInteger"]

class SetExp(EventCommand):
    nid = 'set_exp'
    tag = Tags.MODIFY_UNIT_PROPERTIES

    desc = \
        """
Sets *GlobalUnit*'s current experience amount to *PositiveInteger*.
        """

    keywords = ["GlobalUnit", "PositiveInteger"]

class GiveWexp(EventCommand):
    nid = 'give_wexp'
    tag = Tags.MODIFY_UNIT_PROPERTIES

    desc = \
        """
Gives a *PositiveInteger* amount of weapon experience in *WeaponType* to *GlobalUnit*. If the *no_banner* flag is set, the player will not be informed that weapon experience was awarded.
        """

    keywords = ["GlobalUnit", "WeaponType", "Integer"]
    flags = ['no_banner']

class GiveSkill(EventCommand):
    nid = 'give_skill'
    tag = Tags.MODIFY_UNIT_PROPERTIES

    desc = \
        """
*GlobalUnit* gains *Skill*. If the *no_banner* flag is set, the player will not be informed of this.
        """

    keywords = ["GlobalUnit", "Skill"]
    flags = ['no_banner']

class RemoveSkill(EventCommand):
    nid = 'remove_skill'
    tag = Tags.MODIFY_UNIT_PROPERTIES

    desc = \
        """
*GlobalUnit* loses *Skill*. If the *no_banner* flag is set, the player will not be informed of this.
        """

    keywords = ["GlobalUnit", "Skill"]
    flags = ['no_banner']

class ChangeAI(EventCommand):
    nid = 'change_ai'
    tag = Tags.MODIFY_UNIT_PROPERTIES

    desc = \
        """
Sets the *AI* used by *GlobalUnit*.
        """

    keywords = ["GlobalUnit", "AI"]

class ChangeParty(EventCommand):
    nid = 'change_party'
    tag = Tags.MODIFY_UNIT_PROPERTIES

    desc = \
        """
Changes the *Party* of *GlobalUnit*. Used for games in which the player's units are divided into multiple parties.
        """

    keywords = ["GlobalUnit", "Party"]

class ChangeTeam(EventCommand):
    nid = 'change_team'
    tag = Tags.MODIFY_UNIT_PROPERTIES

    desc = \
        """
Changes *GlobalUnit*'s *Team*. For example, this can recruit an enemy unit to the player's team in a Talk event script.
        """

    keywords = ["GlobalUnit", "Team"]

class ChangePortrait(EventCommand):
    nid = 'change_portrait'
    tag = Tags.MODIFY_UNIT_PROPERTIES

    desc = \
        """
Changes *GlobalUnit*'s portrait to the one specified by *PortraitNid*.
        """

    keywords = ["GlobalUnit", "PortraitNid"]

class ChangeStats(EventCommand):
    nid = 'change_stats'
    tag = Tags.MODIFY_UNIT_PROPERTIES

    desc = \
        """
Changes the stats (STR, SKL, etc.) of *GlobalUnit*. The *StatList* defines the changes to be applied. This will display the unit's stat changes similarly to a level-up unless the *immediate* flag is set.
        """

    keywords = ["GlobalUnit", "StatList"]
    flags = ['immediate']

class SetStats(EventCommand):
    nid = 'set_stats'
    tag = Tags.MODIFY_UNIT_PROPERTIES

    desc = \
        """
Sets the stats (STR, SKL, etc.) of *GlobalUnit* to specific values defined in *StatList*. This will display the unit's stat changes similarly to a level-up unless the *immediate* flag is set.
        """

    keywords = ["GlobalUnit", "StatList"]
    flags = ['immediate']

class AutolevelTo(EventCommand):
    nid = 'autolevel_to'
    tag = Tags.MODIFY_UNIT_PROPERTIES

    desc = \
        """
Levels *GlobalUnit* up to a level specified by *Condition*. If *Condition* is less than the unit's current level, this does nothing.

If the *hidden* flag is set, the unit still gains the effects of the indicated level-ups, but its actual level is not incremented. In other words, the unit gets more powerful but remains at the same level.
        """

    # Second argument is level that is eval'd
    keywords = ["GlobalUnit", "Condition"]
    # Whether to actually change the unit's level
    flags = ["hidden"]

class SetModeAutolevels(EventCommand):
    nid = 'set_mode_autolevels'
    tag = Tags.GAME_VARS

    desc = \
        """
Changes the number of additional levels that enemy units gain from the difficulty mode setting. This can be used to grant a higher number of bonus levels to enemies later in the game to maintain a resonable difficulty curve. *Condition* specifies the number of levels to be granted. If the *hidden* flag is set, enemy units will still gain the effects of the indicated level-ups, but their actual level is not incremented. In other words, the units get more powerful but remains at the same level.
        """

    keywords = ["Condition"]
    # Whether to actually change the unit's level
    flags = ["hidden"]

class Promote(EventCommand):
    nid = 'promote'
    tag = Tags.MODIFY_UNIT_PROPERTIES

    desc = \
        """
Promotes *GlobalUnit* into a specified class (*Klass*) or, if no *Klass* is given, the unit promotes as normal using its promotion data.
        """

    keywords = ["GlobalUnit"]
    optional_keywords = ["Klass"]

class ChangeClass(EventCommand):
    nid = 'change_class'
    tag = Tags.MODIFY_UNIT_PROPERTIES

    desc = \
        """
Changes *GlobalUnit* into a specified class (*Klass*) or, if no *Klass* is given, the unit class changes as normal using its alternative class data.
If the *silent* flag is given, the unit will change class immediately into the specified class (*Klass*).
        """

    keywords = ["GlobalUnit"]
    optional_keywords = ["Klass"]
    flags = ["silent"]

class AddTag(EventCommand):
    nid = 'add_tag'
    tag = Tags.MODIFY_UNIT_PROPERTIES

    desc = \
        """
Adds a *Tag* to *GlobalUnit*. Examples would include "Lord", "Armor", "Boss", etc.
        """

    keywords = ["GlobalUnit", "Tag"]

class RemoveTag(EventCommand):
    nid = 'remove_tag'
    tag = Tags.MODIFY_UNIT_PROPERTIES

    desc = \
        """
Removes a *Tag* from *GlobalUnit*.
        """

    keywords = ["GlobalUnit", "Tag"]

class AddTalk(EventCommand):
    nid = 'add_talk'
    tag = Tags.LEVEL_VARS

    desc = \
        """
Adds the ability for the two indicated units to "Talk" in the current chapter. The first *Unit* will be able to initiate conversation with the second *Unit*.
        """

    keywords = ["Unit", "Unit"]

class RemoveTalk(EventCommand):
    nid = 'remove_talk'
    tag = Tags.LEVEL_VARS

    desc = \
        """
Removes the ability for the two indicated units to "Talk" in the current chapter. You probably want to use this after the dialogue scene between the two units.
        """

    keywords = ["Unit", "Unit"]

class AddLore(EventCommand):
    nid = 'add_lore'
    nickname = 'unlock_lore'

    desc = \
        """
Unlocks the player's ability to read the specified game *Lore* entry.
        """

    tag = Tags.GAME_VARS

    keywords = ["Lore"]

class RemoveLore(EventCommand):
    nid = 'remove_lore'
    tag = Tags.GAME_VARS

    desc = \
        """
Removes the player's ability to read the specified game *Lore* entry.
        """

    keywords = ["Lore"]

class AddBaseConvo(EventCommand):
    nid = 'add_base_convo'
    tag = Tags.LEVEL_VARS

    desc = \
        """
Unlocks a base conversation specified by *Text* for later viewing by the player.
        """

    keywords = ["Text"]

class IgnoreBaseConvo(EventCommand):
    nid = 'ignore_base_convo'
    tag = Tags.LEVEL_VARS

    desc = \
        """
Sets the base conversation specified by *Text* to unselectable and greyed-out, but still visible. You usually want to use this at the end of a base convo to prevent the player from viewing it again.
        """

    keywords = ["Text"]

class RemoveBaseConvo(EventCommand):
    nid = 'remove_base_convo'
    tag = Tags.LEVEL_VARS

    desc = \
        """
Removes the base conversation specified by *Text* from the list entirely unless it is later re-added using **add_base_convo**.
        """

    keywords = ["Text"]

class IncrementSupportPoints(EventCommand):
    nid = 'increment_support_points'
    tag = Tags.MODIFY_UNIT_PROPERTIES

    desc = \
        """
Adds *PositiveInteger* amount of support points between the two specified units.
        """

    keywords = ['GlobalUnit', 'GlobalUnit', 'PositiveInteger']

class UnlockSupportRank(EventCommand):
    nid = 'unlock_support_rank'
    tag = Tags.MODIFY_UNIT_PROPERTIES

    desc = \
        """
Unlocks the specific *SupportRank* between the two specified units.
        """

    keywords = ['GlobalUnit', 'GlobalUnit', 'SupportRank']

class AddMarketItem(EventCommand):
    nid = 'add_market_item'
    tag = Tags.GAME_VARS

    desc = \
        """
Adds *Item* to the list of purchaseable goods in the base's market.
        """

    keywords = ["Item"]

class RemoveMarketItem(EventCommand):
    nid = 'remove_market_item'
    tag = Tags.GAME_VARS

    desc = \
        """
Removes *Item* from the list of purchaseable goods in the base's market.
        """

    keywords = ["Item"]

class AddRegion(EventCommand):
    nid = 'add_region'
    tag = Tags.REGION

    desc = \
        """
Adds a new region to the map that can be referenced by events. *Nid* will be the new regions identifier. *Position* is the map coordinate desired for the upper-left corner of the new region. *Size* is the dimensions of the new region. *RegionType* defines the type of region that is created (status region, etc.).

The optional *String* keyword can be used to specify the sub-region type. When set, the *only_once* flag prevents multiples of the same region from being created.
        """

    keywords = ["Nid", "Position", "Size", "RegionType"]
    optional_keywords = ["String"]
    flags = ["only_once"]

class RegionCondition(EventCommand):
    nid = 'region_condition'
    tag = Tags.REGION

    desc = \
        """
Modifies the trigger *Condition* for the event-type region specified by *Nid*.
        """

    keywords = ["Nid", "Condition"]

class RemoveRegion(EventCommand):
    nid = 'remove_region'
    tag = Tags.REGION

    desc = \
        """
Removes the region specified by *Nid*.
        """

    keywords = ["Nid"]

class ShowLayer(EventCommand):
    nid = 'show_layer'
    tag = Tags.TILEMAP

    desc = \
        """
Causes the specified map *Layer* to be displayed. The optional *LayerTransition* keyword controls whether the layer fades in (default) or is immediately displayed.
        """

    keywords = ["Layer"]
    optional_keywords = ["LayerTransition"]

class HideLayer(EventCommand):
    nid = 'hide_layer'
    tag = Tags.TILEMAP

    desc = \
        """
Causes the specified map *Layer* to be hidden. The optional *LayerTransition* keyword controls whether the layer fades out (default) or is immediately hidden.
        """

    keywords = ["Layer"]
    optional_keywords = ["LayerTransition"]

class AddWeather(EventCommand):
    nid = 'add_weather'
    tag = Tags.TILEMAP

    desc = \
        """
Adds the specified *Weather* to the current map.
        """

    keywords = ["Weather"]

class RemoveWeather(EventCommand):
    nid = 'remove_weather'
    tag = Tags.TILEMAP

    desc = \
        """
Removes the specified *Weather* from the current map.
        """

    keywords = ["Weather"]

class ChangeObjectiveSimple(EventCommand):
    nid = 'change_objective_simple'
    tag = Tags.LEVEL_VARS

    desc = \
        """
Changes the simple version of the chapter's objective text to *Text*.
        """

    keywords = ["Text"]

class ChangeObjectiveWin(EventCommand):
    nid = 'change_objective_win'
    tag = Tags.LEVEL_VARS

    desc = \
        """
Changes the victory condition of the chapter's objective text to *Text*.
        """

    keywords = ["Text"]

class ChangeObjectiveLoss(EventCommand):
    nid = 'change_objective_loss'
    tag = Tags.LEVEL_VARS

    desc = \
        """
Changes the defeat condition of the chapter's objective text to *Text*.
        """

    keywords = ["Text"]

class SetPosition(EventCommand):
    nid = 'set_position'
    tag = Tags.MISCELLANEOUS

    desc = \
        """
Stores a given position (*Condition*) as the event's home position. It can later be referenced in this event script using {position}.
        """

    keywords = ["Condition"]

class MapAnim(EventCommand):
    nid = 'map_anim'
    tag = Tags.TILEMAP
    desc = ('Plays a map animation denoted by the nid *MapAnim* at *Position*. Optional args: a speed multiplier'
            ' *Float*, which increases the length of time it takes to play the animation (larger is slower)')
    keywords = ["MapAnim", "FloatPosition"]
    optional_keywords = ["Float"]
    flags = ["no_block", "permanent", "blend"]

class RemoveMapAnim(EventCommand):
    nid = 'remove_map_anim'
    tag = Tags.TILEMAP
    desc = ('Removes a map animation denoted by the nid *MapAnim* at *Position*. Only removes MapAnims that were created using'
            ' the "permanent" flag')
    keywords = ["MapAnim", "Position"]

class MergeParties(EventCommand):
    nid = 'merge_parties'
    tag = Tags.MISCELLANEOUS
    # Merges the second party onto the first party
    # The second will still exist, but will have no money, bexp,
    # items in convoy, or units associated with it
    # The first will gain all of those properties

    desc = \
        """
Merges two parties together. The second specified party's units, money, and bonus experience will be added to the first specified party. Note that the second party will still exist but will now be empty.
        """

    keywords = ["Party", "Party"]

class ArrangeFormation(EventCommand):
    nid = 'arrange_formation'
    tag = Tags.MISCELLANEOUS
    # Puts units on formation tiles automatically

    desc = \
        """
Places units on the map's formation tiles automatically.
        """

class Prep(EventCommand):
    nid = 'prep'
    tag = Tags.MISCELLANEOUS

    desc = \
        """
Display the prep screen. *Bool* sets whether the "Pick Units" menu will be available in the prep screen. The optional *Music* keyword specifies the music track that will be played during the preparations menu.
        """

    optional_keywords = ["Bool", "Music"]  # Pick units

class Base(EventCommand):
    nid = 'base'
    tag = Tags.MISCELLANEOUS

    desc = \
        """
When called, the player is sent to the Base menu. The *Panorama* and *Music* keywords specify the background image and the music track that will be played for the base.
        """

    keywords = ["Panorama"]
    optional_keywords = ["Music"]
    flags = ["show_map"]

class Shop(EventCommand):
    nid = 'shop'
    tag = Tags.MISCELLANEOUS

    desc = \
        """
Causes *Unit* to enter a shop that sells *ItemList* items. The optional *ShopFlavor* keyword determines whether the shop appears as a vendor or an armory.
        """

    keywords = ["Unit", "ItemList"]
    optional_keywords = ["ShopFlavor"]

class Choice(EventCommand):
    nid = 'choice'
    tag = Tags.MISCELLANEOUS

    desc = \
        """
Presents the player with a menu in which he/she can choose from several options. An example would be the choice to go with Eirika or Ephraim in The Sacred Stones.

*Nid* is the name of this choice, which can be checked later to recall the player's decision.
*Text* is the text describing the choice, such as "which will you choose?"
*StringList* specifies the different options that the player can choose among.
The optional *Orientation* keyword specifies whether the options are displayed as a vertical list or side-by-side.
        """

    keywords = ['Nid', 'Text', 'StringList']
    optional_keywords = ['Orientation']

class ChapterTitle(EventCommand):
    nid = 'chapter_title'
    tag = Tags.MISCELLANEOUS

    desc = \
        """
Brings up the chapter title screen, optionally with the specified *Music* and chapter name (*Text*).
        """

    optional_keywords = ["Music", "Text"]

class DrawOverlaySprite(EventCommand):
    nid = 'draw_overlay_sprite'
    nickname = 'draw_overlay'
    tag = Tags.MISCELLANEOUS

    desc = \
"""
Draws a sprite on the screen at the specified position. Position defaults to 0, 0.
Will always draw immediately behind the dialog.
You can control the order that multiple siimultaneous overlays are drawn by choosing a custom z-level.
Higher z-level sprites will cover lower z-level sprites occupying the same positions.
"""

    keywords = ['String', 'Sprite']
    optional_keywords = ['PositionOffset', 'Integer']
    keyword_names = ['Name', 'Sprite_ID', 'Position', 'Z-Level']

class RemoveOverlaySprite(EventCommand):
    nid = 'remove_overlay_sprite'
    nickname = 'delete_overlay'
    tag = Tags.MISCELLANEOUS

    desc = \
"""
Removes an overlay sprite with the given name from the screen.
"""

    keywords = ['String']

class Alert(EventCommand):
    nid = 'alert'
    tag = Tags.DIALOGUE_TEXT

    desc = \
        """
Displays the text given in *Text* in an alert box. This is used for events such as "The switch was pulled!".
        """

    keywords = ["Text"]

class AlertItem(EventCommand):
    nid = 'alert_item'
    tag = Tags.DIALOGUE_TEXT

    desc = \
        """
Displays the text given in *Text* in an alert box. This is used for events such as "The switch was pulled!".

Also takes in a item icon from *Item* to display.

The icon always appears on the left side.
        """

    keywords = ["Text", "Item"]

class AlertSkill(EventCommand):
    nid = 'alert_skill'
    tag = Tags.DIALOGUE_TEXT

    desc = \
        '''
Displays the text given in *Text* in an alert box. This is used for events such as "The switch was pulled!".

Also takes in a skill icon from *Skill* to display.

The icon always appears on the left side.
        '''

    keywords = ["Text", "Skill"]

class VictoryScreen(EventCommand):
    nid = 'victory_screen'
    tag = Tags.MISCELLANEOUS

    desc = \
        """
Displays the chapter's victory screen. Congratulations!
        """

class RecordsScreen(EventCommand):
    nid = 'records_screen'
    tag = Tags.MISCELLANEOUS

    desc = \
        """
Displays the game's records screen.
        """

class LocationCard(EventCommand):
    nid = 'location_card'
    tag = Tags.DIALOGUE_TEXT

    desc = \
        """
Used to display text (*Text*) in the upper-left corner of the screen. This is often used to indicate the current location shown, such as "Castle Ostia".
        """

    keywords = ["Text"]

class Credits(EventCommand):
    nid = 'credits'
    tag = Tags.DIALOGUE_TEXT

    desc = \
        """
Display a line of credits. The first *Text* specifies the credit type ("Director"). The second *Text* is a comma-delimited list of credits ("Spielberg,Tarantino"). If the *no_split* flag is set, the list will not be split based on the commas in *Text*. The *wait* and *center* flags modify how the credit line is displayed.
        """

    keywords = ["Text", "Text"]
    flags = ['wait', 'center', 'no_split']

class Ending(EventCommand):
    nid = 'ending'
    tag = Tags.DIALOGUE_TEXT

    desc = \
        """
Displays the epilogue text for a character. *Portrait* is the portrait to be displayed, the first *Text* is the name displayed (ex: "Marcus, Badass Paladin"), the second *Text* is the block of text describing what happened to the character.
        """

    keywords = ["Portrait", "Text", "Text"]

class PopDialog(EventCommand):
    nid = 'pop_dialog'
    tag = Tags.DIALOGUE_TEXT
    desc = \
        """
Removes the most recent dialog text box from the screen. Generally only used in conjunction with the `ending` command to remove the Ending box during a transition.

Example:

```
ending;Coyote;Coyote, Man of Mystery;Too mysterious for words.
transition;Close
pop_dialog
transition;Open
```
        """

class Unlock(EventCommand):
    nid = 'unlock'
    tag = Tags.REGION

    desc = \
        """
A convenient wrapper function that combines **find_unlock** and **spend_unlock**. This is ususally used in a region's event script to cause *Unit* to spend a key to unlock the current region.
        """

    keywords = ["Unit"]

class FindUnlock(EventCommand):
    nid = 'find_unlock'
    tag = Tags.HIDDEN

    desc = \
        """
Use **unlock** instead.
        """

    keywords = ["Unit"]

class SpendUnlock(EventCommand):
    nid = 'spend_unlock'
    tag = Tags.HIDDEN

    desc = \
        """
Use **unlock** instead.
        """

    keywords = ["Unit"]

class TriggerScript(EventCommand):
    nid = 'trigger_script'
    tag = Tags.MISCELLANEOUS

    desc = \
        """
Executes the event script specified by *Event*. Can optionally feed two *GlobalUnits* into the script as {unit} and {unit2}.
        """

    keywords = ["Event"]
    optional_keywords = ["GlobalUnit", "GlobalUnit"]

class LoopUnits(EventCommand):
    nid = 'loop_units'
    tag = Tags.MISCELLANEOUS

    desc = \
        """
The first argument to this command should be a Python expression that evaluates to a list of unit nids.

This command will run the designated event script for each unit in the list.

Example:
```
# This gives all player units 1 fatigue using the Gain Fatigue Event script
loop_units;[unit.nid for unit in game.get_player_units()];Gain Fatigue Event
```
        """

    keywords = ["Condition", "Event"]

class ChangeRoaming(EventCommand):
    nid = 'change_roaming'
    tag = Tags.MISCELLANEOUS
    desc = "Turn free roam mode on or off"

    keywords = ["Bool"]

class ChangeRoamingUnit(EventCommand):
    nid = 'change_roaming_unit'
    tag = Tags.MISCELLANEOUS
    desc = "Changes the level's current roaming unit."

    keywords = ["Unit"]

class CleanUpRoaming(EventCommand):
    nid = 'clean_up_roaming'
    tag = Tags.MISCELLANEOUS
    desc = "Removes all units other than the roaming unit"

    keywords = []

class AddToInitiative(EventCommand):
    nid = 'add_to_initiative'
    tag = Tags.MISCELLANEOUS
    desc = "Adds the specified unit to the specified point in the initiative order. 0 is the current initiative position."

    keywords = ["Unit", "Integer"]

class MoveInInitiative(EventCommand):
    nid = 'move_in_initiative'
    tag = Tags.MISCELLANEOUS
    desc = "Moves the initiative of the specified unit."

    keywords = ["Unit", "Integer"]

class PairUp(EventCommand):
    nid = 'pair_up'
    tag = Tags.MISCELLANEOUS
    desc = "Pairs the first unit into the second"

    keywords = ["Unit", "Unit"]

class Separate(EventCommand):
    nid = 'separate'
    tag = Tags.MISCELLANEOUS
    desc = "Sets the unit's traveler to none. Does not place that partner on the map."

    keywords = ["Unit"]

class StartOverworldCinematic(EventCommand):
    nid = 'overworld_cinematic'
    tag = Tags.OVERWORLD
    desc = 'Sets the background to the overworld, allowing us to create cutscenes set in the overworld'

    optional_keywords = ['OverworldNID']

class OverworldSetPosition(EventCommand):
    nid = 'set_overworld_position'
    tag = Tags.OVERWORLD
    desc = "Sets the position of a specific party in the overworld to a specific coordinate or node in the overworld"

    keywords = ['OverworldEntity', 'OverworldLocation']
    flags = ['no_animate']

class OverworldMoveUnit(EventCommand):
    nid = 'overworld_move_unit'
    nickname = 'omove'
    tag = Tags.OVERWORLD
    desc = ('Issues a move command to *OverworldEntity* to move from its current position to given *OverworldLocation*. '
            'Alternately, moves *OverworldEntity* along a path denoted by the *PointList* in the format "(x, y)-(x1,y1)-(x2,y2)-...". '
            'You can adjust the travel time via the *Float* parameter - higher is slower (2 is twice as slow, 3 is thrice...)'
            '\n the `disable_after` flag determines whether or not to remove the unit after the move concludes. Useful for cinematics.')

    keywords = ["OverworldEntity"]
    optional_keywords = ['OverworldLocation', 'Float', 'PointList']
    flags = ['no_block', 'no_follow', 'disable_after', 'no_sound']

class OverworldRevealNode(EventCommand):
    nid = 'reveal_overworld_node'
    tag = Tags.OVERWORLD
    desc = ('Reveals an overworld node on the map: moves the camera to the new location, plays the animation, and fades in the nodes.'
            'By default, fades in via animation; the *Bool* can be set to **True** to skip this anim.')

    keywords = ['OverworldNodeNID']
    optional_keywords = ['Bool']

class OverworldRevealRoad(EventCommand):
    nid = 'reveal_overworld_road'
    tag = Tags.OVERWORLD
    desc = ('Enables a road between two overworld nodes. *OverworldNodeNID* denotes the NID of a valid node. '
            'By default, fades in via animation; the *Bool* can be set to **True** to skip this anim.')

    keywords = ['OverworldNodeNID', 'OverworldNodeNID']
    optional_keywords = ['Bool']

class CreateOverworldEntity(EventCommand):
    nid = 'create_overworld_entity'
    tag = Tags.OVERWORLD
    desc = ('Create an overworld entity in memory with nid *Nid*. This can be used for purely cinematic purposes,'
            ' or alternatively, used to spawn enemy reinforcements on the map.'
            'If the `delete` flag is passed, this command will instead delete the entity with said NID')

    keywords = ['Nid']
    optional_keywords = ['Unit']
    flags = ['delete']

class DisableOverworldEntity(EventCommand):
    nid = 'disable_overworld_entity'
    tag = Tags.OVERWORLD
    desc = ('remove an overworld entity from the map, with or without animation')

    keywords = ['Nid']
    flags = ['no_animate']

class ToggleNarrationMode(EventCommand):
    nid = 'toggle_narration_mode'
    tag = Tags.DIALOGUE_TEXT
    desc = ('Enter or exit a full-screen narration mode.')

    keywords = ['Direction']
    optional_keywords = ['Speed']

def get_commands():
    return EventCommand.__subclasses__()

def restore_command(dat):
    if len(dat) == 2:
        nid, values = dat
        display_values = None
    elif len(dat) == 3:
        nid, values, display_values = dat
    subclasses = EventCommand.__subclasses__()
    for command in subclasses:
        if command.nid == nid:
            copy = command(values, display_values)
            return copy
    logging.error("Couldn't restore event command: NID: %s; Display Values: %s", nid, display_values)
    if not display_values:
        display_values = values
    return Comment([nid + ';' + str.join(';', display_values)])

def parse_text(text: str, strict=False) -> EventCommand:
    """parses a line into a command

    Args:
        text (str): text to be parsed
        strict (bool, optional): whether invalid command should be parsed as comments, or None.
        This defaults to false; usually, invalid commands are caused by engine version mismatch,
        and parsing them as None will erase the user's hard work. Parsing them as comments allows them to be
        preserved harmlessly. However, in certain cases - such as event validation - strict will be useful.

    Returns:
        EventCommand: parsed command
    """
    if text.startswith('#'):
        return Comment([text])
    arguments = text.split(';')
    command_nid = arguments[0]
    subclasses = EventCommand.__subclasses__()
    for command in subclasses:
        if command.nid == command_nid or command.nickname == command_nid:
            cmd_args = arguments[1:]
            true_cmd_args = []
            command_info = command()
            for idx, arg in enumerate(cmd_args):
                if idx < len(command_info.keywords):
                    cmd_keyword = command_info.keywords[idx]
                elif idx - len(command_info.keywords) < len(command_info.optional_keywords):
                    cmd_keyword = command_info.optional_keywords[idx - len(command_info.keywords)]
                else:
                    cmd_keyword = "N/A"
                # if parentheses exists, then they contain the "true" arg, with everything outside parens essentially as comments
                # we do NOT want to use this with evals, hence the '{' and '}' stoppage
                if '(' in arg and ')' in arg and '{' not in arg and '}' not in arg and ('FLAG' in arg or not (cmd_keyword in ['Condition', 'Text', 'StringList', 'PointList', 'DashList'])):
                    true_arg = arg[arg.find("(")+1:arg.find(")")]
                    true_cmd_args.append(true_arg)
                else:
                    true_cmd_args.append(arg)
            copy = command(true_cmd_args, cmd_args)
            return copy
    if strict:
        return None
    else:
        return Comment([text])

def parse(command, _eval_evals: Callable[[str], str] = None, _eval_vars: Callable[[str], str] = None):
    values = command.values
    num_keywords = len(command.keywords)
    true_values = values[:num_keywords]
    flags = {v for v in values[num_keywords:] if v in command.flags}
    optional_keywords = [v for v in values[num_keywords:] if v not in flags]
    true_values += optional_keywords
    if _eval_evals:
        true_values = [_eval_evals(value) for value in true_values]
    if _eval_vars:
        true_values = [_eval_vars(value) for value in true_values]
    return true_values, flags

def convert_parse(command: EventCommand):
    from app.events.event_validators import convert
    values = command.values
    num_keywords = len(command.keywords)
    num_optionals = len(command.optional_keywords)
    num_total_keywords = num_keywords + num_optionals
    true_values = [None] * num_total_keywords

    kwd_idx = 0
    for keyword_idx, keyword in enumerate(values[:num_keywords]):
        true_values[kwd_idx] = convert(command.keywords[keyword_idx], keyword)
        kwd_idx += 1
    flags = {v for v in values[num_keywords:] if v in command.flags}
    for okeyword_idx, okeyword in enumerate(values[num_keywords:]):
        if okeyword not in flags:
            if kwd_idx < len(true_values):
                true_values[kwd_idx] = convert(command.optional_keywords[okeyword_idx], okeyword)
        kwd_idx += 1
    return true_values, flags
