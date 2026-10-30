"""Unit tests for Step-by-Step Review mode (StepAction, UndoManager, collision resolution)."""
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.config_manager import ConfigManager, DEFAULT_SETTINGS
from core.models import FileItem, FileStatus, StepAction
from core.undo import UndoManager, _resolve_trash_collision


class TestStepReview(unittest.TestCase):
    """Test cases for file review actions and reversible batch processing."""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="filespy_test_step_"))
        self.trash_dir = self.test_dir / "_Papelera"
        self.undo_mgr = UndoManager()

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_file(self, rel_path: str, content: str = "test content") -> Path:
        p = self.test_dir / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return p

    def _create_item(
        self,
        file_path: Path,
        new_name: str,
        target_folder: Path,
        status: FileStatus = FileStatus.READY,
    ) -> FileItem:
        return FileItem(
            original_path=file_path,
            original_name=file_path.name,
            extension=file_path.suffix.lower(),
            size_bytes=file_path.stat().st_size if file_path.exists() else 0,
            modified_time=file_path.stat().st_mtime if file_path.exists() else 0.0,
            new_name=new_name,
            target_folder=target_folder,
            selected=True,
            status=status,
            status_message="",
        )

    def test_step_action_enum(self):
        self.assertEqual(StepAction.APPLY.value, "APPLY")
        self.assertEqual(StepAction.KEEP.value, "KEEP")
        self.assertEqual(StepAction.DISCARD.value, "DISCARD")

    def test_apply_reviewed_batch_apply_and_keep(self):
        f1 = self._create_file("doc1.txt", "doc 1")
        f2 = self._create_file("doc2.txt", "doc 2")

        target_dir = self.test_dir / "Organizados"
        item1 = self._create_item(f1, "renamed_doc1.txt", target_dir)
        item2 = self._create_item(f2, "renamed_doc2.txt", target_dir)

        # item1 -> APPLY, item2 -> KEEP
        reviewed = [
            (item1, StepAction.APPLY),
            (item2, StepAction.KEEP),
        ]

        modified, discarded, errors = self.undo_mgr.apply_reviewed_batch(reviewed, self.trash_dir)

        self.assertEqual(errors, [])
        self.assertEqual(modified, 1)
        self.assertEqual(discarded, 0)

        # item1 should be moved and renamed
        expected_dest1 = target_dir / "renamed_doc1.txt"
        self.assertTrue(expected_dest1.exists())
        self.assertFalse(f1.exists())

        # item2 should stay unchanged
        self.assertTrue(f2.exists())
        self.assertFalse((target_dir / "renamed_doc2.txt").exists())

    def test_apply_reviewed_batch_discard_to_trash(self):
        f1 = self._create_file("unwanted.log", "log data")
        item1 = self._create_item(f1, "unwanted.log", self.test_dir)

        reviewed = [(item1, StepAction.DISCARD)]
        modified, discarded, errors = self.undo_mgr.apply_reviewed_batch(reviewed, self.trash_dir)

        self.assertEqual(errors, [])
        self.assertEqual(modified, 0)
        self.assertEqual(discarded, 1)

        self.assertFalse(f1.exists())
        self.assertTrue((self.trash_dir / "unwanted.log").exists())

    def test_trash_collision_resolution(self):
        self.trash_dir.mkdir(parents=True, exist_ok=True)
        (self.trash_dir / "item.txt").write_text("existing", encoding="utf-8")

        resolved_1 = _resolve_trash_collision(self.trash_dir, "item.txt")
        self.assertEqual(resolved_1.name, "item_1.txt")

        # Simulate item_1 also existing
        resolved_1.write_text("existing 1", encoding="utf-8")
        resolved_2 = _resolve_trash_collision(self.trash_dir, "item.txt")
        self.assertEqual(resolved_2.name, "item_2.txt")

    def test_step_review_undo_restores_both_modified_and_discarded(self):
        f_mod = self._create_file("to_rename.txt", "rename me")
        f_disc = self._create_file("to_delete.txt", "delete me")
        f_keep = self._create_file("to_keep.txt", "keep me")

        target_dir = self.test_dir / "Subfolder"
        item_mod = self._create_item(f_mod, "renamed.txt", target_dir)
        item_disc = self._create_item(f_disc, "to_delete.txt", self.test_dir)
        item_keep = self._create_item(f_keep, "ignored.txt", target_dir)

        reviewed = [
            (item_mod, StepAction.APPLY),
            (item_disc, StepAction.DISCARD),
            (item_keep, StepAction.KEEP),
        ]

        modified, discarded, errors = self.undo_mgr.apply_reviewed_batch(reviewed, self.trash_dir)
        self.assertEqual(modified, 1)
        self.assertEqual(discarded, 1)
        self.assertEqual(errors, [])

        self.assertTrue((target_dir / "renamed.txt").exists())
        self.assertTrue((self.trash_dir / "to_delete.txt").exists())
        self.assertTrue(f_keep.exists())

        # Perform Undo
        restored, undo_errors = self.undo_mgr.undo_last()
        self.assertEqual(undo_errors, [])
        self.assertEqual(restored, 2)

        # All files must be back at original paths
        self.assertTrue(f_mod.exists())
        self.assertTrue(f_disc.exists())
        self.assertTrue(f_keep.exists())
        self.assertFalse((target_dir / "renamed.txt").exists())
        self.assertFalse((self.trash_dir / "to_delete.txt").exists())

    def test_apply_reviewed_batch_rollback_on_error(self):
        f1 = self._create_file("file1.txt", "content 1")
        f2 = self._create_file("file2.txt", "content 2")

        item1 = self._create_item(f1, "renamed1.txt", self.test_dir / "Out")
        item2 = self._create_item(f2, "renamed2.txt", self.test_dir / "Out")

        reviewed = [
            (item1, StepAction.APPLY),
            (item2, StepAction.APPLY),
        ]

        # Patch shutil.move to fail on the second move
        real_move = shutil.move
        call_count = 0

        def failing_move(src, dst):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise PermissionError("Simulated write error")
            return real_move(src, dst)

        with patch("shutil.move", side_effect=failing_move):
            mod, disc, errors = self.undo_mgr.apply_reviewed_batch(reviewed, self.trash_dir)

        self.assertEqual(mod, 0)
        self.assertEqual(disc, 0)
        self.assertTrue(len(errors) > 0)
        # Verify rollback restored file1
        self.assertTrue(f1.exists())
        self.assertTrue(f2.exists())

    def test_config_manager_trash_folder(self):
        cfg = ConfigManager(self.test_dir / "settings.json")
        self.assertEqual(cfg.trash_folder, "_Papelera")
        self.assertIn("_Papelera", cfg.get_ignored_set())


