"""File inspector and preview panel with image thumbnails and metadata in Flet."""
import base64
import io
from pathlib import Path
from typing import Optional
import flet as ft
from PIL import Image

from core.models import FileItem
from ui.theme import (
    COLOR_BORDER_DARK,
    COLOR_CARD_DARK,
    COLOR_PRIMARY,
    COLOR_SURFACE_DARK,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    format_bytes,
    format_timestamp,
    safe_update,
)

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff"}
TEXT_EXTENSIONS = {".txt", ".py", ".json", ".csv", ".md", ".html", ".css", ".xml", ".log", ".yaml", ".yml"}


class InspectorPanel(ft.Container):
    """Side panel displaying file details, thumbnail preview, and properties."""

    def __init__(self):
        super().__init__()
        self.width = 260
        self.current_item: Optional[FileItem] = None

        self._build_widgets()

    def _build_widgets(self):
        lbl_title = ft.Text(
            value="Vista Previa e Inspeccion",
            size=13,
            weight=ft.FontWeight.W_600,
            color=COLOR_TEXT_PRIMARY,
        )

        # Preview Container
        self.preview_content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.IMAGE_OUTLINED, size=32, color=COLOR_TEXT_MUTED),
                    ft.Text("Selecciona un archivo\npara ver su vista previa", size=11, color=COLOR_TEXT_MUTED, text_align=ft.TextAlign.CENTER),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=COLOR_CARD_DARK,
            border_radius=8,
            height=160,
            alignment=ft.Alignment.CENTER,
            border=ft.Border.all(1, COLOR_BORDER_DARK),
        )

        # Property Labels
        self.txt_orig_name = ft.Text("-", size=11, color=COLOR_TEXT_PRIMARY, selectable=True)
        self.txt_new_name = ft.Text("-", size=11, color=COLOR_PRIMARY, weight=ft.FontWeight.W_600, selectable=True)
        self.txt_size = ft.Text("-", size=11, color=COLOR_TEXT_PRIMARY)
        self.txt_mtime = ft.Text("-", size=11, color=COLOR_TEXT_PRIMARY)
        self.txt_dest_folder = ft.Text("-", size=11, color=COLOR_TEXT_MUTED, selectable=True)

        def make_prop_box(label: str, control: ft.Control):
            return ft.Column(
                controls=[
                    ft.Text(label, size=10, weight=ft.FontWeight.W_600, color=COLOR_TEXT_MUTED),
                    control,
                ],
                spacing=2,
            )

        self.padding = ft.Padding.all(12)
        self.bgcolor = COLOR_SURFACE_DARK
        self.border_radius = 8
        self.border = ft.Border.all(1, COLOR_BORDER_DARK)

        self.content = ft.Column(
            controls=[
                lbl_title,
                self.preview_content,
                ft.Divider(height=1, color=COLOR_BORDER_DARK),
                make_prop_box("Nombre Original:", self.txt_orig_name),
                make_prop_box("Nuevo Nombre:", self.txt_new_name),
                make_prop_box("Tamano:", self.txt_size),
                make_prop_box("Modificado:", self.txt_mtime),
                make_prop_box("Carpeta Destino:", self.txt_dest_folder),
            ],
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
        )

    def inspect_file(self, item: Optional[FileItem]):
        self.current_item = item
        if not item:
            self._clear_display()
            return

        self.txt_orig_name.value = item.original_name
        self.txt_new_name.value = item.new_name
        self.txt_size.value = format_bytes(item.size_bytes)
        self.txt_mtime.value = format_timestamp(item.modified_time)
        self.txt_dest_folder.value = str(item.target_folder)

        path = item.original_path
        ext = item.extension.lower()

        if ext in IMAGE_EXTENSIONS and path.exists():
            self._show_image_thumbnail(path)
        elif ext in TEXT_EXTENSIONS and path.exists():
            self._show_text_snippet(path)
        else:
            self._show_generic_icon(ext)

        safe_update(self)

    def _show_image_thumbnail(self, path: Path):
        try:
            with Image.open(path) as img:
                img.thumbnail((220, 150))
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGB")
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                b64 = base64.b64encode(buf.getvalue()).decode()

            self.preview_content.content = ft.Image(
                src_base64=b64,
                fit=ft.ImageFit.CONTAIN,
                border_radius=ft.BorderRadius.all(6),
            )
        except Exception:
            self._show_generic_icon(path.suffix)

    def _show_text_snippet(self, path: Path):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                snippet = "".join(f.readline() for _ in range(8))

            self.preview_content.content = ft.Container(
                content=ft.Text(
                    value=snippet,
                    font_family="monospace",
                    size=10,
                    color=COLOR_TEXT_PRIMARY,
                ),
                padding=6,
                alignment=ft.Alignment.TOP_LEFT,
            )
        except Exception:
            self._show_generic_icon(path.suffix)

    def _show_generic_icon(self, ext: str):
        self.preview_content.content = ft.Column(
            controls=[
                ft.Icon(ft.Icons.INSERT_DRIVE_FILE_OUTLINED, size=36, color=COLOR_TEXT_MUTED),
                ft.Text(f"[{ext.upper() if ext else 'ARCHIVO'}]", size=12, weight=ft.FontWeight.W_600, color=COLOR_TEXT_MUTED),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _clear_display(self):
        self.txt_orig_name.value = "-"
        self.txt_new_name.value = "-"
        self.txt_size.value = "-"
        self.txt_mtime.value = "-"
        self.txt_dest_folder.value = "-"
        self._show_generic_icon("")
        safe_update(self)
