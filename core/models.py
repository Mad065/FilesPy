"""Data models for FilesPy file organization and batch renaming."""
from dataclasses import dataclass, field
from enum import Enum
import mimetypes
from pathlib import Path
import stat as stat_module
from typing import List, Tuple, Optional


IMAGE_METADATA_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff", ".ico"}


class FileStatus(str, Enum):
    UNCHANGED = "UNCHANGED"
    READY = "READY"
    CONFLICT_NAME = "CONFLICT_NAME"
    CONFLICT_EXISTS = "CONFLICT_EXISTS"
    ERROR = "ERROR"


class StepAction(str, Enum):
    APPLY = "APPLY"       # Aplicar reglas de renombrado / organizacion
    KEEP = "KEEP"         # Conservar archivo original sin modificaciones
    DISCARD = "DISCARD"   # Mover archivo a carpeta de descarte/papelera


class FolderMonitorStatus(str, Enum):
    ORDERED = "ORDERED"           # Ya está ordenado (0 pendientes)
    IN_PROGRESS = "IN_PROGRESS"   # En proceso actualmente
    PENDING = "PENDING"           # Aún no ordenado (archivos pendientes)
    ERROR = "ERROR"               # Error o carpeta inexistente


@dataclass
class FileItem:
    """Represents a file being inspected or prepared for renaming/organizing."""
    original_path: Path
    original_name: str
    extension: str
    size_bytes: int
    modified_time: float
    new_name: str
    target_folder: Path
    selected: bool = True
    status: FileStatus = FileStatus.UNCHANGED
    status_message: str = ""
    created_time: float = 0.0
    access_time: float = 0.0
    permissions_mode: int = 0
    _cached_dimensions: Optional[str] = field(default=None, repr=False, compare=False)

    @property
    def target_path(self) -> Path:
        """Full destination path including new name."""
        return self.target_folder / self.new_name

    @property
    def is_modified(self) -> bool:
        """Returns True if the file will change name or folder."""
        return self.target_path.resolve() != self.original_path.resolve()

    @property
    def has_conflict(self) -> bool:
        """Returns True if this item has an unresolved conflict or error."""
        return self.status in (
            FileStatus.CONFLICT_NAME,
            FileStatus.CONFLICT_EXISTS,
            FileStatus.ERROR,
        )

    @property
    def stem(self) -> str:
        """Filename without extension."""
        return self.original_path.stem

    @property
    def original_folder(self) -> str:
        """Parent folder name of the original path."""
        return self.original_path.parent.name or "/"

    @property
    def original_full_path(self) -> str:
        """Full original file path string."""
        return str(self.original_path)

    @property
    def target_full_path(self) -> str:
        """Full destination file path string."""
        return str(self.target_path)

    @property
    def is_hidden(self) -> bool:
        """Returns True if the file is hidden (starts with '.')."""
        return self.original_name.startswith(".")

    @property
    def mime_type(self) -> str:
        """Returns the guessed MIME type for the file."""
        guessed, _ = mimetypes.guess_type(self.original_name)
        return guessed or "application/octet-stream"

    @property
    def permissions_str(self) -> str:
        """Returns Unix-style permission string (e.g. '-rw-r--r--')."""
        mode = self.permissions_mode
        if not mode:
            try:
                mode = self.original_path.stat().st_mode
                self.permissions_mode = mode
            except OSError:
                return "-"
        try:
            return stat_module.filemode(mode)
        except Exception:
            return "-"

    def get_dimensions(self) -> str:
        """Returns lazily cached pixel dimensions (WxH) for image files, or '-'."""
        if self._cached_dimensions is not None:
            return self._cached_dimensions
        if self.extension.lower() not in IMAGE_METADATA_EXTENSIONS:
            self._cached_dimensions = "-"
            return "-"
        try:
            from PIL import Image
            with Image.open(self.original_path) as img:
                w, h = img.size
                self._cached_dimensions = f"{w}x{h}"
        except Exception:
            self._cached_dimensions = "-"
        return self._cached_dimensions


@dataclass
class RenameConfig:
    """Configuration for batch renaming."""
    find_text: str = ""
    replace_text: str = ""
    match_case: bool = False
    use_regex: bool = False
    prefix: str = ""
    suffix: str = ""
    numbering_enabled: bool = False
    numbering_start: int = 1
    numbering_digits: int = 3
    case_mode: str = "original"  # "original", "lower", "upper", "title", "snake", "kebab"
    preserve_extension: bool = True
    custom_extension: str = ""


@dataclass
class OrganizeConfig:
    """Configuration for file sorting/organization into folders."""
    mode: str = "none"  # "none", "by_extension", "by_category", "by_date", "custom_subfolder", "manual"
    date_format: str = "%Y/%m"  # e.g., 2026/10
    custom_subfolder: str = ""
    custom_category_map: dict = field(default_factory=dict)
    no_extension_folder: str = "SIN_EXTENSION"
    unorganized_folder: str = "Otros"
    manual_folders: list = field(default_factory=list)
    auto_advance_on_folder_select: bool = True
    auto_rename_on_step: bool = False


