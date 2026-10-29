"""Preview table component showing before/after filenames, destinations, and status in Flet."""
from typing import Callable, List, Optional
import flet as ft

from core.models import FileItem, FileStatus
from ui.theme import (
    COLOR_BORDER_DARK,
    COLOR_CARD_DARK,
    COLOR_DANGER,
    COLOR_PRIMARY,
    COLOR_SUCCESS,
    COLOR_SURFACE_DARK,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    format_bytes,
    safe_update,
)


class PreviewTable(ft.Container):
    """Scrollable table displaying original names, new names, target paths, and status badges."""

    def __init__(
        self,
        on_item_inspected: Callable[[FileItem], None],
        on_selection_toggled: Callable[[], None],
    ):
        super().__init__()
        self.on_item_inspected = on_item_inspected
        self.on_selection_toggled = on_selection_toggled
        self.items: List[FileItem] = []

        self._build_header()
        self._build_table_view()

    def _build_header(self):
        self.chk_all = ft.Checkbox(
            value=True,
            active_color=COLOR_PRIMARY,
            on_change=self._on_toggle_all,
        )

        self.header_row = ft.Container(
            content=ft.Row(
                controls=[
                    self.chk_all,
                    ft.Container(content=ft.Text("Nombre Original", weight=ft.FontWeight.W_600, size=11, color=COLOR_TEXT_MUTED), width=220),
                    ft.Container(width=20),
                    ft.Container(content=ft.Text("Nuevo Nombre", weight=ft.FontWeight.W_600, size=11, color=COLOR_TEXT_MUTED), width=220),
                    ft.Container(content=ft.Text("Carpeta Destino", weight=ft.FontWeight.W_600, size=11, color=COLOR_TEXT_MUTED), width=150),
                    ft.Container(content=ft.Text("Tamano", weight=ft.FontWeight.W_600, size=11, color=COLOR_TEXT_MUTED, text_align=ft.TextAlign.RIGHT), width=75),
                    ft.Container(content=ft.Text("Estado", weight=ft.FontWeight.W_600, size=11, color=COLOR_TEXT_MUTED, text_align=ft.TextAlign.CENTER), width=90),
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=COLOR_CARD_DARK,
            padding=ft.Padding.symmetric(horizontal=10, vertical=6),
            border_radius=8,
            border=ft.Border.all(1, COLOR_BORDER_DARK),
            width=880,
        )

    def _build_table_view(self):
        self.empty_view = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.FOLDER_OPEN_OUTLINED, size=40, color=COLOR_TEXT_MUTED),
                    ft.Text(
                        value="Ningun archivo cargado.\nSelecciona una carpeta arriba para comenzar.",
                        size=12,
                        color=COLOR_TEXT_MUTED,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            alignment=ft.Alignment.CENTER,
            expand=True,
        )

        self.list_view = ft.ListView(
            expand=True,
            spacing=4,
            padding=ft.Padding.symmetric(vertical=4),
        )

        self.table_column = ft.Column(
            controls=[
                self.header_row,
                ft.Container(content=self.empty_view, expand=True),
            ],
            spacing=4,
            expand=True,
            width=880,
        )

        self.expand = True
        self.content = ft.Row(
            controls=[self.table_column],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def set_items(self, items: List[FileItem]):
        self.items = items
        self.list_view.controls.clear()

        if not items:
            self.table_column.controls[1] = ft.Container(content=self.empty_view, expand=True)
            safe_update(self)
            return

        for idx, item in enumerate(items):
            row_ctrl = self._create_row(idx, item)
            self.list_view.controls.append(row_ctrl)

        self.table_column.controls[1] = ft.Container(content=self.list_view, expand=True)
        safe_update(self)

    def _create_row(self, idx: int, item: FileItem) -> ft.Container:
        chk = ft.Checkbox(
            value=item.selected,
            active_color=COLOR_PRIMARY,
            on_change=lambda e, it=item: self._on_item_checked(it, e.control.value),
        )

        # New Name Styling:
        if item.has_conflict:
            new_name_color = COLOR_DANGER
            new_name_weight = ft.FontWeight.W_600
        elif item.is_modified:
            new_name_color = COLOR_PRIMARY
            new_name_weight = ft.FontWeight.W_600
        else:
            new_name_color = COLOR_TEXT_MUTED
            new_name_weight = ft.FontWeight.NORMAL

        badge_text, badge_bg, badge_fg = self._get_status_badge(item)

        status_chip = ft.Container(
            content=ft.Text(badge_text, size=9.5, weight=ft.FontWeight.W_600, color=badge_fg),
            bgcolor=badge_bg,
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=6, vertical=3),
            alignment=ft.Alignment.CENTER,
            width=90,
        )

        row_content = ft.Row(
            controls=[
                chk,
                ft.Container(
                    content=ft.Text(item.original_name, size=11, color=COLOR_TEXT_PRIMARY, overflow=ft.TextOverflow.ELLIPSIS),
                    width=220,
                ),
                ft.Container(
                    content=ft.Text("->", size=10, color=COLOR_PRIMARY if item.is_modified else COLOR_TEXT_MUTED),
                    width=20,
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Container(
                    content=ft.Text(item.new_name, size=11, color=new_name_color, weight=new_name_weight, overflow=ft.TextOverflow.ELLIPSIS),
                    width=220,
                ),
                ft.Container(
                    content=ft.Text(item.target_folder.name or "/", size=11, color=COLOR_TEXT_MUTED, overflow=ft.TextOverflow.ELLIPSIS),
                    width=150,
                ),
                ft.Container(
                    content=ft.Text(format_bytes(item.size_bytes), size=10.5, color=COLOR_TEXT_MUTED, text_align=ft.TextAlign.RIGHT),
                    width=75,
                ),
                status_chip,
            ],
            spacing=6,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        row_container = ft.Container(
            content=row_content,
            bgcolor=COLOR_SURFACE_DARK if idx % 2 == 0 else COLOR_CARD_DARK,
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            width=880,
            on_click=lambda _, it=item: self.on_item_inspected(it),
            ink=True,
        )
        return row_container

    def _get_status_badge(self, item: FileItem):
        if item.has_conflict:
            return "Conflicto", "#380f12", COLOR_DANGER
        elif item.status == FileStatus.READY or item.is_modified:
            return "Listo", "#0d3320", COLOR_SUCCESS
        else:
            return "Sin cambio", "#1e2433", COLOR_TEXT_MUTED

    def _on_item_checked(self, item: FileItem, checked: bool):
        item.selected = checked
        self.on_selection_toggled()

    def _on_toggle_all(self, e):
        val = bool(self.chk_all.value)
        for it in self.items:
            it.selected = val
        self.set_items(self.items)
        self.on_selection_toggled()
