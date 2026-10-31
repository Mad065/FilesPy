"""Data models for FilesPy file organization and batch renaming."""
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Tuple, Optional


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
    mode: str = "none"  # "none", "by_extension", "by_category", "by_date", "manual"
    date_format: str = "%Y/%m"  # e.g., 2026/10
    custom_category_map: dict = field(default_factory=dict)
    no_extension_folder: str = "SIN_EXTENSION"
    unorganized_folder: str = "Otros"
    manual_folders: list = field(default_factory=list)
    auto_advance_on_folder_select: bool = True
    auto_rename_on_step: bool = False


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
