# Breakable Walls

_last updated v0.1_

Weirdly enough, breakable walls in the **Lex Talionis** are not created using tiles or regions, but rather are invisible units you place on the map on top of the wall tile.

Since the breakable wall is a unit, it can interact in interesting ways with all the items and skills you have in your game.

## Creating a breakable wall

![WallClass](images/WallClass.png)

1. Create a "Wall" class. The wall class should use an invisible map sprite. The HP of the "Wall" class determines the HP of the resulting breakable wall.

![NoAvoidSkill](images/NoAvoidSkill.png)

2. If you want the "Wall" to behave like a GBA wall where it can't be doubled, can't be crit, and cannot avoid attacks, you'll need to give it a skill that gives it a lot of defense speed, a lot of crit avoid and a negative amount of regular avoid.

3. For the chapter you want the wall to be present in, create a generic unit of the "Wall" class for each wall.

![BreakableWallEvent](images/BreakableWallEvent.png)

4. Now, you just need to catch the wall's death event and do something when the wall dies.

```
# Show destruction anim
map_anim;Snag;{position}
# Show the new layer
show_layer;Breakable1
```
