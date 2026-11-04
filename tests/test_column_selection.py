"""Unit tests for file property catalog, column customization, and PreviewTable rendering."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

import flet as ft
from PIL import Image

from core.config_manager import (
    COLUMN_DEFINITIONS,
    ConfigManager,
    DEFAULT_VISIBLE_COLUMNS,
)
from core.models import FileItem, FileStatus
from core.scanner import scan_directory
from ui.components.preview_table import PreviewTable
from ui.components.settings_dialog import SettingsDialog


class TestColumnSelectionAndProperties(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name).resolve()
        self.config_file = self.base_path / "test_settings.json"
        self.config_manager = ConfigManager(config_file=self.config_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_default_visible_columns_and_catalog(self):
        self.assertEqual(len(COLUMN_DEFINITIONS), 18)
        self.assertEqual(
            DEFAULT_VISIBLE_COLUMNS,
            ["original_name", "new_name", "target_folder", "size", "status"],
        )
        self.assertEqual(
            self.config_manager.get_visible_columns(),
            DEFAULT_VISIBLE_COLUMNS,
        )

    def test_save_and_load_visible_columns_persistence(self):
        custom_cols = [
            "original_name",
            "size",
            "modified_time",
            "created_time",
            "mime_type",
            "dimensions",
            "invalid_column_id",
        ]
        self.config_manager.save_visible_columns(custom_cols)

        reloaded_cm = ConfigManager(config_file=self.config_file)
        loaded_cols = reloaded_cm.get_visible_columns()
        self.assertEqual(
            loaded_cols,
            [
                "original_name",
                "size",
                "modified_time",
                "created_time",
                "mime_type",
                "dimensions",
            ],
        )

        # Empty list falls back to defaults
        self.config_manager.save_visible_columns([])
        self.assertEqual(
            self.config_manager.get_visible_columns(),
            DEFAULT_VISIBLE_COLUMNS,
        )

    def test_extended_file_item_properties_and_image_dimensions(self):
        # 1. Create a real test image (320x240)
        img_path = self.base_path / "foto_vacaciones.png"
        img = Image.new("RGB", (320, 240), color=(255, 0, 0))
        img.save(img_path)

        # 2. Create a hidden text file
        hidden_path = self.base_path / ".secreto.txt"
        hidden_path.write_text("contenido oculto", encoding="utf-8")

        scanned = scan_directory(self.base_path, include_hidden=True)
        by_name = {it.original_name: it for it in scanned}

        self.assertIn("foto_vacaciones.png", by_name)
        self.assertIn(".secreto.txt", by_name)

        img_item = by_name["foto_vacaciones.png"]
        self.assertEqual(img_item.stem, "foto_vacaciones")
        self.assertEqual(img_item.original_folder, self.base_path.name)
        self.assertEqual(img_item.original_full_path, str(img_path))
        self.assertFalse(img_item.is_hidden)
        self.assertEqual(img_item.mime_type, "image/png")
        self.assertEqual(img_item.get_dimensions(), "320x240")
        self.assertGreater(img_item.created_time, 0)
        self.assertGreater(img_item.access_time, 0)
        self.assertTrue(img_item.permissions_str.startswith("-"))

        hidden_item = by_name[".secreto.txt"]
        self.assertTrue(hidden_item.is_hidden)
        self.assertEqual(hidden_item.get_dimensions(), "-")
        self.assertEqual(hidden_item.mime_type, "text/plain")

    def test_preview_table_dynamic_columns_and_arrow_visibility(self):
        mock_page = MagicMock(spec=ft.Page)
        table = PreviewTable(
            on_item_inspected=lambda _: None,
            on_selection_toggled=lambda: None,
            page=mock_page,
            config_manager=self.config_manager,
        )

        sample_file = self.base_path / "documento.pdf"
        sample_file.write_bytes(b"PDF-1.4 dummy")
        items = scan_directory(self.base_path)
        table.set_items(items)

        # Default 5 columns + checkbox + arrow ('->') = 7 controls in header and row
        self.assertEqual(len(table.header_controls_row.controls), 7)
        first_row = table.list_view.controls[0]
        self.assertEqual(len(first_row.content.controls), 7)

        # Hide 'new_name' -> arrow should also disappear
        table.update_visible_columns(["original_name", "size", "mime_type"])
        # Checkbox + 3 columns = 4 controls (no arrow)
        self.assertEqual(len(table.header_controls_row.controls), 4)
        first_row_updated = table.list_view.controls[0]
        self.assertEqual(len(first_row_updated.content.controls), 4)

        # Enable all 18 columns -> Checkbox + 18 columns + 1 arrow = 20 controls
        all_col_ids = [c["id"] for c in COLUMN_DEFINITIONS]
        table.update_visible_columns(all_col_ids)
        self.assertEqual(len(table.header_controls_row.controls), 20)
        first_row_all = table.list_view.controls[0]
        self.assertEqual(len(first_row_all.content.controls), 20)
        self.assertGreater(table.header_row.width, 1500)

    def test_column_selector_dialog_and_settings_dialog_integration(self):
        mock_page = MagicMock(spec=ft.Page)
        table = PreviewTable(
            on_item_inspected=lambda _: None,
            on_selection_toggled=lambda: None,
            page=mock_page,
            config_manager=self.config_manager,
        )

        table.open_column_selector_dialog()
        self.assertTrue(mock_page.show_dialog.called)

        settings_dlg = SettingsDialog(
            page=mock_page,
            config_manager=self.config_manager,
            on_saved=lambda: None,
        )
        self.assertEqual(len(settings_dlg.column_checkboxes), 18)


if __name__ == "__main__":
    unittest.main()
