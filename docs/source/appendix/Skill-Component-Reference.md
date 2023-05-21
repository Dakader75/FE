# Skill Component Dictionary

The item components in this dictionary are broken down by icon going from left to right, with each icon's aspects being explained top to bottom.

## Attribute Components

| Component | Description |
| ------ | ------ |
| **Hidden** |  The skill/status will not appear anywhere in the unit's info menu. |
| **Class Skill** |  The skill/status will appear in the unit's 'personal data' page in their info menu, rather than on the 'weapon and support level' page. |
| **Stack** |  The skill/status can be applied multiple times. Useful when creating skills such as "+1 Strength every time an enemy is defeated". |
| **Feat** |  The skill/status can be selected as a _Feat_.  |
| **Negative** |  Skill/status is considered _Detrimental_. This status cannot be applied to a unit with any skill using the "ImmuneStatus" skill component. This status can be cleared by an item using the "Restore" item component. |
| **Global** |  All units will be affected by this skill/status. |
| **Negate** |  Negates all effective damage. |
| **Negate Tags** |  Negates effective damage against the specified tags. For example, to recreate Iote's shield, we would select the "Flying" tag. |

## Base Components

| Component | Description |
| ------ | ------ |
| **Unselectable** |  Unit cannot be selected by the player. A use case would be for a berserked ally. |
| **Cannot Use Items** |  The unit cannot use nor equip any items. |
| **Cannot Use Magic Items** |  The unit cannot use nor equip any items that have the "Magic" item component. Also prevents using items with the "Magic At Range" component from greater than range 1. |
| **Additional Accessories** |  Trades item slots for accessory slots. |
| **Ignore Alliances** |  The affected unit can attack any team. Useful for stuff like Thracia Green units that could attack the player. |
| **Change AI** |  Changes the unit's AI to the one specified. Can accept any AI setting, including those made with the AI editor. |
| **Change Buy Price** |  Multiplies shop prices by the value given for the affected unit. For a Silver Card, one would use a value of .50 (i.e., 50% of the normal price). |
| **Exp Multiplier** |  Multiplies the amount of EXP the affected unit receives by the specified value. For Paragon, one would enter a value of 2.00 (i.e., 200% of the normal amount). |
| **Enemy Exp Multiplier** |  Alters the amount of EXP this unit gives. For Void Curse, one would give this a value of 0.00 and assign it to enemies. These enemies now give no EXP when fought. |
| **Wexp Multiplier** |  Multiplies the amount of WEXP the affected unit receives by the specified value. |
| **Can Use Weapon Type** |  Allows usage of the specified weapon type. Do note that the unit will still need a WEXP value above 0 for this to work. This component exists to allow a class to wield a weapon they normally could not use. For example, if Franz had 1 Axe WEXP and did not have this component, he would still not be able to use an Iron Axe. Once this component is applied, he will be able to use the Iron Axe.
| **Enemy Wexp Multiplier** |  Alters the amount of WEXP that units besides the affected unit receives, by the specified value. |
| **Locktouch** |  Gives the affected unit the ability to unlock. `can_unlock` will return True for this unit, allowing them to interact with regions that use `can_unlock` as a condition. Refer to the eventing tutorials for more details. |
| **Sight Range Bonus** |  Unit can illuminate additional spaces when Fog of War is active. |
| **Decreasing Sight Range Bonus** |  Unit can illuminate additional spaces when Fog of War is active. This bonus lowers by 1 every turn. |
| **Ignore Fatigue** |  The affected unit will not accumulate Fatigue. |

## Movement Components

| Component | Description |
| ------ | ------ |
| **Canto** |  Unit can move again after certain actions, excluding actions such as attacking or healing. |
| **Canto Plus** | Unit can move again after any action, including attacks. |
| **Canto Sharp** | Unit can move and attack in either order. Prevents units from moving, attacking, and then using canto. |
| **Movement Type** | Unit will have a non-default movement type. Commonly used for flying or pirates. |
| **Pass** | Unit can move through enemies. |
| **Ignore Terrain** | Unit will not be affected by terrain in any way. |
| **Ignore Rescue Penalty** | Unit will ignore the rescue penalty. |
| **Grounded** | Unit cannot be forcibly moved such as through shove or reposition. |
| **No Attack After Move** | Unit can either move or attack, but not both. |

## Combat Components

