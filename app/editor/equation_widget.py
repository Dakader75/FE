from PyQt5.QtWidgets import QStyle
from PyQt5.QtCore import Qt

from app.utilities import str_utils
from app.utilities.data import Data
from app.data.database import DB

from app.extensions.custom_gui import DeletionDialog, PropertyBox, ComboBox
from app.extensions.list_dialogs import MultiAttrListDialog
from app.extensions.list_models import MultiAttrListModel

from app.data import equations, level_units, item_components, components

import logging

class EquationMultiModel(MultiAttrListModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.EditRole:
            data = self._data[index.row()]
            attr = self._headers[index.column()]
            return getattr(data, attr)
        if index.column() == 1 and role == Qt.DecorationRole:
            equation = self._data[index.row()]
            good = self.test_equation(equation)
            if good:
                icon = self.window.style().standardIcon(QStyle.SP_DialogApplyButton)
            else:
                icon = self.window.style().standardIcon(QStyle.SP_DialogCancelButton)
            return icon
        elif role == Qt.DisplayRole or role == Qt.EditRole:
            data = self._data[index.row()]
            attr = self._headers[index.column()]
            return getattr(data, attr)
        return None

    def test_equation(self, equation) -> bool:
        try:
            from app.engine import equations as parse
            parser = parse.Parser()
            test_unit = level_units.UniqueUnit(DB.units[0].nid, 'player', None, (0, 0))
            test_unit.stats = {k: v for (k, v) in test_unit.bases.items()}
            test_unit.stat_bonus = lambda x: 0
            result = parser.get(equation.nid, test_unit)
            result = parser.get_expression(equation.expression, test_unit)
            return True
        except Exception as e:
            logging.error("TestEquation Error: %s" % e)
            return False

    def delete(self, idx):
        element = self._data[idx]
        affected_items = item_components.get_items_using(components.Type.Equation, element.nid, DB)
        if affected_items:
            affected = Data(affected_items)
            from app.editor.item_editor.item_model import ItemModel
            model = ItemModel
            msg = "Deleting Equation <b>%s</b> would affect these items" % element.nid
            combo_box = PropertyBox("Equation", ComboBox, self.window)
            objs = [eq for eq in DB.equations if eq.nid != element.nid]
            combo_box.edit.addItems([eq.nid for eq in objs])
            obj_idx, ok = DeletionDialog.get_simple_swap(affected, model, msg, combo_box)
            if ok:
                swap = objs[obj_idx]
                item_components.swap_values(affected_items, components.Type.Equation, element.nid, swap.nid)
            else:
                return
        super().delete(idx)

    def create_new(self):
        nids = [d.nid for d in self._data]
        nid = str_utils.get_next_name("EQUATION", nids)
        new_equation = equations.Equation(nid)
        DB.equations.append(new_equation)
        return new_equation

    def on_attr_changed(self, data, attr, old_value, new_value):
        if attr == 'nid':
            self._data.update_nid(data, new_value)
            affected_items = item_components.get_items_using(components.Type.Equation, old_value, DB)
            item_components.swap_values(affected_items, components.Type.Equation, old_value, new_value)

class EquationDialog(MultiAttrListDialog):
    locked_vars = {"HIT", "AVOID", "CRIT_HIT", "CRIT_AVOID",
                   "DAMAGE", "DEFENSE", "MAGIC_DAMAGE", "MAGIC_DEFENSE",
                   "HITPOINTS", "MOVEMENT", "THRACIA_CRIT", "CRIT_ADD", "CRIT_MULT",
                   "SPEED_TO_DOUBLE", "STEAL_ATK", "STEAL_DEF",
                   "HEAL", "RESCUE_AID", "RESCUE_WEIGHT", "RATING"}

    @classmethod
    def create(cls):
        def deletion_func(model, index):
            return model._data[index.row()].nid not in cls.locked_vars

        dlg = cls(DB.equations, "Equation", ("nid", "expression"),
                  EquationMultiModel, (deletion_func, None, deletion_func), cls.locked_vars)
        return dlg

    def accept(self):
        super().accept()
        from app.engine import equations
        equations.clear()

# Testing
# Run "python -m app.editor.equation_widget"
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    DB.load('default.ltproj')
    window = EquationDialog.create()
    window.show()
    app.exec_()
