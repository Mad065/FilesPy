"""Organization engine for sorting files into subfolders by extension, category, or date."""
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set
from core.models import FileItem, OrganizeConfig

DEFAULT_CATEGORIES: Dict[str, Set[str]] = {
    "Documentos": {
        ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt",
        ".txt", ".csv", ".rtf", ".odt", ".epub",
    },
    "Imágenes": {
        ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp",
        ".tiff", ".ico", ".raw", ".heic",
    },
    "Audio": {
        ".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma",
    },
    "Video": {
        ".mp4", ".mkv", ".mov", ".avi", ".webm", ".wmv", ".flv",
    },
    "Comprimidos": {
        ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz",
    },
    "Código": {
        ".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css",
        ".json", ".xml", ".sql", ".sh", ".c", ".cpp", ".java",
        ".rs", ".go", ".php",
    },
}


def get_category_for_extension(
    ext: str,
    custom_categories: Dict[str, Set[str]] = None,
    default_category: str = "Otros",
) -> str:
    """Returns the category name for a given file extension."""
    norm_ext = ext.lower().strip()
    categories = custom_categories if custom_categories is not None else DEFAULT_CATEGORIES
    
    for category_name, extensions in categories.items():
        if norm_ext in extensions:
            return category_name
    return default_category


def apply_organization_rules(
    items: List[FileItem],
    base_dir: Path,
    config: OrganizeConfig,
) -> List[FileItem]:
    """Applies folder organization rules to each FileItem in the list."""
    base_dir = Path(base_dir).resolve()

    no_ext_name = getattr(config, "no_extension_folder", "SIN_EXTENSION") or "SIN_EXTENSION"
    unorg_name = getattr(config, "unorganized_folder", "Otros") or "Otros"

    for item in items:
        if not item.selected:
            item.target_folder = item.original_path.parent
            continue

        if config.mode == "by_extension":
            ext = item.extension.lstrip(".").upper()
            folder_name = ext if ext else no_ext_name
            item.target_folder = base_dir / folder_name

        elif config.mode == "by_category":
            if not item.extension.strip():
                category = no_ext_name
            else:
                category = get_category_for_extension(
                    item.extension,
                    config.custom_category_map or None,
                    default_category=unorg_name,
                )
            item.target_folder = base_dir / category

        elif config.mode == "by_date":
            try:
                date_str = datetime.fromtimestamp(item.modified_time).strftime(config.date_format or "%Y/%m")
            except (ValueError, OSError):
                date_str = "Fecha_Desconocida"
            item.target_folder = base_dir / date_str

        elif config.mode == "manual":
            # In manual mode, retain existing target_folder if explicitly set, else parent
            if not getattr(item, "target_folder", None):
                item.target_folder = item.original_path.parent

        else:  # "none"
            item.target_folder = item.original_path.parent

    return items


def assign_manual_target(item: FileItem, folder_name: str, base_dir: Path) -> Path:
    """Assigns item's target_folder to base_dir / folder_name."""
    base = Path(base_dir).resolve()
    clean_name = folder_name.strip().strip("/\\")
    if clean_name:
        target = base / clean_name
    else:
        target = base
    item.target_folder = target
    return target
