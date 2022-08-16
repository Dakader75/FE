try:
    import cPickle as pickle
except ImportError:
    import pickle

from app.map_maker.utilities import random_choice, find_bounding_rect
# import app.map_maker.dancing_links as dancing_links
import app.map_maker.rain_algorithm_x as rain_algorithm_x

class Generator():
    MAX_SIZE = 3
    NUM_VARIANTS = 10

    def __init__(self):
        self.seed = 0
        self.organization = {}
        self.to_process = []  # Keeps track of what tiles still need to be process for group
        self.order = []  # Keeps track of the order that tiles have been processed
        self.locked_values = {}  # Keeps track of what coords unfortunately don't work
        self.mountain_data = None
        self.terrain_grid = self.generate_simple_terrain_grid3()

        data_loc = 'app/map_maker/mountain_data.p'
        with open(data_loc, 'rb') as fp:
            self.mountain_data = pickle.load(fp)
        self.border_dict = {}  # Coord: Index (0-15)
        self.index_dict = {i: set() for i in range(16)}  # Index: Coord 
        self.noneless_rules = {}
        for coord, rules in self.mountain_data.items():
            north_edge = None in rules['up']
            south_edge = None in rules['down']
            east_edge = None in rules['right']
            west_edge = None in rules['left']
            index = 1 * north_edge + 2 * east_edge + 4 * south_edge + 8 * west_edge
            self.border_dict[coord] = index
            self.index_dict[index].add(coord)
            # Keep track of the rules when None is not present as well
            noneless_rules = {}
            noneless_rules['up'] = {k: v for k, v in rules['up'].items() if k is not None}
            noneless_rules['down'] = {k: v for k, v in rules['down'].items() if k is not None}
            noneless_rules['left'] = {k: v for k, v in rules['left'].items() if k is not None}
            noneless_rules['right'] = {k: v for k, v in rules['right'].items() if k is not None}
            self.noneless_rules[coord] = noneless_rules

        import time
        start = time.time_ns() / 1e6
        self.terrain_organization = (self.terrain_grid, [])
        # For each seed
        for idx in range(self.NUM_VARIANTS):
            print(idx)
            self.seed = idx
            self.organization.clear()
            # self.process_terrain_grid()
            self.process_algorithm_x()
            self.terrain_organization[1].append(self.organization.copy())
        total_time = time.time_ns() / 1e6 - start
        print("Total Time %f ms" % total_time)

    def generate_complex_terrain_grid(self) -> set:
        terrain_grid_example = {
            (0, 2), (0, 4), (0, 5), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6),
            (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7),
            (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6), (3, 7),
            (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (4, 6), (4, 7),
            (5, 0), (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (5, 6),
            (6, 1), (6, 2), (6, 3), (6, 4), (6, 5), (6, 6),
            (7, 4)
        }
        return frozenset(terrain_grid_example)

    def generate_simple_terrain_grid(self) -> set:
        terrain_grid_example = {
            (0, 0), (0, 1), (1, 0), (1, 1), (2, 0)
        }
        return frozenset(terrain_grid_example)

    def generate_simple_terrain_grid2(self) -> set:
        terrain_grid_example = {
            (0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)
        }
        return frozenset(terrain_grid_example)

    def generate_simple_terrain_grid3(self) -> set:
        terrain_grid_example = {
            (0, 2), (0, 4), (0, 5), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6),
            (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7),
            (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6), (3, 7)
        }
        return frozenset(terrain_grid_example)

    def determine_sprite_coords(self, tilemap, pos: tuple) -> tuple:
        new_coords = self.organization[pos]
        new_coords1 = [(new_coords[0]*2, new_coords[1]*2)]
        new_coords2 = [(new_coords[0]*2 + 1, new_coords[1]*2)]
        new_coords3 = [(new_coords[0]*2 + 1, new_coords[1]*2 + 1)]
        new_coords4 = [(new_coords[0]*2, new_coords[1]*2 + 1)]
        return new_coords1, new_coords2, new_coords3, new_coords4

    def find_valid_coord(self, pos) -> bool:
        north, east, south, west = self.get_cardinal_terrain(pos)
        north_edge = not north
        south_edge = not south
        east_edge = not east
        west_edge = not west
        valid_coords = \
            [coord for coord, rules in self.mountain_data.items() if
             ((north_edge and None in rules['up']) or (not north_edge and self.noneless_rules[coord]['up'])) and
             ((south_edge and None in rules['down']) or (not south_edge and self.noneless_rules[coord]['down'])) and
             ((east_edge and None in rules['right']) or (not east_edge and self.noneless_rules[coord]['right'])) and
             ((west_edge and None in rules['left']) or (not west_edge and self.noneless_rules[coord]['left']))]
        north_pos = (pos[0], pos[1] - 1)
        south_pos = (pos[0], pos[1] + 1)
        east_pos = (pos[0] + 1, pos[1])
        west_pos = (pos[0] - 1, pos[1])
        # print("*Valid Coord", pos, self.order)
        # print(sorted(valid_coords))
        # Remove locked coords
        if pos in self.locked_values:
            # print("Locked", sorted(self.locked_values[pos]))
            valid_coords = [coord for coord in valid_coords if coord not in self.locked_values[pos]]
        if not north_edge and north_pos in self.organization:
            chosen_coord = self.organization[north_pos]
            valid_coords = [coord for coord in valid_coords if coord in self.mountain_data[chosen_coord]['down']]
        if not south_edge and south_pos in self.organization:
            chosen_coord = self.organization[south_pos]
            valid_coords = [coord for coord in valid_coords if coord in self.mountain_data[chosen_coord]['up']]
        if not east_edge and east_pos in self.organization:
            chosen_coord = self.organization[east_pos]
            valid_coords = [coord for coord in valid_coords if coord in self.mountain_data[chosen_coord]['left']]
        if not west_edge and west_pos in self.organization:
            chosen_coord = self.organization[west_pos]
            valid_coords = [coord for coord in valid_coords if coord in self.mountain_data[chosen_coord]['right']]
        # print(sorted(valid_coords))
        if not valid_coords:
            # print("Reverting Order...")
            if pos in self.locked_values:
                del self.locked_values[pos]
            self.revert_order()
            # valid_coords = self.index_dict[15]
            return False
        valid_coord = random_choice(list(valid_coords), pos, self.seed)
        # print("Final", valid_coord)
        self.organization[pos] = valid_coord
        return True

    def revert_order(self):
        if not self.order:
            print("Major loop error! No valid solution")
            # Just fill it up with generic pieces
            for pos in self.to_process:
                valid_coords = self.index_dict[15]
                valid_coord = random_choice(list(valid_coords), pos, self.seed)
                self.organization[pos] = valid_coord
            self.to_process.clear()
            return

        pos = self.order.pop()
        coord = self.organization[pos]
        del self.organization[pos]
        self.to_process.insert(0, pos)
        if pos not in self.locked_values:
            self.locked_values[pos] = set()
        self.locked_values[pos].add(coord)
        # print("Locking ", coord, "for ", pos)

    def get_terrain(self, pos: tuple) -> bool:
        return pos in self.terrain_grid

    def get_cardinal_terrain(self, pos: tuple) -> tuple:
        north = self.get_terrain((pos[0], pos[1] - 1))
        east = self.get_terrain((pos[0] + 1, pos[1]))
        south = self.get_terrain((pos[0], pos[1] + 1))
        west = self.get_terrain((pos[0] - 1, pos[1]))
        return north, east, south, west

    def find_num_borders(self, pos) -> int:
        north, east, south, west = self.get_cardinal_terrain(pos)
        num_borders = sum((not north, not south, not east, not west))
        return num_borders

    def find_num_partners(self, pos) -> int:
        north_pos = (pos[0], pos[1] - 1)
        south_pos = (pos[0], pos[1] + 1)
        east_pos = (pos[0] + 1, pos[1])
        west_pos = (pos[0] - 1, pos[1])
        north_edge = north_pos in self.organization
        south_edge = south_pos in self.organization
        east_edge = east_pos in self.organization
        west_edge = west_pos in self.organization
        num_partners = sum((north_edge, south_edge, east_edge, west_edge))
        return num_partners

    def process_terrain_grid(self):
        # Determine coord 
        # print("--- Process Group ---")
        self.locked_values.clear()
        self.order.clear()
        self.to_process = sorted(self.terrain_grid)

        def process(seq):
            pos = seq[0]
            did_work = self.find_valid_coord(pos)
            if did_work:
                self.to_process.remove(pos)
                self.order.append(pos)
            self.to_process = sorted(self.to_process)

        while self.to_process:
            process(self.to_process)

    def find_valid_coords(self, pos) -> list:
        north, east, south, west = self.get_cardinal_terrain(pos)
        north_edge = not north
        south_edge = not south
        east_edge = not east
        west_edge = not west
        valid_coords = \
            [coord for coord, rules in self.mountain_data.items() if
             ((north_edge and None in rules['up']) or (not north_edge and self.noneless_rules[coord]['up'])) and
             ((south_edge and None in rules['down']) or (not south_edge and self.noneless_rules[coord]['down'])) and
             ((east_edge and None in rules['right']) or (not east_edge and self.noneless_rules[coord]['right'])) and
             ((west_edge and None in rules['left']) or (not west_edge and self.noneless_rules[coord]['left']))]
        return valid_coords

    def process_algorithm_x(self):
        self.to_process = sorted(self.terrain_grid)

        columns = [(pos, True) for pos in self.to_process]
        # valid_coords = [self.find_valid_coords(pos) for pos in self.to_process]
        valid_coords_dict = {pos: self.find_valid_coords(pos) for pos in self.to_process}

        rows = []
        row_names = []
        column_names = [pos for pos in self.to_process]

        for idx, pos in enumerate(self.to_process):
            right = (pos[0] + 1, pos[1])
            down = (pos[0], pos[1] + 1)
            for valid_coord in valid_coords_dict[pos]:
                row = [idx]
                rows.append(row)
                row_names.append((pos, valid_coord))

                # Right
                if right in valid_coords_dict:
                    invalid_coords_right = {coord for coord in valid_coords_dict[right] if coord not in self.mountain_data[valid_coord]['right']}
                    if invalid_coords_right:
                        identifier = (pos, right, valid_coord, invalid_coords_right)
                        column_names.append(identifier)
                        columns.append((identifier, False))
                        row.append(len(columns) - 1)

                # Down
                if down in valid_coords_dict:
                    invalid_coords_down = {coord for coord in valid_coords_dict[down] if coord not in self.mountain_data[valid_coord]['down']}
                    if invalid_coords_down:
                        identifier = (pos, down, valid_coord, invalid_coords_down)
                        column_names.append(identifier)
                        columns.append((identifier, False))
                        row.append(len(columns) - 1)

        # Now we have each column and row, the primary columns are completely filled
        # the secondary columns are halfway filled. They need their other sections to 
        # be filled to completion
        assert len(row_names) == len(rows)
        column_idxs_to_be_filled = range(len(self.to_process), len(columns))
        for cidx in column_idxs_to_be_filled:
            pos, partner_pos, valid_coord, invalid_coords = column_names[cidx]
            for ridx, row_name in enumerate(row_names):
                # Find the rows that apply to this partner pos and are in the set of invalid coords
                if partner_pos == row_name[0] and row_name[1] in invalid_coords:
                    # Add a 1 here
                    rows[ridx].append(cidx)

        # print("Column Names")
        # for c in columns:
        #     print(c[0])
        # print("Row Names")
        # for row_name in row_names:
        #     print(row_name)
        # print("Grid")
        # for idx, r in enumerate(rows):
        #     print(row_names[idx]),
        #     print(r)
        if self.seed == 0:
            print("Num Rows: %d, Num Cols: %d" % (len(rows), len(columns)))

        d = rain_algorithm_x.RainAlgorithmX(columns, row_names, rows, self.to_process[0], self.seed)
        output = d.solve()
        if output:
            for pos, coord in d.get_solution():
                self.organization[pos] = coord
        else:
            print("No valid solution!")

