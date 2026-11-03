"""Folder selection header bar component for Flet."""
from pathlib import Path
from typing import Callable, Optional
import flet as ft

from ui.theme import (
    COLOR_BORDER_DARK,
    COLOR_CARD_DARK,
    COLOR_INFO,
    COLOR_PRIMARY,
    COLOR_SUCCESS,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_WARNING,
    safe_update,
)


class FolderBar(ft.Container):
    """Top bar for selecting directory, toggling recursive scan, and opening settings/automation."""

    def __init__(
        self,
        on_folder_selected: Callable[[Path, bool], None],
        on_open_settings: Callable[[], None],
        on_open_automation: Optional[Callable[[], None]] = None,
    ):
        super().__init__()
        self.on_folder_selected = on_folder_selected
        self.on_open_settings = on_open_settings
        self.on_open_automation = on_open_automation
        self.current_folder: Optional[Path] = None

        # Controls
        self.path_field = ft.TextField(
            hint_text="Ruta de la carpeta...",
            dense=True,
            expand=True,
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            text_size=12,
            on_submit=self._on_path_submitted,
        )

        self.file_picker = ft.FilePicker(on_result=self._on_dir_picked)

        self.btn_browse = ft.IconButton(
            icon=ft.Icons.FOLDER_OPEN_OUTLINED,
            tooltip="Explorar carpeta...",
            icon_color=COLOR_TEXT_PRIMARY,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                bgcolor=COLOR_CARD_DARK,
                side=ft.BorderSide(1, COLOR_BORDER_DARK),
            ),
            on_click=self._on_browse_click,
        )

        self.switch_recursive = ft.Switch(
            label="Subcarpetas",
            value=False,
            active_color=COLOR_PRIMARY,
            label_text_style=ft.TextStyle(size=11, color=COLOR_TEXT_MUTED),
            on_change=self._on_option_changed,
        )

        self.count_text = ft.Text(
            value="0 archivos",
            size=11,
            color=COLOR_TEXT_MUTED,
        )

        self.btn_automation = ft.OutlinedButton(
            "Automatización y Monitor",
            icon=ft.Icons.BOLT_ROUNDED,
            tooltip="Abrir ventana de Automatización y Monitorización de Carpetas",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                bgcolor=COLOR_CARD_DARK,
                side=ft.BorderSide(1, COLOR_PRIMARY),
                color=COLOR_TEXT_PRIMARY,
                padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                text_style=ft.TextStyle(size=11.5, weight=ft.FontWeight.W_600),
            ),
            on_click=lambda _: self.on_open_automation() if self.on_open_automation else None,
        )

        self.btn_settings = ft.IconButton(
            icon=ft.Icons.SETTINGS_OUTLINED,
            tooltip="Configuracion",
            icon_color=COLOR_TEXT_PRIMARY,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                bgcolor=COLOR_CARD_DARK,
                side=ft.BorderSide(1, COLOR_BORDER_DARK),
            ),
            on_click=lambda _: self.on_open_settings(),
        )

        self.padding = ft.Padding.symmetric(horizontal=12, vertical=8)
        self.border = ft.Border.only(bottom=ft.BorderSide(1, COLOR_BORDER_DARK))
        self.content = ft.Row(
            controls=[
                self.btn_browse,
                self.path_field,
                self.switch_recursive,
                self.count_text,
                self.btn_automation,
                self.btn_settings,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )

    async def _on_browse_click(self, e):
        path = await self.file_picker.get_directory_path(
            dialog_title="Seleccionar Carpeta a Procesar"
        )
        if path:
            folder = Path(path).resolve()
            self.set_folder(folder)

    def _on_dir_picked(self, e: ft.FilePickerResultEvent):
        if hasattr(e, "path") and e.path:
            folder = Path(e.path).resolve()
            self.set_folder(folder)

    def _on_path_submitted(self, e):
        text = self.path_field.value.strip() if self.path_field.value else ""
        if text:
            folder = Path(text).resolve()
            if folder.is_dir():
                self.set_folder(folder)

    def _on_option_changed(self, e):
        if self.current_folder:
            self.on_folder_selected(self.current_folder, self.switch_recursive.value)

    def set_folder(self, folder: Path):
        self.current_folder = folder
        self.path_field.value = str(folder)
        safe_update(self.path_field)
        self.on_folder_selected(self.current_folder, self.switch_recursive.value)

    def update_count(self, total: int, modified: int = 0):
        if modified > 0:
            self.count_text.value = f"{total} archivos ({modified} a modificar)"
        else:
            self.count_text.value = f"{total} archivos"
        safe_update(self.count_text)

    def update_automation_status(
        self,
        total_monitored: int,
        pending_folders: int,
        in_progress_folders: int,
    ):
        """Updates the Automation & Monitor button label and border color in the top bar."""
        if total_monitored == 0:
            self.btn_automation.content = "Automatización y Monitor"
            self.btn_automation.style.side = ft.BorderSide(1, COLOR_PRIMARY)
        elif in_progress_folders > 0:
            self.btn_automation.content = f"Monitor ({in_progress_folders} en proceso...)"
            self.btn_automation.style.side = ft.BorderSide(1.5, COLOR_INFO)
        elif pending_folders > 0:
            self.btn_automation.content = f"Monitor ({pending_folders} pendiente{'s' if pending_folders != 1 else ''})"
            self.btn_automation.style.side = ft.BorderSide(1.5, COLOR_WARNING)
        else:
            self.btn_automation.content = f"Monitor ({total_monitored} ordenada{'s' if total_monitored != 1 else ''})"
            self.btn_automation.style.side = ft.BorderSide(1.5, COLOR_SUCCESS)
        safe_update(self.btn_automation)
