"""Folder selection header bar component for Flet."""
from pathlib import Path
from typing import Callable, Optional
import flet as ft

from ui.theme import (
    COLOR_BORDER_DARK,
    COLOR_CARD_DARK,
    COLOR_PRIMARY,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    safe_update,
)


class FolderBar(ft.Container):
    """Top bar for selecting directory, toggling recursive scan, and opening settings."""

    def __init__(
        self,
        on_folder_selected: Callable[[Path, bool], None],
        on_open_settings: Callable[[], None],
    ):
        super().__init__()
        self.on_folder_selected = on_folder_selected
        self.on_open_settings = on_open_settings
        self.current_folder: Optional[Path] = None

        # Controls
        self.path_field = ft.TextField(
            hint_text="Selecciona o escribe la ruta de una carpeta...",
            dense=True,
            expand=True,
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            text_size=13,
            on_submit=self._on_path_submitted,
        )

        self.file_picker = ft.FilePicker(on_result=self._on_dir_picked)

        self.btn_browse = ft.Button(
            "Explorar...",
            icon=ft.Icons.FOLDER_OPEN_OUTLINED,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                color=COLOR_TEXT_PRIMARY,
                bgcolor=COLOR_CARD_DARK,
            ),
            on_click=lambda _: self.file_picker.get_directory_path(
                dialog_title="Seleccionar Carpeta a Procesar"
            ),
        )

        self.switch_recursive = ft.Switch(
            label="Subcarpetas",
            value=False,
            active_color=COLOR_PRIMARY,
            label_text_style=ft.TextStyle(size=12, color=COLOR_TEXT_MUTED),
            on_change=self._on_option_changed,
        )

        self.count_text = ft.Text(
            value="0 archivos",
            size=12,
            color=COLOR_TEXT_MUTED,
        )

        self.btn_settings = ft.OutlinedButton(
            "Configuracion",
            icon=ft.Icons.SETTINGS_OUTLINED,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(1, COLOR_BORDER_DARK),
                color=COLOR_TEXT_PRIMARY,
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
                self.btn_settings,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )

    def _on_dir_picked(self, e: ft.FilePickerResultEvent):
        if e.path:
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
