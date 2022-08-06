from app.resources.resources import RESOURCES
from app.engine import bmpfont, image_mods

class FontType():
    def __init__(self, name, default):
        self.name = name
        self.colors = {}
        self.default = default

NORMAL_FONT_COLORS = ['white', 'blue', 'green', 'red', 'grey', 'yellow', 'brown']

text = FontType('text', 'white')
text.colors['white'] = ((248, 248, 248, 255), (160, 136, 216, 255), (56, 48, 40, 255))
text.colors['blue'] = ((192, 248, 248, 255), (80, 112, 248, 255), (24, 24, 88, 255))
text.colors['green'] = ((72, 232, 32, 255), (112, 160, 72, 255), (24, 88, 24, 255))
text.colors['red'] = ((224, 96, 80, 255), (160, 88, 72, 255), (88, 24, 24, 255))
text.colors['grey'] = ((184, 176, 176, 255), (136, 128, 120, 255), (56, 48, 40, 255))
text.colors['yellow'] = ((248, 240, 136, 255), (168, 168, 72, 255), (72, 64, 8, 255))
text.colors['brown'] = ((248, 248, 248, 255), (144, 112, 88, 255), (80, 40, 0, 255))

narrow = FontType('narrow', 'white')
narrow.colors = text.colors

small = FontType('small', 'white')
small.colors = text.colors

info = FontType('info', 'black')
info.colors['black'] = ((56, 48, 40, 255), (160, 136, 216, 255))
info.colors['grey'] = ((56, 48, 40, 255), (184, 176, 176, 255))

convo = FontType('convo', 'black')
convo.colors['black'] = ((40, 40, 40, 255), (184, 184, 184, 255))
convo.colors['red'] = ((160, 0, 0, 255), (248, 200, 168, 255))
convo.colors['white'] = ((248, 248, 248, 255), (112, 104, 96, 255))
convo.colors['yellow'] = ((248, 240, 136, 255), (168, 168, 72, 255))

chapter = FontType('chapter', 'yellow')
chapter.colors['yellow'] = ((248, 248, 248, 255), (232, 240, 96, 255), (168, 176, 128, 255),
                            (144, 152, 112, 255), (128, 128, 96, 255), (96, 104, 56, 255),
                            (80, 80, 64, 255))
chapter.colors['grey'] = ((248, 248, 248, 255), (232, 232, 232, 255), (200, 200, 200, 255),
                          (200, 200, 200, 255), (152, 152, 152, 255), (112, 112, 112, 255),
                          (56, 56, 56, 255))
chapter.colors['black'] = ((96, 96, 96, 255), (88, 88, 88, 255), (80, 80, 80, 255),
                           (80, 80, 80, 255), (64, 64, 64, 255), (40, 40, 40, 255),
                           (24, 24, 24, 255))
chapter.colors['white'] = ((248, 248, 248, 255), (204, 196, 136, 255), (168, 168, 144, 255),
                           (144, 144, 128, 255), (128, 120, 112, 255), (104, 96, 72, 255),
                           (80, 80, 80, 255))
chapter.colors['green'] = ((232, 232, 232, 255), (144, 224, 160, 255), (128, 208, 144, 255),
                           (104, 184, 120, 255), (112, 160, 104, 255), (56, 112, 64, 255),
                           (16, 8, 8, 255))

font_types = [text, narrow, small, info, convo, chapter]

# Load in default, uncolored fonts
FONT = {}
for font in RESOURCES.fonts.values():
    title = font.nid.split('-')[0]
    idx_path = font.full_path.replace(font.nid, title).replace('.png', '.idx')
    FONT[font.nid] = bmpfont.BmpFont(font.full_path, idx_path)

# Convert colors
for font_type in font_types:
    for color, value in font_type.colors.items():
        if color == font_type.default:
            continue
        text = FONT[font_type.name + '-' + font_type.default]
        new_text = font_type.name + '-' + color
        FONT[new_text] = bmpfont.BmpFont(text.png_path, text.idx_path)
        dic = {a: b for a, b in zip(font_type.colors[font_type.default], font_type.colors[color])}
        FONT[new_text].surface = image_mods.color_convert_alpha(FONT[new_text].surface, dic)
