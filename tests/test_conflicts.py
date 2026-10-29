import unittest
from pathlib import Path
from core.models import FileItem, FileStatus
from core.conflicts import validate_conflicts


class TestConflicts(unittest.TestCase):
    def test_name_collision_in_batch(self):
        folder = Path("/tmp/conflict_test")
        item1 = FileItem(
            original_path=folder / "foto1.jpg",
            original_name="foto1.jpg",
            extension=".jpg",
            size_bytes=100,
            modified_time=0.0,
            new_name="misma_foto.jpg",
            target_folder=folder,
        )
        item2 = FileItem(
            original_path=folder / "foto2.jpg",
            original_name="foto2.jpg",
            extension=".jpg",
            size_bytes=200,
            modified_time=0.0,
            new_name="misma_foto.jpg",
            target_folder=folder,
        )

        items = validate_conflicts([item1, item2])
        self.assertEqual(items[0].status, FileStatus.CONFLICT_NAME)
        self.assertEqual(items[1].status, FileStatus.CONFLICT_NAME)
        self.assertTrue(items[0].has_conflict)

    def test_invalid_characters(self):
        folder = Path("/tmp/conflict_test")
        item = FileItem(
            original_path=folder / "archivo.txt",
            original_name="archivo.txt",
            extension=".txt",
            size_bytes=100,
            modified_time=0.0,
            new_name="invalido*nombre?.txt",
            target_folder=folder,
        )
        items = validate_conflicts([item])
        self.assertEqual(items[0].status, FileStatus.ERROR)
        self.assertTrue(items[0].has_conflict)

    def test_ready_status_when_valid(self):
        folder = Path("/tmp/conflict_test")
        item = FileItem(
            original_path=folder / "antiguo.txt",
            original_name="antiguo.txt",
            extension=".txt",
            size_bytes=100,
            modified_time=0.0,
            new_name="nuevo.txt",
            target_folder=folder,
        )
        items = validate_conflicts([item])
        self.assertEqual(items[0].status, FileStatus.READY)
        self.assertFalse(items[0].has_conflict)


if __name__ == "__main__":
    unittest.main()
