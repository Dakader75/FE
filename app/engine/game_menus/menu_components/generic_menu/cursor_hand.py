

from enum import Enum
from app.engine import engine
from app.sprites import SPRITES

class CursorDrawMode(Enum):
  NO_DRAW = 0
  DRAW = 1
  DRAW_STATIC = 2

class CursorHand():
  def __init__(self) -> None:
    self.cursor_sprite = SPRITES.get('menu_hand')
    self.offsets = [0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 3, 3, 2, 2, 2, 1, 1, 1, 1]
    self.offset_index = 0
    self.mode: CursorDrawMode = CursorDrawMode.DRAW

  def get_offset(self):
    return self.offsets[self.offset_index]

  def update(self):
    self.offset_index = (self.offset_index + 1) % len(self.offsets)

  def draw(self, surf, topleft) -> engine.Surface:
    x, y = topleft
    engine.blit(surf, self.cursor_sprite, (x + self.get_offset(), y))
    return surf