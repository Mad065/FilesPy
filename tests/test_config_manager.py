import tempfile
import unittest
from pathlib import Path

from core.config_manager import ConfigManager, normalize_extension, DEFAULT_CATEGORIES
from core.models import FileItem, OrganizeConfig
from core.organizer import apply_organization_rules
from core.scanner import scan_directory


class TestConfigManager(unittest.TestCase):
    def test_normalize_extension(self):
        self.assertEqual(normalize_extension("pdf"), ".pdf")
        self.assertEqual(normalize_extension(".PDF"), ".pdf")
        self.assertEqual(normalize_extension("  .png  "), ".png")
        self.assertEqual(normalize_extension(""), "")

    def test_defaults_created_on_missing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg_path = Path(tmpdir) / "sub" / "settings.json"
            manager = ConfigManager(cfg_path)
            self.assertTrue(cfg_path.exists())
            self.assertIn("Documentos", manager.settings["categories"])
            self.assertEqual(manager.no_extension_folder, "SIN_EXTENSION")
            self.assertEqual(manager.unorganized_folder, "Otros")

    def test_save_and_load_custom_categories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg_path = Path(tmpdir) / "settings.json"
            manager = ConfigManager(cfg_path)

            custom_categories = {
                "Modelado 3D": [".blend", ".obj", ".fbx"],
                "Documentos": [".pdf", ".docx", ".mobi"],
            }
            new_settings = dict(manager.settings)
            new_settings["categories"] = custom_categories
            manager.save_settings(new_settings)

            # Reload
            manager2 = ConfigManager(cfg_path)
            cat_dict = manager2.get_categories_dict()
            self.assertIn("Modelado 3D", cat_dict)
            self.assertIn(".blend", cat_dict["Modelado 3D"])
            self.assertIn(".mobi", cat_dict["Documentos"])

    def test_reset_to_defaults(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg_path = Path(tmpdir) / "settings.json"
            manager = ConfigManager(cfg_path)
            new_settings = dict(manager.settings)
            new_settings["no_extension_folder"] = "CUSTOM_NO_EXT"
            manager.save_settings(new_settings)
            self.assertEqual(manager.no_extension_folder, "CUSTOM_NO_EXT")

            manager.reset_to_defaults()
            self.assertEqual(manager.no_extension_folder, "SIN_EXTENSION")

    def test_integration_with_organizer(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir).resolve()
            item = FileItem(
                original_path=base / "modelo.blend",
                original_name="modelo.blend",
                extension=".blend",
                size_bytes=500,
                modified_time=0.0,
                new_name="modelo.blend",
                target_folder=base,
            )

            # With custom categories
            custom_map = {"3D": {".blend", ".fbx"}}
            config = OrganizeConfig(mode="by_category", custom_category_map=custom_map)
            items = apply_organization_rules([item], base, config)
            self.assertEqual(items[0].target_folder, base / "3D")

    def test_integration_with_scanner_ignored(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir).resolve()
            (base / "normal.txt").write_text("ok")
            (base / "ignorar.tmp").write_text("omitir")

            scanned = scan_directory(base, ignored_names={"ignorar.tmp"})
            names = [f.original_name for f in scanned]
            self.assertIn("normal.txt", names)
            self.assertNotIn("ignorar.tmp", names)


if __name__ == "__main__":
    unittest.main()
