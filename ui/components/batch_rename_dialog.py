"""macOS Finder-style Batch Rename Modal Dialog in Flet."""
from typing import Callable, List, Optional
import flet as ft

from core.models import FileItem, RenameConfig
from core.renamer import generate_example_name
from ui.theme import (
    COLOR_BORDER_DARK,
    COLOR_CARD_DARK,
    COLOR_PRIMARY,
    COLOR_SURFACE_DARK,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    safe_update,
)


class BatchRenameDialog:
    """Modal dialog modeled directly on Apple macOS Finder's Batch Rename utility."""

    def __init__(
        self,
        page: ft.Page,
        items: List[FileItem],
        initial_config: Optional[RenameConfig] = None,
        on_rename_confirmed: Optional[Callable[[RenameConfig], None]] = None,
    ):
        self.page = page
        self.items = [it for it in items if it.selected] or list(items)
        self.config = initial_config or RenameConfig(mode="format")
        self.on_rename_confirmed = on_rename_confirmed

        # Determine sample file from first selected item
        if self.items:
            first = self.items[0]
            self.sample_name = first.original_name
            self.sample_mtime = first.modified_time
        else:
            self.sample_name = "Captura de pantalla 2022-12-21 a las 15.3.png"
            self.sample_mtime = 1671658230.0

        self._build_dialog()
        self._sync_visibility_and_example(update_ui=False)

    def _build_dialog(self):
        # 1. Mode Dropdown: Reemplazar texto | Agregar texto | Formato
        self.mode_dropdown = ft.Dropdown(
            value=self.config.mode or "format",
            dense=True,
            text_size=12,
            width=200,
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            bgcolor=COLOR_CARD_DARK,
            options=[
                ft.dropdown.Option("replace", "Reemplazar texto"),
                ft.dropdown.Option("add_text", "Agregar texto"),
                ft.dropdown.Option("format", "Formato"),
            ],
            on_select=lambda _: self._on_input_changed(),
        )

        # --- MODE 1: REEMPLAZAR TEXTO ---
        self.find_field = ft.TextField(
            value=self.config.find_text,
            dense=True,
            text_size=12,
            width=200,
            border_radius=6,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            bgcolor=COLOR_CARD_DARK,
            on_change=lambda _: self._on_input_changed(),
        )

        self.replace_field = ft.TextField(
            value=self.config.replace_text,
            dense=True,
            text_size=12,
            width=200,
            border_radius=6,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            bgcolor=COLOR_CARD_DARK,
            on_change=lambda _: self._on_input_changed(),
        )

        self.replace_container = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text("Buscar:", size=12, color=COLOR_TEXT_PRIMARY, weight=ft.FontWeight.W_500),
                    self.find_field,
                    ft.Container(width=12),
                    ft.Text("Reemplazar por:", size=12, color=COLOR_TEXT_PRIMARY, weight=ft.FontWeight.W_500),
                    self.replace_field,
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            padding=ft.Padding.symmetric(vertical=8),
        )

        # --- MODE 2: AGREGAR TEXTO ---
        self.add_text_field = ft.TextField(
            value=self.config.add_text,
            hint_text="Texto a agregar",
            dense=True,
            text_size=12,
            width=220,
            border_radius=6,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            bgcolor=COLOR_CARD_DARK,
            on_change=lambda _: self._on_input_changed(),
        )

        self.add_location_dropdown = ft.Dropdown(
            value=self.config.add_location or "after",
            dense=True,
            text_size=12,
            width=190,
            border_radius=6,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            bgcolor=COLOR_CARD_DARK,
            options=[
                ft.dropdown.Option("after", "Después del nombre"),
                ft.dropdown.Option("before", "Antes del nombre"),
            ],
            on_select=lambda _: self._on_input_changed(),
        )

        self.add_text_container = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text("Agregar texto:", size=12, color=COLOR_TEXT_PRIMARY, weight=ft.FontWeight.W_500),
                    self.add_text_field,
                    ft.Container(width=12),
                    ft.Text("Ubicación:", size=12, color=COLOR_TEXT_PRIMARY, weight=ft.FontWeight.W_500),
                    self.add_location_dropdown,
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            padding=ft.Padding.symmetric(vertical=8),
        )

        # --- MODE 3: FORMATO ---
        self.format_style_dropdown = ft.Dropdown(
            value=self.config.format_style or "name_counter",
            dense=True,
            text_size=12,
            width=190,
            border_radius=6,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            bgcolor=COLOR_CARD_DARK,
            options=[
                ft.dropdown.Option("name_counter", "Nombre y contador"),
                ft.dropdown.Option("name_index", "Nombre e índice"),
                ft.dropdown.Option("name_date", "Nombre y fecha"),
            ],
            on_select=lambda _: self._on_input_changed(),
        )

        self.format_location_dropdown = ft.Dropdown(
            value=self.config.format_location or "after",
            dense=True,
            text_size=12,
            width=190,
            border_radius=6,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            bgcolor=COLOR_CARD_DARK,
            options=[
                ft.dropdown.Option("after", "Después del nombre"),
                ft.dropdown.Option("before", "Antes del nombre"),
            ],
            on_select=lambda _: self._on_input_changed(),
        )

        self.custom_format_field = ft.TextField(
            value=self.config.custom_format if self.config.custom_format is not None else "Archivo",
            dense=True,
            text_size=12,
            width=190,
            border_radius=6,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            bgcolor=COLOR_CARD_DARK,
            on_change=lambda _: self._on_input_changed(),
        )

        self.counter_start_field = ft.TextField(
            value=str(self.config.counter_start if self.config.counter_start is not None else 1),
            dense=True,
            text_size=12,
            width=150,
            border_radius=6,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            bgcolor=COLOR_CARD_DARK,
            on_change=lambda _: self._on_input_changed(),
        )

        self.lbl_counter_start = ft.Text(
            "Iniciar números en el:",
            size=12,
            color=COLOR_TEXT_PRIMARY,
            weight=ft.FontWeight.W_500,
        )

        self.format_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Text(
                                    "Formato de nombre:",
                                    size=12,
                                    color=COLOR_TEXT_PRIMARY,
                                    weight=ft.FontWeight.W_500,
                                    text_align=ft.TextAlign.RIGHT,
                                ),
                                width=140,
                            ),
                            self.format_style_dropdown,
                            ft.Container(width=16),
                            ft.Container(
                                content=ft.Text(
                                    "Ubicación:",
                                    size=12,
                                    color=COLOR_TEXT_PRIMARY,
                                    weight=ft.FontWeight.W_500,
                                    text_align=ft.TextAlign.RIGHT,
                                ),
                                width=130,
                            ),
                            self.format_location_dropdown,
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Text(
                                    "Formato personalizado:",
                                    size=12,
                                    color=COLOR_TEXT_PRIMARY,
                                    weight=ft.FontWeight.W_500,
                                    text_align=ft.TextAlign.RIGHT,
                                ),
                                width=140,
                            ),
                            self.custom_format_field,
                            ft.Container(width=16),
                            ft.Container(
                                content=self.lbl_counter_start,
                                width=130,
                                alignment=ft.Alignment.CENTER_RIGHT,
                            ),
                            self.counter_start_field,
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                ],
                spacing=10,
            ),
            padding=ft.Padding.symmetric(vertical=6),
        )

        # Footer: Example + Cancel / Rename buttons
        self.lbl_example = ft.Text(
            "Ejemplo: Archivo 00001.png",
            size=12,
            color=COLOR_TEXT_SECONDARY,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
            expand=True,
        )

        self.btn_cancel = ft.OutlinedButton(
            "Cancelar",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=6),
                side=ft.BorderSide(1, COLOR_BORDER_DARK),
                color=COLOR_TEXT_PRIMARY,
                padding=ft.Padding.symmetric(horizontal=18, vertical=8),
            ),
            on_click=lambda _: self.page.pop_dialog(),
        )

        self.btn_rename = ft.FilledButton(
            "Renombrar",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=6),
                bgcolor=COLOR_PRIMARY,
                color="#FFFFFF",
                padding=ft.Padding.symmetric(horizontal=18, vertical=8),
            ),
            on_click=lambda _: self._confirm(),
        )

        count_str = f" ({len(self.items)} seleccionados)" if self.items else ""
        subtitle_text = f"Renombrar ítems del Finder{count_str}:"

        dialog_body = ft.Container(
            content=ft.Column(
                controls=[
                    # Top Header ("Renombrar")
                    ft.Container(
                        content=ft.Text(
                            "Renombrar",
                            size=14,
                            weight=ft.FontWeight.W_700,
                            color=COLOR_TEXT_PRIMARY,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        alignment=ft.Alignment.CENTER,
                        padding=ft.Padding.only(bottom=6),
                    ),
                    ft.Divider(height=1, color=COLOR_BORDER_DARK),
                    # Subtitle bar ("Renombrar ítems del Finder:")
                    ft.Container(
                        content=ft.Text(
                            subtitle_text,
                            size=13,
                            color=COLOR_TEXT_MUTED,
                            weight=ft.FontWeight.W_500,
                        ),
                        padding=ft.Padding.symmetric(vertical=6),
                    ),
                    ft.Divider(height=1, color=COLOR_BORDER_DARK),
                    # Mode selector & Dynamic body
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                self.mode_dropdown,
                                self.replace_container,
                                self.add_text_container,
                                self.format_container,
                            ],
                            spacing=8,
                        ),
                        padding=ft.Padding.symmetric(vertical=8),
                    ),
                    ft.Divider(height=1, color=COLOR_BORDER_DARK),
                    # Footer bar: Ejemplo + Buttons
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                self.lbl_example,
                                self.btn_cancel,
                                self.btn_rename,
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=10,
                        ),
                        padding=ft.Padding.only(top=8),
                    ),
                ],
                spacing=4,
                tight=True,
            ),
            width=700,
            padding=ft.Padding.all(8),
        )

        self.dialog = ft.AlertDialog(
            content=dialog_body,
            bgcolor=COLOR_SURFACE_DARK,
            shape=ft.RoundedRectangleBorder(radius=12),
        )

    def _on_input_changed(self):
        self._sync_visibility_and_example(update_ui=True)

    def _sync_visibility_and_example(self, update_ui: bool = True):
        mode = self.mode_dropdown.value or "replace"
        self.replace_container.visible = mode == "replace"
        self.add_text_container.visible = mode == "add_text"
        self.format_container.visible = mode == "format"

        if mode == "format":
            fmt_style = self.format_style_dropdown.value or "name_counter"
            uses_numbers = fmt_style in ("name_counter", "name_index")
            self.lbl_counter_start.visible = uses_numbers
            self.counter_start_field.visible = uses_numbers

        cfg = self.get_config()
        example_str = generate_example_name(
            config=cfg,
            sample_name=self.sample_name,
            sample_mtime=self.sample_mtime,
        )
        self.lbl_example.value = f"Ejemplo: {example_str}"

        # Disable 'Renombrar' button only if in replace mode with empty find_text, or add_text with empty text
        if mode == "replace" and not cfg.find_text:
            self.btn_rename.disabled = True
        elif mode == "add_text" and not cfg.add_text:
            self.btn_rename.disabled = True
        else:
            self.btn_rename.disabled = False

        if update_ui:
            safe_update(self.dialog)

    def get_config(self) -> RenameConfig:
        start_val = 1
        try:
            raw_start = (self.counter_start_field.value or "1").strip()
            start_val = int(raw_start)
        except ValueError:
            start_val = 1

        return RenameConfig(
            mode=self.mode_dropdown.value or "replace",
            find_text=self.find_field.value or "",
            replace_text=self.replace_field.value or "",
            add_text=self.add_text_field.value or "",
            add_location=self.add_location_dropdown.value or "after",
            format_style=self.format_style_dropdown.value or "name_counter",
            format_location=self.format_location_dropdown.value or "after",
            custom_format=self.custom_format_field.value if self.custom_format_field.value is not None else "",
            counter_start=start_val,
        )

    def _confirm(self):
        cfg = self.get_config()
        self.page.pop_dialog()
        if self.on_rename_confirmed:
            self.on_rename_confirmed(cfg)

    def show(self):
        self.page.show_dialog(self.dialog)
