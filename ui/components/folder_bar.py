"""Folder selection bar component."""
from pathlib import Path
from tkinter import filedialog
from typing import Callable, Optional
import customtkinter as ctk


class FolderBar(ctk.CTkFrame):
    """Top bar for selecting folder, setting recursive options, and showing counts."""

    def __init__(
        self,
        master,
        on_folder_selected: Callable[[Path, bool], None],
        on_open_settings: Optional[Callable[[], None]] = None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.on_folder_selected = on_folder_selected
        self.on_open_settings = on_open_settings
        self.current_folder: Optional[Path] = None

        self._build_widgets()

    def _build_widgets(self):
        # Path Label & Entry
        self.label = ctk.CTkLabel(
            self,
            text="Carpeta:",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.label.pack(side="left", padx=(12, 6), pady=8)

        self.path_entry = ctk.CTkEntry(
            self,
            placeholder_text="Selecciona una carpeta para ordenar o renombrar...",
            height=32,
        )
        self.path_entry.pack(side="left", fill="x", expand=True, padx=6, pady=8)
        self.path_entry.bind("<Return>", self._on_enter_pressed)

        # Browse Button
        self.browse_btn = ctk.CTkButton(
            self,
            text="Explorar...",
            width=110,
            height=32,
            command=self._on_browse,
        )
        self.browse_btn.pack(side="left", padx=6, pady=8)

        # Recursive Switch
        self.recursive_var = ctk.BooleanVar(value=False)
        self.recursive_switch = ctk.CTkSwitch(
            self,
            text="Subcarpetas",
            variable=self.recursive_var,
            command=self._on_option_changed,
        )
        self.recursive_switch.pack(side="left", padx=(10, 12), pady=8)

        # Settings Button (Right side)
        if self.on_open_settings:
            self.settings_btn = ctk.CTkButton(
                self,
                text="Configuracion",
                width=110,
                height=32,
                fg_color="transparent",
                border_width=1,
                text_color=("gray10", "gray90"),
                command=self.on_open_settings,
            )
            self.settings_btn.pack(side="right", padx=(6, 12), pady=8)

        # Counter Label
        self.count_label = ctk.CTkLabel(
            self,
            text="0 archivos",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        self.count_label.pack(side="right", padx=10, pady=8)

    def _on_browse(self):
        selected = filedialog.askdirectory(title="Seleccionar Carpeta a Procesar")
        if selected:
            folder_path = Path(selected).resolve()
            self.set_folder(folder_path)

    def _on_enter_pressed(self, event=None):
        text = self.path_entry.get().strip()
        if text:
            p = Path(text).resolve()
            if p.is_dir():
                self.set_folder(p)

    def _on_option_changed(self):
        if self.current_folder:
            self.on_folder_selected(self.current_folder, self.recursive_var.get())

    def set_folder(self, folder_path: Path):
        self.current_folder = folder_path
        self.path_entry.delete(0, "end")
        self.path_entry.insert(0, str(folder_path))
        self.on_folder_selected(self.current_folder, self.recursive_var.get())

    def update_count(self, count: int, modified_count: int = 0):
        if modified_count > 0:
            self.count_label.configure(
                text=f"{count} archivos ({modified_count} a modificar)"
            )
        else:
            self.count_label.configure(text=f"{count} archivos")
