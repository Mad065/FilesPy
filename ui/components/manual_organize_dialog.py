"""Interactive Step-by-Step Custom Manual Organization Dialog in Flet."""
import base64
import io
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple
import flet as ft
from PIL import Image

from core.conflicts import INVALID_CHARS_PATTERN
from core.models import FileItem, FileStatus, RenameConfig, StepAction
from core.organizer import assign_manual_target
from core.renamer import clean_to_snake_case, generate_single_auto_name
from ui.theme import (
    COLOR_BG_DARK,
    COLOR_BORDER_DARK,
    COLOR_CARD_DARK,
    COLOR_DANGER,
    COLOR_INFO,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_SUCCESS,
    COLOR_SURFACE_DARK,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_WARNING,
    format_bytes,
    format_timestamp,
    safe_update,
)

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff"}
TEXT_EXTENSIONS = {".txt", ".py", ".json", ".csv", ".md", ".html", ".css", ".xml", ".log", ".yaml", ".yml"}


class ManualOrganizeDialog:
    """Modal dialog for step-by-step custom manual file organization and hybrid renaming."""

    def __init__(
        self,
        page: ft.Page,
        items: List[FileItem],
        base_dir: Path,
        manual_folders: List[str],
        rename_config: RenameConfig,
        trash_folder: Path,
        on_finished: Callable[[List[Tuple[FileItem, StepAction]]], None],
        on_folders_updated: Optional[Callable[[List[str]], None]] = None,
        auto_advance: bool = True,
    ):
        self.page = page
        self.items = list(items)
        self.base_dir = Path(base_dir).resolve()
        self.manual_folders = list(manual_folders) or ["Documentos", "Imágenes", "Facturas", "Trabajo", "Personal"]
        self.rename_config = rename_config
        self.trash_folder = trash_folder
        self.on_finished = on_finished
        self.on_folders_updated = on_folders_updated
        self.auto_advance = auto_advance

        self.current_idx = 0

        # State dictionaries mapped by file index
        self.decisions: Dict[int, StepAction] = {}
        self.target_folders: Dict[int, Path] = {}
        self.new_names: Dict[int, str] = {}

        for idx, it in enumerate(self.items):
            self.decisions[idx] = StepAction.KEEP
            self.target_folders[idx] = it.original_path.parent
            self.new_names[idx] = it.original_name

        self._build_ui()
        if self.items:
            self._render_current_item()

    def _build_ui(self):
        # 1. Header
        self.txt_title = ft.Text(
            "Organización Manual Personalizada",
            weight=ft.FontWeight.W_600,
            size=15,
            color=COLOR_TEXT_PRIMARY,
        )
        self.badge_counter = ft.Container(
            content=ft.Text("Archivo 1 de 1", size=11, weight=ft.FontWeight.W_600, color=COLOR_TEXT_PRIMARY),
            bgcolor=COLOR_CARD_DARK,
            border_radius=12,
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            border=ft.Border.all(1, COLOR_BORDER_DARK),
        )

        self.progress_bar = ft.ProgressBar(
            value=0.0,
            color=COLOR_PRIMARY,
            bgcolor=COLOR_CARD_DARK,
            height=4,
        )

        self.stat_pill_apply = ft.Text("Organizar: 0", size=11, color=COLOR_SUCCESS, weight=ft.FontWeight.W_600)
        self.stat_pill_keep = ft.Text("Conservar: 0", size=11, color=COLOR_TEXT_MUTED, weight=ft.FontWeight.W_600)
        self.stat_pill_discard = ft.Text("Eliminar: 0", size=11, color=COLOR_DANGER, weight=ft.FontWeight.W_600)

        header_row = ft.Row(
            controls=[
                ft.Icon(ft.Icons.DRIVE_FILE_MOVE_ROUNDED, color=COLOR_PRIMARY, size=22),
                self.txt_title,
                ft.Container(expand=True),
                self.stat_pill_apply,
                ft.Text("•", color=COLOR_BORDER_DARK),
                self.stat_pill_keep,
                ft.Text("•", color=COLOR_BORDER_DARK),
                self.stat_pill_discard,
                ft.Container(width=10),
                self.badge_counter,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        )

        # 2. Left Column: Preview and File Info
        self.preview_display = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.IMAGE_OUTLINED, size=44, color=COLOR_TEXT_MUTED),
                    ft.Text("Vista Previa", size=11, color=COLOR_TEXT_MUTED),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=COLOR_CARD_DARK,
            border_radius=8,
            height=200,
            width=280,
            alignment=ft.Alignment.CENTER,
            border=ft.Border.all(1, COLOR_BORDER_DARK),
        )

        self.lbl_orig_name = ft.Text("-", size=11, color=COLOR_TEXT_PRIMARY, selectable=True, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS)
        self.lbl_orig_folder = ft.Text("-", size=10, color=COLOR_TEXT_MUTED, selectable=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
        self.lbl_size = ft.Text("-", size=10.5, color=COLOR_TEXT_PRIMARY)
        self.lbl_mtime = ft.Text("-", size=10.5, color=COLOR_TEXT_PRIMARY)

        self.chk_auto_advance = ft.Checkbox(
            label="Avanzar automáticamente al elegir carpeta",
            value=self.auto_advance,
            label_style=ft.TextStyle(size=10.5, color=COLOR_TEXT_SECONDARY),
            on_change=self._on_auto_advance_changed,
        )

        left_column = ft.Column(
            controls=[
                self.preview_display,
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Nombre Original:", size=9.5, weight=ft.FontWeight.W_600, color=COLOR_TEXT_MUTED),
                            self.lbl_orig_name,
                            ft.Container(height=2),
                            ft.Text("Ubicación Actual:", size=9.5, weight=ft.FontWeight.W_600, color=COLOR_TEXT_MUTED),
                            self.lbl_orig_folder,
                            ft.Container(height=2),
                            ft.Row(
                                controls=[
                                    ft.Text("Tamaño: ", size=9.5, weight=ft.FontWeight.W_600, color=COLOR_TEXT_MUTED),
                                    self.lbl_size,
                                    ft.Container(width=10),
                                    ft.Text("Fecha: ", size=9.5, weight=ft.FontWeight.W_600, color=COLOR_TEXT_MUTED),
                                    self.lbl_mtime,
                                ],
                                spacing=4,
                            ),
                        ],
                        spacing=2,
                    ),
                    width=280,
                ),
                ft.Container(height=4),
                self.chk_auto_advance,
            ],
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            width=290,
        )

        # 3. Right Column: Custom Naming + Target Folder Selection + Conflict Box
        # 3.1 Naming Section
        self.txt_filename = ft.TextField(
            label="Nombre del Archivo (Manual)",
            dense=True,
            text_size=11.5,
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            label_style=ft.TextStyle(size=10, color=COLOR_TEXT_MUTED),
            expand=True,
            on_change=self._on_name_input_changed,
        )

        self.btn_auto_name = ft.OutlinedButton(
            "⚡ Auto-nombrar",
            icon=ft.Icons.AUTO_FIX_HIGH,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(1, COLOR_PRIMARY),
                color=COLOR_PRIMARY,
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            ),
            tooltip="Genera el nombre automáticamente usando las reglas de renombrado configuradas",
            on_click=lambda _: self._apply_auto_name(),
        )

        self.btn_snake = ft.OutlinedButton(
            "snake_case",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(1, COLOR_BORDER_DARK),
                color=COLOR_TEXT_PRIMARY,
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            ),
            tooltip="Convierte el nombre a minúsculas con guiones bajos",
            on_click=lambda _: self._apply_snake_name(),
        )

        self.btn_restore_name = ft.TextButton(
            "↺ Original",
            style=ft.ButtonStyle(color=COLOR_TEXT_MUTED),
            tooltip="Restablece el nombre original del archivo",
            on_click=lambda _: self._restore_original_name(),
        )

        naming_controls_row = ft.Row(
            controls=[
                self.txt_filename,
                self.btn_auto_name,
                self.btn_snake,
                self.btn_restore_name,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6,
        )

        # 3.2 Target Folder Section
        lbl_folders_header = ft.Row(
            controls=[
                ft.Icon(ft.Icons.FOLDER_OPEN, size=16, color=COLOR_PRIMARY),
                ft.Text("Elige la Carpeta de Destino:", size=11, weight=ft.FontWeight.W_600, color=COLOR_TEXT_PRIMARY),
                ft.Container(expand=True),
                ft.Text("(Haz clic en una carpeta para asignarla)", size=9.5, color=COLOR_TEXT_MUTED),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6,
        )

        self.folders_wrap = ft.Row(
            controls=[],
            wrap=True,
            spacing=8,
            run_spacing=8,
        )

        self.folders_container = ft.Container(
            content=self.folders_wrap,
            bgcolor=COLOR_CARD_DARK,
            border_radius=8,
            padding=10,
            border=ft.Border.all(1, COLOR_BORDER_DARK),
            height=120,
            alignment=ft.Alignment.TOP_LEFT,
        )

        # New Folder Input
        self.txt_new_folder = ft.TextField(
            hint_text="Crear y agregar nueva carpeta...",
            dense=True,
            text_size=10.5,
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            expand=True,
            on_submit=lambda _: self._on_add_folder_click(),
        )

        self.btn_add_folder = ft.OutlinedButton(
            "＋ Agregar Carpeta",
            icon=ft.Icons.CREATE_NEW_FOLDER_OUTLINED,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(1, COLOR_BORDER_DARK),
                color=COLOR_TEXT_PRIMARY,
            ),
            tooltip="Agrega una nueva carpeta de destino a la lista",
            on_click=lambda _: self._on_add_folder_click(),
        )

        self.btn_keep_original_folder = ft.OutlinedButton(
            "Conservar Carpeta Actual",
            icon=ft.Icons.FOLDER_OFF_OUTLINED,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(1, COLOR_BORDER_DARK),
                color=COLOR_TEXT_MUTED,
            ),
            tooltip="Mantiene el archivo en su ubicación actual sin moverlo a otra carpeta",
            on_click=lambda _: self._on_keep_folder_click(),
        )

        folder_input_row = ft.Row(
            controls=[
                self.txt_new_folder,
                self.btn_add_folder,
                self.btn_keep_original_folder,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6,
        )

        # 3.3 Status & Destination Summary
        self.status_box = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.INFO_OUTLINE, size=15, color=COLOR_INFO),
                    ft.Text("Estado", size=10.5, color=COLOR_TEXT_PRIMARY),
                ],
                spacing=6,
            ),
            bgcolor=COLOR_CARD_DARK,
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=10, vertical=6),
            border=ft.Border.all(1, COLOR_BORDER_DARK),
        )

        right_column = ft.Column(
            controls=[
                naming_controls_row,
                ft.Divider(height=1, color=COLOR_BORDER_DARK),
                lbl_folders_header,
                self.folders_container,
                folder_input_row,
                ft.Divider(height=1, color=COLOR_BORDER_DARK),
                self.status_box,
            ],
            spacing=8,
            expand=True,
        )

        # Body row
        body_row = ft.Row(
            controls=[
                left_column,
                ft.VerticalDivider(width=1, thickness=1, color=COLOR_BORDER_DARK),
                right_column,
            ],
            spacing=14,
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
        )

        # 4. Stepper Navigation & Actions
        self.btn_prev = ft.TextButton(
            "← Anterior",
            icon=ft.Icons.ARROW_BACK,
            style=ft.ButtonStyle(color=COLOR_TEXT_PRIMARY),
            on_click=lambda _: self._on_prev(),
        )

        self.btn_next = ft.TextButton(
            "Siguiente →",
            icon=ft.Icons.ARROW_FORWARD,
            style=ft.ButtonStyle(color=COLOR_TEXT_PRIMARY),
            on_click=lambda _: self._on_next(),
        )

        self.btn_skip_file = ft.OutlinedButton(
            "Omitir Archivo",
            icon=ft.Icons.NOT_INTERESTED,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(1, COLOR_BORDER_DARK),
                color=COLOR_TEXT_MUTED,
            ),
            tooltip="No realizar cambios en este archivo (conservar nombre y carpeta)",
            on_click=lambda _: self._skip_current_file(),
        )

        self.btn_discard_file = ft.OutlinedButton(
            "Mover a Papelera",
            icon=ft.Icons.DELETE_OUTLINE,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(1, COLOR_DANGER),
                color=COLOR_DANGER,
            ),
            tooltip="Mover a la carpeta _Papelera de forma segura y reversible",
            on_click=lambda _: self._discard_current_file(),
        )

        nav_row = ft.Row(
            controls=[
                self.btn_prev,
                self.btn_next,
                ft.Container(expand=True),
                self.btn_skip_file,
                self.btn_discard_file,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        )

        # Main Dialog content container
        dialog_content = ft.Container(
            content=ft.Column(
                controls=[
                    header_row,
                    self.progress_bar,
                    ft.Divider(height=1, color=COLOR_BORDER_DARK),
                    body_row,
                    ft.Divider(height=1, color=COLOR_BORDER_DARK),
                    nav_row,
                ],
                spacing=8,
                expand=True,
            ),
            width=850,
            height=510,
            padding=ft.Padding.all(4),
        )

        self.dialog = ft.AlertDialog(
            content=dialog_content,
            actions=[
                ft.TextButton(
                    "Cancelar",
                    style=ft.ButtonStyle(color=COLOR_TEXT_MUTED),
                    on_click=lambda _: self.page.pop_dialog(),
                ),
                ft.FilledButton(
                    "Finalizar y Aplicar Cambios",
                    icon=ft.Icons.CHECK,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8),
                        bgcolor=COLOR_PRIMARY,
                        color="#FFFFFF",
                    ),
                    on_click=lambda _: self._on_confirm_click(),
                ),
            ],
        )

    def show(self):
        """Displays the manual organize modal dialog on the page."""
        if not self.items:
            return
        self._update_stats()
        self.page.show_dialog(self.dialog)

    def _render_current_item(self):
        if not self.items or self.current_idx < 0 or self.current_idx >= len(self.items):
            return

        item = self.items[self.current_idx]
        total = len(self.items)

        # 1. Update header and progress
        self.badge_counter.content.value = f"Archivo {self.current_idx + 1} de {total}"
        self.progress_bar.value = (self.current_idx + 1) / total

        # 2. Update navigation button states
        self.btn_prev.disabled = (self.current_idx == 0)
        self.btn_next.disabled = (self.current_idx == total - 1)

        # 3. Update Preview
        path = item.original_path
        ext = item.extension.lower()

        if ext in IMAGE_EXTENSIONS and path.exists():
            self._render_image_preview(path)
        elif ext in TEXT_EXTENSIONS and path.exists():
            self._render_text_preview(path)
        else:
            self._render_generic_preview(ext)

        # 4. Update Left Metadata
        self.lbl_orig_name.value = item.original_name
        self.lbl_orig_folder.value = str(item.original_path.parent)
        self.lbl_size.value = format_bytes(item.size_bytes)
        self.lbl_mtime.value = format_timestamp(item.modified_time)

        # 5. Update Naming input
        current_name = self.new_names.get(self.current_idx, item.original_name)
        self.txt_filename.value = current_name

        # 6. Render destination folder buttons
        self._render_folder_buttons()

        # 7. Update status and conflict box
        self._validate_and_update_status()

        # 8. Update stats pills
        self._update_stats()

        safe_update(self.dialog)

    def _render_folder_buttons(self):
        current_target = self.target_folders.get(self.current_idx, self.items[self.current_idx].original_path.parent)
        current_decision = self.decisions.get(self.current_idx, StepAction.KEEP)

        controls: List[ft.Control] = []
        for folder_name in self.manual_folders:
            folder_path = (self.base_dir / folder_name).resolve()
            is_active = (current_decision == StepAction.APPLY and current_target == folder_path)

            # Count how many files are currently directed to this folder
            count = sum(
                1 for idx in range(len(self.items))
                if self.decisions.get(idx) == StepAction.APPLY and self.target_folders.get(idx) == folder_path
            )

            btn = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(
                            ft.Icons.FOLDER if is_active else ft.Icons.FOLDER_OUTLINED,
                            size=15,
                            color="#FFFFFF" if is_active else COLOR_PRIMARY,
                        ),
                        ft.Text(
                            f"{folder_name} ({count})",
                            size=11,
                            weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.NORMAL,
                            color="#FFFFFF" if is_active else COLOR_TEXT_PRIMARY,
                        ),
                    ],
                    spacing=5,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                bgcolor=COLOR_PRIMARY if is_active else COLOR_SURFACE_DARK,
                border_radius=8,
                padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                border=ft.Border.all(1, COLOR_PRIMARY if is_active else COLOR_BORDER_DARK),
                ink=True,
                on_click=lambda _, f=folder_name: self._on_folder_selected(f),
            )
            controls.append(btn)

        self.folders_wrap.controls = controls

    def _on_folder_selected(self, folder_name: str):
        target_path = (self.base_dir / folder_name.strip()).resolve()
        self.target_folders[self.current_idx] = target_path
        self.decisions[self.current_idx] = StepAction.APPLY

        if self.chk_auto_advance.value and self.current_idx < len(self.items) - 1:
            self.current_idx += 1

        self._render_current_item()

    def _on_keep_folder_click(self):
        item = self.items[self.current_idx]
        self.target_folders[self.current_idx] = item.original_path.parent
        # If the name is changed, it can still be APPLY (rename only). If unchanged, KEEP.
        cur_name = self.new_names.get(self.current_idx, item.original_name)
        if cur_name != item.original_name:
            self.decisions[self.current_idx] = StepAction.APPLY
        else:
            self.decisions[self.current_idx] = StepAction.KEEP

        self._render_current_item()

    def _on_add_folder_click(self):
        raw_val = (self.txt_new_folder.value or "").strip()
        if not raw_val:
            return

        clean_name = raw_val.strip("/\\")
        if clean_name and clean_name not in self.manual_folders:
            self.manual_folders.append(clean_name)
            if self.on_folders_updated:
                self.on_folders_updated(self.manual_folders)

        self.txt_new_folder.value = ""
        # Immediately assign the new folder to current item
        self._on_folder_selected(clean_name)

    def _on_name_input_changed(self, e):
        new_val = self.txt_filename.value or ""
        self.new_names[self.current_idx] = new_val
        item = self.items[self.current_idx]
        target_f = self.target_folders.get(self.current_idx, item.original_path.parent)

        if new_val != item.original_name or target_f != item.original_path.parent:
            self.decisions[self.current_idx] = StepAction.APPLY
        else:
            self.decisions[self.current_idx] = StepAction.KEEP

        self._validate_and_update_status()
        self._update_stats()
        safe_update(self.status_box)

    def _apply_auto_name(self):
        item = self.items[self.current_idx]
        auto_name = generate_single_auto_name(item, self.rename_config, index=self.current_idx)
        self.new_names[self.current_idx] = auto_name
        self.txt_filename.value = auto_name
        self._on_name_input_changed(None)

    def _apply_snake_name(self):
        current_name = self.new_names.get(self.current_idx, self.items[self.current_idx].original_name)
        snake_name = clean_to_snake_case(current_name)
        self.new_names[self.current_idx] = snake_name
        self.txt_filename.value = snake_name
        self._on_name_input_changed(None)

    def _restore_original_name(self):
        orig_name = self.items[self.current_idx].original_name
        self.new_names[self.current_idx] = orig_name
        self.txt_filename.value = orig_name
        self._on_name_input_changed(None)

    def _on_auto_advance_changed(self, e):
        self.auto_advance = bool(self.chk_auto_advance.value)

    def _skip_current_file(self):
        item = self.items[self.current_idx]
        self.decisions[self.current_idx] = StepAction.KEEP
        self.target_folders[self.current_idx] = item.original_path.parent
        self.new_names[self.current_idx] = item.original_name
        if self.current_idx < len(self.items) - 1:
            self.current_idx += 1
        self._render_current_item()

    def _discard_current_file(self):
        self.decisions[self.current_idx] = StepAction.DISCARD
        if self.current_idx < len(self.items) - 1:
            self.current_idx += 1
        self._render_current_item()

    def _on_prev(self):
        if self.current_idx > 0:
            self.current_idx -= 1
            self._render_current_item()

    def _on_next(self):
        if self.current_idx < len(self.items) - 1:
            self.current_idx += 1
            self._render_current_item()

    def _validate_and_update_status(self):
        item = self.items[self.current_idx]
        decision = self.decisions.get(self.current_idx, StepAction.KEEP)
        name = self.new_names.get(self.current_idx, item.original_name).strip()
        target = self.target_folders.get(self.current_idx, item.original_path.parent)

        if decision == StepAction.DISCARD:
            self.status_box.content = ft.Row(
                controls=[
                    ft.Icon(ft.Icons.DELETE_OUTLINE, size=15, color=COLOR_DANGER),
                    ft.Text("Decisión: Mover a la papelera (_Papelera)", size=10.5, color=COLOR_DANGER, weight=ft.FontWeight.W_600),
                ],
                spacing=6,
            )
            self.status_box.bgcolor = "#2c1517"
            self.status_box.border = ft.Border.all(1, COLOR_DANGER)
            return

        if not name:
            self.status_box.content = ft.Row(
                controls=[
                    ft.Icon(ft.Icons.ERROR_OUTLINE, size=15, color=COLOR_DANGER),
                    ft.Text("Error: El nombre de archivo no puede estar vacío.", size=10.5, color=COLOR_DANGER, weight=ft.FontWeight.W_600),
                ],
                spacing=6,
            )
            self.status_box.bgcolor = "#2c1517"
            self.status_box.border = ft.Border.all(1, COLOR_DANGER)
            return

        if INVALID_CHARS_PATTERN.search(name):
            self.status_box.content = ft.Row(
                controls=[
                    ft.Icon(ft.Icons.ERROR_OUTLINE, size=15, color=COLOR_DANGER),
                    ft.Text("Error: El nombre contiene caracteres inválidos (/ \\ : * ? \" < > |).", size=10.5, color=COLOR_DANGER, weight=ft.FontWeight.W_600),
                ],
                spacing=6,
            )
            self.status_box.bgcolor = "#2c1517"
            self.status_box.border = ft.Border.all(1, COLOR_DANGER)
            return

        resolved_dest = (target / name).resolve()
        # Check collision with existing file on disk
        if resolved_dest.exists() and resolved_dest != item.original_path.resolve():
            self.status_box.content = ft.Row(
                controls=[
                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, size=15, color=COLOR_WARNING),
                    ft.Text(f"Aviso de Colisión: Ya existe un archivo '{name}' en '{target.name}'.", size=10.5, color=COLOR_WARNING, weight=ft.FontWeight.W_600),
                ],
                spacing=6,
            )
            self.status_box.bgcolor = "#2e2410"
            self.status_box.border = ft.Border.all(1, COLOR_WARNING)
            return

        # Check collision with another item in this session
        collision_with_other = False
        for o_idx in range(len(self.items)):
            if o_idx != self.current_idx and self.decisions.get(o_idx) == StepAction.APPLY:
                o_target = self.target_folders.get(o_idx, self.items[o_idx].original_path.parent)
                o_name = self.new_names.get(o_idx, self.items[o_idx].original_name).strip()
                if (o_target / o_name).resolve() == resolved_dest:
                    collision_with_other = True
                    break

        if collision_with_other:
            self.status_box.content = ft.Row(
                controls=[
                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, size=15, color=COLOR_DANGER),
                    ft.Text(f"Conflicto interno: Otro archivo en la sesión tiene este mismo destino.", size=10.5, color=COLOR_DANGER, weight=ft.FontWeight.W_600),
                ],
                spacing=6,
            )
            self.status_box.bgcolor = "#2c1517"
            self.status_box.border = ft.Border.all(1, COLOR_DANGER)
            return

        is_modified = (resolved_dest != item.original_path.resolve())
        if decision == StepAction.APPLY and is_modified:
            folder_display = target.name if target != self.base_dir else "(raíz)"
            self.status_box.content = ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=15, color=COLOR_SUCCESS),
                    ft.Text(f"Listo para guardar en '{folder_display}' como '{name}'.", size=10.5, color=COLOR_SUCCESS),
                ],
                spacing=6,
            )
            self.status_box.bgcolor = "#13271d"
            self.status_box.border = ft.Border.all(1, COLOR_SUCCESS)
        else:
            self.status_box.content = ft.Row(
                controls=[
                    ft.Icon(ft.Icons.INFO_OUTLINE, size=15, color=COLOR_TEXT_MUTED),
                    ft.Text("Sin cambios propuestos (conserva nombre y carpeta original).", size=10.5, color=COLOR_TEXT_MUTED),
                ],
                spacing=6,
            )
            self.status_box.bgcolor = COLOR_CARD_DARK
            self.status_box.border = ft.Border.all(1, COLOR_BORDER_DARK)

    def _render_image_preview(self, path: Path):
        try:
            with Image.open(path) as img:
                img.thumbnail((260, 180))
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGB")
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                b64 = base64.b64encode(buf.getvalue()).decode()

            self.preview_display.content = ft.Image(
                src_base64=b64,
                fit=ft.ImageFit.CONTAIN,
                border_radius=ft.BorderRadius.all(6),
            )
        except Exception:
            self._render_generic_preview(path.suffix)

    def _render_text_preview(self, path: Path):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                snippet = "".join(f.readline() for _ in range(10))

            self.preview_display.content = ft.Container(
                content=ft.Text(
                    value=snippet,
                    font_family="monospace",
                    size=9.5,
                    color=COLOR_TEXT_PRIMARY,
                ),
                padding=8,
                alignment=ft.Alignment.TOP_LEFT,
                expand=True,
            )
        except Exception:
            self._render_generic_preview(path.suffix)

    def _render_generic_preview(self, ext: str):
        self.preview_display.content = ft.Column(
            controls=[
                ft.Icon(ft.Icons.INSERT_DRIVE_FILE_OUTLINED, size=48, color=COLOR_TEXT_MUTED),
                ft.Text(
                    f"[{ext.upper() if ext else 'ARCHIVO'}]",
                    size=12,
                    weight=ft.FontWeight.W_600,
                    color=COLOR_TEXT_MUTED,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6,
        )

    def _update_stats(self):
        mod_count = 0
        discard_count = 0
        keep_count = 0

        for idx, it in enumerate(self.items):
            dec = self.decisions.get(idx, StepAction.KEEP)
            if dec == StepAction.DISCARD:
                discard_count += 1
            elif dec == StepAction.APPLY:
                name = self.new_names.get(idx, it.original_name)
                target = self.target_folders.get(idx, it.original_path.parent)
                if (target / name).resolve() != it.original_path.resolve():
                    mod_count += 1
                else:
                    keep_count += 1
            else:
                keep_count += 1

        self.stat_pill_apply.value = f"Organizar: {mod_count}"
        self.stat_pill_keep.value = f"Conservar: {keep_count}"
        self.stat_pill_discard.value = f"Eliminar: {discard_count}"

    def _on_confirm_click(self):
        # Validate that no names are empty or invalid
        errors = []
        for idx, it in enumerate(self.items):
            if self.decisions.get(idx) == StepAction.APPLY:
                name = self.new_names.get(idx, "").strip()
                if not name:
                    errors.append(f"El archivo '{it.original_name}' tiene un nombre vacío.")
                elif INVALID_CHARS_PATTERN.search(name):
                    errors.append(f"El archivo '{name}' contiene caracteres inválidos.")

        if errors:
            err_dialog = ft.AlertDialog(
                title=ft.Text("Errores en Nombres", weight=ft.FontWeight.W_600),
                content=ft.Text("\n".join(errors[:4])),
                actions=[ft.TextButton("Aceptar", on_click=lambda _: self.page.pop_dialog())],
            )
            self.page.show_dialog(err_dialog)
            return

        # Prepare modified items
        reviewed_pairs: List[Tuple[FileItem, StepAction]] = []
        mod_count = 0
        discard_count = 0

        for idx, it in enumerate(self.items):
            dec = self.decisions.get(idx, StepAction.KEEP)
            target = self.target_folders.get(idx, it.original_path.parent)
            new_name = self.new_names.get(idx, it.original_name).strip()

            it.target_folder = target
            it.new_name = new_name
            it.status = FileStatus.READY if (target / new_name).resolve() != it.original_path.resolve() else FileStatus.UNCHANGED

            reviewed_pairs.append((it, dec))
            if dec == StepAction.APPLY and it.is_modified:
                mod_count += 1
            elif dec == StepAction.DISCARD:
                discard_count += 1

        if mod_count == 0 and discard_count == 0:
            self.page.pop_dialog()
            return

        def do_execute(e):
            self.page.pop_dialog()  # Close confirmation dialog
            self.page.pop_dialog()  # Close manual organize dialog
            self.on_finished(reviewed_pairs)

        confirm_msg = (
            f"Se aplicará la organización manual personalizada a {len(self.items)} archivo(s):\n\n"
            f"• {mod_count} archivo(s) serán movidos o renombrados según tus elecciones.\n"
            f"• {discard_count} archivo(s) serán enviados a la papelera de seguridad.\n"
            f"• {len(self.items) - mod_count - discard_count} archivo(s) se conservarán sin cambios.\n\n"
            "Podrás revertir toda esta operación en cualquier momento con el botón 'Deshacer'."
        )

        confirm_dialog = ft.AlertDialog(
            title=ft.Text("Confirmar Organización Manual", weight=ft.FontWeight.W_600),
            content=ft.Text(confirm_msg),
            actions=[
                ft.TextButton("Volver a Revisar", on_click=lambda _: self.page.pop_dialog()),
                ft.FilledButton(
                    "Proceder",
                    on_click=do_execute,
                    bgcolor=COLOR_PRIMARY,
                    color="#FFFFFF",
                ),
            ],
        )
        self.page.show_dialog(confirm_dialog)
