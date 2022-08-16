from collections import Counter

DIRECTIONS = ('left', 'right', 'up', 'down')

class MountainGroup():
    def __init__(self, coords: tuple):
        self.coords = frozenset(coords)
        self.rules = {}
        for direction in DIRECTIONS:
            self.rules[direction] = Counter()

        self.single_rules = {}
        for coord in self.coords:
            self.single_rules[coord] = {}

    def __hash__(self):
        return hash(self.coords)

    def has_rules(self) -> bool:
        return any(sum(self.rules[direction].values()) > 0 for direction in DIRECTIONS)

    def compile(self, individual_rules, groups):
        for coord, palette in individual_rules.items():
            if coord in self.coords:
                for direction in DIRECTIONS:
                    self.single_rules[coord][direction] = palette.rules[direction]
        # Now we have all the individual coords here
        for coord in self.coords:
            for direction in DIRECTIONS:
                connections = self.single_rules[coord].get(direction, {})
                for connection, value in connections.items():
                    for group in groups:
                        if connection in group:
                            self.rules[direction][frozenset(group)] += value
                    if connection is None:
                        self.rules[direction][None] += value
        # print("--- --- ---")
        # print(self.coords)
        # print(self.rules)
        # print(self.single_rules)
