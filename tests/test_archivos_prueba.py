"""Integration test suite executing all workflows against archivos_prueba."""
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from core.models import FileItem, OrganizeConfig, RenameConfig, StepAction
from core.scanner import scan_directory
from core.renamer import apply_rename_rules
from core.organizer import apply_organization_rules
from core.duplicates import find_duplicates
from core.conflicts import validate_conflicts
from core.undo import UndoManager
from core.config_manager import ConfigManager
from ui.app import FilesPyApp
from ui.components.step_review_dialog import StepReviewDialog


class TestArchivosPruebaIntegration(unittest.TestCase):
    """End-to-end test cases verifying all app features with the real archivos_prueba files."""

    @classmethod
    def setUpClass(cls):
        cls.project_root = Path(__file__).resolve().parent.parent
        cls.archivos_prueba_src = cls.project_root / "archivos_prueba"
        if not cls.archivos_prueba_src.exists():
            raise unittest.SkipTest(f"{cls.archivos_prueba_src} does not exist.")

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.temp_prueba = (Path(self.tmp_dir.name) / "archivos_prueba").resolve()
        shutil.copytree(self.archivos_prueba_src, self.temp_prueba)

        self.mock_page = MagicMock()
        self.mock_page.overlay = []
        self.app = FilesPyApp(self.mock_page)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_01_organize_category_and_undo(self):
        dir_org = self.temp_prueba / "01_para_organizar"
        self.app.folder_bar.set_folder(dir_org)

        # 1. Ignored files filter
        scanned_names = {it.original_name for it in self.app.raw_scanned_items}
        self.assertNotIn(".DS_Store", scanned_names)
        self.assertNotIn("Thumbs.db", scanned_names)
        self.assertEqual(len(self.app.raw_scanned_items), 24)

        # 2. Categorization
        self.app._on_organize_rules_changed(OrganizeConfig(mode="by_category"))
        categories_found = {it.target_folder.name for it in self.app.processed_items}
        expected_cats = {"Documentos", "Imagenes", "Audio", "Video", "Comprimidos", "Codigo", "Otros", "SIN_EXTENSION"}
        self.assertEqual(categories_found, expected_cats)

        # 3. Apply and Undo
        items_to_apply = [it for it in self.app.processed_items if it.selected and it.is_modified and not it.has_conflict]
        original_paths = [it.original_path for it in items_to_apply]
        self.app._execute_apply(items_to_apply)

        for cat in expected_cats:
            cat_path = dir_org / cat
            self.assertTrue(cat_path.is_dir())
            self.assertTrue(any(cat_path.iterdir()))

        restored, errors = self.app.undo_manager.undo_last()
        self.assertEqual(errors, [])
        self.assertEqual(restored, len(items_to_apply))
        for orig in original_paths:
            self.assertTrue(orig.exists())

    def test_02_rename_sequential_and_transforms(self):
        dir_ren = self.temp_prueba / "02_para_renombrar"
        self.app.folder_bar.set_folder(dir_ren)
        self.assertEqual(len(self.app.raw_scanned_items), 11)

        # Sequential numbering
        seq_cfg = RenameConfig(
            prefix="Foto_",
            suffix="_final",
            numbering_enabled=True,
            numbering_start=1,
            numbering_digits=3,
        )
        self.app._on_rename_rules_changed(seq_cfg)
        for idx, it in enumerate(self.app.processed_items, start=1):
            self.assertTrue(it.new_name.startswith("Foto_"))
            self.assertIn(f"_{idx:03d}", it.new_name)
            self.assertIn("_final", it.new_name)

        # Snake case transform
        snake_cfg = RenameConfig(case_mode="snake")
        self.app._on_rename_rules_changed(snake_cfg)
        for it in self.app.processed_items:
            stem = Path(it.new_name).stem
            self.assertNotIn(" ", stem)

        # Regex search & replace
        regex_cfg = RenameConfig(find_text=r"-+", replace_text="-", use_regex=True)
        self.app._on_rename_rules_changed(regex_cfg)
        for it in self.app.processed_items:
            self.assertNotIn("--", it.new_name)

    def test_03_duplicate_detection_and_isolation(self):
        dir_dup = self.temp_prueba / "03_para_duplicados"
        self.app.folder_bar.set_folder(dir_dup)

        self.app.duplicate_panel._scan_duplicates(None)
        dup_groups = self.app.duplicate_panel.duplicate_groups
        self.assertEqual(len(dup_groups), 3)

        self.app.duplicate_panel._isolate()
        dup_folder = dir_dup / self.app.config_manager.duplicates_folder
        isolated = [it for it in self.app.processed_items if it.target_folder == dup_folder]
        self.assertEqual(len(isolated), 5)

        items_to_apply = [it for it in self.app.processed_items if it.selected and it.is_modified and not it.has_conflict]
        original_paths = [it.original_path for it in items_to_apply]
        self.app._execute_apply(items_to_apply)
        self.assertTrue(dup_folder.is_dir())
        self.assertEqual(len(list(dup_folder.iterdir())), 5)

        restored, errors = self.app.undo_manager.undo_last()
        self.assertEqual(errors, [])
        self.assertEqual(restored, 5)
        for orig in original_paths:
            self.assertTrue(orig.exists())

    def test_04_organize_by_date(self):
        dir_dates = self.temp_prueba / "04_por_fechas"
        self.app.folder_bar.set_folder(dir_dates)

        self.app._on_organize_rules_changed(OrganizeConfig(mode="by_date", date_format="%Y/%m"))
        date_folders = {it.target_folder.relative_to(dir_dates).as_posix() for it in self.app.processed_items}
        expected_years = {"2023", "2024", "2025", "2026"}
        for y in expected_years:
            self.assertTrue(any(df.startswith(y) for df in date_folders))

    def test_05_step_review_dialog_workflow(self):
        dir_org = self.temp_prueba / "01_para_organizar"
        self.app.folder_bar.set_folder(dir_org)
        self.app._on_organize_rules_changed(OrganizeConfig(mode="by_category"))

        trash_dir = dir_org / self.app.config_manager.trash_folder
        dialog = StepReviewDialog(
            page=self.mock_page,
            items=self.app.processed_items,
            trash_folder=trash_dir,
            on_finished=self.app._on_step_review_finished,
        )

        dialog.current_idx = 0
        dialog._set_decision_and_advance(StepAction.APPLY)
        dialog._set_decision_and_advance(StepAction.KEEP)
        dialog._set_decision_and_advance(StepAction.DISCARD)

        item_apply = self.app.processed_items[0]
        item_keep = self.app.processed_items[1]
        item_discard = self.app.processed_items[2]

        orig_apply = item_apply.original_path
        dest_apply = item_apply.target_folder / item_apply.new_name
        orig_keep = item_keep.original_path
        orig_discard = item_discard.original_path

        reviewed = [(it, dialog.decisions[i]) for i, it in enumerate(self.app.processed_items)]
        mod_count, disc_count, errs = self.app.undo_manager.apply_reviewed_batch(reviewed, trash_dir)
        self.assertEqual(errs, [])
        self.assertEqual(disc_count, 1)

        self.assertTrue(dest_apply.exists())
        self.assertTrue(orig_keep.exists())
        self.assertFalse(orig_discard.exists())
        self.assertTrue((trash_dir / orig_discard.name).exists())

        # Test Undo of step review
        restored, undo_errs = self.app.undo_manager.undo_last()
        self.assertEqual(undo_errs, [])
        self.assertEqual(restored, mod_count + disc_count)
        self.assertTrue(orig_apply.exists())
        self.assertTrue(orig_keep.exists())
        self.assertTrue(orig_discard.exists())

    def test_06_manual_organize_workflow(self):
        from ui.components.manual_organize_dialog import ManualOrganizeDialog

        dir_org = self.temp_prueba / "01_para_organizar"
        self.app.folder_bar.set_folder(dir_org)

        trash_dir = dir_org / self.app.config_manager.trash_folder
        dialog = ManualOrganizeDialog(
            page=self.mock_page,
            items=self.app.processed_items,
            base_dir=dir_org,
            manual_folders=["Facturas_2026", "Fotos_Familia"],
            rename_config=self.app.rename_config,
            trash_folder=trash_dir,
            on_finished=self.app._on_manual_organize_finished,
            on_folders_updated=self.app._on_manual_folders_changed,
            auto_advance=True,
        )

        # File 0: set manual name and select Facturas_2026
        dialog.txt_filename.value = "manual_renamed_0.pdf"
        dialog._on_name_input_changed(None)
        dialog._on_folder_selected("Facturas_2026")

        # File 1: auto-name and select Fotos_Familia
        dialog._apply_auto_name()
        dialog._on_folder_selected("Fotos_Familia")

        # File 2: keep unchanged (skip)
        dialog._skip_current_file()

        item0 = self.app.processed_items[0]
        item1 = self.app.processed_items[1]
        item2 = self.app.processed_items[2]

        orig0 = item0.original_path
        orig1 = item1.original_path
        orig2 = item2.original_path

        dest0 = (dir_org / "Facturas_2026" / "manual_renamed_0.pdf").resolve()
        dest1 = (dir_org / "Fotos_Familia" / dialog.new_names[1]).resolve()

        reviewed = [
            (self.app.processed_items[i], dialog.decisions[i])
            for i in range(len(self.app.processed_items))
        ]
        self.app.processed_items[0].target_folder = dialog.target_folders[0]
        self.app.processed_items[0].new_name = dialog.new_names[0]
        self.app.processed_items[1].target_folder = dialog.target_folders[1]
        self.app.processed_items[1].new_name = dialog.new_names[1]

        mod, disc, errs = self.app.undo_manager.apply_reviewed_batch(reviewed, trash_dir)
        self.assertEqual(errs, [])
        self.assertEqual(mod, 2)

        self.assertTrue(dest0.exists())
        self.assertTrue(dest1.exists())
        self.assertTrue(orig2.exists())

        # Test Undo
        restored, undo_errs = self.app.undo_manager.undo_last()
        self.assertEqual(undo_errs, [])
        self.assertEqual(restored, 2)
        self.assertTrue(orig0.exists())
        self.assertTrue(orig1.exists())
        self.assertTrue(orig2.exists())


if __name__ == "__main__":
    unittest.main()
