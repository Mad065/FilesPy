"""Rename rules configuration panel for Flet."""
from typing import Callable
import flet as ft

from core.models import RenameConfig
from ui.theme import (
    COLOR_BORDER_DARK,
    COLOR_CARD_DARK,
    COLOR_PRIMARY,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    safe_update,
)


class RenamePanel(ft.Container):
    """Configuration panel for batch file renaming rules."""

    def __init__(self, on_change: Callable[[RenameConfig], None]):
        super().__init__()
        self.on_change = on_change
        self._build_widgets()

    def _build_widgets(self):
        # 1. Text Replacement
        self.find_field = ft.TextField(
            label="Buscar texto",
            dense=True,
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            on_change=lambda _: self._trigger_change(),
        )

        self.replace_field = ft.TextField(
            label="Reemplazar con",
            dense=True,
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            on_change=lambda _: self._trigger_change(),
        )

        self.chk_match_case = ft.Checkbox(
            label="Mayus/Minus",
            value=False,
            active_color=COLOR_PRIMARY,
            label_style=ft.TextStyle(size=12, color=COLOR_TEXT_MUTED),
            on_change=lambda _: self._trigger_change(),
        )

        self.chk_regex = ft.Checkbox(
            label="Regex",
            value=False,
            active_color=COLOR_PRIMARY,
            label_style=ft.TextStyle(size=12, color=COLOR_TEXT_MUTED),
            on_change=lambda _: self._trigger_change(),
        )

        # 2. Prefix and Suffix
        self.prefix_field = ft.TextField(
            label="Prefijo (al inicio)",
            dense=True,
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            on_change=lambda _: self._trigger_change(),
        )

        self.suffix_field = ft.TextField(
            label="Sufijo (al final)",
            dense=True,
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            on_change=lambda _: self._trigger_change(),
        )

        # 3. Numbering
        self.chk_numbering = ft.Checkbox(
            label="Numeracion Secuencial",
            value=False,
            active_color=COLOR_PRIMARY,
            label_style=ft.TextStyle(size=12, weight=ft.FontWeight.W_600, color=COLOR_TEXT_PRIMARY),
            on_change=lambda _: self._trigger_change(),
        )

        self.start_field = ft.TextField(
            label="Inicio",
            value="1",
            dense=True,
            width=70,
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            on_change=lambda _: self._trigger_change(),
        )

        self.digits_dropdown = ft.Dropdown(
            label="Digitos",
            value="3",
            dense=True,
            width=85,
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            options=[
                ft.dropdown.Option("1"),
                ft.dropdown.Option("2"),
                ft.dropdown.Option("3"),
                ft.dropdown.Option("4"),
                ft.dropdown.Option("5"),
            ],
            on_select=lambda _: self._trigger_change(),
        )

        # 4. Case Mode
        self.case_dropdown = ft.Dropdown(
            label="Mayusculas / Minusculas",
            value="original",
            dense=True,
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            options=[
                ft.dropdown.Option("original", "Original (Sin cambio)"),
                ft.dropdown.Option("lower", "minusculas"),
                ft.dropdown.Option("upper", "MAYUSCULAS"),
                ft.dropdown.Option("title", "Titulo (Capitalize)"),
                ft.dropdown.Option("snake", "snake_case"),
                ft.dropdown.Option("kebab", "kebab-case"),
            ],
            on_select=lambda _: self._trigger_change(),
        )

        # 5. Extension
        self.ext_field = ft.TextField(
            label="Cambiar extension (opcional)",
            hint_text="ej. jpg o png",
            dense=True,
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            on_change=lambda _: self._trigger_change(),
        )

        # 6. Reset
        self.btn_reset = ft.OutlinedButton(
            "Restablecer Reglas",
            icon=ft.Icons.RESTART_ALT_OUTLINED,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(1, COLOR_BORDER_DARK),
                color=COLOR_TEXT_MUTED,
            ),
            on_click=lambda _: self.reset_rules(),
        )

        self.padding = ft.Padding.all(12)
        self.content = ft.Column(
            controls=[
                self.find_field,
                self.replace_field,
                ft.Row([self.chk_match_case, self.chk_regex], spacing=10),
                ft.Divider(height=1, color=COLOR_BORDER_DARK),
                self.prefix_field,
                self.suffix_field,
                ft.Divider(height=1, color=COLOR_BORDER_DARK),
                self.chk_numbering,
                ft.Row([self.start_field, self.digits_dropdown], spacing=10),
                ft.Divider(height=1, color=COLOR_BORDER_DARK),
                self.case_dropdown,
                self.ext_field,
                ft.Container(height=4),
                self.btn_reset,
            ],
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
        )

    def _trigger_change(self):
        config = self.get_config()
        self.on_change(config)

    def get_config(self) -> RenameConfig:
        start_val = 1
        try:
            start_val = int(self.start_field.value.strip()) if self.start_field.value else 1
        except ValueError:
            start_val = 1

        digits_val = 3
        try:
            digits_val = int(self.digits_dropdown.value) if self.digits_dropdown.value else 3
        except ValueError:
            digits_val = 3

        return RenameConfig(
            find_text=self.find_field.value or "",
            replace_text=self.replace_field.value or "",
            match_case=bool(self.chk_match_case.value),
            use_regex=bool(self.chk_regex.value),
            prefix=self.prefix_field.value or "",
            suffix=self.suffix_field.value or "",
            numbering_enabled=bool(self.chk_numbering.value),
            numbering_start=start_val,
            numbering_digits=digits_val,
            case_mode=self.case_dropdown.value or "original",
            preserve_extension=True,
            custom_extension=(self.ext_field.value or "").strip(),
        )

    def reset_rules(self):
        self.find_field.value = ""
        self.replace_field.value = ""
        self.chk_match_case.value = False
        self.chk_regex.value = False
        self.prefix_field.value = ""
        self.suffix_field.value = ""
        self.chk_numbering.value = False
        self.start_field.value = "1"
        self.digits_dropdown.value = "3"
        self.case_dropdown.value = "original"
        self.ext_field.value = ""
        safe_update(self)
        self._trigger_change()
