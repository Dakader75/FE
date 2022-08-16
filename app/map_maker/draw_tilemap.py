from PyQt5.QtCore import QDateTime
from PyQt5.QtGui import QImage, QPainter, QPixmap, QColor

from app.constants import TILEWIDTH, TILEHEIGHT

from app.map_maker.map_prefab import MapPrefab
from app.map_maker.terrain_database import DB_terrain
from app.map_maker.utilities import random_choice

def get_tilemap_pixmap(tilemap) -> QPixmap:
    return QPixmap.fromImage(draw_tilemap(tilemap))

def draw_tilemap(tilemap: MapPrefab, autotile_fps=29) -> QImage:
    image = QImage(tilemap.width * TILEWIDTH,
                   tilemap.height * TILEHEIGHT,
                   QImage.Format_ARGB32)
    image.fill(QColor(0, 0, 0, 0))

    painter = QPainter()
    painter.begin(image)
    ms = QDateTime.currentMSecsSinceEpoch()

    # Only process the ones that need to be updated
    processed_nids = set()
    for pos in sorted(tilemap.terrain_grid_to_update):
        terrain_nid = tilemap.get_terrain(pos)
        if not terrain_nid:
            continue
        terrain = DB_terrain.get(terrain_nid)
        if terrain_nid not in processed_nids:
            terrain.single_process(tilemap)
            processed_nids.add(terrain_nid)
        determine_sprite(pos, terrain, tilemap)

    # Draw the tile grid
    for pos, tile_coord in tilemap.tile_grid.items():
        terrain_pos = (pos[0]//2, pos[1]//2)
        terrain_nid = tilemap.get_terrain(terrain_pos)
        if not terrain_nid:
            continue
        terrain = DB_terrain.get(terrain_nid)
        pix = terrain.get_pixmap(tile_coord, ms, autotile_fps)
        assert pix.width() == TILEWIDTH//2, pix.width()
        assert pix.height() == TILEHEIGHT//2, pix.height()
        painter.drawPixmap(pos[0] * TILEWIDTH//2,
                           pos[1] * TILEHEIGHT//2,
                           pix)
    painter.end()

    # Make sure we don't need to update it anymore
    tilemap.terrain_grid_to_update.clear()

    return image

def determine_sprite(pos: tuple, terrain, tilemap) -> tuple:
    """
    pos is in terrain space (16x16)
    """
    def _push_to_tilemap(pos: tuple, new_coords: tuple):
        """
        pos is in tile space (8x8)
        """
        # if tilemap.tile_grid.get(pos) in new_coords:
        #     pass
        # else:
        #     new_coord = random.choice(new_coords)
        #     tilemap.tile_grid[pos] = new_coord
        new_coord = random_choice(new_coords, pos)
        tilemap.tile_grid[pos] = new_coord

    new_coords1, new_coords2, new_coords3, new_coords4 = \
        terrain.determine_sprite_coords(tilemap, pos)

    _push_to_tilemap((pos[0] * 2, pos[1] * 2), new_coords1)
    _push_to_tilemap((pos[0] * 2 + 1, pos[1] * 2), new_coords2)
    _push_to_tilemap((pos[0] * 2 + 1, pos[1] * 2 + 1), new_coords3)
    _push_to_tilemap((pos[0] * 2, pos[1] * 2 + 1), new_coords4)
