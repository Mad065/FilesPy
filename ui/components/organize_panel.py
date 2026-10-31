"""Organize rules configuration panel for Flet."""
from typing import Callable, Dict, List, Optional, Set
import flet as ft

from core.models import OrganizeConfig
from ui.theme import (
    COLOR_BORDER_DARK,
    COLOR_CARD_DARK,
    COLOR_DANGER,
    COLOR_PRIMARY,
    COLOR_SURFACE_DARK,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    safe_update,
)


class OrganizePanel(ft.Container):
    """Configuration panel for organizing files into subfolders."""

    def __init__(
        self,
        on_change: Callable[[OrganizeConfig], None],
        on_start_manual_organize: Optional[Callable[[], None]] = None,
        initial_manual_folders: Optional[List[str]] = None,
        on_manual_folders_changed: Optional[Callable[[List[str]], None]] = None,
    ):
        super().__init__()
        self.on_change = on_change
        self.on_start_manual_organize = on_start_manual_organize
        self.manual_folders = list(initial_manual_folders) if initial_manual_folders else [
            "Documentos", "Imágenes", "Facturas", "Trabajo", "Personal"
        ]
        self.on_manual_folders_changed = on_manual_folders_changed
        self._build_widgets()

    def _build_widgets(self):
        lbl_title = ft.Text(
            value="Clasificación en Carpetas",
            size=11,
            weight=ft.FontWeight.W_600,
            color=COLOR_TEXT_PRIMARY,
        )

        self.mode_dropdown = ft.Dropdown(
            label="Modo de Organización",
            value="none",
            dense=True,
            text_size=11,
            label_style=ft.TextStyle(size=10, color=COLOR_TEXT_MUTED),
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            options=[
                ft.dropdown.Option("none", "Desactivado (Sin mover)"),
                ft.dropdown.Option("manual", "Organización Manual Personalizada"),
                ft.dropdown.Option("by_extension", "Por Extensión (PDF, JPG, TXT)"),
                ft.dropdown.Option("by_category", "Por Categorías (Documentos, Fotos...)"),
                ft.dropdown.Option("by_date", "Por Fecha de Modificación (Año/Mes)"),
            ],
            on_select=self._on_mode_changed,
        )

        self.desc_text = ft.Text(
            value="Los archivos permanecerán en su ubicación original.",
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

        # Automatic categories info box
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
            visible=False,
        )

        # Manual organization section
        self.txt_new_folder = ft.TextField(
            hint_text="Nueva carpeta (ej: Facturas)...",
            dense=True,
            text_size=10.5,
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            expand=True,
            on_submit=lambda _: self._on_add_folder(),
        )

        self.btn_add_folder = ft.IconButton(
            icon=ft.Icons.ADD,
            icon_color=COLOR_PRIMARY,
            tooltip="Agregar carpeta a la lista",
            on_click=lambda _: self._on_add_folder(),
        )

        self.folders_chips_row = ft.Row(
            controls=[],
            wrap=True,
            spacing=6,
            run_spacing=6,
        )

        self.btn_start_manual = ft.FilledButton(
            "🚀 Iniciar Recorrido Manual",
            icon=ft.Icons.CHECKLIST_RTL,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                bgcolor=COLOR_PRIMARY,
                color="#FFFFFF",
            ),
            tooltip="Abrir diálogo para recorrer cada archivo y decidir su carpeta y nombre",
            on_click=lambda _: self._on_start_manual_clicked(),
        )

        self.manual_box = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Carpetas de destino configuradas:", size=10, weight=ft.FontWeight.W_600, color=COLOR_TEXT_SECONDARY),
                    ft.Row(controls=[self.txt_new_folder, self.btn_add_folder], spacing=4),
                    self.folders_chips_row,
                    ft.Container(height=4),
                    self.btn_start_manual,
                ],
                spacing=8,
            ),
            bgcolor=COLOR_CARD_DARK,
            border_radius=8,
            padding=8,
            border=ft.Border.all(1, COLOR_BORDER_DARK),
            visible=False,
        )

        self._render_chips()

        self.padding = ft.Padding.all(12)
        self.content = ft.Column(
            controls=[
                lbl_title,
                self.mode_dropdown,
                self.desc_box,
                self.manual_box,
                self.categories_box,
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )

    def _render_chips(self):
        chips: List[ft.Control] = []
        for f in self.manual_folders:
            def make_chip(folder_name=f):
                return ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.FOLDER_OUTLINED, size=13, color=COLOR_PRIMARY),
                            ft.Text(folder_name, size=10, color=COLOR_TEXT_PRIMARY),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_size=11,
                                icon_color=COLOR_TEXT_MUTED,
                                tooltip=f"Eliminar {folder_name}",
                                on_click=lambda _: self._on_remove_folder(folder_name),
                            ),
                        ],
                        spacing=2,
                        tight=True,
                    ),
                    bgcolor=COLOR_SURFACE_DARK,
                    border_radius=12,
                    padding=ft.Padding.only(left=8, right=2, top=1, bottom=1),
                    border=ft.Border.all(1, COLOR_BORDER_DARK),
                )
            chips.append(make_chip())
        self.folders_chips_row.controls = chips

    def _on_add_folder(self):
        val = (self.txt_new_folder.value or "").strip().strip("/\\")
        if val and val not in self.manual_folders:
            self.manual_folders.append(val)
            self._render_chips()
            safe_update(self.manual_box)
            if self.on_manual_folders_changed:
                self.on_manual_folders_changed(self.manual_folders)
        self.txt_new_folder.value = ""
        safe_update(self.txt_new_folder)

    def _on_remove_folder(self, folder_name: str):
        if folder_name in self.manual_folders:
            self.manual_folders.remove(folder_name)
            self._render_chips()
            safe_update(self.manual_box)
            if self.on_manual_folders_changed:
                self.on_manual_folders_changed(self.manual_folders)

    def set_manual_folders(self, folders: List[str]):
        self.manual_folders = list(folders)
        self._render_chips()
        safe_update(self.manual_box)

    def _on_start_manual_clicked(self):
        if self.on_start_manual_organize:
            self.on_start_manual_organize()

    def _on_mode_changed(self, e):
        mode_val = self.mode_dropdown.value or "none"
        if mode_val == "none":
            self.desc_text.value = "Los archivos permanecerán en su ubicación original."
            self.manual_box.visible = False
            self.categories_box.visible = False
        elif mode_val == "manual":
            self.desc_text.value = "Define tus carpetas y recorre cada archivo para decidir su destino y nombre."
            self.manual_box.visible = True
            self.categories_box.visible = False
        elif mode_val == "by_extension":
            self.desc_text.value = "Crea subcarpetas con el nombre de cada extensión (ej: /PDF, /JPG)."
            self.manual_box.visible = False
            self.categories_box.visible = False
        elif mode_val == "by_category":
            self.desc_text.value = "Agrupa según la categoría del archivo (Documentos, Imágenes, etc.)."
            self.manual_box.visible = False
            self.categories_box.visible = True
        elif mode_val == "by_date":
            self.desc_text.value = "Crea subcarpetas por año y mes (ej: /2026/10) según fecha del archivo."
            self.manual_box.visible = False
            self.categories_box.visible = False

        safe_update(self.desc_box)
        safe_update(self.manual_box)
        safe_update(self.categories_box)
        config = self.get_config()
        self.on_change(config)

    def update_categories_info(self, categories: Dict[str, Set[str]]):
        lines = ["Categorías configuradas:"]
        for cat_name, exts in list(categories.items())[:6]:
            ext_str = ", ".join(sorted([e.lstrip(".").upper() for e in exts])[:4])
            if len(exts) > 4:
                ext_str += "..."
            lines.append(f"- {cat_name}: {ext_str}")
        if len(categories) > 6:
            lines.append(f"...y {len(categories) - 6} categoría(s) más")

        self.categories_text.value = "\n".join(lines)
        safe_update(self.categories_box)

    def get_config(self) -> OrganizeConfig:
        mode_val = self.mode_dropdown.value or "none"
        return OrganizeConfig(
            mode=mode_val,
            manual_folders=list(self.manual_folders),
        )

    def reset_rules(self):
        self.mode_dropdown.value = "none"
        self._on_mode_changed(None)
