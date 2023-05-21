# Trigger Reference

This page contains a description of all triggers currently in the editor, along with their usable properties.

Anywhere `unit1` is a supported field, you can also use `unit`. Anywhere `unit2` is a supported field, you can also use `target`.
> `level_start`:  Occurs at the very beginning of a level. The chapter screen and title is usually displayed here, as well as introductory cinematics. 
> - No custom fields

---------------------
> `level_end`:  This occurs once `win_game` is set in another event. This is called at the end of gameplay, and usually handles end cinematics before going to the save screen or overworld. 
> - No custom fields

---------------------
> `overworld_start`:  Occurs upon entering the overworld. 
> - No custom fields

---------------------
> `level_select`:  Occurs when an overworld entity is about to issue a move to the node containing the next level. Because of implementation detail, when this event occurs, it supersedes any queued moves. Therefore, the entity will _not move_ to the selected node. Any events that use this trigger should include a scripted move if movement is desired. 
> - No custom fields

---------------------
> `turn_change`:  Occurs immediately before turn changes to Player Phase. Useful for dialogue or reinforcements. 
> - No custom fields

---------------------
> `enemy_turn_change`:  Occurs immediately before turn changes to Enemy Phase. Useful for "same turn reinforcements" and other evil deeds. 
> - No custom fields

---------------------
> `enemy2_turn_change`:  Occurs immediately before turn changes to Second Enemy's Phase. 
> - No custom fields

---------------------
> `other_turn_change`:  Occurs immediately before turn changes to Other Phase. 
> - No custom fields

---------------------
> `on_region_interact`:  Occurs when a unit interacts with an event region. All event region type events (like Shop, Armory, Visit, etc.) follow this trigger's format.  
> - **unit1** (`UnitObject`):  the unit that is interacting.
> - **position** (`Tuple[int, int]`):  the position of the unit.
> - **region** (`RegionObject`):  the event region.

---------------------
> `unit_death`:  Occurs when any unit dies, including generics.  
> - **unit1** (`UnitObject`):  the unit that died.
> - **unit2** (`UnitObject`):  the unit that killed them (can be None).
> - **position** (`Tuple[int, int]`):  the position they died at.

---------------------
> `unit_wait`:  Occurs when any unit waits.  
> - **unit1** (`UnitObject`):  the unit that waited.
> - **position** (`Tuple[int, int]`):  the position they waited at.
> - **region** (`Optional[RegionObject]`):  region under the unit (can be None)

---------------------
> `unit_select`:  Occurs when a unit is selected by the cursor.  
> - **unit1** (`UnitObject`):  the unit that was selected.
> - **position** (`Tuple[int, int]`):  the position they were selected at.

---------------------
> `unit_level_up`:  Occurs after a unit levels up.  
> - **unit1** (`UnitObject`):  the unit that leveled up
> - **stat_changes** (`Dict[NID, int]`):  a dict containing their stat changes.

---------------------
> `during_unit_level_up`:  Occurs during a unit's level-up screen, immediately after stat changes are granted. This event is useful for implementing level-up quotes.  
> - **unit1** (`UnitObject`):  the unit that leveled up
> - **stat_changes** (`Dict[NID, int]`):  a dict containing their stat changes.

---------------------
> `combat_start`:  Occurs when non-scripted combat is begun between any two units. Useful for boss quotes.  
> - **unit1** (`UnitObject`):  the unit who initiated combat.
> - **unit2** (`UnitObject`):  the target of the combat (can be None).
> - **item** (`ItemObject`):  the item/ability used by unit1.
> - **position** (`Tuple[int, int]`):  the position of the unit1.
> - **is_animation_combat** (`bool`):  a boolean denoting whether or not we are in an actual animation or merely a map animation.

