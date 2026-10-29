import tempfile
import unittest
from pathlib import Path
from core.models import FileItem
from core.duplicates import find_duplicates


class TestDuplicates(unittest.TestCase):
    def test_duplicate_detection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            f1 = tmppath / "original.txt"
            f2 = tmppath / "copia.txt"
            f3 = tmppath / "distinto.txt"

            f1.write_text("Contenido identico 12345")
            f2.write_text("Contenido identico 12345")
            f3.write_text("Otro texto diferente...")

            items = [
                FileItem(
                    original_path=f1, original_name=f1.name, extension=".txt",
                    size_bytes=f1.stat().st_size, modified_time=0.0,
                    new_name=f1.name, target_folder=tmppath
                ),
                FileItem(
                    original_path=f2, original_name=f2.name, extension=".txt",
                    size_bytes=f2.stat().st_size, modified_time=0.0,
                    new_name=f2.name, target_folder=tmppath
                ),
                FileItem(
                    original_path=f3, original_name=f3.name, extension=".txt",
                    size_bytes=f3.stat().st_size, modified_time=0.0,
                    new_name=f3.name, target_folder=tmppath
                ),
            ]

            dups = find_duplicates(items)
            self.assertEqual(len(dups), 1)
            first_group = list(dups.values())[0]
            self.assertEqual(len(first_group), 2)
            names = {it.original_name for it in first_group}
            self.assertEqual(names, {"original.txt", "copia.txt"})


if __name__ == "__main__":
    unittest.main()
