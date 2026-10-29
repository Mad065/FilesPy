"""File inspector and preview panel with image thumbnails and metadata."""
from pathlib import Path
from typing import Optional
import customtkinter as ctk
from PIL import Image

from core.models import FileItem
from ui.theme import format_bytes, format_timestamp

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff"}
TEXT_EXTENSIONS = {".txt", ".py", ".json", ".csv", ".md", ".html", ".css", ".xml", ".log", ".yaml", ".yml"}


class InspectorPanel(ctk.CTkFrame):
    """Side panel displaying file details, thumbnail preview, and properties."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.current_item: Optional[FileItem] = None
        self._thumb_image: Optional[ctk.CTkImage] = None

        self._build_widgets()

    def _build_widgets(self):
        lbl_title = ctk.CTkLabel(
            self,
            text="Vista Previa e Inspección",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        lbl_title.pack(anchor="w", padx=12, pady=(12, 8))

        # Thumbnail / Preview Container
        self.preview_container = ctk.CTkFrame(self, height=180, fg_color=("gray85", "gray20"))
        self.preview_container.pack(fill="x", padx=12, pady=(0, 10))
        self.preview_container.pack_propagate(False)

        self.preview_label = ctk.CTkLabel(
            self.preview_container,
            text="Selecciona un archivo\npara ver su vista previa",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        self.preview_label.pack(expand=True)

        # Text snippet preview (hidden by default)
        self.text_preview = ctk.CTkTextbox(
            self.preview_container,
            font=ctk.CTkFont(family="Courier", size=10),
            wrap="word",
        )

        # File Properties Section
        self.props_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.props_frame.pack(fill="both", expand=True, padx=12, pady=5)

        self.lbl_name_title = ctk.CTkLabel(
            self.props_frame, text="Nombre Original:", font=ctk.CTkFont(size=11, weight="bold")
        )
        self.lbl_name_title.pack(anchor="w")
        self.lbl_name = ctk.CTkLabel(
            self.props_frame, text="-", font=ctk.CTkFont(size=11), wraplength=220, justify="left"
        )
        self.lbl_name.pack(anchor="w", pady=(0, 6))

        self.lbl_new_title = ctk.CTkLabel(
            self.props_frame, text="Nuevo Nombre:", font=ctk.CTkFont(size=11, weight="bold")
        )
        self.lbl_new_title.pack(anchor="w")
        self.lbl_new_name = ctk.CTkLabel(
            self.props_frame, text="-", font=ctk.CTkFont(size=11), wraplength=220, justify="left",
            text_color="#10B981"
        )
        self.lbl_new_name.pack(anchor="w", pady=(0, 6))

        self.lbl_size_title = ctk.CTkLabel(
            self.props_frame, text="Tamaño:", font=ctk.CTkFont(size=11, weight="bold")
        )
        self.lbl_size_title.pack(anchor="w")
        self.lbl_size = ctk.CTkLabel(
            self.props_frame, text="-", font=ctk.CTkFont(size=11)
        )
        self.lbl_size.pack(anchor="w", pady=(0, 6))

        self.lbl_date_title = ctk.CTkLabel(
            self.props_frame, text="Modificado:", font=ctk.CTkFont(size=11, weight="bold")
        )
        self.lbl_date_title.pack(anchor="w")
        self.lbl_date = ctk.CTkLabel(
            self.props_frame, text="-", font=ctk.CTkFont(size=11)
        )
        self.lbl_date.pack(anchor="w", pady=(0, 6))

        self.lbl_target_folder_title = ctk.CTkLabel(
            self.props_frame, text="Carpeta Destino:", font=ctk.CTkFont(size=11, weight="bold")
        )
        self.lbl_target_folder_title.pack(anchor="w")
        self.lbl_target_folder = ctk.CTkLabel(
            self.props_frame, text="-", font=ctk.CTkFont(size=10), wraplength=220, justify="left"
        )
        self.lbl_target_folder.pack(anchor="w")

    def inspect_file(self, item: Optional[FileItem]):
        """Updates the inspector with the selected FileItem."""
        self.current_item = item
        if not item:
            self._clear_display()
            return

        self.lbl_name.configure(text=item.original_name)
        self.lbl_new_name.configure(text=item.new_name)
        self.lbl_size.configure(text=format_bytes(item.size_bytes))
        self.lbl_date.configure(text=format_timestamp(item.modified_time))
        self.lbl_target_folder.configure(text=str(item.target_folder))

        path = item.original_path
        ext = item.extension.lower()

        # If it's an image, create thumbnail with Pillow
        if ext in IMAGE_EXTENSIONS and path.exists():
            self._show_image_thumbnail(path)
        elif ext in TEXT_EXTENSIONS and path.exists():
            self._show_text_snippet(path)
        else:
            self._show_generic_icon(ext)

    def _show_image_thumbnail(self, path: Path):
        try:
            with Image.open(path) as img:
                img.thumbnail((200, 160))
                # Convert to RGB if needed
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGB")
                
                self._thumb_image = ctk.CTkImage(
                    light_image=img,
                    dark_image=img,
                    size=img.size,
                )
                self.text_preview.pack_forget()
                self.preview_label.configure(image=self._thumb_image, text="")
                self.preview_label.pack(expand=True)
        except Exception:
            self._show_generic_icon(path.suffix)

    def _show_text_snippet(self, path: Path):
        try:
            self.preview_label.pack_forget()
            self.text_preview.pack(fill="both", expand=True, padx=4, pady=4)
            self.text_preview.delete("1.0", "end")
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                snippet = "".join(f.readline() for _ in range(12))
            self.text_preview.insert("1.0", snippet)
        except Exception:
            self._show_generic_icon(path.suffix)

    def _show_generic_icon(self, ext: str):
        self.text_preview.pack_forget()
        self.preview_label.configure(
            image=None,
            text=f"[{ext.upper() if ext else 'ARCHIVO'}]",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="gray",
        )
        self.preview_label.pack(expand=True)

    def _clear_display(self):
        self.text_preview.pack_forget()
        self.preview_label.configure(
            image=None,
            text="Selecciona un archivo\npara ver su vista previa",
            font=ctk.CTkFont(size=12),
        )
        self.preview_label.pack(expand=True)
        self.lbl_name.configure(text="-")
        self.lbl_new_name.configure(text="-")
        self.lbl_size.configure(text="-")
        self.lbl_date.configure(text="-")
        self.lbl_target_folder.configure(text="-")
