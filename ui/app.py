"""Main Application Window for FilesPy."""
from pathlib import Path
from tkinter import messagebox
from typing import List, Optional
import customtkinter as ctk

from core.conflicts import validate_conflicts
from core.config_manager import ConfigManager
from core.models import FileItem, OrganizeConfig, RenameConfig
from core.organizer import apply_organization_rules
from core.renamer import apply_rename_rules
from core.scanner import scan_directory
from core.undo import UndoManager

from ui.components.action_bar import ActionBar
from ui.components.duplicate_panel import DuplicatePanel
from ui.components.folder_bar import FolderBar
from ui.components.inspector_panel import InspectorPanel
from ui.components.organize_panel import OrganizePanel
from ui.components.preview_table import PreviewTable
from ui.components.rename_panel import RenamePanel
from ui.components.settings_dialog import SettingsDialog


class FilesPyApp(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        # Window Configuration
        self.title("FilesPy - Organizador y Renombrador de Archivos")
        self.geometry("1180x720")
        self.minsize(960, 580)

        # Set appearance to match system
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Business Logic & Config State
        self.config_manager = ConfigManager()
        self.undo_manager = UndoManager()
        self.current_folder: Optional[Path] = None
        self.is_recursive: bool = False
        self.raw_scanned_items: List[FileItem] = []
        self.processed_items: List[FileItem] = []
        self.rename_config = RenameConfig()
        self.organize_config = OrganizeConfig(
            custom_category_map=self.config_manager.get_categories_dict(),
            no_extension_folder=self.config_manager.no_extension_folder,
            unorganized_folder=self.config_manager.unorganized_folder,
        )

        self._build_ui()

    def _build_ui(self):
        # 1. Top Folder Bar
        self.folder_bar = FolderBar(
            self,
            on_folder_selected=self._on_folder_changed,
            on_open_settings=self._open_settings_dialog,
        )
        self.folder_bar.pack(fill="x", padx=10, pady=(10, 5))

        # 2. Main Content Area (Left: Rules, Center: Table, Right: Inspector)
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Left Column: Rules Tabview
        self.tabs = ctk.CTkTabview(self.content_frame, width=280)
        self.tabs.pack(side="left", fill="y", padx=(0, 6), pady=0)

        tab_rename = self.tabs.add("Renombrar")
        tab_organize = self.tabs.add("Organizar")
        tab_duplicates = self.tabs.add("Duplicados")

        self.rename_panel = RenamePanel(
            tab_rename,
            on_change=self._on_rename_rules_changed,
            fg_color="transparent",
        )
        self.rename_panel.pack(fill="both", expand=True)

        self.organize_panel = OrganizePanel(
            tab_organize,
            on_change=self._on_organize_rules_changed,
            fg_color="transparent",
        )
        self.organize_panel.pack(fill="both", expand=True)
        self.organize_panel.update_categories_info(self.config_manager.get_categories_dict())

        self.duplicate_panel = DuplicatePanel(
            tab_duplicates,
            get_current_items=lambda: self.raw_scanned_items,
            on_isolate_duplicates=self._on_isolate_duplicates,
            fg_color="transparent",
        )
        self.duplicate_panel.pack(fill="both", expand=True)

        # Center Column: Preview Table
        self.preview_table = PreviewTable(
            self.content_frame,
            on_item_inspected=self._on_item_inspected,
            on_selection_toggled=self._on_selection_toggled,
            corner_radius=8,
        )
        self.preview_table.pack(side="left", fill="both", expand=True, padx=4)

        # Right Column: Inspector Panel
        self.inspector = InspectorPanel(
            self.content_frame,
            width=260,
            corner_radius=8,
        )
        self.inspector.pack(side="right", fill="y", padx=(6, 0))

        # 3. Bottom Action Bar
        self.action_bar = ActionBar(
            self,
            on_refresh=self._reload_folder,
            on_apply=self._on_apply_changes,
            on_undo=self._on_undo_changes,
        )
        self.action_bar.pack(fill="x", padx=10, pady=(5, 10))

    def _open_settings_dialog(self):
        """Opens the modal settings configuration dialog."""
        SettingsDialog(
            parent=self,
            config_manager=self.config_manager,
            on_saved=self._on_settings_saved,
        )

    def _on_settings_saved(self):
        """Callback when settings are saved to refresh categories and file scanning."""
        self.organize_panel.update_categories_info(self.config_manager.get_categories_dict())
        self._reload_folder()

    def _on_folder_changed(self, folder: Path, recursive: bool):
        self.current_folder = folder
        self.is_recursive = recursive
        self._reload_folder()

    def _reload_folder(self):
        """Scans the current folder and re-runs the transformation pipeline."""
        if not self.current_folder or not self.current_folder.is_dir():
            return

        self.raw_scanned_items = scan_directory(
            self.current_folder,
            recursive=self.is_recursive,
            ignored_names=self.config_manager.get_ignored_set(),
        )
        self._run_pipeline()

    def _run_pipeline(self):
        """Applies active rename, organize, and conflict rules to scanned items."""
        if not self.current_folder:
            return

        # Clone fresh items from raw scan to preserve original states
        items: List[FileItem] = []
        for it in self.raw_scanned_items:
            # Preserve user's manual selection if previously set
            matching_prev = next((p for p in self.processed_items if p.original_path == it.original_path), None)
            is_selected = matching_prev.selected if matching_prev else True

            clone = FileItem(
                original_path=it.original_path,
                original_name=it.original_name,
                extension=it.extension,
                size_bytes=it.size_bytes,
                modified_time=it.modified_time,
                new_name=it.original_name,
                target_folder=it.target_folder,
                selected=is_selected,
                status=it.status,
                status_message=it.status_message,
            )
            items.append(clone)

        # Step 1: Rename rules
        items = apply_rename_rules(items, self.rename_config)

        # Step 2: Organization rules (with dynamic settings)
        self.organize_config.custom_category_map = self.config_manager.get_categories_dict()
        self.organize_config.no_extension_folder = self.config_manager.no_extension_folder
        self.organize_config.unorganized_folder = self.config_manager.unorganized_folder
        items = apply_organization_rules(items, self.current_folder, self.organize_config)

        # Step 3: Conflict detection
        items = validate_conflicts(items)

        self.processed_items = items
        self.preview_table.set_items(self.processed_items)

        # Update counts
        modified_count = sum(1 for it in items if it.selected and it.is_modified and not it.has_conflict)
        conflict_count = sum(1 for it in items if it.selected and it.has_conflict)

        self.folder_bar.update_count(len(items), modified_count)
        self.action_bar.update_state(
            modified_count=modified_count,
            conflict_count=conflict_count,
            can_undo=self.undo_manager.can_undo(),
        )

    def _on_rename_rules_changed(self, config: RenameConfig):
        self.rename_config = config
        self._run_pipeline()

    def _on_organize_rules_changed(self, config: OrganizeConfig):
        self.organize_config = config
        self._run_pipeline()

    def _on_selection_toggled(self):
        """Called when a checkbox in the preview table is clicked."""
        self._run_pipeline()

    def _on_item_inspected(self, item: FileItem):
        self.inspector.inspect_file(item)

    def _on_isolate_duplicates(self, duplicates_to_move: List[FileItem]):
        """Isolates duplicate files by setting their target folder to the configured duplicates folder."""
        if not self.current_folder:
            return

        dup_paths = {d.original_path for d in duplicates_to_move}
        target_dir = self.current_folder / self.config_manager.duplicates_folder

        for item in self.processed_items:
            if item.original_path in dup_paths:
                item.target_folder = target_dir

        self.processed_items = validate_conflicts(self.processed_items)
        self.preview_table.set_items(self.processed_items)

        modified_count = sum(1 for it in self.processed_items if it.selected and it.is_modified and not it.has_conflict)
        conflict_count = sum(1 for it in self.processed_items if it.selected and it.has_conflict)
        self.action_bar.update_state(
            modified_count=modified_count,
            conflict_count=conflict_count,
            can_undo=self.undo_manager.can_undo(),
        )

    def _on_apply_changes(self):
        """Executes the batch rename/move safely with user confirmation."""
        items_to_apply = [
            it for it in self.processed_items
            if it.selected and it.is_modified and not it.has_conflict
        ]

        if not items_to_apply:
            messagebox.showinfo("Informacion", "No hay cambios pendientes para aplicar.")
            return

        if self.config_manager.confirm_before_apply:
            confirm = messagebox.askyesno(
                "Confirmar Operacion",
                f"Estas seguro de que deseas modificar {len(items_to_apply)} archivo(s)?\n"
                "Podras revertir esta operacion en cualquier momento con el boton 'Deshacer'.",
            )
            if not confirm:
                return

        count, errors = self.undo_manager.apply_batch(items_to_apply)

        if errors:
            err_msg = "\n".join(errors[:5])
            messagebox.showerror("Error", f"Ocurrieron errores durante el proceso:\n{err_msg}")
        else:
            messagebox.showinfo(
                "Operacion Completada",
                f"Se modificaron con exito {count} archivo(s).\n"
                "Puedes usar el boton 'Deshacer' si necesitas revertir los cambios.",
            )

        # Refresh folder from disk
        self._reload_folder()

    def _on_undo_changes(self):
        """Rolls back the last applied batch."""
        if not self.undo_manager.can_undo():
            messagebox.showinfo("Informacion", "No hay transacciones previas para deshacer.")
            return

        confirm = messagebox.askyesno(
            "Deshacer Cambios",
            "Deseas revertir la ultima operacion y restaurar los archivos a su nombre y carpeta original?",
        )
        if not confirm:
            return

        restored, errors = self.undo_manager.undo_last()

        if errors:
            err_msg = "\n".join(errors[:5])
            messagebox.showwarning("Aviso al Deshacer", f"Se restauraron {restored} archivo(s), pero hubo errores:\n{err_msg}")
        else:
            messagebox.showinfo("Deshecho Exitoso", f"Se restauraron {restored} archivo(s) a su estado original.")

        # Refresh folder from disk
        self._reload_folder()
