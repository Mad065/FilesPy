"""Configuration persistence and manager for FilesPy."""
import json
from pathlib import Path
from typing import Dict, List, Optional, Set
from core.models import MonitoredFolderRule

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

DEFAULT_MANUAL_FOLDERS: List[str] = [
    "Documentos",
    "Imágenes",
    "Facturas",
    "Trabajo",
    "Personal",
]

COLUMN_DEFINITIONS: List[dict] = [
    {
        "id": "original_name",
        "label": "Nombre Original",
        "description": "Nombre actual del archivo con su extensión",
        "group": "basicas",
        "default_width": 220,
        "default": True,
        "align": "left",
    },
    {
        "id": "new_name",
        "label": "Nuevo Nombre",
        "description": "Nombre tras aplicar reglas de renombrado",
        "group": "basicas",
        "default_width": 220,
        "default": True,
        "align": "left",
    },
    {
        "id": "target_folder",
        "label": "Carpeta Destino",
        "description": "Subcarpeta asignada para organización",
        "group": "basicas",
        "default_width": 150,
        "default": True,
        "align": "left",
    },
    {
        "id": "original_folder",
        "label": "Carpeta Origen",
        "description": "Carpeta inmediata donde reside actualmente",
        "group": "ubicacion",
        "default_width": 140,
        "default": False,
        "align": "left",
    },
    {
        "id": "original_full_path",
        "label": "Ruta Completa Origen",
        "description": "Ruta absoluta original en disco",
        "group": "ubicacion",
        "default_width": 260,
        "default": False,
        "align": "left",
    },
    {
        "id": "target_full_path",
        "label": "Ruta Completa Destino",
        "description": "Ruta absoluta donde quedará el archivo",
        "group": "ubicacion",
        "default_width": 260,
        "default": False,
        "align": "left",
    },
    {
        "id": "stem",
        "label": "Nombre Base",
        "description": "Nombre limpio del archivo sin extensión",
        "group": "ubicacion",
        "default_width": 160,
        "default": False,
        "align": "left",
    },
    {
        "id": "size",
        "label": "Tamaño",
        "description": "Peso del archivo formateado (B, KB, MB, GB)",
        "group": "sistema",
        "default_width": 80,
        "default": True,
        "align": "right",
    },
    {
        "id": "extension",
        "label": "Extensión",
        "description": "Formato o terminación (.pdf, .jpg, etc.)",
        "group": "sistema",
        "default_width": 75,
        "default": False,
        "align": "center",
    },
    {
        "id": "category",
        "label": "Categoría",
        "description": "Grupo configurado (Documentos, Imágenes, etc.)",
        "group": "sistema",
        "default_width": 110,
        "default": False,
        "align": "left",
    },
    {
        "id": "mime_type",
        "label": "Tipo MIME",
        "description": "Tipo MIME oficial (ej. application/pdf)",
        "group": "sistema",
        "default_width": 150,
        "default": False,
        "align": "left",
    },
    {
        "id": "permissions",
        "label": "Permisos",
        "description": "Modo de acceso del archivo (ej. -rw-r--r--)",
        "group": "sistema",
        "default_width": 95,
        "default": False,
        "align": "center",
    },
    {
        "id": "is_hidden",
        "label": "Oculto",
        "description": "Indica si es un archivo oculto (Sí / No)",
        "group": "sistema",
        "default_width": 70,
        "default": False,
        "align": "center",
    },
    {
        "id": "dimensions",
        "label": "Dimensiones",
        "description": "Resolución en píxeles para imágenes (ej. 1920x1080)",
        "group": "multimedia",
        "default_width": 100,
        "default": False,
        "align": "center",
    },
    {
        "id": "modified_time",
        "label": "Modificado",
        "description": "Fecha y hora de última modificación",
        "group": "fechas",
        "default_width": 130,
        "default": False,
        "align": "center",
    },
    {
        "id": "created_time",
        "label": "Creado",
        "description": "Fecha y hora de creación en disco",
        "group": "fechas",
        "default_width": 130,
        "default": False,
        "align": "center",
    },
    {
        "id": "access_time",
        "label": "Último Acceso",
        "description": "Fecha y hora en que fue abierto/leído por última vez",
        "group": "fechas",
        "default_width": 130,
        "default": False,
        "align": "center",
    },
    {
        "id": "status",
        "label": "Estado",
        "description": "Indicador visual (Listo, Conflicto, Sin cambio)",
        "group": "basicas",
        "default_width": 95,
        "default": True,
        "align": "center",
    },
]

