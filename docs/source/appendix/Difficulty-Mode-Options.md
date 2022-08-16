# Difficulty Mode Options

## Permadeath

- **Casual**: When a unit reaches 0 HP, they are removed from the map for the current chapter, but will be available next map.
- **Classic**: When a unit reaches 0 HP, they die permanently.

## Growth Method

All units have a specific growth rate for each of their stats. This growth rate determines the likelihood that the unit will gain a point in that stat on level-up. A growth rate greater than or equal to 100% guarantees a point on each level-up. A growth rate lower than 0% indicates a chance for the unit to *lose* points in that stat on level-up.

- **Random**: Truly random growths. For each stat, a random number is rolled between 0 and 99. If the number is less than the growth rate, that stat increases.
- **Fixed**: Units will always have their average stats. A unit with a 50% growth rate is guaranteed to get a stat increase every other level.
- **Dynamic**: Like **Random**, but it applies a rubberbanding effect to the growth rate. If a unit fails to increase a stat on level-up, next level-up that stat will have a higher effective growth rate.

## RNG Method

This determines how the engine decides whether an attack is a hit or a miss.

- **Classic**: Used in FE1-5. No modifications. A 70% displayed chance to hit is exactly a 70% real chance to hit.
- **True Hit**: Used in FE6-13. The engine generates two random numbers and averages them. This makes displayed chances to hit above 50% more likely than expected, and those lower than 50% less likely than expected. A 70% displayed chance to hit is actually 82.3%.
- **True Hit+**: Like **True Hit**, but the engine generates *three* random numbers and averages them. A 70% displayed chance to hit is actually 88.2%.
- **Grandmaster**: All attacks hit. However, the damage an attack deals is multiplied by the displayed chance to hit. An attack that deals 10 damage with a 70% displayed chance to hit will always hit, dealing 7 damage.


