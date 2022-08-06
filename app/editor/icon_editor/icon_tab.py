from PyQt5.QtWidgets import QWidget, QGridLayout, QListView, QPushButton, \
    QDialog
from PyQt5.QtCore import QSize, Qt

from app.resources.resources import RESOURCES
from app.editor.data_editor import SingleResourceEditor, MultiResourceEditor

from app.editor.icon_editor import icon_model

class IconTab(QWidget):
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
        self.view.setIconSize(QSize(64, 64))
        self.model = model(self._data, self)
        self.view.setModel(self.model)
        self.view.setViewMode(QListView.IconMode)
        self.view.setResizeMode(QListView.Adjust)
        self.view.setMovement(QListView.Static)
        self.view.setGridSize(QSize(80, 80))

        self.layout.addWidget(self.view, 0, 0, 1, 2)

        self.button = QPushButton("Add New Icon Sheet...")
        self.button.clicked.connect(self.model.append)
        self.layout.addWidget(self.button, 1, 0, 1, 1)

        self.display = None

    def update_list(self):
        # self.model.dataChanged.emit(self.model.index(0), self.model.index(self.model.rowCount()))                
        self.model.layoutChanged.emit()

    def reset(self):
        pass

    @property
    def current(self):
        indices = self.view.selectionModel().selectedIndexes()
        if indices:
            index = indices[0]
            icon = self.model.sub_data[index.row()]
            if icon.parent_nid:
                icon.nid = icon.parent_nid
            return icon
        return None

class IconListView(QListView):
    def delete(self, index):
        self.model().delete(index.row())

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Delete:
            indices = self.selectionModel().selectedIndexes()
            for index in indices:
                self.delete(index)

class Icon16Database(IconTab):
    @classmethod
    def create(cls, parent=None):
        data = RESOURCES.icons16
        title = "16x16 Icon"
        collection_model = icon_model.Icon16Model
        deletion_criteria = None

        dialog = cls(data, title, collection_model, parent)
        return dialog

class Icon32Database(Icon16Database):
    @classmethod
    def create(cls, parent=None):
        data = RESOURCES.icons32
        title = "32x32 Icon"
        collection_model = icon_model.Icon32Model
        deletion_criteria = None

        dialog = cls(data, title, collection_model, parent)
        return dialog

class Icon80Database(Icon16Database):
    @classmethod
    def create(cls, parent=None):
        data = RESOURCES.icons80
        title = "80x72 Icon"
        collection_model = icon_model.Icon80Model
        deletion_criteria = None

        dialog = cls(data, title, collection_model, parent)
        return dialog

class MapIconDatabase(IconTab):
    @classmethod
    def create(cls, parent=None):
        data = RESOURCES.map_icons
        title = 'Map Icons'
        collection_model = icon_model.MapIconModel
        deletion_criteria = None
        
        dialog = cls(data, title, collection_model, parent)
        return dialog
    
    @property
    def current(self):
        indices = self.view.selectionModel().selectedIndexes()
        if indices:
            index = indices[0]
            icon = self.model.sub_data[index.row()]
            return icon
        return None
    
def get_map_icon_editor():
    database = MapIconDatabase
    window = SingleResourceEditor(database, ['map_icons'])
    result = window.exec_()
    if result == QDialog.Accepted:
        selected_icon = window.tab.current
        return selected_icon, True
    else:
        return None, False

def get(width):
    if width == 16:
        resource_type = 'icons16'
        database = Icon16Database
    elif width == 32:
        resource_type = 'icons32'
        database = Icon32Database
    elif width == 80:
        resource_type = 'icons80'
        database = Icon80Database
    else:
        return None, False
    window = SingleResourceEditor(database, [resource_type])
    result = window.exec_()
    if result == QDialog.Accepted:
        selected_icon = window.tab.current
        return selected_icon, True
    else:
        return None, False

def get_full_editor():
    return MultiResourceEditor((Icon16Database, Icon32Database, Icon80Database, MapIconDatabase),
                               ('icons16', 'icons32', 'icons80', 'map_icons'))

# Testing
# Run "python -m app.editor.icon_editor.icon_tab" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    RESOURCES.load('default.ltproj')
    # DB.load('default.ltproj')
    window = MultiResourceEditor((Icon16Database, Icon32Database, Icon80Database),
                                 ('icons16', 'icons32', 'icons80'))
    window.show()
    app.exec_()
