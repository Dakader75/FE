from PyQt5.QtWidgets import QWidget, QGridLayout, QListView, QPushButton, \
    QDialog
from PyQt5.QtCore import QSize

from app.resources.resources import RESOURCES
from app.editor.data_editor import SingleResourceEditor, MultiResourceEditor

from app.editor.tile_editor import tile_model
from app.editor.tilemap_editor import MapEditor
from app.editor.icon_editor.icon_tab import IconListView

class TileTab(QWidget):
    def __init__(self, data, title, model, parent=None):
        super().__init__(parent)
        self.window = parent
        self._data = data
        self.title = title

        self.setWindowTitle(self.title)
        self.setStyleSheet("font: 10pt;")

        self.layout = QGridLayout(self)
        self.setLayout(self.layout)

        self.view = IconListView()
        self.view.setMinimumSize(360, 360)
        self.view.setUniformItemSizes(True)
        self.view.setIconSize(QSize(96, 96))
        self.model = model(self._data, self)
        self.view.setModel(self.model)
        self.view.setUniformItemSizes(True)
        self.view.setViewMode(QListView.IconMode)
        self.view.setResizeMode(QListView.Adjust)
        self.view.setMovement(QListView.Static)
        self.view.setGridSize(QSize(120, 120))

        self.layout.addWidget(self.view, 0, 0, 1, 3)
        self.button = QPushButton("Add New %s..." % self.title)
        self.button.clicked.connect(self.model.append)
        self.layout.addWidget(self.button, 1, 0, 1, 1)

        self.display = None

    def update_list(self):
        self.model.layoutChanged.emit()

    def reset(self):
        pass

    @property
    def current(self):
        indices = self.view.selectionModel().selectedIndexes()
        if indices:
            index = indices[0]
            obj = self.model._data[index.row()]
            return obj
        return None

    def duplicate(self):
        self.model.duplicate(self.current)

class TileSetDatabase(TileTab):
    @classmethod
    def create(cls, parent=None):
        data = RESOURCES.tilesets
        title = "Tileset"
        collection_model = tile_model.TileSetModel
        deletion_criteria = None

        dialog = cls(data, title, collection_model, parent)
        return dialog

class TileMapDatabase(TileTab):
    @classmethod
    def create(cls, parent=None):
        data = RESOURCES.tilemaps
        title = "Tilemap"
        collection_model = tile_model.TileMapModel
        deletion_criteria = None

        dialog = cls(data, title, collection_model, parent)
        dialog.edit_button = QPushButton("Edit Current %s..." % dialog.title)
        dialog.edit_button.clicked.connect(dialog.edit_current)
        dialog.layout.addWidget(dialog.edit_button, 1, 1, 1, 1)

        dialog.duplicate_button = QPushButton("Duplicate Current %s" % dialog.title)
        dialog.duplicate_button.clicked.connect(dialog.duplicate)
        dialog.layout.addWidget(dialog.duplicate_button, 1, 2, 1, 1)
        return dialog

    def edit_current(self):
        current_tilemap = self.current
        if current_tilemap:
            map_editor = MapEditor(self, current_tilemap)
            map_editor.exec_()
            tile_model.create_tilemap_pixmap(current_tilemap)

def get_tilesets() -> tuple:
    window = SingleResourceEditor(TileSetDatabase, ["tilesets"])
    result = window.exec_()
    if result == QDialog.Accepted:
        selected_tileset = window.tab.current
        return selected_tileset, True
    else:
        return None, False

def get_tilemaps() -> tuple:
    window = SingleResourceEditor(TileMapDatabase, ["tilemaps"])
    result = window.exec_()
    if result == QDialog.Accepted:
        selected_tilemap = window.tab.current
        return selected_tilemap, True
    else:
        return None, False

def get_full_editor() -> MultiResourceEditor:
    editor = MultiResourceEditor((TileSetDatabase, TileMapDatabase), 
                                 ("tilesets", "tilemaps"))
    editor.setWindowTitle("Tile Editor")
    return editor

# Testing
# Run "python -m app.editor.tile_editor.tile_tab" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    RESOURCES.load('default.ltproj')
    # DB.load('default.ltproj')
    window = MultiResourceEditor((TileSetDatabase, TileMapDatabase), 
                                 ("tilesets", "tilemaps"))
    window.show()
    app.exec_()
