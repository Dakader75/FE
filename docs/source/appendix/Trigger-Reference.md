# Trigger Reference

_last updated 22-05-04_

This page contains a description of all triggers currently in the editor, along with their usable properties.

Anywhere `unit1` is a supported field, you can also use `unit`. Anywhere `unit2` is a supported field, you can also use `target`.

> `level_start`: Occurs at the very beginning of a level. The chapter screen and title is usually displayed here, as well as introductory cinematics.
> - No custom fields

> `level_end`: This occurs once `win_game` is set in another event. This is called at the end of gameplay, and usually handles end cinematics before going to the save screen or overworld.
> - No custom fields

> `overworld_start`: Occurs upon entering the overworld.
> - No custom fields

> `level_select`: Occurs when an overworld entity is about to issue a move to the node containing the next level. Because of implementation detail, when this event occurs, it supersedes any queued moves. Therefore, the entity will _not move_ to the selected node. Any events that use this trigger should include a scripted move if movement is desired.
> - No custom fields

> `on_overworld_node_select`: Occurs when an entity is about to issue a move to a node (which may or may not contain the next level, or any level at all). Because of implementation detail, when this event occurs, it supersedes any queued moves. Therefore, the entity will _not move_ to the selected node. Any events that use this trigger should include a scripted move if movement is desired.
> - **entity_nid**: Contains the id of entity that will issue a move.
> - **node_nid**: Contains the id of the node.

> `turn_change`" Occurs immediately before turn changes to Player Phase. Useful for dialogue or reinforcements.
> - No custom fields

> `enemy_turn_change`: Occurs immediately before turn changes to Enemy Phase. Useful for "same turn reinforcements" and other evil deeds.
> - No custom fields

> `enemy2_turn_change`: Occurs immediately before turn changes to Second Enemy's Phase.
> - No custom fields

> `other_turn_change`: Occurs immediately before turn changes to Other Phase.
> -No custom fields

> `on_region_interact`: Occurs when a unit interacts with an event region. All event region type events (like Shop, Armory, Visit, etc.) follow this trigger's format.
> - **unit1**: the unit that is interacting.
> - **position**: the position of the unit.
> - **region**: the event region.

> `unit_death`: Occurs when any unit dies, including generics.
> - **unit1**: the unit that died.
> - **unit2**: the unit that killed them (can be None).
> - **position**: the position they died at.

> `unit_wait`: Occurs when any unit waits.
> - **unit1**: the unit that waited.
> - **position**: the position they waited at.
> - **region**: region under the unit (can be None)

> `unit_select`: Occurs when a unit is selected by the cursor.
> - **unit1**: the unit that was selected.
> - **position**: the position they were selected at.

> `unit_level_up`: Occurs after a unit levels up.
> - **unit1**: the unit that leveled up
> - **stat_change**: a `Dict[str, int]` containing their stat changes.

> `during_unit_level_up`: Occurs during a unit's level-up screen, immediately after stat changes are granted. This event is useful for implementing level-up quotes.
> - **unit1**: the unit that leveled up
> - **stat_change**: a `Dict[str, int]` containing their stat changes.

> `combat_start`: Occurs when non-scripted combat is begun between any two units. Useful for boss quotes.
> - **unit1**: the unit who initiated combat.
> - **unit2**: the target of the combat (can be None).
> - **item**: the item/ability used by unit1.
> - **position**: the position of the unit1.
> - **is_animation_combat**: a boolean denoting whether or not we are in an actual animation or merely a map animation.

> `combat_end`: This trigger fires at the end of combat. Useful for checking win or loss conditions.
> - **unit1**: the unit who initiated combat.
> - **unit2**: the target of the combat (can be None).
> - **item**: the item/ability used by unit1.
> - **position**: contains the position of unit1.

> `on_talk`: This trigger fires when two units "Talk" to one another.
> - **unit1**: the unit who is the talk initiator.
> - **unit2**: the unit who is the talk receiver. 
> - **position**: the position of unit1 (is None if triggered during free roam)

> `on_support`: This trigger fires when two units "Support" to one another.
> - **unit1**: the unit who is the support initiator.
> - **unit2**: the unit who is the support receiver. 
> - **position**: the position of unit1 (could be None, for instance during Base).
> - **support_rank_nid**: contains the nid of the support rank (e.g. `A`, `B`, `C`, or `S`)

> `on_base_convo`: This trigger fires when the player selects a base conversation to view.
> - **unit1**: (DEPRECATED) contains the name of the base conversation.
> - **base_convo**: contains the name of the base conversation.

> `on_turnwheel`: This trigger fires after the turnwheel is used.
> - No custom fields

> `on_title_screen`: NOT CURRENTLY IMPLEMENTED. Occurs before the title screen is shown.
> - No custom fields

> `time_region_complete`: Occurs when a time region runs out of time and would be removed.
> - **region**: the region that has run out of time.

## Component Triggers

Some events can be called by components. The most important ones are detailed here:

> `event_on_hit`: Plays before a hit, if the unit will hit with this item.
> - **unit1**: the unit that is attacking.
> - **unit2**: the unit that will be hit.
> - **position**: the position of the attacking unit.
> - **item**: the item/ability that the attacking unit is using.
> - **target_pos*: the position of the defending unit.
> - **mode**: One of (`attack`, `defense`), depending on whether the combat's overall attacker is the one doing this attack, or the combat's defender is the one doing this attack.
> - **attack_info**: A 2-tuple. The first element is the number of attacks that have occurred before this one. The second element is the number of subattacks (think brave attacks) that have occurred within this main attack.

> `event_after_combat`: Plays at the end of combat as long as an attack in combat hit.
> - **unit1**: the unit that is attacking.
> - **unit2**: the unit that will be hit.
> - **position**: the position of the attacking unit.
> - **item**: the item/ability that the attacking unit is using.
> - **target_pos*: the position of the defending unit.
> - **mode**: One of (`attack`, `defense`), depending on whether the combat's overall attacker is the one doing this attack, or the combat's defender is the one doing this attack.

> `event_after_initiated_combat`: Plays at the end of combat initiated by the user.
> - **unit1**: the unit that is attacking.
> - **unit2**: the unit that is defending.
> - **position**: the position of the attacking unit.
> - **item**: the item/ability that the attacking unit is using.
> - **mode**: Always `attack`.

> `event_on_remove`: Plays when the skill is removed.
> - **unit1**: the unit that had the skill.

> `unlock_staff`: Plays when an unlock staff unlocks a region.
> - **unit1**: the unit that is unlocking.
> - **position**: the position of the unlocking unit.
> - **item**: the item/ability that the unlocking unit is using.
> - **region*: the region being unlocked.

## Miscellaneous

The debug screen calls a miniature event when you enter a command. That event has access to:
> - **unit**: the unit under the cursor
> - **position**: the position under the cursor
