import os
import shutil

from app.resources.base_catalog import ManifestCatalog

class MapSprite():
    def __init__(self, nid, stand_full_path=None, move_full_path=None):
        self.nid = nid
        self.stand_full_path = stand_full_path
        self.move_full_path = move_full_path
        self.standing_image = None
        self.moving_image = None
        self.standing_pixmap = None
        self.moving_pixmap = None

    def set_stand_full_path(self, full_path):
        self.stand_full_path = full_path

    def set_move_full_path(self, full_path):
        self.move_full_path = full_path

    def save(self):
        return self.nid

    @classmethod
    def restore(cls, s):
        self = cls(s)
        return self

class MapSpriteCatalog(ManifestCatalog[MapSprite]):
    manifest = 'map_sprites.json'
    title = 'map sprites'
    datatype = MapSprite

    def load(self, loc):
        map_sprite_dict = self.read_manifest(os.path.join(loc, self.manifest))
        for s_dict in map_sprite_dict:
            new_map_sprite = MapSprite.restore(s_dict)
            new_map_sprite.set_stand_full_path(os.path.join(loc, new_map_sprite.nid + '-stand.png'))
            new_map_sprite.set_move_full_path(os.path.join(loc, new_map_sprite.nid + '-move.png'))
            self.append(new_map_sprite)

    def save(self, loc):
        for map_sprite in self:
            # Stand sprite
            new_full_path = os.path.join(loc, map_sprite.nid + '-stand.png')
            if os.path.abspath(map_sprite.stand_full_path) != os.path.abspath(new_full_path):
                shutil.copy(map_sprite.stand_full_path, new_full_path)
                map_sprite.set_stand_full_path(new_full_path)
            # Move sprite
            new_full_path = os.path.join(loc, map_sprite.nid + '-move.png')
            if os.path.abspath(map_sprite.move_full_path) != os.path.abspath(new_full_path):
                shutil.copy(map_sprite.move_full_path, new_full_path)
                map_sprite.set_move_full_path(new_full_path)
        self.dump(loc)

    def valid_files(self) -> set:
        valid_filenames = {datum.nid + '-stand.png' for datum in self}
        valid_filenames |= {datum.nid + '-move.png' for datum in self}
        return valid_filenames
