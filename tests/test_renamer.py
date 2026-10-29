import unittest
from pathlib import Path
from core.models import FileItem, RenameConfig
from core.renamer import apply_rename_rules, transform_case


class TestRenamer(unittest.TestCase):
    def setUp(self):
        self.item1 = FileItem(
            original_path=Path("/tmp/test/vacaciones_verano.jpg"),
            original_name="vacaciones_verano.jpg",
            extension=".jpg",
            size_bytes=1024,
            modified_time=1000.0,
            new_name="vacaciones_verano.jpg",
            target_folder=Path("/tmp/test"),
        )
        self.item2 = FileItem(
            original_path=Path("/tmp/test/reporte_anual_2025.pdf"),
            original_name="reporte_anual_2025.pdf",
            extension=".pdf",
            size_bytes=2048,
            modified_time=2000.0,
            new_name="reporte_anual_2025.pdf",
            target_folder=Path("/tmp/test"),
        )

    def test_text_replacement_case_insensitive(self):
        config = RenameConfig(find_text="VERANO", replace_text="invierno", match_case=False)
        items = apply_rename_rules([self.item1], config)
        self.assertEqual(items[0].new_name, "vacaciones_invierno.jpg")

    def test_text_replacement_case_sensitive(self):
        config = RenameConfig(find_text="verano", replace_text="invierno", match_case=True)
        items = apply_rename_rules([self.item1], config)
        self.assertEqual(items[0].new_name, "vacaciones_invierno.jpg")

        # Should not replace when case differs and match_case=True
        config_mismatch = RenameConfig(find_text="VERANO", replace_text="invierno", match_case=True)
        items = apply_rename_rules([self.item1], config_mismatch)
        self.assertEqual(items[0].new_name, "vacaciones_verano.jpg")

    def test_prefix_and_suffix(self):
        config = RenameConfig(prefix="2026_", suffix="_v2")
        items = apply_rename_rules([self.item1], config)
        self.assertEqual(items[0].new_name, "2026_vacaciones_verano_v2.jpg")

    def test_numbering_sequence(self):
        config = RenameConfig(numbering_enabled=True, numbering_start=1, numbering_digits=3)
        items = apply_rename_rules([self.item1, self.item2], config)
        self.assertEqual(items[0].new_name, "vacaciones_verano_001.jpg")
        self.assertEqual(items[1].new_name, "reporte_anual_2025_002.pdf")

    def test_case_transformations(self):
        config_upper = RenameConfig(case_mode="upper")
        items = apply_rename_rules([self.item1], config_upper)
        self.assertEqual(items[0].new_name, "VACACIONES_VERANO.jpg")

        config_title = RenameConfig(case_mode="title")
        items = apply_rename_rules([self.item1], config_title)
        self.assertEqual(items[0].new_name, "Vacaciones_Verano.jpg")

    def test_custom_extension(self):
        config = RenameConfig(custom_extension="png")
        items = apply_rename_rules([self.item1], config)
        self.assertEqual(items[0].new_name, "vacaciones_verano.png")


if __name__ == "__main__":
    unittest.main()