DEFAULT_VISIBLE_COLUMNS: List[str] = [
    col["id"] for col in COLUMN_DEFINITIONS if col["default"]
]

DEFAULT_SETTINGS: dict = {
    "categories": DEFAULT_CATEGORIES,
    "ignored_patterns": DEFAULT_IGNORED,
    "no_extension_folder": "SIN_EXTENSION",
    "unorganized_folder": "Otros",
    "duplicates_folder": "_Duplicados",
    "trash_folder": "_Papelera",
    "manual_folders": DEFAULT_MANUAL_FOLDERS,
    "confirm_before_apply": True,
    "max_text_preview_size_kb": 512,
    "monitored_folders": [],
    "automation_active": True,
    "visible_columns": DEFAULT_VISIBLE_COLUMNS,
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

    def get_manual_folders(self) -> List[str]:
        """Returns the list of custom manual organization target folders."""
        folders = self.settings.get("manual_folders", DEFAULT_MANUAL_FOLDERS)
        if not isinstance(folders, list):
            return list(DEFAULT_MANUAL_FOLDERS)
        # Deduplicate while preserving order and stripping whitespace
        seen = set()
        clean_folders = []
        for f in folders:
            f_clean = str(f).strip()
            if f_clean and f_clean not in seen:
                seen.add(f_clean)
                clean_folders.append(f_clean)
        return clean_folders or list(DEFAULT_MANUAL_FOLDERS)

    def save_manual_folders(self, folders: List[str]):
        """Persists custom manual organization target folders to settings."""
        seen = set()
        clean_folders = []
        for f in folders:
            f_clean = str(f).strip()
            if f_clean and f_clean not in seen:
                seen.add(f_clean)
                clean_folders.append(f_clean)
        self.settings["manual_folders"] = clean_folders
        self.save_settings(self.settings)

    @property
    def automation_active(self) -> bool:
        return bool(self.settings.get("automation_active", True))

    def set_automation_active(self, active: bool):
        self.settings["automation_active"] = bool(active)
        self.save_settings(self.settings)

    def get_monitored_folders(self) -> List[MonitoredFolderRule]:
        """Returns the list of configured MonitoredFolderRule objects."""
        raw_list = self.settings.get("monitored_folders", [])
        if not isinstance(raw_list, list):
            return []
        rules: List[MonitoredFolderRule] = []
        for item in raw_list:
            if isinstance(item, dict) and item.get("path"):
                try:
                    rules.append(MonitoredFolderRule.from_dict(item))
                except Exception:
                    continue
        return rules

    def save_monitored_folders(self, rules: List[MonitoredFolderRule]):
        """Persists the list of MonitoredFolderRule objects to settings.json."""
        self.settings["monitored_folders"] = [r.to_dict() for r in rules]
        self.save_settings(self.settings)

    def get_visible_columns(self) -> List[str]:
        """Returns the list of active visible column IDs for the file preview table."""
        raw_cols = self.settings.get("visible_columns", DEFAULT_VISIBLE_COLUMNS)
        if not isinstance(raw_cols, list):
            return list(DEFAULT_VISIBLE_COLUMNS)
        valid_ids = {c["id"] for c in COLUMN_DEFINITIONS}
        seen = set()
        clean_cols: List[str] = []
        for col_id in raw_cols:
            c_str = str(col_id).strip()
            if c_str in valid_ids and c_str not in seen:
                seen.add(c_str)
                clean_cols.append(c_str)
        return clean_cols or list(DEFAULT_VISIBLE_COLUMNS)

    def save_visible_columns(self, columns: List[str]):
        """Persists the user's chosen visible column IDs to settings.json."""
        valid_ids = {c["id"] for c in COLUMN_DEFINITIONS}
        seen = set()
        clean_cols: List[str] = []
        for col_id in columns:
            c_str = str(col_id).strip()
            if c_str in valid_ids and c_str not in seen:
                seen.add(c_str)
                clean_cols.append(c_str)
        self.settings["visible_columns"] = clean_cols or list(DEFAULT_VISIBLE_COLUMNS)
        self.save_settings(self.settings)
