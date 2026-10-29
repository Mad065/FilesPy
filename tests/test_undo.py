import tempfile
import unittest
from pathlib import Path
from core.models import FileItem, FileStatus
from core.undo import UndoManager


class TestUndo(unittest.TestCase):
    def test_apply_and_rollback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            f1 = tmppath / "nota.txt"
            f1.write_text("Hola mundo")

            item = FileItem(
                original_path=f1,
                original_name="nota.txt",
                extension=".txt",
                size_bytes=f1.stat().st_size,
                modified_time=0.0,
                new_name="nota_renombrada.txt",
                target_folder=tmppath / "Documentos",
                selected=True,
                status=FileStatus.READY,
            )

            manager = UndoManager()
            self.assertFalse(manager.can_undo())

            # Apply batch
            count, errors = manager.apply_batch([item])
            self.assertEqual(count, 1)
            self.assertEqual(errors, [])
            self.assertTrue(manager.can_undo())

            # Verify file exists at new location and old location is gone
            new_file = tmppath / "Documentos" / "nota_renombrada.txt"
            self.assertTrue(new_file.exists())
            self.assertFalse(f1.exists())

            # Test Undo
            restored, undo_errors = manager.undo_last()
            self.assertEqual(restored, 1)
            self.assertEqual(undo_errors, [])
            self.assertFalse(manager.can_undo())

            # Verify file restored to original path
            self.assertTrue(f1.exists())
            self.assertFalse(new_file.exists())


if __name__ == "__main__":
    unittest.main()
