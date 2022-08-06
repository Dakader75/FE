import functools

from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, \
    QMessageBox, QHBoxLayout, QAction, QToolButton, QToolBar, QTextEdit, \
    QVBoxLayout, QSizePolicy, QSpacerItem, QWidgetAction
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFontMetrics

from app.data.database import DB

from app.extensions.custom_gui import PropertyBox, QHLine
from app.editor.icons import ItemIcon16
from app.editor.settings import MainSettingsController
from app.editor import component_database
from app.utilities import str_utils
from app.extensions.qhelpmenu import QHelpMenu

class ComponentProperties(QWidget):
    title = None
    get_components = None
    get_templates = None

    def __init__(self, parent, current=None):
        super().__init__(parent)
        self.window = parent
        self.model = self.window.left_frame.model
        self._data = self.window._data

        self.current = current

        top_section = QHBoxLayout()

        self.icon_edit = ItemIcon16(self)
        top_section.addWidget(self.icon_edit)

        horiz_spacer = QSpacerItem(40, 10, QSizePolicy.Fixed, QSizePolicy.Fixed)
        top_section.addSpacerItem(horiz_spacer)

        name_section = QVBoxLayout()

        self.nid_box = PropertyBox("Unique ID", QLineEdit, self)
        self.nid_box.edit.textChanged.connect(self.nid_changed)
        self.nid_box.edit.editingFinished.connect(self.nid_done_editing)
        name_section.addWidget(self.nid_box)

        self.name_box = PropertyBox("Display Name", QLineEdit, self)
        self.name_box.edit.textChanged.connect(self.name_changed)
        name_section.addWidget(self.name_box)

        top_section.addLayout(name_section)

        main_section = QGridLayout()

        self.desc_box = PropertyBox("Description", QTextEdit, self)
        self.desc_box.edit.textChanged.connect(self.desc_changed)
        font_height = QFontMetrics(self.desc_box.edit.font())
        self.desc_box.edit.setFixedHeight(font_height.lineSpacing() * 3 + 20)
        main_section.addWidget(self.desc_box, 0, 0, 1, 3)

        component_section = QGridLayout()
        component_label = QLabel("Components")
        component_label.setAlignment(Qt.AlignBottom)
        component_section.addWidget(component_label, 0, 0, Qt.AlignBottom)

        # Create actions
        self.actions = {}
        for component in self.get_components():
            new_func = functools.partial(self.add_component, component)
            new_action = QAction(QIcon(), component.class_name(), self, triggered=new_func)
            new_action.setToolTip(component.desc)
            self.actions[component.nid] = new_action

        # Create toolbar
        self.toolbar = QToolBar(self)
        self.menus = {}

        self.settings = MainSettingsController()
        theme = self.settings.get_theme(0)
        if theme == 0:
            icon_folder = 'icons/icons'
        else:
            icon_folder = 'icons/dark_icons'

        for component in self.get_components():
            if component.tag == 'memento' and \
                    not DB.constants.value('game_nid').lower() == 'memento':
                continue
            if component.tag not in self.menus:
                new_menu = QHelpMenu(self)
                self.menus[component.tag] = new_menu
                toolbutton = QToolButton(self)
                toolbutton.setIcon(QIcon(f"{icon_folder}/component_%s.png" % component.tag))
                toolbutton.setMenu(new_menu)
                toolbutton.setPopupMode(QToolButton.InstantPopup)
                toolbutton_action = QWidgetAction(self)
                toolbutton_action.setDefaultWidget(toolbutton)
                self.toolbar.addAction(toolbutton_action)
            menu = self.menus[component.tag]
            menu.addAction(self.actions.get(component.nid))

        # Template action
        for template_key, template_value in self.get_templates():
            new_func = functools.partial(self.add_template, template_value)
            template_action = QAction(QIcon(), template_key, self, triggered=new_func)
            self.actions[template_key] = template_action

        if self.get_templates():
            template_menu = QHelpMenu(self)
            self.menus['templates'] = template_menu
            toolbutton = QToolButton(self)
            toolbutton.setIcon(QIcon(f"{icon_folder}/component_template.png"))
            toolbutton.setMenu(template_menu)
            toolbutton.setPopupMode(QToolButton.InstantPopup)
            toolbutton_action = QWidgetAction(self)
            toolbutton_action.setDefaultWidget(toolbutton)
            self.toolbar.addAction(toolbutton_action)

        for template_key, template_value in self.get_templates():
            menu = self.menus['templates']
            menu.addAction(self.actions.get(template_key))

        component_section.addWidget(self.toolbar, 1, 0, 1, 2)

        self.component_list = component_database.ComponentList(self)
        component_section.addWidget(self.component_list, 2, 0, 1, 2)
        self.component_list.order_swapped.connect(self.component_moved)

        total_section = QVBoxLayout()
        self.setLayout(total_section)
        total_section.addLayout(top_section)
        total_section.addLayout(main_section)
        h_line = QHLine()
        total_section.addWidget(h_line)
        total_section.addLayout(component_section)

    def nid_changed(self, text):
        # Also change name if they are identical
        if self.current.name == self.current.nid:
            self.name_box.edit.setText(text)
        self.current.nid = text
        self.window.update_list()

    def nid_done_editing(self):
        # Check validity of nid!
        other_nids = [d.nid for d in self._data.values() if d is not self.current]
        if self.current.nid in other_nids:
            QMessageBox.warning(self.window, 'Warning', '%s ID %s already in use' % (self.title, self.current.nid))
            self.current.nid = str_utils.get_next_name(self.current.nid, other_nids)
        self.model.on_nid_changed(self._data.find_key(self.current), self.current.nid)
        self._data.update_nid(self.current, self.current.nid)
        self.window.update_list()

    def name_changed(self, text):
        self.current.name = text
        self.window.update_list()

    def desc_changed(self, text=None):
        self.current.desc = self.desc_box.edit.toPlainText()
        # self.current.desc = text

    def add_template(self, component_list):
        all_components = self.get_components()
        for component_nid in component_list:
            self.add_component(all_components.get(component_nid))

    def add_component(self, component_class):
        component = component_class(component_class.value)
        if component.nid in self.current.components.keys():
            QMessageBox.warning(self.window, 'Warning', '%s component already present' % component.class_name())
        else:
            self.current.components.append(component)
            self.add_component_widget(component)
            # Add other components that this should be paired with
            for pair in component.paired_with:
                if pair not in self.current.components.keys():
                    self.add_component(self.get_components().get(pair))

    def add_component_widget(self, component):
        c = component_database.get_display_widget(component, self)
        self.component_list.add_component(c)

    def remove_component(self, component_widget):
        data = component_widget._data
        self.component_list.remove_component(component_widget)
        self.current.components.delete(data)
        # Remove all paired components
        for pair in data.paired_with:
            if pair in self.current.components.keys():
                idx = self.component_list.index_list.index(pair)
                item = self.component_list.item(idx)
                component_widget = self.component_list.itemWidget(item)
                self.remove_component(component_widget)

    def component_moved(self, start, end):
        self.current.components.move_index(start, end)

    def set_current(self, current):
        self.current = current
        self.nid_box.edit.setText(current.nid)
        self.name_box.edit.setText(current.name)
        self.desc_box.edit.setText(current.desc)
        self.icon_edit.set_current(current.icon_nid, current.icon_index)
        self.component_list.clear()
        for component in current.components.values():
            self.add_component_widget(component)
