
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
