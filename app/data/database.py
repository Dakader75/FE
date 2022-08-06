import os
import json

from app.data import constants, stats, equations, tags, weapons, factions, terrain, mcost, \
    minimap, items, klass, units, parties, ai, difficulty_modes, translations, skills, levels, \
    lore, supports, overworld, overworld_node
from app.events import event_prefab

import logging

class Database(object):
    save_data_types = ("constants", "stats", "equations", "mcost", "terrain", "weapon_ranks",
                       "weapons", "factions", "items", "skills", "tags", "classes", 
                       "support_constants", "support_ranks", "affinities", "units", "support_pairs",
                       "ai", "parties", "difficulty_modes",
                       "translations", "lore", "levels", "events", "overworlds")

    def __init__(self):
        self.constants = constants.constants
        self.teams = ["player", "enemy", "enemy2", "other"]  # Order determine phase order
        self.stats = stats.StatCatalog()
        self.equations = equations.EquationCatalog()
        self.mcost = mcost.McostGrid()
        self.terrain = terrain.TerrainCatalog()
        self.minimap = minimap.MinimapCatalog()
        self.weapon_ranks = weapons.RankCatalog()
        self.weapons = weapons.WeaponCatalog()
        self.factions = factions.FactionCatalog()
        self.items = items.ItemCatalog()
        self.skills = skills.SkillCatalog()
        self.tags = tags.TagCatalog(['Lord', 'Boss', 'Armor', 'Horse', 'Mounted', 'Dragon', 'ZeroMove', 'AutoPromote', 'NoAutoPromote'])
        self.classes = klass.ClassCatalog()

        self.support_constants = supports.constants
        self.support_ranks = supports.SupportRankCatalog(['C', 'B', 'A'])
        self.affinities = supports.AffinityCatalog()

        self.units = units.UnitCatalog()

        self.support_pairs = supports.SupportPairCatalog()

        self.parties = parties.PartyCatalog()
        self.ai = ai.AICatalog()
        self.difficulty_modes = difficulty_modes.DifficultyModeCatalog()
        
        self.overworlds = overworld.OverworldCatalog()

        self.levels = levels.LevelCatalog()
        self.events = event_prefab.EventCatalog()

        self.translations = translations.TranslationCatalog()
        self.lore = lore.LoreCatalog()

    # === Saving and loading important data functions ===
    def restore(self, save_obj):
        for data_type in self.save_data_types:
            logging.info("Database: Restoring %s..." % data_type)
            getattr(self, data_type).restore(save_obj[data_type])

    def save(self):
        # import time
        to_save = {}
        for data_type in self.save_data_types:
            # logging.info("Saving %s..." % data_type)
            # time1 = time.time_ns()/1e6
            to_save[data_type] = getattr(self, data_type).save()
            # time2 = time.time_ns()/1e6 - time1
            # logging.info("Time taken: %s ms" % time2)
        return to_save

    def serialize(self, proj_dir):
        data_dir = os.path.join(proj_dir, 'game_data')
        if not os.path.exists(data_dir):
            os.mkdir(data_dir)
        logging.info("Serializing data in %s..." % data_dir)

        import time
        start = time.time_ns()/1e6

        to_save = self.save()
        # This section is what takes so long!
        for key, value in to_save.items():
            temp_save_loc = os.path.join(data_dir, key + '_temp.json')
            save_loc = os.path.join(data_dir, key + '.json')
            logging.info("Serializing %s to %s" % (key, save_loc))
            with open(temp_save_loc, 'w') as serialize_file:
                json.dump(value, serialize_file, indent=4)
            os.replace(temp_save_loc, save_loc)

        end = time.time_ns()/1e6
        logging.info("Total Time Taken for Database: %s ms" % (end - start))
        logging.info("Done serializing!")

    def load(self, proj_dir):
        data_dir = os.path.join(proj_dir, 'game_data')
        logging.info("Deserializing data from %s..." % data_dir)

        save_obj = {}
        for key in self.save_data_types:
            save_loc = os.path.join(data_dir, key + '.json')
            if os.path.exists(save_loc):
                logging.info("Deserializing %s from %s" % (key, save_loc))
                with open(save_loc) as load_file:
                    save_obj[key] = json.load(load_file)
            else:
                logging.warning("%s does not exist!" % save_loc)
                save_obj[key] = []

        self.restore(save_obj)
        logging.info("Done deserializing!")

DB = Database()

# Testing
# Run "python -m app.data.database" from main directory
