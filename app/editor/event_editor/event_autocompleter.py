from functools import lru_cache
from typing import List, Tuple

from app.events import event_commands, event_validators
from app.utilities.typing import NID
from app.editor.settings import MainSettingsController

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QCompleter


class Completer(QCompleter):
    insertText = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = MainSettingsController()

        self.setFilterMode(Qt.MatchContains)
        self.activated.connect(self.changeCompletion)

    def changeCompletion(self, completion):
        self.insertText.emit(completion)
        self.popup().hide()

    def handleKeyPressEvent(self, event) -> bool:
        """Handles a key press event.

        Args:
            event (Qt.Key): qt key event

        Returns:
            bool: whether or not the event should be consumed.
        """
        if event.key() == self.settings.get_autocomplete_button(Qt.Key_Tab):
            if self.popup().isVisible() and len(self.popup().selectedIndexes()) > 0:
                # If completer is up, Tab/Enter can auto-complete
                completion = self.popup().selectedIndexes()[0].data(Qt.DisplayRole)
                self.changeCompletion(completion)
                return True # should not enter a tab
        elif event.key() == Qt.Key_Backspace:
            # autofill functionality, hides autofill windows
            if self.popup().isVisible():
                self.popup().hide()
        elif event.key() == Qt.Key_Escape:
            if self.popup().isVisible():
                self.popup().hide()
        return False

@lru_cache()
def generate_wordlist_from_validator_type(validator: event_validators.Validator, level: NID = None) -> List[str]:
    if not validator:
        return []
    valid_entries = validator().valid_entries(level)
    autofill_dict = []
    for entry in valid_entries:
        if entry[0] is None:
            # no name, but has nid
            autofill_dict.append('{}'.format(entry[1]))
        else:
            # has name and nid
            autofill_dict.append('{name} ({nid})'.format(
                name=entry[0], nid=entry[1]))
    return autofill_dict


def generate_flags_wordlist(flags: List[str] = []) -> List[str]:
    flaglist = []
    if len(flags) > 0:
        # then we can also put flags in this slot
        for flag in flags:
            flaglist.append('FLAG({flag})'.format(flag=flag))
    return flaglist

def detect_command_under_cursor(line: str) -> event_commands.EventCommand:
    return event_commands.parse_text(line)

def detect_type_under_cursor(line: str, cursor_pos: int) -> Tuple[event_validators.Validator, List[str]]:
    try:
        # turn off typechecking for comments
        comment_index = line.index("#")
        if cursor_pos > comment_index:
            return (event_validators.Validator, [])
    except ValueError:
        # no pound sign
        pass
    arg_idx = line.count(';', 0, cursor_pos) - 1
    flags = []
    # -1 is the command itself, and 0, 1, 2, etc. are the args
    if arg_idx == -1:
        return (event_validators.EventFunction, [])
    try:
        command = event_commands.parse_text(line)
        validator_name = None
        if command:
            if arg_idx >= len(command.keywords):
                # no longer required keywords, now add optionals and flags
                flags = command.flags
                i = arg_idx - len(command.keywords)
                if i < len(command.optional_keywords):
                    validator_name = command.optional_keywords[i]
            else:
                validator_name = command.keywords[arg_idx]
        if validator_name:
            validator = event_validators.get(validator_name)
        else:
            validator = event_validators.Validator
        return (validator, flags)
    except Exception as e:
        print(e)
        return (event_validators.Validator, [])
