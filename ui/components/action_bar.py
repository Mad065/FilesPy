"""Action bar component containing execution, preview, and undo buttons in Flet."""
from typing import Callable, Optional
import flet as ft

from ui.theme import (
    COLOR_BORDER_DARK,
    COLOR_DANGER,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_SUCCESS,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    safe_update,
)


class ActionBar(ft.Container):
    """Bottom action bar with primary execution buttons and summary status."""

    def __init__(
        self,
        on_refresh: Callable[[], None],
        on_apply: Callable[[], None],
        on_undo: Callable[[], None],
        on_step_review: Callable[[], None],
        on_manual_organize: Optional[Callable[[], None]] = None,
    ):
        super().__init__()
        self.on_refresh = on_refresh
        self.on_apply = on_apply
        self.on_undo = on_undo
        self.on_step_review = on_step_review
        self.on_manual_organize = on_manual_organize

        self._build_widgets()

    def _build_widgets(self):
        self.summary_text = ft.Text(
            value="Listo.",
            size=12,
            color=COLOR_TEXT_MUTED,
            expand=True,
        )

        self.btn_refresh = ft.IconButton(
            icon=ft.Icons.REFRESH,
            tooltip="Actualizar lista de archivos",
            icon_color=COLOR_TEXT_PRIMARY,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(1, COLOR_BORDER_DARK),
            ),
            on_click=lambda _: self.on_refresh(),
        )

        self.btn_undo = ft.IconButton(
            icon=ft.Icons.UNDO,
            tooltip="Deshacer última operación",
            disabled=True,
            icon_color=COLOR_TEXT_PRIMARY,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(1, COLOR_BORDER_DARK),
            ),
            on_click=lambda _: self.on_undo(),
        )

        self.btn_manual_organize = ft.IconButton(
            icon=ft.Icons.DRIVE_FILE_MOVE_OUTLINED,
            tooltip="Organización Manual (recorrer archivo por archivo)",
            disabled=True,
            icon_color=COLOR_TEXT_PRIMARY,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(1, COLOR_BORDER_DARK),
            ),
            on_click=lambda _: self.on_manual_organize() if self.on_manual_organize else None,
        )

        self.btn_step_review = ft.IconButton(
            icon=ft.Icons.CHECKLIST_RTL,
            tooltip="Revisión Paso a Paso",
            disabled=True,
            icon_color=COLOR_TEXT_PRIMARY,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(1, COLOR_BORDER_DARK),
            ),
            on_click=lambda _: self.on_step_review(),
        )

        self.btn_apply = ft.FilledButton(
            "Aplicar Cambios",
            icon=ft.Icons.CHECK,
            disabled=True,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                bgcolor=COLOR_PRIMARY,
                color="#FFFFFF",
            ),
            on_click=lambda _: self.on_apply(),
        )

        self.padding = ft.Padding.symmetric(horizontal=12, vertical=8)
        self.border = ft.Border.only(top=ft.BorderSide(1, COLOR_BORDER_DARK))
        self.content = ft.Row(
            controls=[
                self.summary_text,
                self.btn_refresh,
                self.btn_undo,
                self.btn_manual_organize,
                self.btn_step_review,
                self.btn_apply,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )

    def update_state(self, modified_count: int, conflict_count: int, can_undo: bool, total_files: int = 0):
        self.btn_undo.disabled = not can_undo
        self.btn_manual_organize.disabled = (total_files == 0)
        self.btn_step_review.disabled = (total_files == 0)

        if conflict_count > 0:
            self.btn_apply.disabled = True
            self.btn_apply.content = "Hay Conflictos"
            self.summary_text.value = f"{conflict_count} conflicto(s) detectado(s). Resuélvelos para continuar."
            self.summary_text.color = COLOR_DANGER
        elif modified_count > 0:
            self.btn_apply.disabled = False
            self.btn_apply.content = f"Aplicar Cambios ({modified_count})"
            self.summary_text.value = f"{modified_count} archivo(s) listos para modificar."
            self.summary_text.color = COLOR_SUCCESS
        else:
            self.btn_apply.disabled = True
            self.btn_apply.content = "Aplicar Cambios"
            self.summary_text.value = "No hay cambios pendientes."
            self.summary_text.color = COLOR_TEXT_MUTED

        safe_update(self)
