"""Duplicate finder panel component for Flet."""
from typing import Callable, Dict, List
import flet as ft

from core.models import FileItem
from core.duplicates import find_duplicates
from ui.theme import (
    COLOR_BORDER_DARK,
    COLOR_CARD_DARK,
    COLOR_PRIMARY,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_WARNING,
    format_bytes,
    safe_update,
)


class DuplicatePanel(ft.Container):
    """Panel to search and manage duplicate files using SHA-256."""

    def __init__(
        self,
        get_current_items: Callable[[], List[FileItem]],
        on_isolate_duplicates: Callable[[List[FileItem]], None],
    ):
        super().__init__()
        self.get_current_items = get_current_items
        self.on_isolate_duplicates = on_isolate_duplicates
        self.duplicate_groups: Dict[str, List[FileItem]] = {}

        self._build_widgets()

    def _build_widgets(self):
        lbl_title = ft.Text(
            value="Deteccion de Duplicados",
            size=13,
            weight=ft.FontWeight.W_600,
            color=COLOR_TEXT_PRIMARY,
        )

        lbl_desc = ft.Text(
            value=(
                "Compara los archivos por su contenido real "
                "(hash criptografico SHA-256), independientemente "
                "de si tienen nombres distintos."
            ),
            size=11,
            color=COLOR_TEXT_MUTED,
        )

        self.btn_scan = ft.Button(
            "Buscar Duplicados",
            icon=ft.Icons.SEARCH_OUTLINED,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                color=COLOR_TEXT_PRIMARY,
                bgcolor=COLOR_CARD_DARK,
            ),
            on_click=self._scan_duplicates,
        )

        self.result_text = ft.Text(
            value="Sin escanear aun.",
            size=11,
            color=COLOR_TEXT_MUTED,
            text_align=ft.TextAlign.CENTER,
        )

        self.results_box = ft.Container(
            content=self.result_text,
            bgcolor=COLOR_CARD_DARK,
            border_radius=8,
            padding=10,
            border=ft.Border.all(1, COLOR_BORDER_DARK),
            alignment=ft.Alignment.CENTER,
        )

        self.btn_isolate = ft.FilledButton(
            "Mover Copias a _Duplicados",
            icon=ft.Icons.COPY_ALL_OUTLINED,
            disabled=True,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                color="#FFFFFF",
                bgcolor=COLOR_WARNING,
            ),
            on_click=lambda _: self._isolate(),
        )

        self.padding = ft.Padding.all(12)
        self.content = ft.Column(
            controls=[
                lbl_title,
                lbl_desc,
                self.btn_scan,
                self.results_box,
                self.btn_isolate,
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )

    def _scan_duplicates(self, e):
        items = self.get_current_items()
        if not items:
            self.result_text.value = "No hay archivos cargados para escanear."
            safe_update(self.results_box)
            return

        self.btn_scan.disabled = True
        self.btn_scan.content = "Calculando hashes..."
        safe_update(self.btn_scan)

        self.duplicate_groups = find_duplicates(items)
        group_count = len(self.duplicate_groups)

        if group_count == 0:
            self.result_text.value = "No se encontraron archivos duplicados."
            self.btn_isolate.disabled = True
        else:
            total_dup_files = sum(len(grp) - 1 for grp in self.duplicate_groups.values())
            wasted_bytes = sum((len(grp) - 1) * grp[0].size_bytes for grp in self.duplicate_groups.values())

            self.result_text.value = (
                f"Se encontraron {group_count} grupos de duplicados.\n"
                f"Copias repetidas: {total_dup_files}\n"
                f"Espacio recuperable: {format_bytes(wasted_bytes)}"
            )
            self.btn_isolate.disabled = False

        self.btn_scan.disabled = False
        self.btn_scan.content = "Buscar Duplicados"
        safe_update(self)

    def _isolate(self):
        items_to_move: List[FileItem] = []
        for grp in self.duplicate_groups.values():
            for copy_item in grp[1:]:
                items_to_move.append(copy_item)

        if items_to_move:
            self.on_isolate_duplicates(items_to_move)
