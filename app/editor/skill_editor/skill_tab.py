import os

from PyQt5.QtWidgets import QFileDialog

from app.data.database import DB

from app.editor.data_editor import SingleDatabaseEditor
from app.editor.base_database_gui import DatabaseTab

import app.engine.skill_component_access as SCA

from app.editor.settings import MainSettingsController
from app.editor.skill_editor import skill_model, skill_import
from app.editor.component_properties import ComponentProperties

class SkillProperties(ComponentProperties):
    title = "Skill"
    get_components = staticmethod(SCA.get_skill_components)
    get_templates = staticmethod(SCA.get_templates)

class SkillDatabase(DatabaseTab):
    allow_import_from_lt = True
    allow_copy_and_paste = True

    @classmethod
    def create(cls, parent=None):
        data = DB.skills
        title = "Skill"
        right_frame = SkillProperties
        deletion_criteria = None
        collection_model = skill_model.SkillModel
        dialog = cls(data, title, right_frame, deletion_criteria, collection_model, parent)
        return dialog

    def import_data(self):
        settings = MainSettingsController()
        starting_path = settings.get_last_open_path()
        fn, ok = QFileDialog.getOpenFileName(self, "Import skills from status.xml", starting_path, "Status XML (status.xml);;All Files(*)")
        if ok and fn.endswith('status.xml'):
            parent_dir = os.path.split(fn)[0]
            settings.set_last_open_path(parent_dir)
            new_skills = skill_import.get_from_xml(parent_dir, fn)
            for skill in new_skills:
                self._data.append(skill)
            self.update_list()

# Testing
# Run "python -m app.editor.skill_editor.skill_tab" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    from app.resources.resources import RESOURCES
    RESOURCES.load('default.ltproj')
    DB.load('default.ltproj')
    window = SingleDatabaseEditor(SkillDatabase)
    window.show()
    app.exec_()
