"""Action bar component containing execution, preview, and undo buttons."""
from typing import Callable
import customtkinter as ctk

from ui.theme import (
    COLOR_SUCCESS,
    COLOR_SUCCESS_HOVER,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
)
from ui.icons import get_icon


class ActionBar(ctk.CTkFrame):
    """Bottom action bar with primary action buttons."""

    def __init__(
        self,
        master,
        on_refresh: Callable[[], None],
        on_apply: Callable[[], None],
        on_undo: Callable[[], None],
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.on_refresh = on_refresh
        self.on_apply = on_apply
        self.on_undo = on_undo

        self._build_widgets()

    def _build_widgets(self):
        # Left side: Status summary label
        self.summary_label = ctk.CTkLabel(
            self,
            text="Listo.",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        self.summary_label.pack(side="left", padx=14, pady=10)

        # Right side: Action Buttons
        self.btn_apply = ctk.CTkButton(
            self,
            text="Aplicar Cambios",
            image=get_icon("check", (16, 16)),
            compound="left",
            fg_color=COLOR_SUCCESS,
            hover_color=COLOR_SUCCESS_HOVER,
            font=ctk.CTkFont(size=13, weight="bold"),
            height=34,
            command=self.on_apply,
        )
        self.btn_apply.pack(side="right", padx=(6, 14), pady=10)

        self.btn_undo = ctk.CTkButton(
            self,
            text="Deshacer",
            image=get_icon("undo", (15, 15)),
            compound="left",
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            height=34,
            state="disabled",
            command=self.on_undo,
        )
        self.btn_undo.pack(side="right", padx=6, pady=10)

        self.btn_refresh = ctk.CTkButton(
            self,
            text="Actualizar",
            image=get_icon("refresh", (15, 15)),
            compound="left",
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            height=34,
            command=self.on_refresh,
        )
        self.btn_refresh.pack(side="right", padx=6, pady=10)

    def update_state(self, modified_count: int, conflict_count: int, can_undo: bool):
        """Updates button states and summary message based on current validation."""
        self.btn_undo.configure(state="normal" if can_undo else "disabled")

        if conflict_count > 0:
            self.btn_apply.configure(
                state="disabled",
                text="Hay Conflictos",
                fg_color="gray50",
            )
            self.summary_label.configure(
                text=f"{conflict_count} conflicto(s) detectado(s). Resuélvelos para continuar.",
                text_color="#EF4444",
            )
        elif modified_count > 0:
            self.btn_apply.configure(
                state="normal",
                text=f"Aplicar Cambios ({modified_count})",
                fg_color=COLOR_SUCCESS,
            )
            self.summary_label.configure(
                text=f"{modified_count} archivo(s) listos para modificar.",
                text_color="#10B981",
            )
        else:
            self.btn_apply.configure(
                state="disabled",
                text="Aplicar Cambios",
                fg_color="gray50",
            )
            self.summary_label.configure(
                text="No hay cambios pendientes.",
                text_color="gray",
            )
