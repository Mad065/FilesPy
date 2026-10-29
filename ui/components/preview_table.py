"""Preview table component showing before/after filenames, destinations, and status."""
from typing import Callable, List, Optional
import customtkinter as ctk

from core.models import FileItem, FileStatus
from ui.theme import (
    COLOR_SUCCESS,
    COLOR_DANGER,
    COLOR_MUTED,
    format_bytes,
)


class PreviewTable(ctk.CTkFrame):
    """Scrollable table displaying original names, new names, target paths, and status."""

    def __init__(
        self,
        master,
        on_item_inspected: Callable[[FileItem], None],
        on_selection_toggled: Callable[[], None],
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.on_item_inspected = on_item_inspected
        self.on_selection_toggled = on_selection_toggled
        self.items: List[FileItem] = []
        self.row_frames: List[ctk.CTkFrame] = []

        self._build_header()
        self._build_scroll_area()

    def _build_header(self):
        self.header_frame = ctk.CTkFrame(self, height=36, fg_color=("gray85", "gray20"))
        self.header_frame.pack(fill="x", padx=4, pady=(4, 2))
        self.header_frame.pack_propagate(False)

        # Master checkbox
        self.master_var = ctk.BooleanVar(value=True)
        self.master_chk = ctk.CTkCheckBox(
            self.header_frame,
            text="",
            width=24,
            variable=self.master_var,
            command=self._on_toggle_all,
        )
        self.master_chk.pack(side="left", padx=(10, 5), pady=4)

        # Header Columns
        ctk.CTkLabel(
            self.header_frame, text="Nombre Original", font=ctk.CTkFont(size=12, weight="bold"), width=180, anchor="w"
        ).pack(side="left", padx=4)

        ctk.CTkLabel(
            self.header_frame, text="", width=20
        ).pack(side="left", padx=2)

        ctk.CTkLabel(
            self.header_frame, text="Nuevo Nombre", font=ctk.CTkFont(size=12, weight="bold"), width=180, anchor="w"
        ).pack(side="left", padx=4)

        ctk.CTkLabel(
            self.header_frame, text="Carpeta Destino", font=ctk.CTkFont(size=12, weight="bold"), width=130, anchor="w"
        ).pack(side="left", padx=4)

        ctk.CTkLabel(
            self.header_frame, text="Tamaño", font=ctk.CTkFont(size=12, weight="bold"), width=70, anchor="e"
        ).pack(side="left", padx=4)

        ctk.CTkLabel(
            self.header_frame, text="Estado", font=ctk.CTkFont(size=12, weight="bold"), width=100, anchor="center"
        ).pack(side="left", padx=(8, 10))

    def _build_scroll_area(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=4, pady=2)

        self.empty_label = ctk.CTkLabel(
            self.scroll_frame,
            text="Ningún archivo cargado.\nSelecciona una carpeta arriba para comenzar.",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        )
        self.empty_label.pack(pady=40)

    def set_items(self, items: List[FileItem]):
        """Renders the given list of FileItem objects."""
        self.items = items

        # Clear existing row widgets
        for row in self.row_frames:
            row.destroy()
        self.row_frames.clear()

        if not items:
            self.empty_label.pack(pady=40)
            return
        else:
            self.empty_label.pack_forget()

        for idx, item in enumerate(items):
            self._create_row(idx, item)

    def _create_row(self, idx: int, item: FileItem):
        # Alternate subtle background
        row_bg = ("gray95", "#1E293B") if idx % 2 == 0 else ("gray90", "#182234")
        row = ctk.CTkFrame(self.scroll_frame, height=34, fg_color=row_bg, corner_radius=6)
        row.pack(fill="x", pady=2)
        row.pack_propagate(False)

        # Row Checkbox
        chk_var = ctk.BooleanVar(value=item.selected)

        def on_chk_toggle():
            item.selected = chk_var.get()
            self.on_selection_toggled()

        chk = ctk.CTkCheckBox(row, text="", width=24, variable=chk_var, command=on_chk_toggle)
        chk.pack(side="left", padx=(10, 5), pady=4)

        # Clickable row binding for inspection
        def on_click(event=None):
            self.on_item_inspected(item)

        row.bind("<Button-1>", on_click)

        # 1. Original Name
        lbl_orig = ctk.CTkLabel(row, text=item.original_name, width=180, anchor="w", font=ctk.CTkFont(size=11))
        lbl_orig.pack(side="left", padx=4)
        lbl_orig.bind("<Button-1>", on_click)

        # 2. Arrow indicator
        arrow_color = COLOR_SUCCESS if item.is_modified else "gray"
        lbl_arrow = ctk.CTkLabel(row, text="->", width=20, text_color=arrow_color, font=ctk.CTkFont(size=11))
        lbl_arrow.pack(side="left", padx=2)
        lbl_arrow.bind("<Button-1>", on_click)

        # 3. New Name
        new_color = COLOR_DANGER if item.has_conflict else (COLOR_SUCCESS if item.is_modified else ("gray20", "gray80"))
        lbl_new = ctk.CTkLabel(
            row, text=item.new_name, width=180, anchor="w",
            text_color=new_color,
            font=ctk.CTkFont(size=11, weight="bold" if item.is_modified else "normal")
        )
        lbl_new.pack(side="left", padx=4)
        lbl_new.bind("<Button-1>", on_click)

        # 4. Target Folder
        target_name = item.target_folder.name or "/"
        lbl_folder = ctk.CTkLabel(row, text=target_name, width=130, anchor="w", font=ctk.CTkFont(size=11), text_color="gray")
        lbl_folder.pack(side="left", padx=4)
        lbl_folder.bind("<Button-1>", on_click)

        # 5. Size
        lbl_size = ctk.CTkLabel(row, text=format_bytes(item.size_bytes), width=70, anchor="e", font=ctk.CTkFont(size=11), text_color="gray")
        lbl_size.pack(side="left", padx=4)
        lbl_size.bind("<Button-1>", on_click)

        # 6. Status Badge
        badge_text, badge_color = self._get_status_badge(item)
        badge = ctk.CTkLabel(
            row,
            text=badge_text,
            width=90,
            corner_radius=4,
            fg_color=badge_color,
            text_color="white",
            font=ctk.CTkFont(size=10, weight="bold"),
        )
        badge.pack(side="left", padx=(8, 10), pady=4)
        badge.bind("<Button-1>", on_click)

        self.row_frames.append(row)

    def _get_status_badge(self, item: FileItem) -> tuple:
        if item.has_conflict:
            return "Conflicto", COLOR_DANGER
        elif item.status == FileStatus.READY or item.is_modified:
            return "Listo", COLOR_SUCCESS
        else:
            return "Sin cambio", COLOR_MUTED

    def _on_toggle_all(self):
        val = self.master_var.get()
        for it in self.items:
            it.selected = val
        self.set_items(self.items)
        self.on_selection_toggled()
