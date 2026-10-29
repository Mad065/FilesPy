"""Conflict and collision detection for batch file renaming and organization."""
import re
from collections import defaultdict
from pathlib import Path
from typing import List
from core.models import FileItem, FileStatus

INVALID_CHARS_PATTERN = re.compile(r'[\x00/\\:\*\?"<>\|]')


def validate_conflicts(items: List[FileItem]) -> List[FileItem]:
    """Validates the target paths of all items and updates their status.
    
    Detects:
    - Invalid characters in filenames
    - Collision among items in the batch targeting the same path
    - Pre-existing files at target paths on disk
    """
    target_counts = defaultdict(list)

    # First pass: identify basic validity and group by resolved target path
    for item in items:
        if not item.selected:
            item.status = FileStatus.UNCHANGED
            item.status_message = "No seleccionado"
            continue

        # Check for empty name
        if not item.new_name.strip():
            item.status = FileStatus.ERROR
            item.status_message = "El nombre no puede estar vacío"
            continue

        # Check for invalid characters in the filename itself
        if INVALID_CHARS_PATTERN.search(item.new_name):
            item.status = FileStatus.ERROR
            item.status_message = "El nombre contiene caracteres inválidos (/ \\ : * ? \" < > |)"
            continue

        resolved_target = (item.target_folder / item.new_name).resolve()
        target_counts[resolved_target].append(item)

    # Second pass: check collisions within the batch and on disk
    for resolved_target, group in target_counts.items():
        if len(group) > 1:
            # Batch collision: multiple items end up with the exact same path
            for it in group:
                it.status = FileStatus.CONFLICT_NAME
                it.status_message = f"Conflicto: {len(group)} archivos tendrían este mismo nombre"
        else:
            item = group[0]
            # Check if target already exists on disk and is a different file
            if resolved_target.exists() and resolved_target != item.original_path.resolve():
                item.status = FileStatus.CONFLICT_EXISTS
                item.status_message = "Conflicto: ya existe un archivo con este nombre en destino"
            elif item.is_modified:
                item.status = FileStatus.READY
                item.status_message = "Listo para aplicar"
            else:
                item.status = FileStatus.UNCHANGED
                item.status_message = "Sin cambios"

    return items
