from __future__ import annotations
from enum import Enum

class Direction(Enum):
    LEFT = 0
    UP = 1
    RIGHT = 2
    DOWN = 3

    UP_LEFT = 4
    UP_RIGHT = 5
    DOWN_RIGHT = 6
    DOWN_LEFT = 7

    NONE = -1

    @classmethod
    def parse_map_direction(cls, x, y) -> Direction:
        if x > 0:
            if y > 0:
                return Direction.DOWN_RIGHT
            elif y == 0:
                return Direction.RIGHT
            elif y < 0:
                return Direction.UP_RIGHT
        elif x == 0:
            if y > 0:
                return Direction.DOWN
            elif y == 0:
                return Direction.NONE
            elif y < 0:
                return Direction.UP
        elif x < 0:
            if y > 0:
                return Direction.DOWN_LEFT
            elif y == 0:
                return Direction.LEFT
            elif y < 0:
                return Direction.UP_LEFT

    @classmethod
    def which_vertical_dir(cls, direction: Direction) -> int:
        if (direction == Direction.UP or
            direction == Direction.UP_LEFT or
            direction == Direction.UP_RIGHT):
            return 1
        elif (direction == Direction.DOWN or
             direction == Direction.DOWN_LEFT or
             direction == Direction.DOWN_RIGHT):
            return -1
        else:
            return 0

    @classmethod
    def which_horizontal_dir(cls, direction:Direction) -> int:
        if (direction == Direction.UP_LEFT or
            direction == Direction.DOWN_LEFT or
            direction == Direction.LEFT):
            return -1
        elif (direction == Direction.RIGHT or
             direction == Direction.UP_RIGHT or
             direction == Direction.DOWN_RIGHT):
            return 1
        else:
            return 0