---------------------
> `combat_end`:  This trigger fires at the end of combat. Useful for checking win or loss conditions.  
> - **unit1** (`UnitObject`):  the unit who initiated combat.
> - **unit2** (`UnitObject`):  the target of the combat (can be None).
> - **item** (`ItemObject`):  the item/ability used by unit1.
> - **position** (`Tuple[int, int]`):  contains the position of unit1.
> - **playback** (`List[PlaybackBrush]`):  a list of the playback brushes from the combat.

---------------------
> `on_talk`:  This trigger fires when two units "Talk" to one another.  
> - **unit1** (`UnitObject`):  the unit who is the talk initiator.
> - **unit2** (`UnitObject`):  the unit who is the talk receiver.
> - **position** (`Tuple[int, int]`):  the position of unit1 (is None if triggered during free roam)

---------------------
> `on_support`:  This trigger fires when two units "Support" to one another.  
> - **unit1** (`UnitObject`):  the unit who is the support initiator.
> - **unit2** (`UnitObject`):  the unit who is the support receiver.
> - **position** (`Tuple[int, int]`):  the position of unit1 (could be None, for instance during Base).
> - **support_rank_nid** (`NID`):  contains the nid of the support rank (e.g. `A`, `B`, `C`, or `S`)
> - **is_replay** (`bool`):  whether or not this is just a replay of the support convo from the base menu.

---------------------
> `on_base_convo`:  This trigger fires when the player selects a base conversation to view.  
> - **base_convo** (`NID`):  contains the name of the base conversation.
> - **unit** (`NID`):  DEPRECATED, contains the name of the base conversation.

---------------------
> `on_prep_start`:  Occurs each time the player enters preps. 
> - No custom fields

---------------------
> `on_base_start`:  Occurs each time the player enters base. 
> - No custom fields

---------------------
> `on_turnwheel`:  Occurs after the turnwheel is used. 
> - No custom fields

---------------------
> `on_title_screen`:  Occurs before the title screen is shown. 
> - No custom fields

---------------------
> `on_startup`:  Occurs whenever the engine starts. 
> - No custom fields

---------------------
> `time_region_complete`:  Occurs when a time region runs out of time and would be removed. 
> - **position** (`Tuple[int, int]`):  the position of the region that has run out of time.
> - **region** (`RegionObject`):  the region that has run out of time.

---------------------
> `on_overworld_node_select`:  Occurs when an entity is about to issue a move to a node (which may or may not contain the next level, or any level at all). Because of implementation detail, when this event occurs, it supersedes any queued moves. Therefore, the entity will _not move_ to the selected node. Any events that use this trigger should include a scripted move if movement is desired.  
> - **entity_nid** (`NID`):  Contains the id of entity that will issue a move.
> - **node_nid** (`NID`):  Contains the id of the node.

---------------------
> `roam_press_start`:  Occurs when the `start` key is pressed in Free Roam.  
> - **unit1** (`UnitObject`):  The current roam unit.

---------------------
> `roam_press_info`:  Occurs when the `info` key is pressed in Free Roam.  
> - **unit1** (`UnitObject`):  The current roam unit.
> - **unit2** (`UnitObject`):  the closest nearby other unit, if there is any unit nearby.

---------------------
> `roaming_interrupt`:  Occurs when the player enters an `interrupt` region on the map.  
> - **unit1** (`UnitObject`):  The current roam unit.
> - **position** (`Tuple[int, int]`):  The position of the current roam unit
> - **region** (`RegionObject`):  The region that was triggered.

---------------------
> `RegionTrigger`:  Special trigger. This trigger has a custom nid, and will be created whenever you make an interactable event region.  
> - **nid** (`NID`):  the nid of the region
> - **unit1** (`UnitObject`):  The unit triggering the region
> - **position** (`Tuple[int, int]`):  The position of the unit triggering the region
> - **region** (`RegionObject`):  the name of the region that was triggered
> - **item** (`ItemObject`):  the item used to trigger this region (used with unlock staves and keys)

---------------------
