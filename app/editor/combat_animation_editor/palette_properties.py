import os

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QFileDialog, QVBoxLayout, \
    QGraphicsView, QGraphicsScene, QLineEdit, QSizePolicy, QPushButton, \
    QMessageBox, QDialog, QAction, QApplication
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPen, QPixmap, QImage, QPainter, qRgb

from typing import Tuple

from app.constants import WINWIDTH, WINHEIGHT
from app.resources.resources import RESOURCES

from app.editor.settings import MainSettingsController

from app.editor import timer
from app.utilities import str_utils
from app.extensions.custom_gui import PropertyBox, ComboBox, Dialog
from app.editor.combat_animation_editor.frame_selector import FrameSelector
from app.editor.combat_animation_editor import combat_animation_model
from app.editor.combat_animation_editor.color_editor import ColorEditorWidget
from app.resources.combat_anims import Frame
from app.resources.combat_palettes import Palette
from app.editor.icon_editor.icon_view import IconView
import app.editor.utilities as editor_utilities

import logging

class UndoStack():
    def __init__(self):
        self.current_idx = -1
        self._list = []

    def clear(self):
        self.current_idx = -1
        self._list.clear()

    def append(self, val):
        self._list = self._list[:self.current_idx + 1]
        self._list.append(val)
        self.current_idx += 1

    def undo(self):
        if not self._list or self.current_idx < 0:
            return
        command = self._list[self.current_idx]
        command.undo()
        self.current_idx -= 1
        if self.current_idx >= 0 and command.can_stack(self._list[self.current_idx]):
            self.undo()

    def redo(self):
        if not self._list or self.current_idx >= len(self._list) - 1:
            return
        self.current_idx += 1
        command = self._list[self.current_idx]
        command.redo()
        if self.current_idx < len(self._list) - 1 and command.can_stack(self._list[self.current_idx + 1]):
            self.redo()

palette_commands = UndoStack()

class CommandChangePaletteColor():
    nid = 'change_palette_color'

    def __init__(self, palette: Palette, coord: tuple, new_color: QColor):
        self.palette = palette
        self.coord = coord
        self.new_color = new_color.getRgb()[:3]
        self.old_color = self.palette.colors.get(self.coord)

        self.swap_coord = None
        if self.new_color in self.palette.colors.values():
            for coord, color in self.palette.colors.items():
                if color == self.new_color and self.old_color:
                    self.swap_coord = coord
                    break

    def redo(self): 
        if self.swap_coord:
            self.palette.colors[self.swap_coord] = self.old_color
        self.palette.colors[self.coord] = self.new_color

    def undo(self):
        if self.swap_coord:
            self.palette.colors[self.swap_coord] = self.new_color

        if self.old_color is not None:
            self.palette.colors[self.coord] = self.old_color
        else:
            del self.palette.colors[self.coord]

    def can_stack(self, other) -> bool:
        return self.nid == other.nid and self.palette == other.palette and self.coord == other.coord

