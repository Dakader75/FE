import os

from app import sprites

from app.resources.fonts import FontCatalog
from app.resources.icons import Icon16Catalog, Icon32Catalog, Icon80Catalog
from app.resources.portraits import PortraitCatalog
from app.resources.animations import AnimationCatalog
from app.resources.panoramas import PanoramaCatalog
from app.resources.map_icons import MapIconCatalog
from app.resources.map_sprites import MapSpriteCatalog
from app.resources.tiles import TileSetCatalog, TileMapCatalog
from app.resources.sounds import SFXCatalog, MusicCatalog
from app.resources.combat_palettes import PaletteCatalog
from app.resources.combat_anims import CombatCatalog, CombatEffectCatalog

import logging

class Resources():
    save_data_types = ("icons16", "icons32", "icons80", "portraits", "animations", "panoramas",
                       "map_icons", "map_sprites", "combat_palettes", "combat_anims", "combat_effects", "music", "sfx",
                       "tilesets", "tilemaps")

    def __init__(self):
        self.main_folder = None

        # Modifiable Resources
        self.clear()

        # Standardized, Locked resources
        self.load_standard_resources()

    def load_standard_resources(self):
        self.platforms = self.get_sprites('resources', 'platforms')
        self.fonts = FontCatalog()
        self.fonts.load('resources/fonts')

    def get_sprites(self, home, sub):
        s = {}
        loc = os.path.join(home, sub)
        for root, dirs, files in os.walk(loc):
            for name in files:
                if name.endswith('.png'):
                    full_name = os.path.join(root, name)
                    s[name[:-4]] = full_name
        return s

    def get_platform_types(self):
        names = list(sorted({fn.split('-')[0] for fn in self.platforms.keys()}))
        sprites = [n + '-Melee' for n in names]
        return list(zip(names, sprites))

    def clear(self):
        self.icons16 = Icon16Catalog()
        self.icons32 = Icon32Catalog()
        self.icons80 = Icon80Catalog()

        self.portraits = PortraitCatalog()
        self.animations = AnimationCatalog()

        self.panoramas = PanoramaCatalog()
        self.map_icons = MapIconCatalog()
        self.map_sprites = MapSpriteCatalog()
        self.combat_palettes = PaletteCatalog()
        self.combat_anims = CombatCatalog()
        self.combat_effects = CombatEffectCatalog()

        self.tilesets = TileSetCatalog()
        self.tilemaps = TileMapCatalog()

        self.music = MusicCatalog()
        self.sfx = SFXCatalog()

    def load(self, proj_dir, specific=None):
        self.main_folder = os.path.join(proj_dir, 'resources')

        # Load custom sprites for the UI
        # This should overwrite the regular sprites in the "/sprites" folder
        sprites.reset()
        sprites.load_sprites(os.path.join(self.main_folder, 'custom_sprites'))

        if specific:
            save_data_types = specific
        else:
            save_data_types = self.save_data_types
        for data_type in save_data_types:
            logging.info("Loading %s from %s..." % (data_type, self.main_folder))
            getattr(self, data_type).clear()  # Now always clears first
            getattr(self, data_type).load(os.path.join(self.main_folder, data_type))

    def save(self, proj_dir, specific=None, progress=None):
        logging.warning("Starting Resource Serialization...")
        import time
        start = time.time_ns()/1e6
        # Make the directory to save this resource pack in
        if not os.path.exists(proj_dir):
            os.mkdir(proj_dir)
        resource_dir = os.path.join(proj_dir, 'resources')
        if not os.path.exists(resource_dir):
            os.mkdir(resource_dir)

        if specific == 'autosave':
            save_data_types = list(self.save_data_types)
            save_data_types.remove('music')
            save_data_types.remove('sfx')
            save_data_types = tuple(save_data_types)
        elif specific:
            save_data_types = specific
        else:
            save_data_types = self.save_data_types
        for idx, data_type in enumerate(save_data_types):
            data_dir = os.path.join(resource_dir, data_type)
            if not os.path.exists(data_dir):
                os.mkdir(data_dir)
            logging.warning("Saving %s..." % data_type)
            time1 = time.time_ns()/1e6
            getattr(self, data_type).save(data_dir)
            time2 = time.time_ns()/1e6 - time1
            logging.warning("Time Taken: %s ms" % time2)
            if progress:
                progress.setValue(int(idx / len(save_data_types) * 75))

        end = time.time_ns()/1e6
        logging.warning("Total Time Taken for Resources: %s ms" % (end - start))
        logging.warning('Done Resource Serializing!')

    def clean(self, proj_dir) -> bool:
        """
        Returns bool -> whether cleaning was successful
        """
        logging.warning("Starting Resource Cleaning...")
        import time
        start = time.time_ns()/1e6

        if not os.path.exists(proj_dir):
            return False
        resource_dir = os.path.join(proj_dir, 'resources')
        if not os.path.exists(resource_dir):
            return False

        for idx, data_type in enumerate(self.save_data_types):
            data_dir = os.path.join(resource_dir, data_type)
            if not os.path.exists(data_dir):
                continue
            try:
                getattr(self, data_type).clean(data_dir)
            except Exception as e:
                logging.exception(e)
                logging.error("Could not successfully clean %s" % data_type)

        end = time.time_ns() / 1e6
        logging.warning("Total Time Taken for cleaning resource directory: %s ms" % (end - start))
        logging.warning("Done Resource Cleaning!")
        return True

RESOURCES = Resources()

# Testing
# Run "python -m app.resources.resources" from main directory
