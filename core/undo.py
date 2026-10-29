"""Transaction manager and undo/rollback system for safe file operations."""
import json
import shutil
import time
import uuid
from pathlib import Path
from typing import List, Optional, Tuple
from core.models import FileItem, FileStatus, OperationRecord, Transaction


class UndoManager:
    """Manages transactions and undo/rollback functionality."""

    def __init__(self, log_dir: Optional[Path] = None):
        self.history: List[Transaction] = []
        self.log_dir = log_dir

    def can_undo(self) -> bool:
        """Returns True if there is a transaction that can be undone."""
        return len(self.history) > 0

    def apply_batch(self, items: List[FileItem]) -> Tuple[int, List[str]]:
        """Applies rename and move operations for all valid and selected items.
        
        Returns:
            Tuple of (number of successful operations, list of error messages).
        """
        items_to_process = [
            item for item in items
            if item.selected and item.is_modified and not item.has_conflict
        ]

        if not items_to_process:
            return 0, ["No hay archivos válidos seleccionados para modificar."]

        tx_id = str(uuid.uuid4())
        tx = Transaction(id=tx_id, timestamp=time.time())
        applied_ops: List[OperationRecord] = []
        errors: List[str] = []

        try:
            for item in items_to_process:
                source = item.original_path.resolve()
                dest = (item.target_folder / item.new_name).resolve()

                if source == dest:
                    continue

                # Ensure destination directory exists
                dest.parent.mkdir(parents=True, exist_ok=True)

                # Move/Rename file safely
                shutil.move(str(source), str(dest))
                op = OperationRecord(source_path=source, destination_path=dest)
                applied_ops.append(op)

                # Update item in-memory to reflect new state
                item.original_path = dest
                item.original_name = dest.name
                item.extension = dest.suffix.lower()
                item.new_name = dest.name
                item.target_folder = dest.parent
                item.status = FileStatus.UNCHANGED
                item.status_message = "Completado con éxito"

            tx.operations = applied_ops
            self.history.append(tx)
            return len(applied_ops), []

        except Exception as ex:
            errors.append(f"Error durante la operación: {str(ex)}. Ejecutando rollback...")
            # Rollback any already executed operations in this transaction
            for op in reversed(applied_ops):
                try:
                    if op.destination_path.exists():
                        op.source_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(op.destination_path), str(op.source_path))
                except Exception as rollback_err:
                    errors.append(f"Error crítico en rollback: {rollback_err}")
            return 0, errors

    def undo_last(self) -> Tuple[int, List[str]]:
        """Rolls back the most recent transaction.
        
        Returns:
            Tuple of (number of restored files, list of error messages).
        """
        if not self.history:
            return 0, ["No hay transacciones previas para deshacer."]

        tx = self.history.pop()
        restored = 0
        errors: List[str] = []

        # Reverse operations order to avoid overwriting or missing folders
        for op in reversed(tx.operations):
            try:
                dest = op.destination_path
                orig = op.source_path

                if dest.exists():
                    orig.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(dest), str(orig))
                    restored += 1
                else:
                    errors.append(f"No se encontró el archivo a revertir: {dest.name}")
            except Exception as ex:
                errors.append(f"Error al revertir {op.destination_path.name}: {str(ex)}")

        return restored, errors