class CommandChangePaletteSlot():
    nid = 'change_palette_slot'

    def __init__(self, palette: Palette, frame_set, coord: tuple, new_coord: tuple):
        self.palette = palette
        self.frame_set = frame_set
        self.old_coord = coord
        self.new_coord = new_coord

        self.swap_coord = False
        if self.new_coord in self.palette.colors.keys():
            self.swap_coord = True

    def redo(self):
        print(self.swap_coord) 
        if self.swap_coord:
            # old_color = self.palette.colors[self.old_coord]
            # new_color = self.palette.colors[self.new_coord]
            # self.palette.colors[self.old_coord] = new_color
            # self.palette.colors[self.new_coord] = old_color
            temp_coord = (255, 255)
            convert_dict = {qRgb(0, *self.old_coord): qRgb(0, *temp_coord), 
                            qRgb(0, *self.new_coord): qRgb(0, *self.old_coord)}
            second_convert_dict = {qRgb(0, *temp_coord): qRgb(0, *self.new_coord)}
            for frame in self.frame_set.frames:
                frame.pixmap = editor_utilities.color_convert_pixmap(frame.pixmap, convert_dict)
                frame.pixmap = editor_utilities.color_convert_pixmap(frame.pixmap, second_convert_dict)
            self.frame_set.pixmap = editor_utilities.color_convert_pixmap(self.frame_set.pixmap, convert_dict)
            self.frame_set.pixmap = editor_utilities.color_convert_pixmap(self.frame_set.pixmap, second_convert_dict)

        else:
            # color = self.palette.colors[self.old_coord]
            # self.palette.colors[self.new_coord] = color
            # del self.palette.colors[self.old_coord]
            convert_dict = {qRgb(0, *self.old_coord): qRgb(0, *self.new_coord)}
            for frame in self.frame_set.frames:
                frame.pixmap = editor_utilities.color_convert_pixmap(frame.pixmap, convert_dict)
            # Propagate changes up to main anim
            self.frame_set.pixmap = editor_utilities.color_convert_pixmap(self.frame_set.pixmap, convert_dict)
        self.frame_set.full_path = None  # So it saves the new pixmap

    def undo(self):
        if self.swap_coord:
            # old_color = self.palette.colors[self.old_coord]
            # new_color = self.palette.colors[self.new_coord]
            # self.palette.colors[self.old_coord] = old_color
            # self.palette.colors[self.new_coord] = new_color
            temp_coord = (255, 255)
            # Swap back
            convert_dict = {qRgb(0, *self.old_coord): qRgb(0, *temp_coord), 
                            qRgb(0, *self.new_coord): qRgb(0, *self.old_coord)}
            second_convert_dict = {qRgb(0, *temp_coord): qRgb(0, *self.new_coord)}
            for frame in self.frame_set.frames:
                frame.pixmap = editor_utilities.color_convert_pixmap(frame.pixmap, convert_dict)
                frame.pixmap = editor_utilities.color_convert_pixmap(frame.pixmap, second_convert_dict)
            self.frame_set.pixmap = editor_utilities.color_convert_pixmap(self.frame_set.pixmap, convert_dict)
            self.frame_set.pixmap = editor_utilities.color_convert_pixmap(self.frame_set.pixmap, second_convert_dict)
        else:
            # color = self.palette.colors[self.new_coord]
            # self.palette.colors[self.old_coord] = color
            # del self.palette.colors[self.new_coord]
            convert_dict = {qRgb(0, *self.new_coord): qRgb(0, *self.old_coord)}
            for frame in self.frame_set.frames:
                frame.pixmap = editor_utilities.color_convert_pixmap(frame.pixmap, convert_dict)
            # Propagate changes up to main anim
            self.frame_set.pixmap = editor_utilities.color_convert_pixmap(self.frame_set.pixmap, convert_dict)
        self.frame_set.full_path = None

    def can_stack(self, other) -> bool:
        return False

class CommandDeleteColor():
    def __init__(self, palette, coord):
        self.palette = palette
        self.coord = coord
        self.old_color = self.palette.colors[self.coord]

    def redo(self):
        del self.palette.colors[self.coord]

    def undo(self):
        self.palette.colors[self.coord] = self.old_color

    def can_stack(self, other) -> bool: 
        return False

class AnimView(IconView):
    def get_color_at_pos(self, pixmap, pos) -> Tuple[int, int, int]:
        image = pixmap.toImage()
        if pos[0] >= 0 and pos[1] >= 0:
            current_color = image.pixel(*pos)
            color = QColor(current_color)
            return (color.red(), color.green(), color.blue())
        return (0, 0, 0)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        scene_pos = self.mapToScene(event.pos())
        pos = int(scene_pos.x()), int(scene_pos.y())

        # Need to get original frame with base palette
        frame = self.window.current_frame
        if not frame:
            return
        offset_x, offset_y = frame.offset
        pos = pos[0] - offset_x, pos[1] - offset_y
        pixmap = frame.pixmap

        coord_color: Tuple[int, int, int] = self.get_color_at_pos(pixmap, pos)
        coord = coord_color[1], coord_color[2]  # Just the G, B channels

        palette = self.window.current_palette
        if not palette:
            return
        palette_coords = palette.colors.keys()
        if coord not in palette_coords:
            logging.warning("Cannot find coord: %s in %s" % (coord, palette_coords))
            return

        if event.buttons() == Qt.LeftButton:
            # overwrite current color with painting color
            painting_color = self.window.get_painting_color()
            command = CommandChangePaletteColor(palette, coord, painting_color)
            palette_commands.append(command)
            command.redo()
            self.window.draw_frame()

        elif event.buttons() == Qt.RightButton:
            # replace painting color with current color
            current_color = palette.colors[coord]
            color = QColor(*current_color)
            self.window.set_painting_color(color)

