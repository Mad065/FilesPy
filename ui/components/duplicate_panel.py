"""Duplicate finder panel component."""
from typing import Callable, Dict, List
import customtkinter as ctk
from core.models import FileItem
from core.duplicates import find_duplicates
from ui.theme import format_bytes


class DuplicatePanel(ctk.CTkFrame):
    """Panel to search and manage duplicate files."""

    def __init__(
        self,
        master,
        get_current_items: Callable[[], List[FileItem]],
        on_isolate_duplicates: Callable[[List[FileItem]], None],
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.get_current_items = get_current_items
        self.on_isolate_duplicates = on_isolate_duplicates
        self.duplicate_groups: Dict[str, List[FileItem]] = {}

        self._build_widgets()

    def _build_widgets(self):
        lbl_title = ctk.CTkLabel(
            self,
            text="Detección de Duplicados:",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        lbl_title.pack(anchor="w", padx=10, pady=(12, 4))

        lbl_desc = ctk.CTkLabel(
            self,
            text=(
                "Compara los archivos por su contenido real "
                "(hash criptográfico SHA-256), independientemente "
                "de si tienen nombres distintos."
            ),
            font=ctk.CTkFont(size=11),
            justify="left",
            wraplength=220,
            text_color="gray",
        )
        lbl_desc.pack(anchor="w", padx=10, pady=(0, 10))

        self.btn_scan = ctk.CTkButton(
            self,
            text="Buscar Duplicados",
            command=self._scan_duplicates,
            height=32,
        )
        self.btn_scan.pack(fill="x", padx=10, pady=5)

        self.results_box = ctk.CTkFrame(self, fg_color=("gray90", "gray20"))
        self.results_box.pack(fill="x", padx=10, pady=10)

        self.lbl_result = ctk.CTkLabel(
            self.results_box,
            text="Sin escanear aún.",
            font=ctk.CTkFont(size=11),
            justify="center",
        )
        self.lbl_result.pack(padx=10, pady=8)

        self.btn_isolate = ctk.CTkButton(
            self,
            text="Mover Copias a _Duplicados",
            command=self._isolate,
            state="disabled",
            fg_color="#F59E0B",
            hover_color="#D97706",
            height=32,
        )
        self.btn_isolate.pack(fill="x", padx=10, pady=5)

    def _scan_duplicates(self):
        items = self.get_current_items()
        if not items:
            self.lbl_result.configure(text="No hay archivos cargados para escanear.")
            return

        self.btn_scan.configure(state="disabled", text="Calculando hashes...")
        self.update_idletasks()

        self.duplicate_groups = find_duplicates(items)
        group_count = len(self.duplicate_groups)
        
        if group_count == 0:
            self.lbl_result.configure(text="No se encontraron archivos duplicados.")
            self.btn_isolate.configure(state="disabled")
        else:
            total_dup_files = sum(len(grp) - 1 for grp in self.duplicate_groups.values())
            wasted_bytes = sum((len(grp) - 1) * grp[0].size_bytes for grp in self.duplicate_groups.values())
            
            self.lbl_result.configure(
                text=(
                    f"Se encontraron {group_count} grupos de duplicados.\n"
                    f"Copias repetidas: {total_dup_files}\n"
                    f"Espacio recuperable: {format_bytes(wasted_bytes)}"
                )
            )
            self.btn_isolate.configure(state="normal")

        self.btn_scan.configure(state="normal", text="Buscar Duplicados")

    def _isolate(self):
        """Prepares the duplicate items to be moved into a '_Duplicados' subfolder."""
        items_to_move: List[FileItem] = []
        for grp in self.duplicate_groups.values():
            # Keep the first original, move subsequent copies
            for copy_item in grp[1:]:
                items_to_move.append(copy_item)

        if items_to_move:
            self.on_isolate_duplicates(items_to_move)
