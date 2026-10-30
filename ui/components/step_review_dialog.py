"""Interactive Step-by-Step File Review Dialog in Flet."""
import base64
import io
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple
import flet as ft
from PIL import Image

from core.models import FileItem, FileStatus, StepAction
from ui.theme import (
    COLOR_BG_DARK,
    COLOR_BORDER_DARK,
    COLOR_CARD_DARK,
    COLOR_DANGER,
    COLOR_INFO,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_SUCCESS,
    COLOR_SURFACE_DARK,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_WARNING,
    format_bytes,
    format_timestamp,
    safe_update,
)

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff"}
TEXT_EXTENSIONS = {".txt", ".py", ".json", ".csv", ".md", ".html", ".css", ".xml", ".log", ".yaml", ".yml"}


class StepReviewDialog:
    """Modal dialog allowing step-by-step interactive inspection and action selection for each file."""

    def __init__(
        self,
        page: ft.Page,
        items: List[FileItem],
        trash_folder: Path,
        on_finished: Callable[[List[Tuple[FileItem, StepAction]]], None],
    ):
        self.page = page
        self.items = list(items)
        self.trash_folder = trash_folder
        self.on_finished = on_finished

        self.current_idx = 0
        # Initialize default decisions: APPLY if modified and no conflict, else KEEP
        self.decisions: Dict[int, StepAction] = {}
        for idx, it in enumerate(self.items):
            if it.is_modified and not it.has_conflict:
                self.decisions[idx] = StepAction.APPLY
            else:
                self.decisions[idx] = StepAction.KEEP

        self._build_ui()
        if self.items:
            self._render_current_item()

    def _build_ui(self):
        # 1. Header controls
        self.txt_title = ft.Text(
            "Revisión Paso a Paso",
            weight=ft.FontWeight.W_600,
            size=16,
            color=COLOR_TEXT_PRIMARY,
        )
        self.badge_counter = ft.Container(
            content=ft.Text("Archivo 1 de 1", size=11, weight=ft.FontWeight.W_600, color=COLOR_TEXT_PRIMARY),
            bgcolor=COLOR_CARD_DARK,
            border_radius=12,
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            border=ft.Border.all(1, COLOR_BORDER_DARK),
        )

        self.progress_bar = ft.ProgressBar(
            value=0.0,
            color=COLOR_PRIMARY,
            bgcolor=COLOR_CARD_DARK,
            height=4,
        )

        self.stat_pill_apply = ft.Text("Modificar: 0", size=11, color=COLOR_SUCCESS, weight=ft.FontWeight.W_600)
        self.stat_pill_keep = ft.Text("Conservar: 0", size=11, color=COLOR_TEXT_MUTED, weight=ft.FontWeight.W_600)
        self.stat_pill_discard = ft.Text("Eliminar: 0", size=11, color=COLOR_DANGER, weight=ft.FontWeight.W_600)

        header_row = ft.Row(
            controls=[
                ft.Icon(ft.Icons.CHECKLIST_RTL, color=COLOR_PRIMARY, size=22),
                self.txt_title,
                ft.Container(expand=True),
                self.stat_pill_apply,
                ft.Text("•", color=COLOR_BORDER_DARK),
                self.stat_pill_keep,
                ft.Text("•", color=COLOR_BORDER_DARK),
                self.stat_pill_discard,
                ft.Container(width=10),
                self.badge_counter,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        )

        # 2. Left Column: Preview Container
        self.preview_display = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.IMAGE_OUTLINED, size=48, color=COLOR_TEXT_MUTED),
                    ft.Text("Vista Previa", size=12, color=COLOR_TEXT_MUTED),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=COLOR_CARD_DARK,
            border_radius=8,
            height=250,
            width=330,
            alignment=ft.Alignment.CENTER,
            border=ft.Border.all(1, COLOR_BORDER_DARK),
        )

        self.txt_preview_filename = ft.Text(
            "-",
            size=11,
            color=COLOR_TEXT_SECONDARY,
            text_align=ft.TextAlign.CENTER,
            max_lines=2,
            overflow=ft.TextOverflow.ELLIPSIS,
        )

        left_column = ft.Column(
            controls=[
                self.preview_display,
                ft.Container(content=self.txt_preview_filename, width=330, alignment=ft.Alignment.CENTER),
            ],
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # 3. Right Column: Metadata & Decision Info
        self.lbl_orig_name = ft.Text("-", size=11, color=COLOR_TEXT_PRIMARY, selectable=True)
        self.lbl_new_name = ft.Text("-", size=12, color=COLOR_PRIMARY, weight=ft.FontWeight.W_600, selectable=True)
        self.lbl_target_folder = ft.Text("-", size=11, color=COLOR_TEXT_MUTED, selectable=True)
        self.lbl_size = ft.Text("-", size=11, color=COLOR_TEXT_PRIMARY)
        self.lbl_mtime = ft.Text("-", size=11, color=COLOR_TEXT_PRIMARY)

        self.status_box = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.INFO_OUTLINE, size=16, color=COLOR_INFO),
                    ft.Text("Estado", size=11, color=COLOR_TEXT_PRIMARY),
                ],
                spacing=6,
            ),
            bgcolor=COLOR_CARD_DARK,
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=8, vertical=6),
            border=ft.Border.all(1, COLOR_BORDER_DARK),
        )

        self.decision_badge = ft.Container(
            content=ft.Text("DECISIÓN: CONSERVAR", size=11, weight=ft.FontWeight.W_600),
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            border_radius=6,
        )

        def make_field(label: str, control: ft.Control):
            return ft.Column(
                controls=[
                    ft.Text(label, size=10, weight=ft.FontWeight.W_600, color=COLOR_TEXT_MUTED),
                    control,
                ],
                spacing=2,
            )

        right_column = ft.Column(
            controls=[
                make_field("Nombre Original:", self.lbl_orig_name),
                make_field("Nuevo Nombre Propuesto:", self.lbl_new_name),
                make_field("Carpeta Destino Propuesta:", self.lbl_target_folder),
                ft.Row(
                    controls=[
                        ft.Container(content=make_field("Tamaño:", self.lbl_size), expand=True),
                        ft.Container(content=make_field("Modificado:", self.lbl_mtime), expand=True),
                    ],
                    spacing=12,
                ),
                self.status_box,
                ft.Divider(height=1, color=COLOR_BORDER_DARK),
                ft.Row(
                    controls=[
                        ft.Text("Decisión para este archivo:", size=11, color=COLOR_TEXT_MUTED),
                        self.decision_badge,
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
            ],
            spacing=8,
            expand=True,
        )

        # Body row
        body_row = ft.Row(
            controls=[
                left_column,
                ft.VerticalDivider(width=1, thickness=1, color=COLOR_BORDER_DARK),
                right_column,
            ],
            spacing=16,
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
        )

        # 4. Action Buttons per file
        self.btn_keep = ft.OutlinedButton(
            "Conservar Original",
            icon=ft.Icons.BLOCK,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(1, COLOR_BORDER_DARK),
                color=COLOR_TEXT_PRIMARY,
            ),
            tooltip="Conservar archivo sin modificar nombre ni carpeta (Omitir)",
            on_click=lambda _: self._set_decision_and_advance(StepAction.KEEP),
        )

        self.btn_apply = ft.FilledButton(
            "Aplicar Acción",
            icon=ft.Icons.CHECK_CIRCLE,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                bgcolor=COLOR_PRIMARY,
                color="#FFFFFF",
            ),
            tooltip="Aplicar nuevo nombre y organización calculada",
            on_click=lambda _: self._set_decision_and_advance(StepAction.APPLY),
        )

        self.btn_discard = ft.OutlinedButton(
            "Eliminar Archivo",
            icon=ft.Icons.DELETE_OUTLINE,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(1, COLOR_DANGER),
                color=COLOR_DANGER,
            ),
            tooltip="Mover a la carpeta _Papelera de forma segura y reversible",
            on_click=lambda _: self._set_decision_and_advance(StepAction.DISCARD),
        )

        action_buttons_row = ft.Row(
            controls=[
                self.btn_keep,
                self.btn_apply,
                self.btn_discard,
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        # 5. Stepper Navigation & Batch Helpers
        self.btn_prev = ft.TextButton(
            "← Anterior",
            icon=ft.Icons.ARROW_BACK,
            style=ft.ButtonStyle(color=COLOR_TEXT_PRIMARY),
            on_click=lambda _: self._on_prev(),
        )

        self.btn_next = ft.TextButton(
            "Siguiente →",
            icon=ft.Icons.ARROW_FORWARD,
            style=ft.ButtonStyle(color=COLOR_TEXT_PRIMARY),
            on_click=lambda _: self._on_next(),
        )

        self.btn_apply_remaining = ft.TextButton(
            "Aplicar a Restantes",
            icon=ft.Icons.DONE_ALL,
            style=ft.ButtonStyle(color=COLOR_TEXT_MUTED),
            on_click=lambda _: self._apply_remaining(),
        )

        self.btn_keep_remaining = ft.TextButton(
            "Conservar Restantes",
            icon=ft.Icons.REMOVE_DONE,
            style=ft.ButtonStyle(color=COLOR_TEXT_MUTED),
            on_click=lambda _: self._keep_remaining(),
        )

        nav_row = ft.Row(
            controls=[
                self.btn_prev,
                self.btn_next,
                ft.Container(expand=True),
                self.btn_keep_remaining,
                self.btn_apply_remaining,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        )

        # Main Dialog content container
        dialog_content = ft.Container(
            content=ft.Column(
                controls=[
                    header_row,
                    self.progress_bar,
                    ft.Divider(height=1, color=COLOR_BORDER_DARK),
                    body_row,
                    ft.Divider(height=1, color=COLOR_BORDER_DARK),
                    action_buttons_row,
                    nav_row,
                ],
                spacing=10,
                expand=True,
            ),
            width=800,
            height=490,
            padding=ft.Padding.all(4),
        )

        self.dialog = ft.AlertDialog(
            content=dialog_content,
            actions=[
                ft.TextButton(
                    "Cancelar",
                    style=ft.ButtonStyle(color=COLOR_TEXT_MUTED),
                    on_click=lambda _: self.page.pop_dialog(),
                ),
                ft.FilledButton(
                    "Finalizar y Aplicar Cambios",
                    icon=ft.Icons.CHECK,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8),
                        bgcolor=COLOR_PRIMARY,
                        color="#FFFFFF",
                    ),
                    on_click=lambda _: self._on_confirm_click(),
                ),
            ],
        )

    def show(self):
        """Displays the step review modal dialog on the page."""
        if not self.items:
            return
        self._update_stats()
        self.page.show_dialog(self.dialog)

    def _render_current_item(self):
        if not self.items or self.current_idx < 0 or self.current_idx >= len(self.items):
            return

        item = self.items[self.current_idx]
        total = len(self.items)

        # 1. Update header and progress
        self.badge_counter.content.value = f"Archivo {self.current_idx + 1} de {total}"
        self.progress_bar.value = (self.current_idx + 1) / total

        # 2. Update navigation button states
        self.btn_prev.disabled = (self.current_idx == 0)
        self.btn_next.disabled = (self.current_idx == total - 1)

        # 3. Update Preview
        self.txt_preview_filename.value = item.original_name
        ext = item.extension.lower()
        path = item.original_path

        if ext in IMAGE_EXTENSIONS and path.exists():
            self._render_image_preview(path)
        elif ext in TEXT_EXTENSIONS and path.exists():
            self._render_text_preview(path)
        else:
            self._render_generic_preview(ext)

        # 4. Update Metadata
        self.lbl_orig_name.value = item.original_name
        self.lbl_new_name.value = item.new_name
        self.lbl_target_folder.value = str(item.target_folder)
        self.lbl_size.value = format_bytes(item.size_bytes)
        self.lbl_mtime.value = format_timestamp(item.modified_time)

        # Check modifications and conflicts
        if item.has_conflict:
            self.status_box.content = ft.Row(
                controls=[
                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, size=16, color=COLOR_DANGER),
                    ft.Text(f"Conflicto: {item.status_message or 'Destino no válido'}", size=11, color=COLOR_DANGER, weight=ft.FontWeight.W_600),
                ],
                spacing=6,
            )
            self.status_box.bgcolor = "#2c1517"
            self.status_box.border = ft.Border.all(1, COLOR_DANGER)
            self.btn_apply.disabled = True
        elif item.is_modified:
            self.status_box.content = ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=16, color=COLOR_SUCCESS),
                    ft.Text("Listo para modificar (renombrado o clasificado)", size=11, color=COLOR_SUCCESS),
                ],
                spacing=6,
            )
            self.status_box.bgcolor = "#13271d"
            self.status_box.border = ft.Border.all(1, COLOR_SUCCESS)
            self.btn_apply.disabled = False
        else:
            self.status_box.content = ft.Row(
                controls=[
                    ft.Icon(ft.Icons.INFO_OUTLINE, size=16, color=COLOR_TEXT_MUTED),
                    ft.Text("Sin cambios propuestos (mantiene nombre y carpeta)", size=11, color=COLOR_TEXT_MUTED),
                ],
                spacing=6,
            )
            self.status_box.bgcolor = COLOR_CARD_DARK
            self.status_box.border = ft.Border.all(1, COLOR_BORDER_DARK)
            self.btn_apply.disabled = False

        # 5. Current Decision Badge
        decision = self.decisions.get(self.current_idx, StepAction.KEEP)
        if decision == StepAction.APPLY:
            self.decision_badge.content.value = "✓ APLICAR ACCIÓN"
            self.decision_badge.content.color = COLOR_SUCCESS
            self.decision_badge.bgcolor = "#13271d"
            self.decision_badge.border = ft.Border.all(1, COLOR_SUCCESS)
        elif decision == StepAction.DISCARD:
            self.decision_badge.content.value = "✕ ELIMINAR A PAPELERA"
            self.decision_badge.content.color = COLOR_DANGER
            self.decision_badge.bgcolor = "#2c1517"
            self.decision_badge.border = ft.Border.all(1, COLOR_DANGER)
        else:
            self.decision_badge.content.value = "— CONSERVAR ORIGINAL"
            self.decision_badge.content.color = COLOR_TEXT_MUTED
            self.decision_badge.bgcolor = COLOR_CARD_DARK
            self.decision_badge.border = ft.Border.all(1, COLOR_BORDER_DARK)

        self._update_stats()
        safe_update(self.dialog)

    def _render_image_preview(self, path: Path):
        try:
            with Image.open(path) as img:
                img.thumbnail((300, 210))
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGB")
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                b64 = base64.b64encode(buf.getvalue()).decode()

            self.preview_display.content = ft.Image(
                src_base64=b64,
                fit=ft.ImageFit.CONTAIN,
                border_radius=ft.BorderRadius.all(6),
            )
        except Exception:
            self._render_generic_preview(path.suffix)

    def _render_text_preview(self, path: Path):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                snippet = "".join(f.readline() for _ in range(12))

            self.preview_display.content = ft.Container(
                content=ft.Text(
                    value=snippet,
                    font_family="monospace",
                    size=10,
                    color=COLOR_TEXT_PRIMARY,
                ),
                padding=10,
                alignment=ft.Alignment.TOP_LEFT,
                expand=True,
            )
        except Exception:
            self._render_generic_preview(path.suffix)

    def _render_generic_preview(self, ext: str):
        self.preview_display.content = ft.Column(
            controls=[
                ft.Icon(ft.Icons.INSERT_DRIVE_FILE_OUTLINED, size=56, color=COLOR_TEXT_MUTED),
                ft.Text(
                    f"[{ext.upper() if ext else 'ARCHIVO'}]",
                    size=14,
                    weight=ft.FontWeight.W_600,
                    color=COLOR_TEXT_MUTED,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        )

    def _update_stats(self):
        mod_count = sum(
            1 for idx, it in enumerate(self.items)
            if self.decisions.get(idx) == StepAction.APPLY and it.is_modified and not it.has_conflict
        )
        discard_count = sum(
            1 for idx, it in enumerate(self.items)
            if self.decisions.get(idx) == StepAction.DISCARD
        )
        keep_count = len(self.items) - mod_count - discard_count

        self.stat_pill_apply.value = f"Modificar: {mod_count}"
        self.stat_pill_keep.value = f"Conservar: {keep_count}"
        self.stat_pill_discard.value = f"Eliminar: {discard_count}"

    def _set_decision_and_advance(self, action: StepAction):
        self.decisions[self.current_idx] = action
        if self.current_idx < len(self.items) - 1:
            self.current_idx += 1
        self._render_current_item()

    def _on_prev(self):
        if self.current_idx > 0:
            self.current_idx -= 1
            self._render_current_item()

    def _on_next(self):
        if self.current_idx < len(self.items) - 1:
            self.current_idx += 1
            self._render_current_item()

    def _apply_remaining(self):
        for idx in range(self.current_idx, len(self.items)):
            it = self.items[idx]
            if it.is_modified and not it.has_conflict:
                self.decisions[idx] = StepAction.APPLY
            else:
                self.decisions[idx] = StepAction.KEEP
        self._render_current_item()

    def _keep_remaining(self):
        for idx in range(self.current_idx, len(self.items)):
            self.decisions[idx] = StepAction.KEEP
        self._render_current_item()

    def _on_confirm_click(self):
        mod_count = sum(
            1 for idx, it in enumerate(self.items)
            if self.decisions.get(idx) == StepAction.APPLY and it.is_modified and not it.has_conflict
        )
        discard_count = sum(
            1 for idx, it in enumerate(self.items)
            if self.decisions.get(idx) == StepAction.DISCARD
        )
        keep_count = len(self.items) - mod_count - discard_count

        if mod_count == 0 and discard_count == 0:
            self.page.pop_dialog()
            return

        def do_execute(e):
            self.page.pop_dialog()  # Close confirm dialog
            self.page.pop_dialog()  # Close step review dialog
            reviewed_pairs = [(it, self.decisions[idx]) for idx, it in enumerate(self.items)]
            self.on_finished(reviewed_pairs)

        confirm_msg = (
            f"Se aplicarán las decisiones tomadas sobre {len(self.items)} archivo(s):\n\n"
            f"• {mod_count} archivo(s) serán renombrados o clasificados.\n"
            f"• {keep_count} archivo(s) se conservarán sin ningún cambio.\n"
            f"• {discard_count} archivo(s) serán movidos a la carpeta '{self.trash_folder.name}'.\n\n"
            "Podrás revertir esta operación en cualquier momento con el botón 'Deshacer'."
        )

        confirm_dialog = ft.AlertDialog(
            title=ft.Text("Confirmar Decisiones de Revisión", weight=ft.FontWeight.W_600),
            content=ft.Text(confirm_msg),
            actions=[
                ft.TextButton("Volver a Revisar", on_click=lambda _: self.page.pop_dialog()),
                ft.FilledButton(
                    "Proceder",
                    on_click=do_execute,
                    bgcolor=COLOR_PRIMARY,
                    color="#FFFFFF",
                ),
            ],
        )
        self.page.show_dialog(confirm_dialog)
