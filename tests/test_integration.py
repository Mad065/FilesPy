"""Integration test simulating the full workflow of FilesPy."""
import tempfile
import unittest
from pathlib import Path
from PIL import Image

from core.models import RenameConfig, OrganizeConfig
from core.scanner import scan_directory
from core.renamer import apply_rename_rules
from core.organizer import apply_organization_rules
from core.conflicts import validate_conflicts
from core.undo import UndoManager


class TestIntegrationWorkflow(unittest.TestCase):
    def test_full_pipeline_and_undo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir).resolve()

            # Create test files: 2 images, 2 documents, 1 text
            (tmppath / "foto_a.png").write_bytes(b"dummy image data")
            (tmppath / "foto_b.png").write_bytes(b"dummy image data")
            (tmppath / "reporte_enero.pdf").write_bytes(b"dummy pdf data")
            (tmppath / "reporte_febrero.pdf").write_bytes(b"dummy pdf data")
            (tmppath / "notas.txt").write_bytes(b"dummy text data")

            # 1. Scan directory
            scanned = scan_directory(tmppath)
            self.assertEqual(len(scanned), 5)

            # 2. Configure renaming: Prefix 'DOC_', numbering, uppercase
            rename_cfg = RenameConfig(
                prefix="DOC_",
                numbering_enabled=True,
                numbering_start=1,
                numbering_digits=2,
            )
            renamed = apply_rename_rules(scanned, rename_cfg)

            # 3. Configure organization: By extension
            org_cfg = OrganizeConfig(mode="by_extension")
            organized = apply_organization_rules(renamed, tmppath, org_cfg)

            # 4. Validate conflicts
            validated = validate_conflicts(organized)
            for it in validated:
                self.assertFalse(it.has_conflict)
                self.assertTrue(it.is_modified)

            # 5. Apply batch with UndoManager
            manager = UndoManager()
            applied_count, errors = manager.apply_batch(validated)
            self.assertEqual(applied_count, 5)
            self.assertEqual(errors, [])

            # Check files in organized directories
            png_folder = tmppath / "PNG"
            pdf_folder = tmppath / "PDF"
            txt_folder = tmppath / "TXT"

            self.assertTrue(png_folder.is_dir())
            self.assertTrue(pdf_folder.is_dir())
            self.assertTrue(txt_folder.is_dir())

            self.assertTrue((png_folder / "DOC_foto_a_01.png").exists())
            self.assertTrue((tmppath / "TXT" / "DOC_notas_03.txt").exists())
            self.assertTrue((pdf_folder / "DOC_reporte_enero_04.pdf").exists())

            # 6. Undo batch
            self.assertTrue(manager.can_undo())
            restored_count, undo_errors = manager.undo_last()
            self.assertEqual(restored_count, 5)
            self.assertEqual(undo_errors, [])

            # Verify files are back in original folder with original names
            self.assertTrue((tmppath / "foto_a.png").exists())
            self.assertTrue((tmppath / "foto_b.png").exists())
            self.assertTrue((tmppath / "reporte_enero.pdf").exists())
            self.assertTrue((tmppath / "notas.txt").exists())


if __name__ == "__main__":
    unittest.main()
