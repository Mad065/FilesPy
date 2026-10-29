"""Main Application Layout and Logic for FilesPy (Flet)."""
from pathlib import Path
from typing import List, Optional
import flet as ft

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
from ui.theme import (
    COLOR_BG_DARK,
    COLOR_BORDER_DARK,
    COLOR_PRIMARY,
    COLOR_SURFACE_DARK,
    COLOR_TEXT_MUTED,
    safe_update,
)


class FilesPyApp:
    """Main Flet Application controller."""

    def __init__(self, page: ft.Page):
        self.page = page

        # Window & Theme configuration
        self.page.title = "FilesPy — Organizador y Renombrador de Archivos"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 0
        self.page.spacing = 0
        self.page.bgcolor = COLOR_BG_DARK
        self.page.theme = ft.Theme(
            color_scheme_seed=COLOR_PRIMARY,
        )

        # Core State
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
            on_folder_selected=self._on_folder_changed,
            on_open_settings=self._open_settings_dialog,
        )
        self.page.overlay.append(self.folder_bar.file_picker)

        # 2. Left Column: Rules Navigation (SegmentedButton)
        self.rename_panel = RenamePanel(on_change=self._on_rename_rules_changed)
        self.organize_panel = OrganizePanel(on_change=self._on_organize_rules_changed)
        self.organize_panel.update_categories_info(self.config_manager.get_categories_dict())
        self.duplicate_panel = DuplicatePanel(
            get_current_items=lambda: self.raw_scanned_items,
            on_isolate_duplicates=self._on_isolate_duplicates,
        )

        self.panel_container = ft.Container(
            content=self.rename_panel,
            expand=True,
        )

        def on_nav_changed(e):
            sel = e.control.selected
            val = list(sel)[0] if sel else "rename"
            if val == "rename":
                self.panel_container.content = self.rename_panel
            elif val == "organize":
                self.panel_container.content = self.organize_panel
            elif val == "duplicates":
                self.panel_container.content = self.duplicate_panel
            safe_update(self.panel_container)

        self.nav_segmented = ft.SegmentedButton(
            selected=["rename"],
            allow_empty_selection=False,
            segments=[
                ft.Segment(value="rename", label=ft.Text("Renombrar", size=11), icon=ft.Icons.EDIT_OUTLINED),
                ft.Segment(value="organize", label=ft.Text("Organizar", size=11), icon=ft.Icons.CATEGORY_OUTLINED),
                ft.Segment(value="duplicates", label=ft.Text("Duplicados", size=11), icon=ft.Icons.COPY_ALL_OUTLINED),
            ],
            on_change=on_nav_changed,
        )

        self.left_sidebar = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(content=self.nav_segmented, padding=ft.Padding.symmetric(horizontal=8, vertical=6)),
                    ft.Divider(height=1, color=COLOR_BORDER_DARK),
                    self.panel_container,
                ],
                spacing=0,
                expand=True,
            ),
            width=310,
            bgcolor=COLOR_SURFACE_DARK,
            border=ft.Border.only(right=ft.BorderSide(1, COLOR_BORDER_DARK)),
        )

        # 3. Center: Preview Table
        self.preview_table = PreviewTable(
            on_item_inspected=self._on_item_inspected,
            on_selection_toggled=self._on_selection_toggled,
        )
        self.center_container = ft.Container(
            content=self.preview_table,
            expand=True,
            padding=10,
        )

        # 4. Right Column: Inspector Panel
        self.inspector = InspectorPanel()
        self.right_container = ft.Container(
            content=self.inspector,
            padding=ft.Padding.only(top=10, bottom=10, right=10),
        )

        # 5. Bottom Action Bar
        self.action_bar = ActionBar(
            on_refresh=self._reload_folder,
            on_apply=self._on_apply_changes,
            on_undo=self._on_undo_changes,
        )

        # Workspace Row
        self.workspace_row = ft.Row(
            controls=[
                self.left_sidebar,
                self.center_container,
                self.right_container,
            ],
            spacing=0,
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
        )

        # Main Layout Column
        self.main_layout = ft.Column(
            controls=[
                self.folder_bar,
                self.workspace_row,
                self.action_bar,
            ],
            spacing=0,
            expand=True,
        )

        self.page.add(self.main_layout)

    def _open_settings_dialog(self):
        dialog = SettingsDialog(
            page=self.page,
            config_manager=self.config_manager,
            on_saved=self._on_settings_saved,
        )
        dialog.show()

    def _on_settings_saved(self):
        self.organize_panel.update_categories_info(self.config_manager.get_categories_dict())
        self._reload_folder()

    def _on_folder_changed(self, folder: Path, recursive: bool):
        self.current_folder = folder
        self.is_recursive = recursive
        self._reload_folder()

    def _reload_folder(self):
        if not self.current_folder or not self.current_folder.is_dir():
            return

        self.raw_scanned_items = scan_directory(
            self.current_folder,
            recursive=self.is_recursive,
            ignored_names=self.config_manager.get_ignored_set(),
        )
        self._run_pipeline()

    def _run_pipeline(self):
        if not self.current_folder:
            return

        items: List[FileItem] = []
        for it in self.raw_scanned_items:
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

        # Step 2: Organization rules
        self.organize_config.custom_category_map = self.config_manager.get_categories_dict()
        self.organize_config.no_extension_folder = self.config_manager.no_extension_folder
        self.organize_config.unorganized_folder = self.config_manager.unorganized_folder
        items = apply_organization_rules(items, self.current_folder, self.organize_config)

        # Step 3: Conflict detection
        items = validate_conflicts(items)

        self.processed_items = items
        self.preview_table.set_items(self.processed_items)

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
        self._run_pipeline()

    def _on_item_inspected(self, item: FileItem):
        self.inspector.inspect_file(item)

    def _on_isolate_duplicates(self, duplicates_to_move: List[FileItem]):
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
        items_to_apply = [
            it for it in self.processed_items
            if it.selected and it.is_modified and not it.has_conflict
        ]

        if not items_to_apply:
            self._show_info_dialog("Informacion", "No hay cambios pendientes para aplicar.")
            return

        if self.config_manager.confirm_before_apply:
            def do_apply(e):
                self.page.pop_dialog()
                self._execute_apply(items_to_apply)

            confirm_dialog = ft.AlertDialog(
                title=ft.Text("Confirmar Operacion", weight=ft.FontWeight.W_600),
                content=ft.Text(
                    f"Deseas aplicar los cambios a {len(items_to_apply)} archivo(s)?\n"
                    "Podras revertir la operacion con el boton 'Deshacer'."
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda _: self.page.pop_dialog()),
                    ft.FilledButton("Aplicar", on_click=do_apply, bgcolor=COLOR_PRIMARY, color="#FFFFFF"),
                ],
            )
            self.page.show_dialog(confirm_dialog)
        else:
            self._execute_apply(items_to_apply)

    def _execute_apply(self, items_to_apply: List[FileItem]):
        count, errors = self.undo_manager.apply_batch(items_to_apply)
        if errors:
            err_msg = "\n".join(errors[:5])
            self._show_info_dialog("Error", f"Ocurrieron errores durante el proceso:\n{err_msg}")
        else:
            self._show_info_dialog(
                "Operacion Completada",
                f"Se modificaron con exito {count} archivo(s).\n"
                "Puedes usar el boton 'Deshacer' si necesitas revertir los cambios.",
            )
        self._reload_folder()

    def _on_undo_changes(self):
        if not self.undo_manager.can_undo():
            self._show_info_dialog("Informacion", "No hay transacciones previas para deshacer.")
            return

        def do_undo(e):
            self.page.pop_dialog()
            restored, errors = self.undo_manager.undo_last()
            if errors:
                err_msg = "\n".join(errors[:5])
                self._show_info_dialog("Aviso al Deshacer", f"Se restauraron {restored} archivo(s), pero hubo errores:\n{err_msg}")
            else:
                self._show_info_dialog("Deshecho Exitoso", f"Se restauraron {restored} archivo(s) a su estado original.")
            self._reload_folder()

        undo_dialog = ft.AlertDialog(
            title=ft.Text("Deshacer Cambios", weight=ft.FontWeight.W_600),
            content=ft.Text("Deseas revertir la ultima operacion y restaurar los archivos a su nombre y carpeta original?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self.page.pop_dialog()),
                ft.FilledButton("Deshacer", on_click=do_undo, bgcolor=COLOR_PRIMARY, color="#FFFFFF"),
            ],
        )
        self.page.show_dialog(undo_dialog)

    def _show_info_dialog(self, title: str, message: str):
        dialog = ft.AlertDialog(
            title=ft.Text(title, weight=ft.FontWeight.W_600),
            content=ft.Text(message),
            actions=[
                ft.TextButton("Aceptar", on_click=lambda _: self.page.pop_dialog()),
            ],
        )
        self.page.show_dialog(dialog)
