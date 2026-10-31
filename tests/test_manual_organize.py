"""Unit and integration tests for Custom Manual Organization and Hybrid Naming."""
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from core.config_manager import ConfigManager
from core.models import FileItem, FileStatus, RenameConfig, StepAction
from core.organizer import assign_manual_target, apply_organization_rules, OrganizeConfig
from core.renamer import clean_to_snake_case, generate_single_auto_name, add_date_prefix
from core.undo import UndoManager
from ui.components.manual_organize_dialog import ManualOrganizeDialog


class TestManualOrganizeCore(unittest.TestCase):
    """Tests for core logic: config, renamer, and organizer helpers."""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="filespy_test_core_"))

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_config_manager_manual_folders(self):
        cfg_file = self.test_dir / "settings.json"
        cfg = ConfigManager(cfg_file)

        # Default manual folders
        folders = cfg.get_manual_folders()
        self.assertIn("Facturas", folders)
        self.assertIn("Documentos", folders)

        # Save customized manual folders
        new_folders = ["  Facturas  ", "Proyectos 2026", "Facturas", "Personal"]
        cfg.save_manual_folders(new_folders)

        loaded = cfg.get_manual_folders()
        self.assertEqual(loaded, ["Facturas", "Proyectos 2026", "Personal"])

    def test_renamer_generate_single_auto_name_default(self):
        p = self.test_dir / "DOCUMENTO IMPORTANTE CON ESPACIOS.PDF"
        p.touch()
        item = FileItem(
            original_path=p,
            original_name=p.name,
            extension=p.suffix.lower(),
            size_bytes=0,
            modified_time=0.0,
            new_name=p.name,
            target_folder=self.test_dir,
        )

        auto_name = generate_single_auto_name(item, config=None)
        self.assertEqual(auto_name, "documento_importante_con_espacios.pdf")

    def test_renamer_generate_single_auto_name_with_rules(self):
        p = self.test_dir / "reporte.txt"
        p.touch()
        item = FileItem(
            original_path=p,
            original_name=p.name,
            extension=".txt",
            size_bytes=0,
            modified_time=0.0,
            new_name=p.name,
            target_folder=self.test_dir,
        )

        cfg = RenameConfig(
            prefix="PRE_",
            suffix="_FINAL",
            case_mode="upper",
            numbering_enabled=True,
            numbering_start=5,
            numbering_digits=3,
        )

        auto_name = generate_single_auto_name(item, config=cfg, index=0)
        self.assertEqual(auto_name, "PRE_REPORTE_FINAL_005.txt")

    def test_renamer_clean_to_snake_case(self):
        res = clean_to_snake_case("Mi Archivo--Con  Guiones (1).docx")
        self.assertTrue(res.endswith(".docx"))
        self.assertNotIn(" ", res)
        self.assertNotIn("--", res)

    def test_organizer_assign_manual_target(self):
        p = self.test_dir / "archivo.txt"
        p.touch()
        item = FileItem(
            original_path=p,
            original_name=p.name,
            extension=".txt",
            size_bytes=0,
            modified_time=0.0,
            new_name=p.name,
            target_folder=self.test_dir,
        )

        target = assign_manual_target(item, "Subcarpeta/Facturas", self.test_dir)
        self.assertEqual(target, (self.test_dir / "Subcarpeta/Facturas").resolve())
        self.assertEqual(item.target_folder, target)

    def test_organize_rules_mode_manual(self):
        p = self.test_dir / "sample.txt"
        p.touch()
        item = FileItem(
            original_path=p,
            original_name=p.name,
            extension=".txt",
            size_bytes=0,
            modified_time=0.0,
            new_name=p.name,
            target_folder=self.test_dir / "CustomFolder",
        )

        cfg = OrganizeConfig(mode="manual")
        items = apply_organization_rules([item], self.test_dir, cfg)
        self.assertEqual(items[0].target_folder, self.test_dir / "CustomFolder")