# Run from main lt-maker directory with
# python -m app.map_maker.mountain_generator
if __name__ == '__main__':
    import os, sys

    from PyQt5.QtGui import QImage, QColor, QPainter
    from PyQt5.QtWidgets import QApplication

    from app.constants import TILEWIDTH, TILEHEIGHT

    import cProfile
    pr = cProfile.Profile()

    app = QApplication(sys.argv)

    tileset = 'app/map_maker/palettes/westmarch/main.png'
    save_dir = 'app/map_maker/test_output/'
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    main_image = QImage(tileset)

    pr.enable()
    g = Generator()
    pr.disable()
    pr.print_stats(sort='time')
    key, terrain_grids = g.terrain_organization
    print(key)
    _, _, width, height = find_bounding_rect(key)

    for idx, terrain_grid in enumerate(terrain_grids):
        new_im = QImage(width * TILEWIDTH, height * TILEHEIGHT, QImage.Format_RGB32)
        new_im.fill(QColor(0, 0, 0))
        painter = QPainter()
        painter.begin(new_im)

        for pos, coord in terrain_grid.items():
            rect = (coord[0] * TILEWIDTH, coord[1] * TILEHEIGHT, TILEWIDTH, TILEHEIGHT)
            im = main_image.copy(*rect)
            painter.drawImage(pos[0] * TILEWIDTH, pos[1] * TILEHEIGHT, im)

        painter.end()

        h = str(hash(key))[:16]
        new_im.save(save_dir + ('%s_%02d.png' % (h, idx)))