class TestStepReviewDialogLogic(unittest.TestCase):
    """Test dialog navigation, action tracking, and mass decision operations."""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="filespy_test_dialog_"))
        self.trash_dir = self.test_dir / "_Papelera"

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_item(self, name: str, new_name: str, modified: bool = True) -> FileItem:
        p = self.test_dir / name
        p.write_text("dummy", encoding="utf-8")
        target_folder = self.test_dir if not modified else (self.test_dir / "Sub")
        target_name = name if not modified else new_name
        return FileItem(
            original_path=p,
            original_name=name,
            extension=p.suffix.lower(),
            size_bytes=p.stat().st_size,
            modified_time=p.stat().st_mtime,
            new_name=target_name,
            target_folder=target_folder,
            selected=True,
            status=FileStatus.READY if modified else FileStatus.UNCHANGED,
            status_message="",
        )

    def test_dialog_decision_workflow(self):
        from ui.components.step_review_dialog import StepReviewDialog

        item0 = self._create_item("file0.txt", "new0.txt", modified=True)
        item1 = self._create_item("file1.txt", "file1.txt", modified=False)
        item2 = self._create_item("file2.txt", "new2.txt", modified=True)

        items = [item0, item1, item2]
        mock_page = unittest.mock.MagicMock()
        finished_results = []

        dialog = StepReviewDialog(
            page=mock_page,
            items=items,
            trash_folder=self.trash_dir,
            on_finished=lambda res: finished_results.extend(res),
        )

        # Initial default decisions
        self.assertEqual(dialog.decisions[0], StepAction.APPLY)
        self.assertEqual(dialog.decisions[1], StepAction.KEEP)
        self.assertEqual(dialog.decisions[2], StepAction.APPLY)
        self.assertEqual(dialog.current_idx, 0)

        # File 0: User decides to DISCARD -> advances to idx 1
        dialog._set_decision_and_advance(StepAction.DISCARD)
        self.assertEqual(dialog.decisions[0], StepAction.DISCARD)
        self.assertEqual(dialog.current_idx, 1)

        # File 1: User decides to KEEP -> advances to idx 2
        dialog._set_decision_and_advance(StepAction.KEEP)
        self.assertEqual(dialog.decisions[1], StepAction.KEEP)
        self.assertEqual(dialog.current_idx, 2)

        # Navigation: back to 1
        dialog._on_prev()
        self.assertEqual(dialog.current_idx, 1)

        # Navigation: forward to 2
        dialog._on_next()
        self.assertEqual(dialog.current_idx, 2)

        # File 2: User decides to KEEP_REMAINING
        dialog._keep_remaining()
        self.assertEqual(dialog.decisions[2], StepAction.KEEP)

        # Check final decisions
        self.assertEqual(dialog.decisions[0], StepAction.DISCARD)
        self.assertEqual(dialog.decisions[1], StepAction.KEEP)
        self.assertEqual(dialog.decisions[2], StepAction.KEEP)


if __name__ == "__main__":
    unittest.main()
