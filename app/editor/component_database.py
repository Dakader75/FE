from functools import partial

from PyQt5.QtWidgets import QComboBox, QWidget, QLabel, QToolButton, QDoubleSpinBox, \
    QSpinBox, QHBoxLayout, QListWidgetItem, QItemDelegate, QLineEdit
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import Qt

from app.resources.resources import RESOURCES
from app.data.database import DB
from app.data.components import Type

from app.extensions.color_icon import ColorIcon, AlphaColorIcon
from app.extensions.custom_gui import ComboBox
from app.extensions.widget_list import WidgetList
from app.extensions import list_models
from app.extensions.list_widgets import AppendMultiListWidget, AppendSingleListWidget

class ComponentList(WidgetList):
    def add_component(self, component):
        item = QListWidgetItem()
        item.setSizeHint(component.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, component)
        self.index_list.append(component.data.nid)
        return item

    def remove_component(self, component):
        if component.data.nid in self.index_list:
            idx = self.index_list.index(component.data.nid)
            self.index_list.remove(component.data.nid)
            return self.takeItem(idx)
        return None

class BoolItemComponent(QWidget):
    delegate = None

    def __init__(self, data, parent, delegate=None):
        super().__init__(parent)
        self._data = data
        self.window = parent
        self.delegate = delegate

        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        self.setLayout(hbox)

        self.setToolTip(self._data.desc)

        name_label = QLabel(self._data.name)
        hbox.addWidget(name_label)

        self.create_editor(hbox)

        x_button = QToolButton(self)
        x_button.setIcon(QIcon("icons/icons/x.png"))
        x_button.setStyleSheet("QToolButton { border: 0px solid #575757; background-color: palette(base); }")
        x_button.clicked.connect(partial(self.window.remove_component, self))
        hbox.addWidget(x_button, Qt.AlignRight)

    def create_editor(self, hbox):
        pass

    def on_value_changed(self, val):
        self._data.value = val

    @property
    def data(self):
        return self._data

class IntItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        self.editor = QSpinBox(self)
        self.set_format()
        if self._data.value is None:
            self._data.value = 0
        self.editor.setValue(self._data.value)
        self.editor.valueChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

    def on_value_changed(self, val):
        self._data.value = int(val)

    def set_format(self):
        self.editor.setMaximumWidth(60)
        self.editor.setRange(-1000, 1000)

class HitItemComponent(IntItemComponent):
    def set_format(self):
        self.editor.setMaximumWidth(60)
        self.editor.setRange(-1000, 1000)
        self.editor.setSingleStep(5)

class ValueItemComponent(IntItemComponent):
    def set_format(self):
        self.editor.setMaximumWidth(70)
        self.editor.setRange(0, 99999)

class FloatItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        self.editor = QDoubleSpinBox(self)
        self.editor.setMaximumWidth(60)
        self.editor.setRange(0, 10)
        self.editor.setSingleStep(.05)
        if self._data.value is None:
            self._data.value = 0
        self.editor.setValue(self._data.value)
        self.editor.valueChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

    def on_value_changed(self, val):
        self._data.value = float(val)

class StringItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        self.editor = QLineEdit(self)
        self.editor.setMaximumWidth(640)
        if not self._data.value:
            self._data.value = ''
        self.editor.setText(str(self._data.value))
        self.editor.textChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

    def on_value_changed(self, text):
        self._data.value = text

class DropDownItemComponent(BoolItemComponent):
    def __init__(self, data, parent, options):
        self.options = options if options else ['N/A']
        super().__init__(data, parent)

    def create_editor(self, hbox):
        self.editor = QComboBox(self)
        self.editor.setMaximumWidth(320)
        self.editor.addItems(self.options)
        if not self._data.value:
            self._data.value = self.options[0]
        self.editor.setCurrentIndex(self.options.index(self._data.value))
        self.editor.currentIndexChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

    def on_value_changed(self, val):
        self._data.value = self.options[val]

class WeaponTypeItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        self.editor = ComboBox(self)
        self.editor.setMaximumWidth(120)
        for weapon_type in DB.weapons.values():
            self.editor.addItem(weapon_type.nid)
        if not self._data.value and DB.weapons:
            self._data.value = DB.weapons[0].nid
        self.editor.setValue(self._data.value)
        self.editor.currentTextChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

class WeaponRankItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        self.editor = ComboBox(self)
        self.editor.setMaximumWidth(120)
        for weapon_rank in DB.weapon_ranks.values():
            self.editor.addItem(weapon_rank.nid)
        if not self._data.value and DB.weapon_ranks:
            self._data.value = DB.weapon_ranks[0].nid
        self.editor.setValue(self._data.value)
        self.editor.currentTextChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

class EquationItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        self.editor = ComboBox(self)
        self.editor.setMaximumWidth(120)
        self.editor.addItems(DB.equations.keys())
        if not self._data.value and DB.equations:
            self._data.value = DB.equations[0].nid
        self.editor.setValue(self._data.value)
        self.editor.currentTextChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

    def on_value_changed(self):
        val = self.editor.currentText()
        self._data.value = val

class Color3ItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        if not self._data.value:
            self._data.value = (0, 0, 0)
        color = self._data.value
        self.color = ColorIcon(QColor(*color), self)
        self.color.set_size(32)
        self.color.colorChanged.connect(self.on_value_changed)
        hbox.addWidget(self.color)

    def on_value_changed(self, val):
        color = self.color.color()
        r, g, b = color.red(), color.green(), color.blue()
        self._data.value = (r, g, b)

class Color4ItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        if not self._data.value:
            self._data.value = (0, 0, 0, 0)
        color = self._data.value
        self.color = AlphaColorIcon(QColor(*color), self)
        self.color.set_size(32)
        self.color.colorChanged.connect(self.on_value_changed)
        hbox.addWidget(self.color)

    def on_value_changed(self, val):
        color = self.color.color()
        r, g, b, a = color.red(), color.green(), color.blue(), color.alpha()
        self._data.value = (r, g, b, a)

class ClassItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        self.editor = ComboBox(self)
        self.editor.setMaximumWidth(120)
        for klass in DB.classes.values():
            self.editor.addItem(klass.nid)
        if not self._data.value and DB.classes:
            self._data.value = DB.classes[0].nid
        self.editor.setValue(self._data.value)
        self.editor.currentTextChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

class AffinityItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        self.editor = ComboBox(self)
        self.editor.setMaximumWidth(120)
        for affinity in DB.affinities.values():
            self.editor.addItem(affinity.nid)
        if not self._data.value and DB.affinities:
            self._data.value = DB.affinities[0].nid
        self.editor.setValue(self._data.value)
        self.editor.currentTextChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

class ItemItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        self.editor = ComboBox(self)
        self.editor.setMaximumWidth(120)
        for item in DB.items.values():
            self.editor.addItem(item.nid)
        if not self._data.value and DB.items:
            self._data.value = DB.items[0].nid
        self.editor.setValue(self._data.value)
        self.editor.currentTextChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

class SkillItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        self.editor = ComboBox(self)
        self.editor.setMaximumWidth(120)
        for skill in DB.skills.values():
            self.editor.addItem(skill.nid)
        if not self._data.value and DB.skills:
            self._data.value = DB.skills[0].nid
        self.editor.setValue(self._data.value)
        self.editor.currentTextChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

class SoundItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        self.editor = ComboBox(self)
        self.editor.setMaximumWidth(120)
        for sound in RESOURCES.sfx.values():
            self.editor.addItem(sound.nid)
        if not self._data.value and RESOURCES.sfx:
            self._data.value = RESOURCES.sfx[0].nid
        self.editor.setValue(self._data.value)
        self.editor.currentTextChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

class MapAnimationItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        self.editor = ComboBox(self)
        self.editor.setMaximumWidth(120)
        for map_anim in RESOURCES.animations.values():
            self.editor.addItem(map_anim.nid)
        if not self._data.value and RESOURCES.animations:
            self._data.value = RESOURCES.animations[0].nid
        self.editor.setValue(self._data.value)
        self.editor.currentTextChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

class EffectAnimationItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        self.editor = ComboBox(self)
        self.editor.setMaximumWidth(120)
        for effect_anim in RESOURCES.combat_effects.values():
            self.editor.addItem(effect_anim.nid)
        if not self._data.value and RESOURCES.combat_effects:
            self._data.value = RESOURCES.combat_effects[0].nid
        self.editor.setValue(self._data.value)
        self.editor.currentTextChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

class AIItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        self.editor = ComboBox(self)
        self.editor.setMaximumWidth(120)
        self.editor.addItems(DB.ai.keys())
        if not self._data.value and DB.ai:
            self._data.value = DB.ai[0].nid
        self.editor.setValue(self._data.value)
        self.editor.currentTextChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

    def on_value_changed(self):
        val = self.editor.currentText()
        self._data.value = val

class MovementTypeItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        self.editor = ComboBox(self)
        self.editor.setMaximumWidth(120)
        self.editor.addItems(DB.mcost.unit_types)
        if not self._data.value and DB.mcost.unit_types:
            self._data.value = DB.mcost.unit_types[0]
        self.editor.setValue(self._data.value)
        self.editor.currentTextChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

    def on_value_changed(self):
        val = self.editor.currentText()
        self._data.value = val

class StatItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        self.editor = ComboBox(self)
        self.editor.setMaximumWidth(120)
        self.editor.addItems(DB.stats.keys())
        if not self._data.value and DB.stats:
            self._data.value = DB.stats[0].nid
        self.editor.setValue(self._data.value)
        self.editor.currentTextChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

    def on_value_changed(self):
        val = self.editor.currentText()
        self._data.value = val

class EventItemComponent(BoolItemComponent):
    def create_editor(self, hbox):
        self.editor = ComboBox(self)
        self.editor.setMaximumWidth(120)
        # Only use global events
        valid_events = [event for event in DB.events.values() if not event.level_nid]
        for event in valid_events:
            self.editor.addItem(event.nid)
        if not self._data.value and valid_events:
            self._data.value = valid_events[0].nid
        self.editor.setValue(self._data.value)
        self.editor.currentTextChanged.connect(self.on_value_changed)
        hbox.addWidget(self.editor)

# Delegates
class UnitDelegate(QItemDelegate):
    data = DB.units
    name = "Unit"
    is_float = False

    def createEditor(self, parent, option, index):
        if index.column() == 0:
            editor = ComboBox(parent)
            for obj in self.data:
                editor.addItem(obj.nid)
            return editor
        elif index.column() == 1:  # Integer value column
            if self.is_float:
                editor = QDoubleSpinBox(parent)
                editor.setRange(0, 10)
            else:
                editor = QSpinBox(parent)
                editor.setRange(-1000, 1000)
            return editor
        else:
            return super().createEditor(parent, option, index)

class ClassDelegate(UnitDelegate):
    data = DB.classes
    name = "Class"

class AffinityDelegate(UnitDelegate):
    data = DB.affinities
    name = "Affinity"

class TagDelegate(UnitDelegate):
    data = DB.tags
    name = "Tag"

class ItemDelegate(UnitDelegate):
    data = DB.items
    name = "Item"

class StatDelegate(UnitDelegate):
    data = DB.stats
    name = "Stat"

class WeaponTypeDelegate(UnitDelegate):
    data = DB.weapons
    name = "Weapon Type"

class ListItemComponent(BoolItemComponent):
    delegate = None

    def create_editor(self, hbox):
        if not self._data.value:
            self._data.value = []
        self.editor = AppendSingleListWidget(self._data.value, self._data.name, self.delegate, self)
        self.editor.view.setColumnWidth(0, 100)
        self.editor.view.setMaximumHeight(75)
        self.editor.model.nid_column = 0

        hbox.addWidget(self.editor)

