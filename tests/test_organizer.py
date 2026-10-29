import unittest
from pathlib import Path
from core.models import FileItem, OrganizeConfig
from core.organizer import apply_organization_rules, get_category_for_extension


class TestOrganizer(unittest.TestCase):
    def setUp(self):
        self.base = Path("/tmp/files_test").resolve()
        self.item_pdf = FileItem(
            original_path=self.base / "documento.pdf",
            original_name="documento.pdf",
            extension=".pdf",
            size_bytes=1000,
            modified_time=1761800000.0,
            new_name="documento.pdf",
            target_folder=self.base,
        )
        self.item_jpg = FileItem(
            original_path=self.base / "foto.jpg",
            original_name="foto.jpg",
            extension=".jpg",
            size_bytes=2000,
            modified_time=1761800000.0,
            new_name="foto.jpg",
            target_folder=self.base,
        )

    def test_organize_by_extension(self):
        config = OrganizeConfig(mode="by_extension")
        items = apply_organization_rules([self.item_pdf, self.item_jpg], self.base, config)
        self.assertEqual(items[0].target_folder, self.base / "PDF")
        self.assertEqual(items[1].target_folder, self.base / "JPG")

    def test_organize_by_category(self):
        config = OrganizeConfig(mode="by_category")
        items = apply_organization_rules([self.item_pdf, self.item_jpg], self.base, config)
        self.assertEqual(items[0].target_folder, self.base / "Documentos")
        self.assertEqual(items[1].target_folder, self.base / "Imágenes")

    def test_category_lookup(self):
        self.assertEqual(get_category_for_extension(".py"), "Código")
        self.assertEqual(get_category_for_extension(".mp3"), "Audio")
        self.assertEqual(get_category_for_extension(".zip"), "Comprimidos")
        self.assertEqual(get_category_for_extension(".xyz"), "Otros")


if __name__ == "__main__":
    unittest.main()
