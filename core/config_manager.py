"""Configuration persistence and manager for FilesPy."""
import json
from pathlib import Path
from typing import Dict, List, Optional, Set

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "settings.json"

DEFAULT_CATEGORIES: Dict[str, List[str]] = {
    "Documentos": [
        ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt",
        ".txt", ".csv", ".rtf", ".odt", ".epub",
    ],
    "Imagenes": [
        ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp",
        ".tiff", ".ico", ".raw", ".heic",
    ],
    "Audio": [
        ".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma",
    ],
    "Video": [
        ".mp4", ".mkv", ".mov", ".avi", ".webm", ".wmv", ".flv",
    ],
    "Comprimidos": [
        ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz",
    ],
    "Codigo": [
        ".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css",
        ".json", ".xml", ".sql", ".sh", ".c", ".cpp", ".java",
        ".rs", ".go", ".php",
    ],
}

DEFAULT_IGNORED: List[str] = [
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",
    ".git",
    ".gitignore",
    "node_modules",
    "__pycache__",
    ".venv",
    "_Papelera",
]

DEFAULT_SETTINGS: dict = {
    "categories": DEFAULT_CATEGORIES,
    "ignored_patterns": DEFAULT_IGNORED,
    "no_extension_folder": "SIN_EXTENSION",
    "unorganized_folder": "Otros",
    "duplicates_folder": "_Duplicados",
    "trash_folder": "_Papelera",
    "confirm_before_apply": True,
    "max_text_preview_size_kb": 512,
}


def normalize_extension(ext: str) -> str:
    """Normalizes an extension string to '.ext' in lowercase."""
    cleaned = ext.strip().lower()
    if not cleaned:
        return ""
    if not cleaned.startswith("."):
        cleaned = f".{cleaned}"
    return cleaned


class ConfigManager:
    """Manages application settings loading, saving, and querying."""

    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = Path(config_file).resolve() if config_file else DEFAULT_CONFIG_PATH
        self.settings: dict = {}
        self.load_settings()

    def load_settings(self) -> dict:
        """Loads settings from JSON file or initializes defaults if not present."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    merged = dict(DEFAULT_SETTINGS)
                    merged.update(data)
                    self.settings = merged
                    return self.settings
            except Exception:
                # If reading fails, fallback to defaults
                self.settings = dict(DEFAULT_SETTINGS)
                return self.settings
        else:
            self.settings = dict(DEFAULT_SETTINGS)
            self.save_settings(self.settings)
            return self.settings

    def save_settings(self, new_settings: dict):
        """Saves settings to JSON file."""
        self.settings = dict(new_settings)
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except OSError:
            pass

    def reset_to_defaults(self):
        """Resets all settings back to original defaults."""
        self.save_settings(DEFAULT_SETTINGS)

    def get_categories_dict(self) -> Dict[str, Set[str]]:
        """Returns categories mapped to sets of extensions."""
        raw_cats = self.settings.get("categories", DEFAULT_CATEGORIES)
        result: Dict[str, Set[str]] = {}
        for cat_name, ext_list in raw_cats.items():
            result[cat_name] = {normalize_extension(e) for e in ext_list if normalize_extension(e)}
        return result

    def get_ignored_set(self) -> Set[str]:
        """Returns set of ignored filenames/patterns."""
        return set(self.settings.get("ignored_patterns", DEFAULT_IGNORED))

    @property
    def no_extension_folder(self) -> str:
        return self.settings.get("no_extension_folder", "SIN_EXTENSION")

    @property
    def unorganized_folder(self) -> str:
        return self.settings.get("unorganized_folder", "Otros")

    @property
    def duplicates_folder(self) -> str:
        return self.settings.get("duplicates_folder", "_Duplicados")

    @property
    def trash_folder(self) -> str:
        return self.settings.get("trash_folder", "_Papelera")

    @property
    def confirm_before_apply(self) -> bool:
        return bool(self.settings.get("confirm_before_apply", True))

    @property
    def max_text_preview_size_kb(self) -> int:
        return int(self.settings.get("max_text_preview_size_kb", 512))
