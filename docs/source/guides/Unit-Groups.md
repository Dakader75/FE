# Unit Groups
Suppose that you’re working on a map, and you want to have a part where a bunch of units spawn together and move together at the same time during some part in a cutscene.

If you were to do this one-by-one, only dealing with individual units, you would have to write several lines of event commands for each one. It’s not long before this gets out of hand.

```python
# Spawns our gang of enemies
add_unit;Enemy1;x,y
add_unit;Enemy2;x,y
add_unit;Enemy3;x,y
# Moves them to their starting positions simultaneously
move_unit;Enemy1;x,y;no_block
move_unit;Enemy2;x,y;no_block
move_unit;Enemy3;x,y
```

You have to use a command to add each unit, then you need to use a move command on each one to get the effect of them all moving together.

There has to be a better way, right?

The solution is to use Unit Groups.

![ExampleUnitGroupMenu](images/UnitGroupMenu.png)

When viewing a single Chapter’s tilemap and units, you’ll see four tabs on the bottom left corner of the editor. As the name suggests, the Groups tab deals with user-defined groups of units.

A unit group can consist of any units loaded on the map, no matter what team they are on.
To create a group, click the Create New Group button at the bottom of the Groups list.

![ExampleNewUnitGroup](images/NewUnitGroup.png)

A blank group should appear on the list. You can rename the group by clicking on the New Group text.

You can add a unit by clicking the + button next to the text box. Pressing it will give you this prompt. You can select any unit you have loaded on the map to add them to the group.

![ExampleLoadUnitInGroup](images/LoadUnitInGroup.png)

Placing each unit works much like the Unit field in the Level Editor. Unit positions are allowed to overlap, making them useful for reinforcements and cutscenes.

Using events, we can move each group with only one command.

Before, we had to use a bunch of individual lines to handle multiple units:
```python
# Spawns our gang of enemies
add_unit;Enemy1;x,y
add_unit;Enemy2;x,y
add_unit;Enemy3;x,y
# Moves them to their starting positions simultaneously
move_unit;Enemy1;x,y;no_block
move_unit;Enemy2;x,y;no_block
move_unit;Enemy3;x,y
```

But now, this statement becomes much simpler:
```python
# Spawns the enemies
spawn_group;Thug n Friends;south;Thug n Friends;fade
# Moves them to their starting positions
move_group;Thug n Friends;Starting
```

## Unit Group Commands
All unit group related event commands:
```python
# Adds a group of units to the map. StartingGroup determines the spawn positions of each unit
# in Group.
add_group;Group;StartingGroup;EntryType;Placement;flags

# This command also adds a group, but causes them to spawn at one of the edges of the 
# screen specified by the CardinalDirection argument. Group specifies which units to spawn. 
# StartingGroup specifies where to spawn those units.
spawn_group;Group;CardinalDirection;StartingGroup;EntryType;Placement;flags

# Moves each unit in Group to their corresponding position in StartingGroup
move_group;Group;StartingGroup

# Removes the specified group from the map
remove_group;Group
```
