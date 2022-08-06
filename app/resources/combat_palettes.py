import os
from app.utilities.data import Prefab
from app.resources.base_catalog import ManifestCatalog

from app.constants import COLORKEY

class Palette(Prefab):
    def __init__(self, nid):
        self.nid = nid
        # Mapping of color indices to true colors
        # Color indices are generally (0, 1) -> (240, 160, 240), etc.
        self.colors = {(0, 0): COLORKEY}

    def is_similar(self, colors) -> bool:
        counter = 0
        my_colors = [color for coord, color in self.colors.items()]
        for color in colors:
            if color in my_colors:
                counter += 1
        # Similar if more than 75% of colors match
        return (counter / len(colors)) > .75

    def assign_colors(self, colors: list):
        self.colors = {
            (int(idx % 8), int(idx / 8)): color for idx, color in enumerate(colors)
        }

    def save(self):
        return (self.nid, list(self.colors.items()))

    @classmethod
    def restore(cls, s):
        self = cls(s[0])
        self.colors = {tuple(k): tuple(v) for k, v in s[1].copy()}
        return self

class PaletteCatalog(ManifestCatalog[Palette]):
    datatype = Palette
    manifest = 'palettes.json'
    title = 'palettes'

    def load(self, loc):
        true_loc = os.path.join(loc, self.manifest)
        if not os.path.exists(true_loc):
            return
        palette_dict = self.read_manifest(true_loc)
        for s_dict in palette_dict:
            new_palette = Palette.restore(s_dict)
            self.append(new_palette)

    def save(self, loc):
        # No need to finagle with full paths
        # Because Palettes don't have any connection to any actual file.
        self.dump(loc)