class DictItemComponent(BoolItemComponent):
    delegate = None

    def create_editor(self, hbox):
        if not self._data.value:
            self.data.value = []
        title = self._data.name
        self.modify_delegate()
        self.editor = AppendMultiListWidget(self._data.value, title, (self.delegate.name, "Value"), self.delegate, self, model=list_models.DoubleListModel)
        self.editor.view.setColumnWidth(0, 100)
        self.editor.view.setMaximumHeight(75)
        self.editor.model.nid_column = 0

        hbox.addWidget(self.editor)

    def modify_delegate(self):
        self.delegate.is_float = False

class FloatDictItemComponent(DictItemComponent):
    def modify_delegate(self):
        self.delegate.is_float = True

def get_display_widget(component, parent):
    if not component.expose:
        c = BoolItemComponent(component, parent)
    elif component.expose == Type.Int:
        if component.nid == 'hit':
            c = HitItemComponent(component, parent)
        elif component.nid == 'value':
            c = ValueItemComponent(component, parent)
        else:
            c = IntItemComponent(component, parent)
    elif component.expose == Type.Float:
        c = FloatItemComponent(component, parent)
    elif component.expose == Type.String:
        c = StringItemComponent(component, parent)
    elif component.expose == Type.WeaponType:
        c = WeaponTypeItemComponent(component, parent)
    elif component.expose == Type.WeaponRank:
        c = WeaponRankItemComponent(component, parent)
    elif component.expose == Type.Color3:
        c = Color3ItemComponent(component, parent)
    elif component.expose == Type.Color4:
        c = Color4ItemComponent(component, parent)
    elif component.expose == Type.Class:
        c = ClassItemComponent(component, parent)
    elif component.expose == Type.Affinity:
        c = AffinityItemComponent(component, parent)
    elif component.expose == Type.Item:
        c = ItemItemComponent(component, parent)
    elif component.expose == Type.Skill:
        c = SkillItemComponent(component, parent)
    elif component.expose == Type.MapAnimation:
        c = MapAnimationItemComponent(component, parent)
    elif component.expose == Type.EffectAnimation:
        c = EffectAnimationItemComponent(component, parent)
    elif component.expose == Type.Equation:
        c = EquationItemComponent(component, parent)
    elif component.expose == Type.Sound:
        c = SoundItemComponent(component, parent)
    elif component.expose == Type.AI:
        c = AIItemComponent(component, parent)
    elif component.expose == Type.Stat:
        c = StatItemComponent(component, parent)
    elif component.expose == Type.Event:
        c = EventItemComponent(component, parent)
    elif component.expose == Type.MovementType:
        c = MovementTypeItemComponent(component, parent)
    elif isinstance(component.expose, tuple):
        delegate = None
        if component.expose[1] == Type.Unit:
            delegate = UnitDelegate
        elif component.expose[1] == Type.Class:
            delegate = ClassDelegate
        elif component.expose[1] == Type.Affinity:
            delegate = AffinityDelegate
        elif component.expose[1] == Type.Tag:
            delegate = TagDelegate
        elif component.expose[1] == Type.Item:
            delegate = ItemDelegate
        elif component.expose[1] == Type.Stat:
            delegate = StatDelegate
        elif component.expose[1] == Type.WeaponType:
            delegate = WeaponTypeDelegate

        if component.expose[0] == Type.List:
            c = ListItemComponent(component, parent, delegate)
        elif component.expose[0] == Type.Dict:
            c = DictItemComponent(component, parent, delegate)
        elif component.expose[0] == Type.FloatDict:
            c = FloatDictItemComponent(component, parent, delegate)
        elif component.expose[0] == Type.MultipleChoice:
            c = DropDownItemComponent(component, parent, component.expose[1])

    else:  # TODO
        c = BoolItemComponent(component, parent)
    return c