| Component | Description |
| ------ | ------ |
| **Stat Change** | Gives integer increases to the specified stats. Used by tiles to give defense bonuses. |
| **Stat Multiplier** | Multiplies the specified stat by a given value. |
| **Growth Change** | Gives integer increases to the growth rates of specified stats. |
| **Equation Growth Change** | Increases the growth of all of a units stats by the specified equation. Must evaluate to an integer. |
| **Damage** | Unit deals X more damage on attacks, where X is the specified integer value. |
| **Eval Damage** | Unit deals X more damage on attacks, where X is the result of the given equation. The equation must evaluate to an integer. |
| **Resist** | Unit gains X more resist, where X is the specified integer value. Resist includes both defense and resistance since it modifies the DEFENSE and MAGIC_DEFENSE equations. |
| **Hit** | Unit gains X more hit, where X is the specified integer. |
| **Avoid** | Unit gains X more avoid, where X is the specified integer. |
| **Crit** | Unit gains X more critical chance, where X is the specified integer. |
| **Crit Avoid** | Unit gains X more critical avoid, where X is the specified integer. Critical avoid is subtracted from the opponent's critical chance. |
| **Attack Speed** | Unit gains X more attack speed, where X is the specified integer. A unit's attack speed is their speed for the purpose of determining whether they are able to double an opponent. |
| **Defense Speed** | Unit gains X more defense speed, where X is the specified integer.  A unit's defense speed is their speed for the purpose of determining whether they are doubled by an opponent. |
| **Damage Multiplier** | Multiplies damage dealt by the specified decimal number. |
| **Dynamic Damage Multiplier** | Multiplies damage dealt by the result of the given equation. Equation must evaluate to either an integer or floating point number. |
| **Resist Multiplier** | Multiplies damage taken by the specified decimal number. |
| **PCC** | Multiplies critical chance by the chosen stat on any strike after the first. |

## Advanced Combat Components

| Component | Description |
| ------ | ------ |
| **Miracle** | Unit cannot be reduced below 1 HP. Often used with the charges system or Proc Rate component. |
| **Ignore Damage** | Unit cannot take damage. HP can still be set via event. |
| **Live to Serve** | Unit heals self X% of healing given to others. |
| **Lifetaker** | Unit heals self X% of max HP after a kill. |
| **Lifelink** | Unit heals self X% of damage dealt to others, such as with Nosferatu or Sol. |
| **Ally Lifelink** | Unit heals adjacent allies X% of damage dealt to others. |
| **Armsthrift** | Attacking with a weapon restores X uses on hit. Uses will not be restored above max. |
| **Limit Maximum Range** | Caps the unit's maximum range with any item to X. |
| **Modify Maximum Range** | Adjusts the maximum range of any item wielded by the unit by X. |
| **Eval Maximum Range** | Functions as Modify Maximum Range, but by providing an equation. |
| **Cannot Double** | Cmon bruh. |
| **Can Double on Defense** | Only meant to be used when units are prevented from doubling on defense through the Constants editor. |
| **Vantage** | Unit attacks first when defending. If two units with Vantage fight, the defender always attacks first. |
| **Guaranteed Crit** | Unit will always crit even if critical hits are turned off in Constants. |
| **Distant Counter** | Unit can counter an attack from any range regardless of weapon effective range. |
| **Cleave** | Unit's attacks will hit all enemies within 1 tile (diagonals included). Functions identically to the Enemy Cleave AoE item component. |
| **Give Status After Combat** | The target is granted the skill after combat, even if the unit did not hit or even attack at all. |
| **Give Status After Attack** | The target is granted the skill after combat if the unit was the attacker, even if the unit does not hit. |
| **Give Status On Hit** | The target is granted the skill after being hit, even if combat has not yet ended. |
| **Gain Skill After Kill** | The unit is granted the skill after killing a target in combat. |
| **Gain Skill After Attacking** | The unit is granted the skill after combat if the unit was the attacker, even if the unit does not hit. |
| **Gain Skill After Active Kill** | The unit is granted the skill after killing a target in combat that the unit initiated. |
| **Delay Initiative Order** | Delays the target's turn by X. Only applies when attacking. |
| **Recoil** | Unit takes X nonlethal damage after combat. |
| **Post Combat Damage** | Target takes X nonlethal damage after combat. |
| **Post Combat Damage Percent** | Target takes X% of max HP nonlethal damage after combat. |
| **Post Combat Splash** | Enemies within AoE range of target take X nonlethal damage after combat. AoE range is defined by the Post Combat Splash AOE component. |
| **Post Combat Splash AOE** | Enemies within X range of target take nonlethal damage after combat as defined by the Post Combat Splash component. |

## Status Components

| Component | Description |
| ------ | ------ |
| **Aura** | Grants skill to qualifying units within aura range. |
| **Aura Range** | Associated aura spreads out to targets within X tiles of unit. |
| **Aura Target** | Must be ally, enemy, or unit. Enemy encompasses both enemy types (enemy, enemy2), while unit encompasses all units. |
| **Pair Up Bonus** | While this unit is the sub unit in guard stance, grants skill to the main unit. |
| **Regeneration** | Unit restores X% of max HP at the beginning of its phase/turn. |
| **Mana Regeneration** | Unit restores X mana at the beginning of its phase/turn. |
| **Upkeep Damage** | Unit takes X damage at the beginning of its phase/turn. Can be lethal. |
| **Endstep Damage** | Unit takes X damage at the beginning of its phase/turn. Can be lethal. |
| **GBAPoison** | Unit randomly takes 1 to X damage at the beginning of its phase/turn. Can be lethal. |
| **Resist Status** | Other skills gained with a time component of duration 2 or greater have that duration decreased to 1 turn. |
| **Immune Status** | Unit cannot acquire skills with the Negative component. |
| **Reflect Status** | When the unit acquires a skill with a Negative component, causes the granter of that skill to also receive it. Does *not* prevent acquisition of the Negative skill. |