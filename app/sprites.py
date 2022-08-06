import os
from dataclasses import dataclass

@dataclass
class BasicSprite(object):
    full_path: str = None
    pixmap: str = None
    image: str = None

class SpriteDict(dict):
    def get(self, val):
        if val in self:
            return self[val].image
        return None

def load_sprites(root):
    for root, dirs, files in os.walk(root):
        for name in files:
            if name.endswith('.png'):
                full_name = os.path.join(root, name)
                SPRITES[name[:-4]] = BasicSprite(full_name)

SPRITES = SpriteDict()
load_sprites('sprites/')

def reset():
    SPRITES.clear()
    load_sprites('sprites/')
