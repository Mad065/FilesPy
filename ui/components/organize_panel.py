"""Organize rules configuration panel for Flet."""
from typing import Callable, Dict, Set
import flet as ft

from core.models import OrganizeConfig
from ui.theme import (
    COLOR_BORDER_DARK,
    COLOR_CARD_DARK,
    COLOR_PRIMARY,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    safe_update,
)


class OrganizePanel(ft.Container):
    """Configuration panel for organizing files into subfolders."""

    def __init__(self, on_change: Callable[[OrganizeConfig], None]):
        super().__init__()
        self.on_change = on_change
        self._build_widgets()

    def _build_widgets(self):
        lbl_title = ft.Text(
            value="Clasificacion en Carpetas",
            size=11,
            weight=ft.FontWeight.W_600,
            color=COLOR_TEXT_PRIMARY,
        )

        self.mode_dropdown = ft.Dropdown(
            label="Modo de Organizacion",
            value="none",
            dense=True,
            text_size=11,
            label_style=ft.TextStyle(size=10, color=COLOR_TEXT_MUTED),
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            options=[
                ft.dropdown.Option("none", "Desactivado (Sin mover)"),
                ft.dropdown.Option("by_extension", "Por Extension (PDF, JPG, TXT)"),
                ft.dropdown.Option("by_category", "Por Categorias (Documentos, Fotos...)"),
                ft.dropdown.Option("by_date", "Por Fecha de Modificacion (Ano/Mes)"),
            ],
            on_select=self._on_mode_changed,
        )

        self.desc_text = ft.Text(
            value="Los archivos permaneceran en su ubicacion original.",
            size=10,
            color=COLOR_TEXT_MUTED,
        )

        self.desc_box = ft.Container(
            content=self.desc_text,
            bgcolor=COLOR_CARD_DARK,
            border_radius=8,
            padding=8,
            border=ft.Border.all(1, COLOR_BORDER_DARK),
        )

        self.categories_text = ft.Text(
            value="",
            size=9.5,
            color=COLOR_TEXT_MUTED,
        )

        self.categories_box = ft.Container(
            content=self.categories_text,
            bgcolor=COLOR_CARD_DARK,
            border_radius=8,
            padding=8,
            border=ft.Border.all(1, COLOR_BORDER_DARK),
        )

        self.padding = ft.Padding.all(12)
        self.content = ft.Column(
            controls=[
                lbl_title,
                self.mode_dropdown,
                self.desc_box,
                ft.Container(height=4),
                self.categories_box,
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )

    def _on_mode_changed(self, e):
        mode_val = self.mode_dropdown.value or "none"
        if mode_val == "none":
            self.desc_text.value = "Los archivos permaneceran en su ubicacion original."
        elif mode_val == "by_extension":
            self.desc_text.value = "Crea subcarpetas con el nombre de cada extension (ej: /PDF, /JPG)."
        elif mode_val == "by_category":
            self.desc_text.value = "Agrupa segun la categoria del archivo (Documentos, Imagenes, etc.)."
        elif mode_val == "by_date":
            self.desc_text.value = "Crea subcarpetas por ano y mes (ej: /2026/10) segun fecha del archivo."

        safe_update(self.desc_box)
        config = self.get_config()
        self.on_change(config)

    def update_categories_info(self, categories: Dict[str, Set[str]]):
        lines = ["Categorias configuradas:"]
        for cat_name, exts in list(categories.items())[:6]:
            ext_str = ", ".join(sorted([e.lstrip(".").upper() for e in exts])[:4])
            if len(exts) > 4:
                ext_str += "..."
            lines.append(f"- {cat_name}: {ext_str}")
        if len(categories) > 6:
            lines.append(f"...y {len(categories) - 6} categoria(s) mas")

        self.categories_text.value = "\n".join(lines)
        safe_update(self.categories_box)

    def get_config(self) -> OrganizeConfig:
        mode_val = self.mode_dropdown.value or "none"
        return OrganizeConfig(mode=mode_val)

    def reset_rules(self):
        self.mode_dropdown.value = "none"
        self._on_mode_changed(None)
