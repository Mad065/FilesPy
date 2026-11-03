"""Unit tests for Folder Automation and Monitoring Engine and UI."""
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock

import flet as ft

from core.automation import AutomationManager, apply_rule_rename, parse_extension_filter
from core.config_manager import ConfigManager
from core.models import (
    FileItem,
    FolderMonitorStatus,
    MonitoredFolderRule,
    StepAction,
)
from core.undo import UndoManager
from ui.components.automation_dialog import AutomationMonitorDialog, FolderRuleEditorDialog


class TestAutomationEngine(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name).resolve()
        self.config_file = self.base_path / "test_settings.json"
        self.config_manager = ConfigManager(config_file=self.config_file)
        self.undo_manager = UndoManager()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_persistence_of_monitored_folders(self):
        watch_dir = self.base_path / "Watched1"
        watch_dir.mkdir()

        rule = MonitoredFolderRule(
            id="rule-1",
            path=str(watch_dir),
            name="Carpeta Vigilada",
            enabled=True,
            auto_apply=False,
            organize_mode="custom_subfolder",
            custom_subfolder="Guardados",
            rename_enabled=True,
            rename_prefix="AUTO_",
            rename_case_mode="snake",
        )
        self.config_manager.save_monitored_folders([rule])

        reloaded_cm = ConfigManager(config_file=self.config_file)
        loaded_rules = reloaded_cm.get_monitored_folders()
        self.assertEqual(len(loaded_rules), 1)
        self.assertEqual(loaded_rules[0].id, "rule-1")
        self.assertEqual(loaded_rules[0].name, "Carpeta Vigilada")
        self.assertEqual(loaded_rules[0].organize_mode, "custom_subfolder")
        self.assertEqual(loaded_rules[0].custom_subfolder, "Guardados")
        self.assertTrue(loaded_rules[0].rename_enabled)
        self.assertEqual(loaded_rules[0].rename_prefix, "AUTO_")
        self.assertEqual(loaded_rules[0].rename_case_mode, "snake")

    def test_on_demand_status_and_execution(self):
        watch_dir = self.base_path / "Descargas"
        watch_dir.mkdir()

        mgr = AutomationManager(self.config_manager, self.undo_manager)
        rule = MonitoredFolderRule(
            id="r-ondemand",
            path=str(watch_dir),
            name="Descargas",
            enabled=True,
            auto_apply=False,  # Solo cuando el usuario lo diga
            organize_mode="by_category",
            rename_enabled=True,
            rename_case_mode="snake",
        )
        mgr.add_or_update_rule(rule)

        # Initially empty -> ORDERED
        self.assertEqual(rule.status, FolderMonitorStatus.ORDERED)
        self.assertEqual(rule.pending_count, 0)

        # Add 2 files
        f1 = watch_dir / "Mi Reporte Final.pdf"
        f2 = watch_dir / "Foto Vacaciones.jpg"
        f1.write_text("pdf content")
        f2.write_text("jpg content")

        mgr.refresh_all_statuses(trigger_auto=True)
        # Because auto_apply=False, files are NOT moved yet and status is PENDING
        self.assertEqual(rule.status, FolderMonitorStatus.PENDING)
        self.assertEqual(rule.pending_count, 2)
        self.assertTrue(f1.exists())
        self.assertTrue(f2.exists())

        # Now user clicks "Ordenar Ahora"
        count, errors = mgr.execute_rule_now(rule.id, is_automatic=False)
        self.assertEqual(errors, [])
        self.assertEqual(count, 2)
        self.assertEqual(rule.status, FolderMonitorStatus.ORDERED)
        self.assertEqual(rule.pending_count, 0)

        # Check files were moved to category subfolders and renamed to snake_case
        self.assertTrue((watch_dir / "Documentos" / "mi_reporte_final.pdf").exists())
        self.assertTrue((watch_dir / "Imagenes" / "foto_vacaciones.jpg").exists())

    def test_automatic_execution_and_custom_subfolder(self):
        watch_dir = self.base_path / "BandejaEntrada"
        watch_dir.mkdir()

        mgr = AutomationManager(self.config_manager, self.undo_manager)
        rule = MonitoredFolderRule(
            id="r-auto",
            path=str(watch_dir),
            name="Bandeja",
            enabled=True,
            auto_apply=True,
            organize_mode="custom_subfolder",
            custom_subfolder="Recibidos",
            rename_enabled=True,
            rename_prefix="OK_",
        )
        mgr.add_or_update_rule(rule)

        # Create a file with mtime > 1s ago so stability check passes immediately
        f1 = watch_dir / "factura.pdf"
        f1.write_text("data")
        past_time = time.time() - 5.0
        os.utime(f1, (past_time, past_time))

        # Trigger automatic status check
        mgr.refresh_all_statuses(trigger_auto=True)

        # Should have automatically moved to Recibidos/OK_factura.pdf and be ORDERED
        self.assertEqual(rule.status, FolderMonitorStatus.ORDERED)
        self.assertEqual(rule.pending_count, 0)
        self.assertTrue((watch_dir / "Recibidos" / "OK_factura.pdf").exists())
        self.assertFalse(f1.exists())
        self.assertEqual(len(mgr.events), 1)

    def test_idempotent_rename_in_same_folder(self):
        watch_dir = self.base_path / "SoloRenombrar"
        watch_dir.mkdir()

        mgr = AutomationManager(self.config_manager, self.undo_manager)
        rule = MonitoredFolderRule(
            id="r-rename-only",
            path=str(watch_dir),
            enabled=True,
            auto_apply=False,
            organize_mode="none",
            rename_enabled=True,
            rename_prefix="DOC_",
            rename_suffix="_v1",
            rename_case_mode="snake",
        )
        mgr.add_or_update_rule(rule)

        f1 = watch_dir / "Nota Rapida.txt"
        f1.write_text("hola")

        mgr.evaluate_rule_status(rule, trigger_auto=False)
        self.assertEqual(rule.status, FolderMonitorStatus.PENDING)
        self.assertEqual(rule.pending_count, 1)

        count, errors = mgr.execute_rule_now(rule.id)
        self.assertEqual(count, 1)
        self.assertEqual(errors, [])
        renamed_file = watch_dir / "DOC_nota_rapida_v1.txt"
        self.assertTrue(renamed_file.exists())

        # Re-evaluating should detect 0 pending items (idempotent!)
        mgr.evaluate_rule_status(rule, trigger_auto=False)
        self.assertEqual(rule.status, FolderMonitorStatus.ORDERED)
        self.assertEqual(rule.pending_count, 0)

    def test_manual_mode_status_and_completion(self):
        watch_dir = self.base_path / "ManualFolder"
        watch_dir.mkdir()

        mgr = AutomationManager(self.config_manager, self.undo_manager)
        rule = MonitoredFolderRule(
            id="r-manual",
            path=str(watch_dir),
            enabled=True,
            organize_mode="manual",
            manual_folders=["Facturas", "Personal"],
        )
        mgr.add_or_update_rule(rule)

        f1 = watch_dir / "recibo.pdf"
        f2 = watch_dir / "quedarse.txt"
        f1.write_text("1")
        f2.write_text("2")

        mgr.evaluate_rule_status(rule, trigger_auto=True)
        # Manual mode never auto-moves without user click; status is PENDING
        self.assertEqual(rule.status, FolderMonitorStatus.PENDING)
        self.assertEqual(rule.pending_count, 2)

        # Simulate user finishing ManualOrganizeDialog: moving f1 to Facturas and keeping f2
        pending = mgr.get_pending_items_for_rule(rule)
        item_f1 = next(it for it in pending if it.original_name == "recibo.pdf")
        item_f2 = next(it for it in pending if it.original_name == "quedarse.txt")
        item_f1.target_folder = watch_dir / "Facturas"

        mod, disc, errs = self.undo_manager.apply_reviewed_batch(
            [(item_f1, StepAction.APPLY), (item_f2, StepAction.KEEP)],
            trash_folder=watch_dir / "_Papelera",
        )
        self.assertEqual(mod, 1)
        self.assertEqual(errs, [])

        mgr.mark_manual_run_completed(
            rule.id, modified_count=mod, discarded_count=disc, kept_paths=[f2]
        )
        self.assertEqual(rule.status, FolderMonitorStatus.ORDERED)
        self.assertEqual(rule.pending_count, 0)

    def test_ui_dialogs_build_cleanly(self):
        page_mock = MagicMock(spec=ft.Page)
        picker_mock = ft.FilePicker()
        mgr = AutomationManager(self.config_manager, self.undo_manager)

        watch_dir = self.base_path / "UIFolder"
        watch_dir.mkdir()
        rule = MonitoredFolderRule(id="ui-1", path=str(watch_dir), organize_mode="manual")
        mgr.add_or_update_rule(rule)

        dialog = AutomationMonitorDialog(
            page=page_mock,
            automation_manager=mgr,
            file_picker=picker_mock,
            on_open_manual_for_rule=lambda r: None,
            on_load_folder_in_main=lambda p: None,
            on_undo_requested=lambda: None,
            current_folder=watch_dir,
        )
        dialog.show()
        self.assertTrue(page_mock.show_dialog.called)

        editor = FolderRuleEditorDialog(
            page=page_mock,
            file_picker=picker_mock,
            on_save=lambda r: None,
            existing_rule=rule,
        )
        editor.show()
        self.assertEqual(page_mock.show_dialog.call_count, 2)

    def test_filespy_app_automation_integration(self):
        from ui.app import FilesPyApp

        page_mock = MagicMock(spec=ft.Page)
        page_mock.services = []
        page_mock.overlay = []
        app = FilesPyApp(page_mock)
        try:
            app._open_automation_dialog()
            self.assertIsNotNone(app.active_automation_dialog)
            self.assertTrue(page_mock.show_dialog.called)
        finally:
            app.automation_manager.stop_background_monitor()


if __name__ == "__main__":
    unittest.main()