class EaselWidget(QGraphicsView):
    palette_size = 32
    square_size = 8
    # Emitted when the current coord changes
    selectionChanged = pyqtSignal(object)

    def __init__(self, parent):
        super().__init__(parent)
        self.window = parent

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setMouseTracking(True)
        self.setStyleSheet("background-color:rgb(192,192,192);")

        self.current_palette = None
        self.current_frame = None
        self.current_coord = None

        self.working_image = None

        timer.get_timer().tick_elapsed.connect(self.tick)

    def tick(self):
        if self.current_palette:
            self.update_view()

    def clear_scene(self):
        self.scene.clear()

    def update_view(self):
        if self.current_palette:
            self.working_image = QPixmap.fromImage(self.get_palette_image())
            self.show_image()
        else:
            self.clear_scene()

    def show_image(self):
        self.clear_scene()
        self.scene.addPixmap(self.working_image)

    def get_coords_used_in_frame(self, frame: Frame) -> list:
        im = QImage(frame.pixmap)
        unique_colors = editor_utilities.find_palette(im)
        coords = [(uc[1], uc[2]) for uc in unique_colors]
        return coords

    def get_palette_image(self) -> QImage:
        side_length = self.palette_size * self.square_size
        base_image = QImage(side_length, side_length, QImage.Format_ARGB32)
        base_image.fill(QColor(192, 192, 192, 255))

        painting_color = self.window.get_painting_color()
        if painting_color:
            painting_color = painting_color.getRgb()[:3]
        painting_color_coord = None
        if painting_color:
            for coord, color in self.current_palette.colors.items():
                if color == painting_color:
                    painting_color_coord = coord
                    break

        painter = QPainter()
        painter.begin(base_image)
        if self.current_frame:
            painter.setPen(QPen(QColor(0, 0, 0, 255), 1, Qt.SolidLine))
            for coord in self.get_coords_used_in_frame(self.current_frame):
                painter.drawRect(coord[0] * self.palette_size + 1, coord[1] * self.palette_size + 1, self.palette_size - 2, self.palette_size - 2)
        # Outline painting color in dashed line
        if painting_color_coord:
            painter.setPen(QPen(QColor(255, 255, 0, 255), 1, Qt.DashLine))
            coord = painting_color_coord
            painter.drawRect(coord[0] * self.palette_size, coord[1] * self.palette_size, self.palette_size, self.palette_size)
        # Outline chosen coord in bright cyan
        if self.current_coord:
            painter.setPen(QPen(QColor(0, 255, 255, 255), 2, Qt.SolidLine))
            coord = self.current_coord
            painter.drawRect(coord[0] * self.palette_size, coord[1] * self.palette_size, self.palette_size, self.palette_size)
        # draw actual colors
        for coord, color in self.current_palette.colors.items():
            write_color = QColor(color[0], color[1], color[2])
            painter.fillRect(coord[0] * self.palette_size + 2, coord[1] * self.palette_size + 2, self.palette_size - 4, self.palette_size - 4, write_color)
        painter.end()
        return base_image

    def set_current(self, current_palette: Palette, current_frame: Frame):
        self.current_palette = current_palette
        self.current_frame = current_frame
        self.current_coord = None
        self.update_view()
        self.selectionChanged.emit(None)

    def set_current_color(self, color: QColor):
        if self.current_palette and self.current_coord:
            command = CommandChangePaletteColor(self.current_palette, self.current_coord, color)
            palette_commands.append(command)
            command.redo()
            self.window.draw_frame()

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Delete:
            if self.current_coord:
                command = CommandDeleteColor(self.current_palette, self.current_coord)
                palette_commands.append(command)
                command.redo()
                self.window.draw_frame()

    def mousePressEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        tile_pos = int(scene_pos.x() // self.palette_size), \
            int(scene_pos.y() // self.palette_size)

        if event.button() == Qt.RightButton:
            print(tile_pos)
            # Set current slot to this coord
            if (QApplication.keyboardModifiers() & Qt.ControlModifier):
                if self.current_frame and self.window.current_frame_set and tile_pos in self.current_palette.colors:
                    self.current_coord = tile_pos
            # Set painting color to this coord
            else:
                self.current_coord = None
                self.selectionChanged.emit(self.current_palette.colors.get(tile_pos))

        elif event.button() == Qt.LeftButton:
            # If control is pressed, move current coord to new position
            if self.current_coord:
                # Modify base frame if it exists
                if self.current_frame and self.window.current_frame_set:
                    command = CommandChangePaletteSlot(self.current_palette, self.window.current_frame_set, self.current_coord, tile_pos)
                    palette_commands.append(command)
                    command.redo()
                    self.current_coord = None
                    self.window.draw_frame()
            else:
                # overwrite current color with painting color
                painting_color = self.window.get_painting_color()
                command = CommandChangePaletteColor(self.current_palette, tile_pos, painting_color)
                palette_commands.append(command)
                command.redo()
                self.window.draw_frame()

class WeaponAnimSelection(Dialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.window = parent

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.current_combat_anim = None

        self.combat_box = PropertyBox("Combat Animations", ComboBox, self)
        self.combat_box.edit.addItems(RESOURCES.combat_anims.keys())
        self.current_combat_anim = RESOURCES.combat_anims[0]
        self.combat_box.edit.currentIndexChanged.connect(self.combat_changed)
        
        self.weapon_box = PropertyBox("Weapon Animations", ComboBox, self)
        if RESOURCES.combat_anims:
            weapon_anims = self.current_combat_anim.weapon_anims
            self.weapon_box.edit.addItems(weapon_anims.keys())

        main_layout.addWidget(self.combat_box)
        main_layout.addWidget(self.weapon_box)
        main_layout.addWidget(self.buttonbox)

    def combat_changed(self, idx):
        combat_text = self.combat_box.edit.currentText()
        self.current_combat_anim = RESOURCES.combat_anims.get(combat_text)
        self.weapon_box.edit.clear()
        weapon_anims = self.current_combat_anim.weapon_anims
        self.weapon_box.edit.addItems([weapon_anim.nid for weapon_anim in weapon_anims])

    @classmethod
    def get(cls, parent) -> tuple:
        dlg = cls(parent)
        result = dlg.exec_()
        if result == QDialog.Accepted:
            return dlg.combat_box.edit.currentText(), dlg.weapon_box.edit.currentText()
        else:
            return None, None

    @classmethod
    def autoget(cls, current_palette: Palette) -> tuple:
        for combat_anim in RESOURCES.combat_anims:
            palette_nids = [nid for name, nid in combat_anim.palettes]
            if current_palette.nid in palette_nids:
                if combat_anim.weapon_anims:
                    return combat_anim.nid, combat_anim.weapon_anims[0].nid
        return None, None

class PaletteProperties(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.window = parent
        self._data = self.window._data
        self.model = self.window.left_frame.model

        self.settings = MainSettingsController()

        self.current_palette = None
        self.current_frame = None
        self.current_frame_set = None
        self.painting_color: QColor = QColor(0, 0, 0)

        self.undo_action = QAction("Undo", self, shortcut="Ctrl+Z", triggered=self.undo)
        self.redo_action = QAction("Redo", self, triggered=self.redo)
        self.redo_action.setShortcuts(["Ctrl+Shift+Z", "Ctrl+Y"])
        self.addAction(self.undo_action)
        self.addAction(self.redo_action)

        self.nid_box = PropertyBox("Unique ID", QLineEdit, self)
        self.nid_box.edit.textChanged.connect(self.nid_changed)
        self.nid_box.edit.editingFinished.connect(self.nid_done_editing)

        self.import_box = QPushButton("Import from PNG Image...")
        self.import_box.clicked.connect(self.import_palette_from_image)

        left_frame = self.window.left_frame
        grid = left_frame.layout()
        grid.addWidget(self.import_box, 3, 0, 1, 2)
        grid.addWidget(self.nid_box, 4, 0, 1, 2)
        
        self.raw_view = AnimView(self)
        self.raw_view.static_size = True
        self.raw_view.setSceneRect(0, 0, WINWIDTH, WINHEIGHT)
        self.raw_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.autoselect_frame_button = QPushButton("Autoselect Frame", self)
        self.autoselect_frame_button.clicked.connect(self.autoselect_frame)

        self.select_frame_button = QPushButton("Select Frame...", self)
        self.select_frame_button.clicked.connect(self.select_frame)

        self.easel_widget = EaselWidget(self)
        self.color_editor_widget = ColorEditorWidget(self)

        self.easel_widget.selectionChanged.connect(self.easel_selection_changed)
        self.color_editor_widget.colorChanged.connect(self.set_painting_color)
        
        main_layout = QVBoxLayout()
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.easel_widget)
        view_layout = QVBoxLayout()
        view_layout.addWidget(self.raw_view)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.autoselect_frame_button)
        button_layout.addWidget(self.select_frame_button)
        view_layout.addLayout(button_layout)
        top_layout.addLayout(view_layout)
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.color_editor_widget)
        self.setLayout(main_layout)

    def undo(self):
        palette_commands.undo()
        self.draw_frame()

    def redo(self):
        palette_commands.redo()
        self.draw_frame()

    def nid_changed(self, text):
        self.current_palette.nid = text
        self.window.update_list()

    def nid_done_editing(self):
        # Check validity of nid!
        other_nids = [d.nid for d in self._data.values() if d is not self.current_palette]
        if self.current_palette.nid in other_nids:
            QMessageBox.warning(self.window, 'Warning', 'Palette ID %s already in use' % self.current_palette.nid)
            self.current_palette.nid = str_utils.get_next_name(self.current_palette.nid, other_nids)
        self.model.on_nid_changed(self._data.find_key(self.current_palette), self.current_palette.nid)
        self._data.update_nid(self.current_palette, self.current_palette.nid)
        self.window.update_list()

    @property
    def current(self):
        return self.current_palette

    def set_current(self, current):
        palette_commands.clear()
        self.current_palette = current
        self.nid_box.edit.setText(self.current_palette.nid)
        self.easel_widget.set_current(current, self.current_frame)
        self.draw_frame()

    def get_current_palette(self):
        return self.current_palette.nid

    def select_frame(self):
        combat_anim_nid, weapon_anim_nid = WeaponAnimSelection.get(self)
        combat_anim = RESOURCES.combat_anims.get(combat_anim_nid)
        if not combat_anim:
            return
        weapon_anim = combat_anim.weapon_anims.get(weapon_anim_nid)
        if not weapon_anim:
            return
        frame, ok = FrameSelector.get(combat_anim, weapon_anim, self)
        if frame and ok:
            self.current_frame_set = weapon_anim
            self.current_frame = frame
            self.easel_widget.set_current(self.current_palette, self.current_frame)
            self.draw_frame()

    def autoselect_frame(self):
        if not self.current_palette:
            return
        combat_anim_nid, weapon_anim_nid = WeaponAnimSelection.autoget(self.current_palette)
        combat_anim = RESOURCES.combat_anims.get(combat_anim_nid)
        if not combat_anim:
            QMessageBox.critical(self, "Autoselect Error", 'Could not find a good frame. Try using manual "Select".')
            return
        weapon_anim = combat_anim.weapon_anims.get(weapon_anim_nid)
        if not weapon_anim:
            QMessageBox.critical(self, "Autoselect Error", 'Could not find a good frame. Try using manual "Select".')
            return
        if not weapon_anim.frames:
            QMessageBox.critical(self, "Autoselect Error", 'Could not find a good frame. Try using manual "Select".')
            return
        frame = weapon_anim.frames[0]
        if frame:
            self.current_frame_set = weapon_anim
            self.current_frame = frame
            self.easel_widget.set_current(self.current_palette, self.current_frame)
            self.draw_frame()

    def easel_selection_changed(self, current_color):
        if current_color:
            self.painting_color = QColor(*current_color)
        if self.painting_color:
            self.color_editor_widget.set_current(self.painting_color)

    def set_painting_color(self, color: QColor):
        self.painting_color = color
        self.color_editor_widget.set_current(color)

    def get_painting_color(self) -> QColor:
        return self.painting_color

    def draw_frame(self):
        if self.current_frame and self.current_palette:
            im = combat_animation_model.palette_swap(self.current_frame.pixmap, self.get_current_palette())
            base_image = QImage(WINWIDTH, WINHEIGHT, QImage.Format_ARGB32)
            base_image.fill(editor_utilities.qCOLORKEY)
            painter = QPainter()
            painter.begin(base_image)
            offset_x, offset_y = self.current_frame.offset
            painter.drawImage(offset_x, offset_y, im)
            painter.end()
            self.raw_view.set_image(QPixmap.fromImage(base_image))
            self.raw_view.show_image()

    def import_palette_from_image(self):
        starting_path = self.settings.get_last_open_path()
        fns, ok = QFileDialog.getOpenFileNames(self.window, "Select Legacy Script Files", starting_path, "PNG Files (*.png);;All Files (*)")
        if fns and ok:
            parent_dir = os.path.split(fns[-1])[0]
            self.settings.set_last_open_path(parent_dir)

            did_import = False
            for image_fn in fns:
                if image_fn.endswith('.png'):
                    head, tail = os.path.split(image_fn)
                    palette_nid = tail[:-4]
                    palette_nid = str_utils.get_next_name(palette_nid, RESOURCES.combat_palettes.keys())
                    pix = QPixmap(image_fn)
                    palette_colors = editor_utilities.find_palette(pix.toImage())
                    new_palette = Palette(palette_nid)
                    colors = {(int(idx % 8), int(idx / 8)): color for idx, color in enumerate(palette_colors)}
                    new_palette.colors = colors
                    RESOURCES.combat_palettes.append(new_palette)
                    did_import = True
            if did_import:
                # Move view
                self.model.move_to_bottom()
