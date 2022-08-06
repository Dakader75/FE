import functools

from PyQt5.QtWidgets import QPushButton, QLineEdit, \
    QWidget, QDialog, QVBoxLayout, QMessageBox, QListWidgetItem, \
    QGridLayout, QApplication
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QBrush, QColor, QIcon

from app.utilities import str_utils
from app.utilities.data import Data
from app.data.database import DB
from app.data.level_units import GenericUnit

from app.editor import timer

from app.extensions.widget_list import WidgetList
from app.extensions.custom_gui import Dialog, RightClickListView, QHLine
from app.editor.custom_widgets import ObjBox
from app.editor.level_editor.unit_painter_menu import AllUnitModel, InventoryDelegate
from app.editor.base_database_gui import DragDropCollectionModel
from app.editor.class_editor import class_model

from app.data.level_units import UnitGroup

import logging

class UnitGroupMenu(QWidget):
    def __init__(self, state_manager):
        super().__init__()
        self.state_manager = state_manager
        self.current_level = None
        self._data = Data()

        grid = QVBoxLayout()
        self.setLayout(grid)

        self.group_list = GroupList(self)
        for group in self._data:
            self.group_list.add_group(group)
        grid.addWidget(self.group_list)

        self.create_button = QPushButton("Create New Group")
        self.create_button.clicked.connect(self.create_new_group)
        grid.addWidget(self.create_button)

        self.state_manager.subscribe_to_key(
            UnitGroupMenu.__name__, 'selected_level', self.set_current_level)

    def set_current_level(self, level_nid):
        level = DB.levels.get(level_nid)
        self.current_level = level
        self._data = self.current_level.unit_groups
        self.group_list.clear()
        for group in self._data:
            self.group_list.add_group(group)

    def create_new_group(self):
        nid = str_utils.get_next_name('New Group', self._data.keys())
        new_group = UnitGroup(nid, [], {})
        self._data.append(new_group)
        self.group_list.add_group(new_group)
        return new_group

    def on_visibility_changed(self, state):
        pass

    def get_current(self):
        if self.group_list.currentIndex():
            idx = self.group_list.currentIndex().row()
            if len(self._data) > 0 and idx < len(self._data):
                return self._data[idx]
        return None

    def get_current_unit(self):
        current_group = self.get_current()
        if current_group:
            idx = self._data.index(current_group.nid)
            item = self.group_list.item(idx)
            item_widget = self.group_list.itemWidget(item)
            unit = item_widget.get_current()
            return unit
        return None

    def select_group(self, group):
        idx = self._data.index(group.nid)
        self.group_list.setCurrentRow(idx)

    def select(self, group, unit_nid):
        idx = self._data.index(group.nid)
        self.group_list.setCurrentRow(idx)
        item = self.group_list.item(idx)
        item_widget = self.group_list.itemWidget(item)
        uidx = group.units.index(unit_nid)
        item_widget.select(uidx)

    def deselect(self):
        self.group_list.clearSelection()

    def remove_group(self, group):
        self.group_list.remove_group(group)
        self._data.delete(group)


class GroupList(WidgetList):
    def add_group(self, group):
        item = QListWidgetItem()
        group_widget = GroupWidget(group, self.parent())
        item.setSizeHint(group_widget.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, group_widget)
        self.index_list.append(group)
        return item

    def remove_group(self, group):
        if group in self.index_list:
            idx = self.index_list.index(group)
            self.index_list.remove(group)
            return self.takeItem(idx)
        else:
            logging.warning("Cannot find group in index_list")
        return None


