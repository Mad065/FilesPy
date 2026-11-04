"""macOS Finder-style batch rename configuration panel for Flet."""
from typing import Callable, Optional
import flet as ft

from core.models import RenameConfig
from core.renamer import generate_example_name
from ui.theme import (
    COLOR_BORDER_DARK,
    COLOR_CARD_DARK,
    COLOR_PRIMARY,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    safe_update,
)


class RenamePanel(ft.Container):
    """Configuration panel for batch file renaming modeled after Apple macOS Finder."""

    def __init__(
        self,
        on_change: Callable[[RenameConfig], None],
        on_open_mac_dialog: Optional[Callable[[], None]] = None,
    ):
        super().__init__()
        self.on_change = on_change
        self.on_open_mac_dialog = on_open_mac_dialog
        self.sample_name: str = "Captura de pantalla 2022-12-21 a las 15.3.png"
        self.sample_mtime: float = 1671658230.0
        self._build_widgets()
        self._sync_visibility_and_example(update_ui=False)

    def _build_widgets(self):
        # Header
        self.lbl_header = ft.Text(
            "Renombrar ítems:",
            size=12,
            weight=ft.FontWeight.W_600,
            color=COLOR_TEXT_SECONDARY,
        )

        # 0. Primary Mode Selector: Reemplazar texto | Agregar texto | Formato
        self.mode_dropdown = ft.Dropdown(
            value="replace",
            dense=True,
            text_size=11.5,
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            bgcolor=COLOR_CARD_DARK,
            options=[
                ft.dropdown.Option("replace", "Reemplazar texto"),
                ft.dropdown.Option("add_text", "Agregar texto"),
                ft.dropdown.Option("format", "Formato"),
            ],
            on_select=lambda _: self._on_mode_or_field_changed(),
        )

        # --- MODE 1: REEMPLAZAR TEXTO ---
        self.find_field = ft.TextField(
            label="Buscar:",
            dense=True,
            text_size=11,
            label_style=ft.TextStyle(size=10.5, color=COLOR_TEXT_MUTED),
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            bgcolor=COLOR_CARD_DARK,
            on_change=lambda _: self._on_mode_or_field_changed(),
        )

        self.replace_field = ft.TextField(
            label="Reemplazar por:",
            dense=True,
            text_size=11,
            label_style=ft.TextStyle(size=10.5, color=COLOR_TEXT_MUTED),
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            bgcolor=COLOR_CARD_DARK,
            on_change=lambda _: self._on_mode_or_field_changed(),
        )

        self.replace_section = ft.Column(
            controls=[
                self.find_field,
                self.replace_field,
            ],
            spacing=8,
        )

        # --- MODE 2: AGREGAR TEXTO ---
        self.add_text_field = ft.TextField(
            label="Agregar texto:",
            dense=True,
            text_size=11,
            label_style=ft.TextStyle(size=10.5, color=COLOR_TEXT_MUTED),
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            bgcolor=COLOR_CARD_DARK,
            on_change=lambda _: self._on_mode_or_field_changed(),
        )

        self.add_location_dropdown = ft.Dropdown(
            label="Ubicación:",
            value="after",
            dense=True,
            text_size=11,
            label_style=ft.TextStyle(size=10.5, color=COLOR_TEXT_MUTED),
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            bgcolor=COLOR_CARD_DARK,
            options=[
                ft.dropdown.Option("after", "Después del nombre"),
                ft.dropdown.Option("before", "Antes del nombre"),
            ],
            on_select=lambda _: self._on_mode_or_field_changed(),
        )

        self.add_text_section = ft.Column(
            controls=[
                self.add_text_field,
                self.add_location_dropdown,
            ],
            spacing=8,
        )

        # --- MODE 3: FORMATO ---
        self.format_style_dropdown = ft.Dropdown(
            label="Formato de nombre:",
            value="name_counter",
            dense=True,
            text_size=11,
            label_style=ft.TextStyle(size=10.5, color=COLOR_TEXT_MUTED),
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            bgcolor=COLOR_CARD_DARK,
            options=[
                ft.dropdown.Option("name_counter", "Nombre y contador"),
                ft.dropdown.Option("name_index", "Nombre e índice"),
                ft.dropdown.Option("name_date", "Nombre y fecha"),
            ],
            on_select=lambda _: self._on_mode_or_field_changed(),
        )

        self.format_location_dropdown = ft.Dropdown(
            label="Ubicación:",
            value="after",
            dense=True,
            text_size=11,
            label_style=ft.TextStyle(size=10.5, color=COLOR_TEXT_MUTED),
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            bgcolor=COLOR_CARD_DARK,
            options=[
                ft.dropdown.Option("after", "Después del nombre"),
                ft.dropdown.Option("before", "Antes del nombre"),
            ],
            on_select=lambda _: self._on_mode_or_field_changed(),
        )

        self.custom_format_field = ft.TextField(
            label="Formato personalizado:",
            value="Archivo",
            dense=True,
            text_size=11,
            label_style=ft.TextStyle(size=10.5, color=COLOR_TEXT_MUTED),
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            bgcolor=COLOR_CARD_DARK,
            on_change=lambda _: self._on_mode_or_field_changed(),
        )

        self.counter_start_field = ft.TextField(
            label="Iniciar números en el:",
            value="1",
            dense=True,
            text_size=11,
            label_style=ft.TextStyle(size=10.5, color=COLOR_TEXT_MUTED),
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            bgcolor=COLOR_CARD_DARK,
            on_change=lambda _: self._on_mode_or_field_changed(),
        )

        self.format_section = ft.Column(
            controls=[
                self.format_style_dropdown,
                self.format_location_dropdown,
                self.custom_format_field,
                self.counter_start_field,
            ],
            spacing=8,
        )

        # Live Example Card ("Ejemplo: Archivo 00001.png")
        self.lbl_example = ft.Text(
            "Ejemplo: Captura de pantalla 2022-12-21 a las 15.3.png",
            size=11,
            color=COLOR_TEXT_PRIMARY,
            weight=ft.FontWeight.W_500,
            max_lines=2,
            overflow=ft.TextOverflow.ELLIPSIS,
        )

        self.example_box = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.VISIBILITY_OUTLINED, size=14, color=COLOR_PRIMARY),
                    ft.Container(content=self.lbl_example, expand=True),
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=COLOR_CARD_DARK,
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=10, vertical=8),
            border=ft.Border.all(1, COLOR_BORDER_DARK),
        )

        # Open floating Mac dialog button
        self.btn_open_dialog = ft.OutlinedButton(
            "Ventana Renombrar (Mac)",
            icon=ft.Icons.OPEN_IN_NEW_ROUNDED,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(1, COLOR_PRIMARY),
                color=COLOR_TEXT_PRIMARY,
                text_style=ft.TextStyle(size=10.5, weight=ft.FontWeight.W_500),
            ),
            on_click=lambda _: self.on_open_mac_dialog() if self.on_open_mac_dialog else None,
        )

        # Reset button
        self.btn_reset = ft.OutlinedButton(
            "Restablecer",
            icon=ft.Icons.RESTART_ALT_OUTLINED,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(1, COLOR_BORDER_DARK),
                color=COLOR_TEXT_MUTED,
                text_style=ft.TextStyle(size=10),
            ),
            on_click=lambda _: self.reset_rules(),
        )

        self.padding = ft.Padding.all(12)
        self.content = ft.Column(
            controls=[
                self.lbl_header,
                self.mode_dropdown,
                ft.Divider(height=1, color=COLOR_BORDER_DARK),
                self.replace_section,
                self.add_text_section,
                self.format_section,
                ft.Divider(height=1, color=COLOR_BORDER_DARK),
                self.example_box,
                ft.Container(height=2),
                self.btn_open_dialog,
                self.btn_reset,
            ],
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
        )

    def _on_mode_or_field_changed(self):
        self._sync_visibility_and_example(update_ui=True)
        self._trigger_change()

    def _sync_visibility_and_example(self, update_ui: bool = True):
        mode = self.mode_dropdown.value or "replace"
        self.replace_section.visible = mode == "replace"
        self.add_text_section.visible = mode == "add_text"
        self.format_section.visible = mode == "format"

        if mode == "format":
            fmt_style = self.format_style_dropdown.value or "name_counter"
            self.counter_start_field.visible = fmt_style in ("name_counter", "name_index")

        cfg = self.get_config()
        example_str = generate_example_name(
            config=cfg,
            sample_name=self.sample_name,
            sample_mtime=self.sample_mtime,
        )
        self.lbl_example.value = f"Ejemplo: {example_str}"

        if update_ui:
            safe_update(self)

    def update_sample(self, sample_name: Optional[str] = None, sample_mtime: Optional[float] = None):
        """Updates the sample file used for the real-time 'Ejemplo:' preview."""
        if sample_name:
            self.sample_name = sample_name
            self.sample_mtime = sample_mtime if sample_mtime is not None else 1671658230.0
        else:
            self.sample_name = "Captura de pantalla 2022-12-21 a las 15.3.png"
            self.sample_mtime = 1671658230.0
        self._sync_visibility_and_example(update_ui=True)

    def _trigger_change(self):
        config = self.get_config()
        self.on_change(config)

    def get_config(self) -> RenameConfig:
        start_val = 1
        try:
            raw = (self.counter_start_field.value or "1").strip()
            start_val = int(raw)
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

    def set_config(self, config: RenameConfig):
        """Synchronizes panel controls with an external RenameConfig."""
        self.mode_dropdown.value = config.mode or "replace"
        self.find_field.value = config.find_text or ""
        self.replace_field.value = config.replace_text or ""
        self.add_text_field.value = config.add_text or ""
        self.add_location_dropdown.value = config.add_location or "after"
        self.format_style_dropdown.value = config.format_style or "name_counter"
        self.format_location_dropdown.value = config.format_location or "after"
        self.custom_format_field.value = config.custom_format if config.custom_format is not None else "Archivo"
        self.counter_start_field.value = str(config.counter_start if config.counter_start is not None else 1)
        self._sync_visibility_and_example(update_ui=True)

    def reset_rules(self):
        self.mode_dropdown.value = "replace"
        self.find_field.value = ""
        self.replace_field.value = ""
        self.add_text_field.value = ""
        self.add_location_dropdown.value = "after"
        self.format_style_dropdown.value = "name_counter"
        self.format_location_dropdown.value = "after"
        self.custom_format_field.value = "Archivo"
        self.counter_start_field.value = "1"
        self._sync_visibility_and_example(update_ui=True)
        self._trigger_change()
