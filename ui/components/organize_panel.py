"""Organize rules configuration panel."""
from typing import Callable
import customtkinter as ctk
from core.models import OrganizeConfig


class OrganizePanel(ctk.CTkFrame):
    """Configuration panel for file organization into folders."""

    def __init__(self, master, on_change: Callable[[OrganizeConfig], None], **kwargs):
        super().__init__(master, **kwargs)
        self.on_change = on_change
        self._build_widgets()

    def _build_widgets(self):
        # Header
        lbl_title = ctk.CTkLabel(
            self,
            text="Clasificación en Carpetas:",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        lbl_title.pack(anchor="w", padx=10, pady=(12, 4))

        self.mode_map = {
            "Desactivado (Sin mover)": "none",
            "Por Extensión (PDF, JPG, TXT)": "by_extension",
            "Por Categorías (Documentos, Fotos...)": "by_category",
            "Por Fecha de Modificación (Año/Mes)": "by_date",
        }

        self.mode_menu = ctk.CTkOptionMenu(
            self,
            values=list(self.mode_map.keys()),
            command=self._on_mode_selected,
        )
        self.mode_menu.set("Desactivado (Sin mover)")
        self.mode_menu.pack(fill="x", padx=10, pady=(4, 10))

        # Description Box
        self.desc_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray20"))
        self.desc_frame.pack(fill="x", padx=10, pady=5)

        self.desc_label = ctk.CTkLabel(
            self.desc_frame,
            text="Los archivos permanecerán en su ubicación original.",
            font=ctk.CTkFont(size=11),
            justify="left",
            wraplength=220,
        )
        self.desc_label.pack(padx=10, pady=8)

        # Category details box
        self.categories_info = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=11),
            justify="left",
            text_color="gray",
            wraplength=230,
        )
        self.categories_info.pack(anchor="w", padx=10, pady=(10, 5))

    def update_categories_info(self, categories: dict):
        """Updates the text showing active categories and their extensions."""
        lines = ["Categorias configuradas:"]
        for cat_name, exts in list(categories.items())[:6]:  # Show top categories
            ext_str = ", ".join(sorted([e.lstrip(".").upper() for e in exts])[:4])
            if len(exts) > 4:
                ext_str += "..."
            lines.append(f"- {cat_name}: {ext_str}")
        if len(categories) > 6:
            lines.append(f"...y {len(categories) - 6} categoria(s) mas")
        self.categories_info.configure(text="\n".join(lines))

    def _on_mode_selected(self, choice: str):
        mode_val = self.mode_map.get(choice, "none")
        if mode_val == "none":
            self.desc_label.configure(text="Los archivos permanecerán en su ubicación actual.")
        elif mode_val == "by_extension":
            self.desc_label.configure(text="Crea subcarpetas con el nombre de cada extensión (ej: /PDF, /JPG).")
        elif mode_val == "by_category":
            self.desc_label.configure(text="Agrupa según el tipo de archivo (Documentos, Imágenes, etc.).")
        elif mode_val == "by_date":
            self.desc_label.configure(text="Crea subcarpetas por año y mes (ej: /2026/10) según fecha del archivo.")

        config = self.get_config()
        self.on_change(config)

    def get_config(self) -> OrganizeConfig:
        mode_val = self.mode_map.get(self.mode_menu.get(), "none")
        return OrganizeConfig(mode=mode_val)

    def reset_rules(self):
        self.mode_menu.set("Desactivado (Sin mover)")
        self._on_mode_selected("Desactivado (Sin mover)")