class GroupWidget(QWidget):
    def __init__(self, group, parent=None):
        super().__init__(parent)
        self.window = parent
        self.current = group
        self.display = None
        self._data = self.window._data

        self.saved_unit_nid = None  # Save the most recent selection

        self.layout = QGridLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.nid_box = QLineEdit(self)
        self.nid_box.textChanged.connect(self.nid_changed)
        self.nid_box.editingFinished.connect(self.nid_done_editing)
        self.layout.addWidget(self.nid_box, 0, 0)

        hline = QHLine()
        self.layout.addWidget(hline, 1, 0, 1, 3)

        add_button = QPushButton("+")
        add_button.setMaximumWidth(30)
        add_button.clicked.connect(self.add_new_unit)
        self.layout.addWidget(add_button, 0, 1, alignment=Qt.AlignRight)

        remove_button = QPushButton("x")
        remove_button.setMaximumWidth(30)
        remove_button.clicked.connect(functools.partial(
            self.window.remove_group, self.current))
        self.layout.addWidget(remove_button, 0, 2, alignment=Qt.AlignRight)

        def false_func(model, index):
            return False

        self.view = RightClickListView(
            (None, false_func, false_func), parent=self)
        self.view.currentChanged = self.on_item_changed
        self.view.clicked.connect(self.on_click)

        self.model = GroupUnitModel([], self)
        self.model.positions = {}
        self.view.setModel(self.model)
        self.view.setIconSize(QSize(32, 32))
        self.inventory_delegate = InventoryDelegate(Data(), self)
        self.view.setItemDelegate(self.inventory_delegate)

        self.layout.addWidget(self.view, 2, 0, 1, 3)

        timer.get_timer().tick_elapsed.connect(self.tick)

        self.set_current(self.current)

    def tick(self):
        self.model.layoutChanged.emit()

    def nid_changed(self, text):
        self.current.nid = text

    def nid_done_editing(self):
        other_nids = [d.nid for d in self._data.values()
                      if d is not self.current]
        if self.current.nid in other_nids:
            QMessageBox.warning(self.window, 'Warning',
                                'Group ID %s already in use' % self.current.nid)
        self.current.nid = str_utils.get_next_name(
            self.current.nid, other_nids)
        self._data.update_nid(self.current, self.current.nid)

    @property
    def current_level(self):
        return self.window.current_level

    def on_item_changed(self, curr, prev):
        pass

    def on_click(self, index):
        self.window.select_group(self.current)

    def set_current(self, group):
        self.current = group
        self.nid_box.setText(group.nid)
        self.model._data = self.current.units
        self.model.positions = self.current.positions
        self.model.update()
        self.inventory_delegate._data = self.current.units

    def get_current(self):
        for index in self.view.selectedIndexes():
            idx = index.row()
            if len(self.current.units) > 0 and idx < len(self.current.units):
                unit_nid = self.current.units[idx]
                return self.window.current_level.units.get(unit_nid)
        return None

    def select(self, idx):
        index = self.model.index(idx)
        self.view.setCurrentIndex(index)

    def deselect(self):
        self.view.clearSelection()

    def add_new_unit(self):
        unit_nid, ok = SelectUnitDialog.get_unit_nid(self, self.saved_unit_nid)
        self.saved_unit_nid = unit_nid
        if ok:
            if unit_nid in self.current.units:
                QMessageBox.critical(self, "Error!", "%s already present in group!" % unit_nid)
            else:
                self.current.units.append(unit_nid)


class SelectUnitDialog(Dialog):
    def __init__(self, parent=None, saved_unit_nid=None):
        super().__init__(parent)
        self.setWindowTitle("Load Unit")
        self.window = parent
        self.view = None
        print(saved_unit_nid)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.unit_box = ObjBox("Units", AllUnitModel,
                               self.window.current_level.units, self)
        self.unit_box.edit.setIconSize(QSize(32, 32))
        self.unit_box.edit.view().setUniformItemSizes(True)
        if saved_unit_nid and saved_unit_nid in self.window.current_level.units.keys():
            idx = self.window.current_level.units.index(saved_unit_nid)
            self.unit_box.edit.setCurrentIndex(idx)
        self.unit_box.edit.activated.connect(self.accept)
        self.view = self.unit_box.edit.view()

        layout.addWidget(self.unit_box)
        self.buttonbox.hide()
        # layout.addWidget(self.buttonbox)

    @classmethod
    def get_unit_nid(cls, parent, saved_unit_nid=None):
        dialog = cls(parent, saved_unit_nid)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            idx = dialog.unit_box.edit.currentIndex()
            unit_nid = dialog.window.current_level.units[idx].nid
            return unit_nid, True
        else:
            return None, False


class GroupUnitModel(DragDropCollectionModel):
    allow_delete_last_obj = True

    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            unit_nid = self._data[index.row()]
            text = str(unit_nid)
            unit = self.window.window.current_level.units.get(unit_nid)
            if isinstance(unit, GenericUnit):
                text += ' (' + str(unit.ai) + ' Lv ' + str(unit.level) + ')'
            return text
        elif role == Qt.DecorationRole:
            unit_nid = self._data[index.row()]
            unit = self.window.window.current_level.units.get(unit_nid)
            if not unit:
                return None
            # Don't draw any units which have been deleted in editor
            if not unit.generic and unit_nid not in DB.units.keys():
                return None
            klass_nid = unit.klass
            num = timer.get_timer().passive_counter.count
            klass = DB.classes.get(klass_nid)
            if not klass:
                logging.error("Class with nid '%s' does not exist in database", klass_nid)
                return
            if self.window.view:
                active = self.window.view.selectionModel().isSelected(index)
            else:
                active = False
            pixmap = class_model.get_map_sprite_icon(klass, num, active, unit.team, unit.variant)
            if pixmap:
                return QIcon(pixmap)
            else:
                return None
        elif role == Qt.ForegroundRole:
            unit_nid = self._data[index.row()]
            if unit_nid in self.positions:
                return QBrush(QApplication.palette().text().color())
            else:
                return QBrush(QColor("red"))
        return None

    def do_drag_drop(self, index):
        if self.drop_to is None:
            return False
        if index < self.drop_to:
            self._data.insert(self.drop_to - 1, self._data.pop(index))
            return index, self.drop_to - 1
        else:
            self._data.insert(self.drop_to, self._data.pop(index))
            return index, self.drop_to

    def create_new(self):
        unit_nid, ok = SelectUnitDialog.get_unit_nid(self.window)
        if ok:
            if unit_nid in self._data:
                QMessageBox.critical(self, "Error!", "%s already present in group!" % unit_nid)
            else:
                self._data.append(unit_nid)
