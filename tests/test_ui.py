"""Unit tests for Flet UI components and integration."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock

from core.models import OrganizeConfig, RenameConfig
from ui.app import FilesPyApp


class TestFilesPyUI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp_dir.name)
        (self.folder / "report.pdf").write_text("dummy pdf")
        (self.folder / "image.png").write_text("dummy png")
        (self.folder / "data.csv").write_text("dummy csv")

        self.mock_page = MagicMock()
        self.mock_page.overlay = []
        self.app = FilesPyApp(self.mock_page)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_app_initialization(self):
        self.assertIsNotNone(self.app.folder_bar)
        self.assertIsNotNone(self.app.rename_panel)
        self.assertIsNotNone(self.app.organize_panel)
        self.assertIsNotNone(self.app.duplicate_panel)
        self.assertIsNotNone(self.app.preview_table)
        self.assertIsNotNone(self.app.inspector)
        self.assertIsNotNone(self.app.action_bar)

    def test_folder_selection_and_pipeline(self):
        self.app.folder_bar.set_folder(self.folder)
        self.assertEqual(len(self.app.raw_scanned_items), 3)

        # Test renaming pipeline
        self.app._on_rename_rules_changed(RenameConfig(prefix="PRE_"))
        self.assertTrue(all(it.new_name.startswith("PRE_") for it in self.app.processed_items))

        # Test organization pipeline
        self.app._on_organize_rules_changed(OrganizeConfig(mode="by_extension"))
        self.assertTrue(all(it.target_folder is not None for it in self.app.processed_items))

    def test_apply_and_undo_flow(self):
        self.app.folder_bar.set_folder(self.folder)
        self.app._on_rename_rules_changed(RenameConfig(prefix="NEW_"))

        items = [it for it in self.app.processed_items if it.selected and it.is_modified]
        self.assertEqual(len(items), 3)

        self.app._execute_apply(items)
        self.assertTrue(self.app.undo_manager.can_undo())
        self.assertTrue((self.folder / "NEW_report.pdf").exists())

        restored, errors = self.app.undo_manager.undo_last()
        self.assertEqual(restored, 3)
        self.assertEqual(len(errors), 0)
        self.assertTrue((self.folder / "report.pdf").exists())


if __name__ == "__main__":
    unittest.main()
