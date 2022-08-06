from PyQt5.QtCore import Qt

from app.data.database import DB
from app.editor.base_database_gui import DragDropCollectionModel

class StatTypeModel(DragDropCollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            stat_type = self._data[index.row()]
            text = stat_type.nid + ": " + stat_type.name
            return text
        return None

    def create_new(self):
        return self._data.add_new_default(DB)
