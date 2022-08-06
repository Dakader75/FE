from app.utilities.data import Prefab

region_types = ['normal', 'status', 'event', 'formation']

class Region(Prefab):
    def __init__(self, nid):
        self.nid = nid
        self.region_type = 'normal'
        self.position = None
        self.size = [1, 1]

        self.sub_nid = None
        self.condition = 'True'
        self.only_once = False

    @property
    def area(self):
        return self.size[0] * self.size[1]

    @property
    def center(self) -> tuple:
        if self.position:
            x = int(self.position[0] + self.size[0] // 2)
            y = int(self.position[1] + self.size[1] // 2)
            return x, y
        else:
            return None
    
    def contains(self, pos: tuple) -> bool:
        x, y = pos
        if self.position:
            return self.position[0] <= x < self.position[0] + self.size[0] and \
                self.position[1] <= y < self.position[1] + self.size[1]
        else:
            return False

    def fuzzy_contains(self, pos: tuple) -> bool:
        x, y = pos
        fuzz = 0.4
        if self.position:
            return self.position[0] - fuzz <= x < self.position[0] + self.size[0] + fuzz and \
                self.position[1] - fuzz <= y < self.position[1] + self.size[1] + fuzz
        else:
            return False

    def get_all_positions(self):
        if self.position:
            positions = []
            for i in range(self.position[0], self.position[0] + self.size[0]):
                for j in range(self.position[1], self.position[1] + self.size[1]):
                    positions.append((i, j))
            return positions
        else:
            return []

    @classmethod
    def default(cls):
        return cls('None')
