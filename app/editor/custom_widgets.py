from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import QSize

# Custom Widgets
from app.utilities.data import Data
from app.data.database import DB

from app.extensions.custom_gui import PropertyBox, ComboBox

class ObjBox(PropertyBox):
    def __init__(self, title, model, database, parent=None, button=False):
        super().__init__(title, ComboBox, parent)
        self.model = model(database, parent)
        self.edit.setModel(self.model)
        if button:
            b = QPushButton('...')
            b.setMaximumWidth(40)
            self.add_button(b)

    def setValue(self, val):
        self.edit.setValue(val)

class UnitBox(ObjBox):
    def __init__(self, parent=None, button=False, exclude=None, title="Unit"):
        from app.editor.unit_editor.unit_model import UnitModel
        database = DB.units
        if exclude:
            database = Data([d for d in DB.units if d is not exclude])
        super().__init__(title, UnitModel, database, parent, button)
        self.edit.setIconSize(QSize(32, 32))
        self.edit.view().setUniformItemSizes(True)

class ClassBox(ObjBox):
    def __init__(self, parent=None, button=False, exclude=None):
        from app.editor.class_editor.class_model import ClassModel
        database = DB.classes
        if exclude:
            database = Data([d for d in DB.classes if d is not exclude])
        super().__init__("Class", ClassModel, database, parent, button)
        self.edit.setIconSize(QSize(32, 32))
        self.edit.view().setUniformItemSizes(True)

class FactionBox(ObjBox):
    def __init__(self, parent=None, button=False, exclude=None):
        from app.editor.faction_editor.faction_model import FactionModel
        database = DB.factions
        if exclude:
            database = Data([d for d in DB.factions if d is not exclude])
        super().__init__("Faction", FactionModel, database, parent, button)

class ItemBox(ObjBox):
    def __init__(self, parent=None, button=False, exclude=None):
        from app.editor.item_editor.item_model import ItemModel
        database = DB.items
        if exclude:
            database = Data([d for d in DB.items if d is not exclude])
        super().__init__("Item", ItemModel, database, parent, button)

class SkillBox(ObjBox):
    def __init__(self, parent=None, button=False, exclude=None):
        from app.editor.skill_editor.skill_model import SkillModel
        database = DB.skills
        if exclude:
            database = Data([d for d in DB.skills if d is not exclude])
        super().__init__("Skill", SkillModel, database, parent, button)

class AIBox(ObjBox):
    def __init__(self, parent=None, button=False, exclude=None):
        from app.editor.ai_editor.ai_model import AIModel
        database = DB.ai
        if exclude:
            database = Data([d for d in DB.ai if d is not exclude])
        super().__init__("AI", AIModel, database, parent, button)

class WeaponTypeBox(ObjBox):
    def __init__(self, parent=None, button=False, exclude=None):
        from app.editor.weapon_editor.weapon_model import WeaponModel
        database = DB.weapons
        if exclude:
            database = Data([d for d in DB.weapons if d is not exclude])
        super().__init__("Weapon Type", WeaponModel, database, parent, button)

class PartyBox(ObjBox):
    def __init__(self, parent=None, button=False, exclude=None):
        from app.editor.party_editor.party_model import PartyModel
        database = DB.parties
        if exclude:
            database = Data([d for d in DB.parties if d is not exclude])
        super().__init__("Party", PartyModel, database, parent, button)

class AffinityBox(ObjBox):
    def __init__(self, parent=None, button=False, exclude=None):
        from app.editor.support_editor.affinity_model import AffinityModel
        database = DB.affinities
        if exclude:
            database = Data([d for d in DB.affinities if d is not exclude])
        super().__init__("Affinity Type", AffinityModel, database, parent, button)

class MovementCostBox(ObjBox):
    def __init__(self, parent=None, button=False):
        from app.editor.mcost_dialog import MovementCostModel
        super().__init__("Movement Cost", MovementCostModel, DB.mcost, parent, button)

class MovementClassBox(ObjBox):
    def __init__(self, parent=None, button=False):
        from app.editor.mcost_dialog import MovementClassModel
        super().__init__("Movement Class", MovementClassModel, DB.mcost, parent, button)
