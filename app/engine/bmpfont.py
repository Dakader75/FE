from app.engine import engine

class BmpFont():
    def __init__(self, png_path, idx_path):
        self.all_uppercase = False
        self.all_lowercase = False
        self.stacked = False
        self.chartable = {}
        self.idx_path = idx_path
        self.png_path = png_path
        self.space_offset = 0
        self._width = 8
        self.height = 16
        self.memory = {}

        with open(self.idx_path, 'r', encoding='utf-8') as fp:
            for x in fp.readlines():
                words = x.strip().split()
                if words[0] == 'alluppercase':
                    self.all_uppercase = True
                elif words[0] == 'alllowercase':
                    self.all_lowercase = True
                elif words[0] == 'stacked':
                    self.stacked = True
                elif words[0] == 'space_offset':
                    self.space_offset = int(words[1])
                elif words[0] == "width":
                    self._width = int(words[1])
                elif words[0] == "height":
                    self.height = int(words[1])
                else:  # Default to index entry.
                    if words[0] == "space":
                        words[0] = ' '
                    if self.all_uppercase:
                        words[0] = words[0].upper()
                    if self.all_lowercase:
                        words[0] = words[0].lower()
                    self.chartable[words[0]] = (int(words[1]) * self._width,
                                                int(words[2]) * self.height,
                                                int(words[3]))

        self.surface = engine.image_load(self.png_path)
        # engine.set_colorkey(self.surface, (0, 0, 0), rleaccel=True)

    def modify_string(self, string: str) -> str:
        if self.all_uppercase:
            string = string.upper()
        if self.all_lowercase:
            string = string.lower()
        # string = string.replace('_', ' ')
        return string

    def blit(self, string, surf, pos=(0, 0)):
        def normal_render(left, top, string):
            for c in string:
                if c not in self.memory:
                    try:
                        char_pos_x = self.chartable[c][0]
                        char_pos_y = self.chartable[c][1]
                        char_width = self.chartable[c][2]
                    except KeyError as e:
                        char_pos_x = 0
                        char_pos_y = 0
                        char_width = 8
                        print(e)
                        print("%s is not chartable" % c)
                        print("string: ", string)
                    subsurf = engine.subsurface(self.surface, (char_pos_x, char_pos_y, self._width, self.height))
                    self.memory[c] = (subsurf, char_width)
                else:
                    subsurf, char_width = self.memory[c]
                engine.blit(surf, subsurf, (left, top))
                left += char_width + self.space_offset

        def stacked_render(left, top, string):
            orig_left = left
            for c in string:
                if c not in self.memory:
                    try:
                        char_pos_x = self.chartable[c][0]
                        char_pos_y = self.chartable[c][1]
                        char_width = self.chartable[c][2]
                    except KeyError as e:
                        char_pos_x = 0
                        char_pos_y = 0
                        char_width = 8
                        print(e)
                        print("%s is not chartable" % c)
                        print("string: ", string)

                    highsurf = engine.subsurface(self.surface, (char_pos_x, char_pos_y, self._width, self.height))
                    lowsurf = engine.subsurface(self.surface, (char_pos_x, char_pos_y + self.height, self._width, self.height))
                    self.memory[c] = (highsurf, lowsurf, char_width)
            for c in string:
                highsurf, lowsurf, char_width = self.memory[c]
                engine.blit(surf, lowsurf, (left, top))
                left += char_width + self.space_offset
            for c in string:
                highsurf, lowsurf, char_width = self.memory[c]
                engine.blit(surf, highsurf, (orig_left, top))
                orig_left += char_width + self.space_offset

        x, y = pos
        surfwidth, surfheight = surf.get_size()

        string = self.modify_string(string)

        if self.stacked:
            stacked_render(x, y, string)
        else:
            normal_render(x, y, string)

    def blit_right(self, string, surf, pos):
        width = self.width(string)
        self.blit(string, surf, (pos[0] - width, pos[1]))

    def blit_center(self, string, surf, pos):
        width = self.width(string)
        self.blit(string, surf, (pos[0] - width//2, pos[1]))

    def size(self, string):
        """
        Returns the length and width of a bitmapped string
        """
        return (self.width(string), self.height)

    def width(self, string):
        """
        Returns the width of a bitmapped string
        """
        length = 0
        string = self.modify_string(string)

        for c in string:
            try:
                char_width = self.chartable[c][2]
            except KeyError as e:
                print(e)
                print("%s is not chartable" % c)
                print("string: ", string)
                char_width = 8
            length += char_width
        length += 1
        return length
