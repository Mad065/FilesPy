"""Unit tests for the Apple macOS Finder-style Batch Renaming engine and UI components."""
from datetime import datetime
from pathlib import Path
import unittest
from unittest.mock import MagicMock

import flet as ft

from core.models import FileItem, RenameConfig
from core.renamer import (
    apply_rename_rules,
    generate_example_name,
    generate_single_auto_name,
    has_active_rename_rules,
)
from ui.components.batch_rename_dialog import BatchRenameDialog
from ui.components.rename_panel import RenamePanel


def _make_item(name: str, mtime: float = 1671658230.0, selected: bool = True) -> FileItem:
    p = Path("/tmp/test_folder") / name
    return FileItem(
        original_path=p,
        original_name=name,
        extension=p.suffix.lower(),
        size_bytes=1024,
        modified_time=mtime,
        new_name=name,
        target_folder=p.parent,
        selected=selected,
    )


class TestMacBatchRenamer(unittest.TestCase):
    def test_replace_text_mode(self):
        items = [
            _make_item("Captura de pantalla 2022-12-21.png"),
            _make_item("Captura de pantalla 2022-12-22.png"),
        ]
        cfg = RenameConfig(
            mode="replace",
            find_text="Captura de pantalla",
            replace_text="Foto",
        )
        updated = apply_rename_rules(items, cfg)
        self.assertEqual(updated[0].new_name, "Foto 2022-12-21.png")
        self.assertEqual(updated[1].new_name, "Foto 2022-12-22.png")

    def test_replace_text_empty_find_keeps_original(self):
        items = [_make_item("Documento Final.pdf")]
        cfg = RenameConfig(mode="replace", find_text="", replace_text="Nuevo")
        updated = apply_rename_rules(items, cfg)
        self.assertEqual(updated[0].new_name, "Documento Final.pdf")

    def test_add_text_after_and_before(self):
        items_after = [_make_item("Reporte.xlsx"), _make_item("Balance.xlsx")]
        cfg_after = RenameConfig(
            mode="add_text",
            add_text=" (Final)",
            add_location="after",
        )
        apply_rename_rules(items_after, cfg_after)
        self.assertEqual(items_after[0].new_name, "Reporte (Final).xlsx")
        self.assertEqual(items_after[1].new_name, "Balance (Final).xlsx")

        items_before = [_make_item("Reporte.xlsx")]
        cfg_before = RenameConfig(
            mode="add_text",
            add_text="2026_",
            add_location="before",
        )
        apply_rename_rules(items_before, cfg_before)
        self.assertEqual(items_before[0].new_name, "2026_Reporte.xlsx")

    def test_format_name_and_counter(self):
        items = [
            _make_item("img_a.png"),
            _make_item("img_b.png"),
            _make_item("img_c.jpg"),
        ]
        # After name ("Después del nombre") starting at 1 -> Archivo 00001.png
        cfg = RenameConfig(
            mode="format",
            format_style="name_counter",
            format_location="after",
            custom_format="Archivo",
            counter_start=1,
        )
        apply_rename_rules(items, cfg)
        self.assertEqual(items[0].new_name, "Archivo 00001.png")
        self.assertEqual(items[1].new_name, "Archivo 00002.png")
        self.assertEqual(items[2].new_name, "Archivo 00003.jpg")

        # Before name ("Antes del nombre") starting at 10 -> 00010 Archivo.png
        cfg_before = RenameConfig(
            mode="format",
            format_style="name_counter",
            format_location="before",
            custom_format="Archivo",
            counter_start=10,
        )
        apply_rename_rules(items, cfg_before)
        self.assertEqual(items[0].new_name, "00010 Archivo.png")
        self.assertEqual(items[1].new_name, "00011 Archivo.png")

    def test_format_name_and_index(self):
        items = [_make_item("doc1.pdf"), _make_item("doc2.pdf")]
        cfg = RenameConfig(
            mode="format",
            format_style="name_index",
            format_location="after",
            custom_format="Capítulo",
            counter_start=1,
        )
        apply_rename_rules(items, cfg)
        self.assertEqual(items[0].new_name, "Capítulo 1.pdf")
        self.assertEqual(items[1].new_name, "Capítulo 2.pdf")

        cfg_before = RenameConfig(
            mode="format",
            format_style="name_index",
            format_location="before",
            custom_format="Capítulo",
            counter_start=5,
        )
        apply_rename_rules(items, cfg_before)
        self.assertEqual(items[0].new_name, "5 Capítulo.pdf")
        self.assertEqual(items[1].new_name, "6 Capítulo.pdf")

    def test_format_name_and_date(self):
        # Fixed timestamp
        dt = datetime(2023, 5, 14, 10, 20, 45)
        ts = dt.timestamp()
        items = [_make_item("foto.png", mtime=ts)]

        cfg = RenameConfig(
            mode="format",
            format_style="name_date",
            format_location="after",
            custom_format="Vacaciones",
        )
        apply_rename_rules(items, cfg)
        self.assertEqual(items[0].new_name, "Vacaciones 2023-05-14 a las 10.20.45.png")

        cfg_before = RenameConfig(
            mode="format",
            format_style="name_date",
            format_location="before",
            custom_format="Vacaciones",
        )
        apply_rename_rules(items, cfg_before)
        self.assertEqual(items[0].new_name, "2023-05-14 a las 10.20.45 Vacaciones.png")

    def test_unselected_items_are_skipped_in_sequence(self):
        items = [
            _make_item("a.png", selected=True),
            _make_item("b.png", selected=False),
            _make_item("c.png", selected=True),
        ]
        cfg = RenameConfig(
            mode="format",
            format_style="name_counter",
            format_location="after",
            custom_format="Archivo",
            counter_start=1,
        )
        apply_rename_rules(items, cfg)
        self.assertEqual(items[0].new_name, "Archivo 00001.png")
        self.assertEqual(items[1].new_name, "b.png")
        self.assertEqual(items[2].new_name, "Archivo 00002.png")

    def test_generate_example_name(self):
        cfg_format = RenameConfig(
            mode="format",
            format_style="name_counter",
            format_location="after",
            custom_format="Archivo",
            counter_start=1,
        )
        example = generate_example_name(cfg_format, sample_name="foto.png")
        self.assertEqual(example, "Archivo 00001.png")

        cfg_replace = RenameConfig(
            mode="replace",
            find_text="2022",
            replace_text="2026",
        )
        example_rep = generate_example_name(
            cfg_replace,
            sample_name="Captura de pantalla 2022-12-21 a las 15.3.png",
        )
        self.assertEqual(example_rep, "Captura de pantalla 2026-12-21 a las 15.3.png")

    def test_rename_panel_and_batch_rename_dialog(self):
        changed_configs = []
        panel = RenamePanel(on_change=lambda c: changed_configs.append(c))

        # Switch panel to format mode
        panel.set_config(
            RenameConfig(
                mode="format",
                format_style="name_counter",
                format_location="after",
                custom_format="Archivo",
                counter_start=1,
            )
        )
        cfg = panel.get_config()
        self.assertEqual(cfg.mode, "format")
        self.assertEqual(cfg.custom_format, "Archivo")
        self.assertEqual(panel.lbl_example.value, "Ejemplo: Archivo 00001.png")

        # Test BatchRenameDialog
        mock_page = MagicMock(spec=ft.Page)
        items = [_make_item("demo.png")]
        confirmed = []
        dlg = BatchRenameDialog(
            page=mock_page,
            items=items,
            initial_config=cfg,
            on_rename_confirmed=lambda c: confirmed.append(c),
        )
        self.assertEqual(dlg.lbl_example.value, "Ejemplo: Archivo 00001.png")
        dlg._confirm()
        self.assertEqual(len(confirmed), 1)
        self.assertEqual(confirmed[0].mode, "format")


if __name__ == "__main__":
    unittest.main()