@dataclass
class MonitoredFolderRule:
    """Configuration and runtime state for a monitored folder in Automation & Monitor."""
    id: str
    path: str
    name: str = ""
    enabled: bool = True
    auto_apply: bool = True  # True: automático en segundo plano; False: bajo demanda cuando el usuario lo diga
    organize_mode: str = "by_category"  # "by_category", "by_extension", "by_date", "custom_subfolder", "manual", "none"
    custom_subfolder: str = ""
    extension_filter: str = ""  # Ej. ".pdf, .jpg" o vacío para todos
    rename_enabled: bool = False
    rename_prefix: str = ""
    rename_suffix: str = ""
    rename_date_prefix: bool = False
    rename_find: str = ""
    rename_replace: str = ""
    rename_case_mode: str = "original"  # "original", "lower", "upper", "title", "snake", "kebab"
    manual_folders: List[str] = field(
        default_factory=lambda: ["Documentos", "Imágenes", "Facturas", "Trabajo", "Personal"]
    )
    # Runtime status fields (not required in settings.json persistence)
    status: FolderMonitorStatus = FolderMonitorStatus.ORDERED
    pending_count: int = 0
    last_run_timestamp: float = 0.0
    last_message: str = "Sin actividad reciente"
    processed_total: int = 0

    @property
    def display_name(self) -> str:
        if self.name and self.name.strip():
            return self.name.strip()
        p = Path(self.path)
        return p.name or self.path

    def to_dict(self) -> dict:
        """Serializes persistent rule configuration to a dictionary."""
        return {
            "id": self.id,
            "path": self.path,
            "name": self.name,
            "enabled": self.enabled,
            "auto_apply": self.auto_apply,
            "organize_mode": self.organize_mode,
            "custom_subfolder": self.custom_subfolder,
            "extension_filter": self.extension_filter,
            "rename_enabled": self.rename_enabled,
            "rename_prefix": self.rename_prefix,
            "rename_suffix": self.rename_suffix,
            "rename_date_prefix": self.rename_date_prefix,
            "rename_find": self.rename_find,
            "rename_replace": self.rename_replace,
            "rename_case_mode": self.rename_case_mode,
            "manual_folders": list(self.manual_folders),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MonitoredFolderRule":
        """Deserializes a dictionary into a MonitoredFolderRule instance."""
        import uuid
        return cls(
            id=str(data.get("id") or uuid.uuid4()),
            path=str(data.get("path", "")),
            name=str(data.get("name", "")),
            enabled=bool(data.get("enabled", True)),
            auto_apply=bool(data.get("auto_apply", True)),
            organize_mode=str(data.get("organize_mode", "by_category")),
            custom_subfolder=str(data.get("custom_subfolder", "")),
            extension_filter=str(data.get("extension_filter", "")),
            rename_enabled=bool(data.get("rename_enabled", False)),
            rename_prefix=str(data.get("rename_prefix", "")),
            rename_suffix=str(data.get("rename_suffix", "")),
            rename_date_prefix=bool(data.get("rename_date_prefix", False)),
            rename_find=str(data.get("rename_find", "")),
            rename_replace=str(data.get("rename_replace", "")),
            rename_case_mode=str(data.get("rename_case_mode", "original")),
            manual_folders=list(
                data.get("manual_folders")
                or ["Documentos", "Imágenes", "Facturas", "Trabajo", "Personal"]
            ),
        )


@dataclass
class AutomationEvent:
    """Log entry for an automatic or on-demand folder action."""
    timestamp: float
    folder_name: str
    folder_path: str
    action_summary: str
    files_count: int = 0
    is_error: bool = False


@dataclass
class AppSettings:
    """User-configurable settings persisted to disk."""
    categories: dict = field(default_factory=dict)
    ignored_patterns: list = field(default_factory=list)
    no_extension_folder: str = "SIN_EXTENSION"
    unorganized_folder: str = "Otros"
    duplicates_folder: str = "_Duplicados"
    trash_folder: str = "_Papelera"
    manual_folders: list = field(default_factory=lambda: ["Documentos", "Imágenes", "Facturas", "Trabajo", "Personal"])
    confirm_before_apply: bool = True
    max_text_preview_size_kb: int = 512
    visible_columns: list = field(
        default_factory=lambda: ["original_name", "new_name", "target_folder", "size", "status"]
    )


@dataclass
class OperationRecord:
    """A single atomic file move/rename operation."""
    source_path: Path
    destination_path: Path


@dataclass
class Transaction:
    """A batch of applied file operations that can be rolled back."""
    id: str
    timestamp: float
    operations: List[OperationRecord] = field(default_factory=list)