class TestManualOrganizeExecutionAndRollback(unittest.TestCase):
    """Tests executing manual organization batch and undoing."""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="filespy_test_exec_"))
        self.trash_dir = self.test_dir / "_Papelera"
        self.undo_mgr = UndoManager()

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_apply_manual_batch_and_undo(self):
        f1 = self.test_dir / "factura.pdf"
        f2 = self.test_dir / "foto.png"
        f3 = self.test_dir / "omitido.txt"

        f1.write_text("factura 1", encoding="utf-8")
        f2.write_text("foto 1", encoding="utf-8")
        f3.write_text("omitido 1", encoding="utf-8")

        target_facturas = self.test_dir / "Facturas"
        target_fotos = self.test_dir / "Fotos"

        item1 = FileItem(
            original_path=f1,
            original_name=f1.name,
            extension=f1.suffix.lower(),
            size_bytes=f1.stat().st_size,
            modified_time=f1.stat().st_mtime,
            new_name="factura_enero_2026.pdf",
            target_folder=target_facturas,
            selected=True,
            status=FileStatus.READY,
        )

        item2 = FileItem(
            original_path=f2,
            original_name=f2.name,
            extension=f2.suffix.lower(),
            size_bytes=f2.stat().st_size,
            modified_time=f2.stat().st_mtime,
            new_name="foto.png",
            target_folder=target_fotos,
            selected=True,
            status=FileStatus.READY,
        )

        item3 = FileItem(
            original_path=f3,
            original_name=f3.name,
            extension=f3.suffix.lower(),
            size_bytes=f3.stat().st_size,
            modified_time=f3.stat().st_mtime,
            new_name=f3.name,
            target_folder=self.test_dir,
            selected=True,
            status=FileStatus.UNCHANGED,
        )

        reviewed = [
            (item1, StepAction.APPLY),
            (item2, StepAction.APPLY),
            (item3, StepAction.KEEP),
        ]

        modified, discarded, errors = self.undo_mgr.apply_reviewed_batch(reviewed, self.trash_dir)
        self.assertEqual(modified, 2)
        self.assertEqual(discarded, 0)
        self.assertEqual(len(errors), 0)

        # Verify disk state
        dest1 = target_facturas / "factura_enero_2026.pdf"
        dest2 = target_fotos / "foto.png"

        self.assertFalse(f1.exists())
        self.assertFalse(f2.exists())
        self.assertTrue(dest1.exists())
        self.assertTrue(dest2.exists())
        self.assertTrue(f3.exists())  # Item 3 kept

        # Test Undo
        self.assertTrue(self.undo_mgr.can_undo())
        restored, undo_errors = self.undo_mgr.undo_last()
        self.assertEqual(restored, 2)
        self.assertEqual(len(undo_errors), 0)

        # Verify restored to original paths and names
        self.assertTrue(f1.exists())
        self.assertTrue(f2.exists())
        self.assertFalse(dest1.exists())
        self.assertFalse(dest2.exists())


class TestManualOrganizeDialog(unittest.TestCase):
    """Tests for the interactive ManualOrganizeDialog user flow."""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="filespy_test_dialog_"))
        self.trash_dir = self.test_dir / "_Papelera"

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_item(self, filename: str) -> FileItem:
        p = self.test_dir / filename
        p.write_text("test", encoding="utf-8")
        return FileItem(
            original_path=p,
            original_name=filename,
            extension=p.suffix.lower(),
            size_bytes=p.stat().st_size,
            modified_time=p.stat().st_mtime,
            new_name=filename,
            target_folder=self.test_dir,
            selected=True,
            status=FileStatus.UNCHANGED,
        )

    def test_dialog_user_workflow(self):
        it1 = self._create_item("DOCUMENTO_A.PDF")
        it2 = self._create_item("DOCUMENTO_B.DOCX")
        it3 = self._create_item("DOCUMENTO_C.TXT")
        items = [it1, it2, it3]

        mock_page = MagicMock()
        finished_results = []
        updated_folders = []

        dialog = ManualOrganizeDialog(
            page=mock_page,
            items=items,
            base_dir=self.test_dir,
            manual_folders=["Facturas", "Personal"],
            rename_config=RenameConfig(),
            trash_folder=self.trash_dir,
            on_finished=lambda res: finished_results.extend(res),
            on_folders_updated=lambda f: updated_folders.extend(f),
            auto_advance=True,
        )

        self.assertEqual(dialog.current_idx, 0)

        # 1. File 1: Set custom manual name and pick folder "Facturas"
        dialog.txt_filename.value = "mi_factura_personalizada.pdf"
        dialog._on_name_input_changed(None)
        self.assertEqual(dialog.new_names[0], "mi_factura_personalizada.pdf")

        # Pick folder "Facturas" -> auto-advances to index 1
        dialog._on_folder_selected("Facturas")
        self.assertEqual(dialog.target_folders[0], (self.test_dir / "Facturas").resolve())
        self.assertEqual(dialog.decisions[0], StepAction.APPLY)
        self.assertEqual(dialog.current_idx, 1)

        # 2. File 2: Auto-nombrar and add a new folder on the fly
        dialog._apply_auto_name()
        self.assertEqual(dialog.new_names[1], "documento_b.docx")

        dialog.txt_new_folder.value = "Trabajo_2026"
        dialog._on_add_folder_click()

        self.assertIn("Trabajo_2026", dialog.manual_folders)
        self.assertIn("Trabajo_2026", updated_folders)
        self.assertEqual(dialog.target_folders[1], (self.test_dir / "Trabajo_2026").resolve())
        self.assertEqual(dialog.decisions[1], StepAction.APPLY)
        self.assertEqual(dialog.current_idx, 2)

        # 3. File 3: Skip file
        dialog._skip_current_file()
        self.assertEqual(dialog.decisions[2], StepAction.KEEP)

        # 4. Confirm decisions
        dialog._on_confirm_click()
        # Verify confirm dialog was presented
        self.assertTrue(mock_page.show_dialog.called)


if __name__ == "__main__":
    unittest.main()
