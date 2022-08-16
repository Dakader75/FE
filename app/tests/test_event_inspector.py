from typing import List
import unittest
from unittest.mock import MagicMock, patch, call
from app.data.items import ItemCatalog
from app.data.klass import ClassCatalog
from app.data.units import UnitCatalog

from app.editor.event_editor.event_inspector import EventInspectorEngine
from app.events.event_commands import GiveItem

class EventInspectorTests(unittest.TestCase):
    def setUp(self):
        from app.data.database import Database
        self.db = Database()
        self.db.load('testing_proj.ltproj')
        self.event_inspector = EventInspectorEngine(self.db.events)

    def tearDown(self) -> None:
        pass

    def test_unit_dump(self):
        give_item_events = self.event_inspector.find_all_calls_of_command(GiveItem())
        self.assertEqual(len(give_item_events), 1)
        self.assertEqual(list(give_item_events.values())[0].to_plain_text(), 'give_item;101;Hand Axe (Hand Axe)')

if __name__ == '__main__':
    unittest.main()
