"""Directory scanner to discover and build FileItem records."""
from pathlib import Path
from typing import List, Optional, Set
from core.models import FileItem, FileStatus

IGNORE_NAMES = {
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",
    ".git",
    ".gitignore",
    "node_modules",
    "__pycache__",
    ".venv",
}


def scan_directory(
    directory: Path,
    recursive: bool = False,
    include_hidden: bool = False,
    extension_filter: Optional[str] = None,
    ignored_names: Optional[Set[str]] = None,
) -> List[FileItem]:
    """Scans the given directory and returns a list of FileItem objects.
    
    Args:
        directory: Directory Path to scan.
        recursive: Whether to scan subdirectories.
        include_hidden: Whether to include hidden files (starting with .).
        extension_filter: Optional extension filter (e.g., '.png' or 'png').
        ignored_names: Optional set of filenames to ignore.
    """
    directory = Path(directory).resolve()
    if not directory.exists() or not directory.is_dir():
        return []

    active_ignored = ignored_names if ignored_names is not None else IGNORE_NAMES
    results: List[FileItem] = []
    
    iterator = directory.rglob("*") if recursive else directory.glob("*")

    target_ext = extension_filter.strip().lower() if extension_filter else None
    if target_ext and not target_ext.startswith("."):
        target_ext = f".{target_ext}"

    for path in sorted(iterator):
        if not path.is_file():
            continue
        
        # Check hidden and ignored
        if path.name in active_ignored:
            continue
        if not include_hidden and path.name.startswith("."):
            continue

        ext = path.suffix.lower()
        if target_ext and ext != target_ext:
            continue

        try:
            stat = path.stat()
            size = stat.st_size
            mtime = stat.st_mtime
        except OSError:
            size = 0
            mtime = 0.0

        item = FileItem(
            original_path=path,
            original_name=path.name,
            extension=ext,
            size_bytes=size,
            modified_time=mtime,
            new_name=path.name,
            target_folder=path.parent,
            selected=True,
            status=FileStatus.UNCHANGED,
            status_message="",
        )
        results.append(item)

    return results
