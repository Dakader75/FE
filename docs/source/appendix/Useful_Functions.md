# Useful Functions

There are a number of useful functions that can be employed in event eval zones to fetch some aspect of the game. This page is exhaustive; it will list every ready-made
function that can query the game state.


## Achievements



#### Has Achievement

    has_achievement(nid) 
		-> 'bool'

Checks if an achievement is completed

        Args:
            nid: nid to check for completion

        Returns:
            bool: if the achievement exists
        
  ---------------------


## Items



#### Get Item

    get_item(unit, item) 
		-> 'Optional[ItemObject]'

Returns a item object by nid.

        Args:
            unit: unit to check
            item: item to check

        Returns:
            Optional[ItemObject] | None: Item if exists on unit, otherwise None
        
  ---------------------


#### Has Item

    has_item(item, nid=None, team=None, tag=None, party=None) 
		-> 'bool'

Check if any unit matching criteria has item.

Example usage:

* `has_item("Iron Sword", team="player")` will check if any player unit is holding an iron sword
* `has_item("Sacred Stone", party='Eirika')` will check if Eirika's party has the item "Sacred Stone"

        Args:
            item: item to check
            nid (optional): use to check specific unit nid
            team (optional): used to match for team. one of 'player', 'enemy', 'enemy2', 'other'
            tag (optional): used to match for tag.
            party (optional): used to match for party

        Returns:
            bool: True if unit has item, else False
        
  ---------------------


## Map Functions



#### Any Unit In Region

    any_unit_in_region(region, nid=None, team=None, tag=None) 
		-> 'bool'

checks if any unit matching the criteria is in the region

Example usage:
* `any_unit_in_region('NorthReinforcements', team='player')` will check if any player unit is in the region
* `any_unit_in_region('NorthReinforcements', nid='Eirika')` will check if Eirika is in the region
* `any_unit_in_region('NorthReinforcements')` will check if ANY unit is in the region

        Args:
            region: region in question
            nid (optional): used to match for NID
            team (optional): used to match for team. one of 'player', 'enemy', 'enemy2', 'other'
            tag (optional): used to match for tag.

        Returns:
            bool: if any unit matching criteria is in the region
        
  ---------------------


#### Get Allies Within Distance

    get_allies_within_distance(position, dist: 'int' = 1) 
		-> 'List[Tuple[UnitObject, int]]'

Return a list containing all player units within `dist` distance to the specific position.

        Args:
            position: position or unit
            dist (int, optional): How far to search. Defaults to 1.

        Returns:
            List[Tuple[UnitObject, int]]: Returns all pairs of `(unit, distance)`
            within the specified `dist`.
        
  ---------------------


#### Get Closest Allies

    get_closest_allies(position, num: 'int' = 1) 
		-> 'List[Tuple[UnitObject, int]]'

Return a list containing the closest player units and their distances.

        Args:
            position: position or unit
            num (int, optional): How many allies to search for. Defaults to 1.

        Returns:
            List[Tuple[UnitObject, int]]: Returns `num` pairs of `(unit, distance)` to the position.
            Will return fewer if there are fewer player units than `num`.
        
  ---------------------


#### Get Terrain

    get_terrain(pos) 
		-> 'Optional[NID]'

Returns the terrain at position, or, if unit is provided,
        the terrain underneath the unit.

        Args:
            pos: Position tuple or unit

        Returns:
            Optional[NID]: the nid of the region, or None if the position is invalid
        
  ---------------------


#### Get Units In Area

    get_units_in_area(position_corner_1: 'Tuple[int, int]', position_corner_2: 'Tuple[int, int]') 
		-> 'List[UnitObject]'

Returns a list of units within a rectangular area.

        Args:
            position_corner_1 (Tuple[int, int]): (x, y) coordinates for one corner of the area
            position_corner_2 (Tuple[int, int]): (x, y) coordinates for the opposite corner

        Returns:
            List[UnitObject]: Returns all units with positions with values between those
            specified by the corners (inclusive), or an empty list if no units exist in that area
        
  ---------------------


#### Get Units In Region

    get_units_in_region(region, nid=None, team=None, tag=None) 
		-> 'List[UnitObject]'

returns all units matching the criteria in the given region

Example usage:
* `get_units_in_region('NorthReinforcements', team='player')` will return all player units in the region
* `get_units_in_region('NorthReinforcements', nid='Eirika')` will return Eirika if Eirika is in the region
* `get_units_in_region('NorthReinforcements')` will return all units in the region

        Args:
            region: region in question
            nid (optional): used to match for NID
            team (optional): used to match for team. one of 'player', 'enemy', 'enemy2', 'other'
            tag (optional): used to match for tag.

        Returns:
            List[UnitObject]: all units matching the criteria in the region
        
  ---------------------


#### Get Units Within Distance

    get_units_within_distance(position, dist: 'int' = 1, nid=None, team=None, tag=None, party=None) 
		-> 'List[Tuple[UnitObject, int]]'

Return a list containing all units within `dist` distance to the specific position
        that match specific criteria

        Args:
            position: position or unit
            dist (int, optional): How far to search. Defaults to 1.
            nid (optional): use to check specific unit nid
            team (optional): used to match for team. one of 'player', 'enemy', 'enemy2', 'other'
            tag (optional): used to match for tag.
            party (optional): used to match for party

        Returns:
            List[Tuple[UnitObject, int]]: Returns all pairs of `(unit, distance)`
            within the specified `dist` that match criteria.
        
  ---------------------


## Skills



#### Get Debuff Count

    get_debuff_count(unit) 
		-> 'int'

Checks how many negative skills the unit has.

        Args:
            unit: Unit in question

        Returns:
            int: Number of unique negative skills on the unit
        
  ---------------------


#### Get Skill

    get_skill(unit, skill) 
		-> 'Optional[SkillObject]'

Returns a skill object by nid.

        Args:
            unit: unit in question
            skill: nid of skill

        Returns:
            Optional[SkillObject] | None: Skill, if exists on unit, else None.
        
  ---------------------


#### Has Skill

    has_skill(unit, skill) 
		-> 'bool'

checks if unit has skill

        Args:
            unit: unit to check
            skill: skill to check

        Returns:
            bool: True if unit has skill, else false
        
  ---------------------


## Units



#### Get Support Rank

    get_support_rank(unit1, unit2) 
		-> 'Optional[NID]'

Returns the most recently obtained support rank between two units.

        Args:
            unit1: unit in the support pair
            unit2: the other unit in the support pair

        Returns:
            Rank nid: if the two units have achieved a support rank.
            none: if the support pair is invalid or no rank has been obtained
        
  ---------------------


#### Is Dead

    is_dead(unit) 
		-> 'bool'

checks if unit is dead

        Args:
            unit: unit to check

        Returns:
            bool: if the unit has died
        
  ---------------------


#### U

    u(unit) 
		-> 'Optional[UnitObject]'

Shorthand for game.get_unit. Fetches the unit object.

        Args:
            unit: unit nid

        Returns:
            Optional[UnitObject]: the actual unit object, if exists, else None
        
  ---------------------


## VARIABLES



#### V

    v(varname, fallback=None) 
		-> 'Any'

shorthand for game.level_vars.get and game.game_vars.get. Fetches the variable
        if game.level_vars and game.game_vars share an identical name,
        game.level_vars takes priority

        Args:
            varname: name of the variable
            fallback: fallback value, if any. Defaults to None

        Returns:
            Any: the value of the variable
        
  ---------------------

