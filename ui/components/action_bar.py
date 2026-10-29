"""Action bar component containing execution, preview, and undo buttons in Flet."""
from typing import Callable
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
    ):
        super().__init__()
        self.on_refresh = on_refresh
        self.on_apply = on_apply
        self.on_undo = on_undo

        self._build_widgets()

    def _build_widgets(self):
        self.summary_text = ft.Text(
            value="Listo.",
            size=12,
            color=COLOR_TEXT_MUTED,
            expand=True,
        )

        self.btn_refresh = ft.OutlinedButton(
            "Actualizar",
            icon=ft.Icons.REFRESH,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(1, COLOR_BORDER_DARK),
                color=COLOR_TEXT_PRIMARY,
            ),
            on_click=lambda _: self.on_refresh(),
        )

        self.btn_undo = ft.OutlinedButton(
            "Deshacer",
            icon=ft.Icons.UNDO,
            disabled=True,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(1, COLOR_BORDER_DARK),
                color=COLOR_TEXT_PRIMARY,
            ),
            on_click=lambda _: self.on_undo(),
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
                self.btn_apply,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )

    def update_state(self, modified_count: int, conflict_count: int, can_undo: bool):
        self.btn_undo.disabled = not can_undo

        if conflict_count > 0:
            self.btn_apply.disabled = True
            self.btn_apply.content = "Hay Conflictos"
            self.summary_text.value = f"{conflict_count} conflicto(s) detectado(s). Resuelvelos para continuar."
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
