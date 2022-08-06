import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path

from app.constants import VERSION
from app.data.database import DB
from app.editor import timer
from app.editor.new_game_dialog import NewGameDialog
from app.editor.settings import MainSettingsController
from app.resources.resources import RESOURCES
from PyQt5.QtCore import QDir, Qt
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QProgressDialog


class ProjectFileBackend():
    def __init__(self, parent, app_state_manager):
        self.parent = parent
        self.app_state_manager = app_state_manager
        self.settings = MainSettingsController()
        self.current_proj = self.settings.get_current_project()

        self.save_progress = QProgressDialog("Saving project to %s" % self.current_proj, None, 0, 100, self.parent)
        self.save_progress.setAutoClose(True)
        self.save_progress.setWindowTitle("Saving Project")
        self.save_progress.setWindowModality(Qt.WindowModal)
        self.save_progress.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.save_progress.reset()

        self.autosave_progress = QProgressDialog("Autosaving project to %s" % os.path.abspath('autosave.ltproj'), None, 0, 100, self.parent)
        self.autosave_progress.setAutoClose(True)
        self.autosave_progress.setWindowTitle("Autosaving Project")
        self.autosave_progress.setWindowModality(Qt.WindowModal)
        self.autosave_progress.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.autosave_progress.reset()

        timer.get_timer().autosave_timer.timeout.connect(self.autosave)

    def maybe_save(self):
        # if not self.undo_stack.isClean():
        if True:  # For now, since undo stack is not being used
            ret = QMessageBox.warning(self.parent, "Main Editor", "The current project may have been modified.\n"
                                      "Do you want to save your changes?",
                                      QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            if ret == QMessageBox.Save:
                return self.save()
            elif ret == QMessageBox.Cancel:
                return False
        return True

    def save(self, new=False):
        # check if we're editing default, if so, prompt to save as
        if self.current_proj and os.path.basename(self.current_proj) == 'default.ltproj':
            self.current_proj = None
        if new or not self.current_proj:
            starting_path = self.current_proj or QDir.currentPath()
            fn, ok = QFileDialog.getSaveFileName(self.parent, "Save Project", starting_path,
                                                 "All Files (*)")
            if ok:
                # Make sure you can't save as "autosave" or "default"
                if os.path.split(fn)[-1] in ('autosave.ltproj', 'default.ltproj', 'autosave', 'default'):
                    QMessageBox.critical(self.parent, "Save Error", "You cannot save project as <b>default.ltproj</b> or <b>autosave.ltproj</b>!\nChoose another name.")
                    return False
                if fn.endswith('.ltproj'):
                    self.current_proj = fn
                else:
                    self.current_proj = fn + '.ltproj'
                self.settings.set_current_project(self.current_proj)
            else:
                return False
            new = True

        if new:
            if os.path.exists(self.current_proj):
                ret = QMessageBox.warning(self.parent, "Save Project", "The file already exists.\nDo you want to overwrite it?",
                                          QMessageBox.Save | QMessageBox.Cancel)
                if ret == QMessageBox.Save:
                    pass
                else:
                    return False

        # Make directory for saving if it doesn't already exist
        if not new and self.settings.get_should_make_backup_save():
            # to make sure we don't accidentally make a bad save
            # we will copy either the autosave, or the existing save (whichever is more recent)
            # as a backup
            self.tmp_proj = self.current_proj + '.lttmp'
            self.save_progress.setLabelText("Making backup to %s" % self.tmp_proj)
            self.save_progress.setValue(1)
            if os.path.exists(self.tmp_proj):
                shutil.rmtree(self.tmp_proj)

            # check if autosave or current save is more recent
            most_recent_path = self.current_proj
            try:
                autosave_dir = os.path.abspath('autosave.ltproj')
                autosave_meta = json.load(open(autosave_dir + '/metadata.json'))
                curr_meta = json.load(open(self.current_proj + '/metadata.json'))
                if autosave_meta['project'] == curr_meta['project']: # make sure same project
                    autosave_ts = datetime.strptime(autosave_meta['date'], '%Y-%m-%d %H:%M:%S.%f')
                    curr_ts = datetime.strptime(curr_meta['date'], '%Y-%m-%d %H:%M:%S.%f')
                    if autosave_ts > curr_ts:
                        most_recent_path = autosave_dir
            except Exception as e:
                # autosave doesn't have metadata, autosave doesn't exist, etc.
                # just copy the previous save
                pass
            shutil.copytree(most_recent_path, self.tmp_proj)
        self.save_progress.setLabelText("Saving project to %s" % self.current_proj)
        self.save_progress.setValue(10)

        # Actually save project
        RESOURCES.save(self.current_proj, progress=self.save_progress)
        self.save_progress.setValue(75)
        DB.serialize(self.current_proj)
        self.save_progress.setValue(99)

        # Save metadata
        self.save_metadata(self.current_proj)

        self.save_progress.setValue(100)

        if not new and self.settings.get_should_make_backup_save():
            # we have fully saved the current project; remove the backup folder
            if os.path.isdir(self.tmp_proj):
                shutil.rmtree(self.tmp_proj)

        return True

    def new(self):
        if self.maybe_save():
            result = NewGameDialog.get()
            if result:
                identifier, title = result

                RESOURCES.load('default.ltproj')
                DB.load('default.ltproj')
                DB.constants.get('game_nid').set_value(identifier)
                DB.constants.get('title').set_value(title)
            return result
        return False

    def open(self):
        if self.maybe_save():
            # Go up one directory when starting
            if self.current_proj:
                starting_path = os.path.join(self.current_proj, '..')
            else:
                starting_path = QDir.currentPath()
            fn = QFileDialog.getExistingDirectory(
                self.parent, "Open Project Directory", starting_path)
            if fn:
                self.current_proj = fn
                self.settings.set_current_project(self.current_proj)
                logging.info("Opening project %s" % self.current_proj)
                self.load()
                return True
            else:
                return False
        return False

    def auto_open_fallback(self):
        self.current_proj = "default.ltproj"
        self.settings.set_current_project(self.current_proj)
        self.load()

    def auto_open(self):
        path = self.settings.get_current_project()
        logging.info("Auto Open: %s" % path)

        if path and os.path.exists(path):
            try:
                self.current_proj = path
                self.settings.set_current_project(self.current_proj)
                self.load()
                return True
            except Exception as e:
                logging.error(e)
                backup_project_name = path + '.lttmp'
                corrupt_project_name = path + '.ltcorrupt'
                logging.warning("Failed to load project at %s. Likely that project is corrupted.", path)
                logging.warning("the corrupt project will be stored at %s.", corrupt_project_name)
                QMessageBox.warning(self.parent, "Load of project failed",
                                    "Failed to load project at %s. Likely that project is corrupted.\nLoading from backup if available." % path)
                logging.info("Attempting load from backup project %s, which will be renamed to %s", backup_project_name, path)
                if os.path.exists(backup_project_name):
                    try:
                        if os.path.exists(corrupt_project_name):
                            shutil.rmtree(corrupt_project_name)
                        shutil.copytree(path, corrupt_project_name)
                        shutil.rmtree(path)
                        shutil.copytree(backup_project_name, path)
                        self.current_proj = path
                        self.settings.set_current_project(self.current_proj)
                        self.load()
                        return True
                    except Exception as e:
                        logging.error(e)
                        logging.warning("failed to load project at %s.", backup_project_name)
                else:
                    logging.warning("no project found at %s", backup_project_name)
                logging.warning("falling back to default.ltproj")
                self.auto_open_fallback()
                return False
        else:
            logging.warning("path %s not found. Falling back to default.ltproj" % path)
            self.auto_open_fallback()
            return False

    def load(self):
        if os.path.exists(self.current_proj):
            RESOURCES.load(self.current_proj)
            DB.load(self.current_proj)
            from app.engine import equations
            equations.clear()

    def autosave(self):
        autosave_dir = os.path.abspath('autosave.ltproj')
        # Make directory for saving if it doesn't already exist
        if not os.path.isdir(autosave_dir):
            os.mkdir(autosave_dir)
        self.autosave_progress.setValue(1)

        try:
            self.parent.status_bar.showMessage(
                'Autosaving project to %s...' % autosave_dir)
        except Exception:
            pass

        # Actually save project
        logging.info("Autosaving project to %s..." % autosave_dir)
        RESOURCES.save(autosave_dir, specific='autosave', progress=self.autosave_progress)
        self.autosave_progress.setValue(75)
        DB.serialize(autosave_dir)
        self.autosave_progress.setValue(99)

        # Save metadata
        self.save_metadata(autosave_dir)

        try:
            self.parent.status_bar.showMessage(
                'Autosave to %s complete!' % autosave_dir)
        except Exception:
            pass
        self.autosave_progress.setValue(100)

    def save_metadata(self, save_dir):
        metadata_loc = os.path.join(save_dir, 'metadata.json')
        metadata = {}
        metadata['date'] = str(datetime.now())
        metadata['version'] = VERSION
        metadata['project'] = DB.constants.get('game_nid').value
        with open(metadata_loc, 'w') as serialize_file:
            json.dump(metadata, serialize_file, indent=4)

    def clean(self):
        RESOURCES.clean(self.current_proj)
