"""Settings modal dialog for configuring categories, extensions, exclusions, and preferences."""
from tkinter import messagebox
from typing import Callable, Dict, List
import customtkinter as ctk

from core.config_manager import ConfigManager, DEFAULT_SETTINGS, normalize_extension
from ui.theme import COLOR_PRIMARY, COLOR_PRIMARY_HOVER, COLOR_SUCCESS, COLOR_SUCCESS_HOVER
from ui.icons import get_icon


class SettingsDialog(ctk.CTkToplevel):
    """Modal dialog for editing app configuration without emojis."""

    def __init__(
        self,
        parent,
        config_manager: ConfigManager,
        on_saved: Callable[[], None],
        **kwargs,
    ):
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.config_manager = config_manager
        self.on_saved = on_saved

        # Working copy of settings
        self.working_settings = dict(self.config_manager.settings)
        # Deep copy categories
        raw_cats = self.working_settings.get("categories", {})
        self.working_categories: Dict[str, List[str]] = {
            k: list(v) for k, v in raw_cats.items()
        }
        self.selected_category: str = next(iter(self.working_categories), "Documentos")

        self.title("Configuracion")
        self.geometry("700x530")
        self.minsize(620, 480)
        self.resizable(False, False)

        # Center on parent window
        self._center_window()

        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _center_window(self):
        self.update_idletasks()
        try:
            px = self.parent.winfo_x()
            py = self.parent.winfo_y()
            pw = self.parent.winfo_width()
            ph = self.parent.winfo_height()
            w = 700
            h = 530
            x = px + max(0, (pw - w) // 2)
            y = py + max(0, (ph - h) // 2)
            self.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            pass

    def _build_ui(self):
        # Tabs
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=12, pady=(8, 4))

        tab_ext = self.tabview.add("Categorias y Extensiones")
        tab_ignored = self.tabview.add("Archivos Ignorados")
        tab_general = self.tabview.add("Opciones Generales")

        self._build_tab_extensions(tab_ext)
        self._build_tab_ignored(tab_ignored)
        self._build_tab_general(tab_general)

        # Bottom Bar
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=12, pady=(6, 12))

        btn_reset = ctk.CTkButton(
            bottom_frame,
            text="Restablecer Valores",
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            height=32,
            command=self._on_reset,
        )
        btn_reset.pack(side="left")

        btn_save = ctk.CTkButton(
            bottom_frame,
            text="Guardar",
            image=get_icon("check", (14, 14)),
            compound="left",
            fg_color=COLOR_SUCCESS,
            hover_color=COLOR_SUCCESS_HOVER,
            height=32,
            width=100,
            command=self._on_save,
        )
        btn_save.pack(side="right", padx=(6, 0))

        btn_cancel = ctk.CTkButton(
            bottom_frame,
            text="Cancelar",
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            height=32,
            width=90,
            command=self.destroy,
        )
        btn_cancel.pack(side="right")

    # ----------------------------------------------------
    # TAB 1: Categorias y Extensiones
    # ----------------------------------------------------
    def _build_tab_extensions(self, parent):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=4, pady=4)

        # Left column: Category list & buttons
        left_col = ctk.CTkFrame(container, width=210)
        left_col.pack(side="left", fill="y", padx=(0, 8), pady=0)
        left_col.pack_propagate(False)

        lbl_cats = ctk.CTkLabel(left_col, text="Categorias:", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_cats.pack(anchor="w", padx=8, pady=(8, 4))

        self.cat_listbox_frame = ctk.CTkScrollableFrame(left_col, fg_color="transparent")
        self.cat_listbox_frame.pack(fill="both", expand=True, padx=4, pady=2)

        btn_new_cat = ctk.CTkButton(
            left_col,
            text="Nueva Categoria",
            image=get_icon("plus", (14, 14)),
            compound="left",
            height=28,
            command=self._on_add_category,
        )
        btn_new_cat.pack(fill="x", padx=6, pady=(6, 3))

        btn_del_cat = ctk.CTkButton(
            left_col,
            text="Eliminar Categoria",
            image=get_icon("trash", (14, 14)),
            compound="left",
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            height=28,
            command=self._on_delete_category,
        )
        btn_del_cat.pack(fill="x", padx=6, pady=(3, 8))

        # Right column: Editor for selected category
        right_col = ctk.CTkFrame(container, fg_color="transparent")
        right_col.pack(side="right", fill="both", expand=True)

        self.lbl_selected_cat = ctk.CTkLabel(
            right_col,
            text="Categoria: Documentos",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.lbl_selected_cat.pack(anchor="w", pady=(4, 6))

        lbl_hint = ctk.CTkLabel(
            right_col,
            text="Extensiones reconocidas (separadas por comas o saltos de linea):",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        lbl_hint.pack(anchor="w", pady=(0, 4))

        self.ext_textbox = ctk.CTkTextbox(right_col, height=190, font=ctk.CTkFont(family="Courier", size=12))
        self.ext_textbox.pack(fill="both", expand=True, pady=(0, 8))
        self.ext_textbox.bind("<KeyRelease>", self._on_extensions_text_changed)

        lbl_example = ctk.CTkLabel(
            right_col,
            text="Ejemplo: .pdf, .docx, .xlsx, .txt, .epub",
            font=ctk.CTkFont(size=10),
            text_color="gray",
        )
        lbl_example.pack(anchor="w")

        self._refresh_categories_list()

    def _refresh_categories_list(self):
        # Clear existing buttons
        for w in self.cat_listbox_frame.winfo_children():
            w.destroy()

        if self.selected_category not in self.working_categories:
            self.selected_category = next(iter(self.working_categories), "")

        for cat_name in list(self.working_categories.keys()):
            is_active = (cat_name == self.selected_category)
            fg = COLOR_PRIMARY if is_active else "transparent"
            txt_color = "white" if is_active else ("gray10", "gray90")

            def select_cat(name=cat_name):
                self._save_current_extensions_from_textbox()
                self.selected_category = name
                self._refresh_categories_list()

            b = ctk.CTkButton(
                self.cat_listbox_frame,
                text=cat_name,
                fg_color=fg,
                text_color=txt_color,
                height=26,
                anchor="w",
                command=select_cat,
            )
            b.pack(fill="x", pady=1)

        # Update right pane
        if self.selected_category:
            self.lbl_selected_cat.configure(text=f"Categoria: {self.selected_category}")
            current_exts = self.working_categories.get(self.selected_category, [])
            self.ext_textbox.delete("1.0", "end")
            self.ext_textbox.insert("1.0", ", ".join(current_exts))
        else:
            self.lbl_selected_cat.configure(text="No hay categorias seleccionadas")
            self.ext_textbox.delete("1.0", "end")

    def _save_current_extensions_from_textbox(self):
        if not self.selected_category:
            return
        content = self.ext_textbox.get("1.0", "end").strip()
        # Parse tokens
        raw_tokens = [t.strip() for t in content.replace("\n", ",").split(",") if t.strip()]
        normalized = []
        for token in raw_tokens:
            norm = normalize_extension(token)
            if norm and norm not in normalized:
                normalized.append(norm)
        self.working_categories[self.selected_category] = normalized

    def _on_extensions_text_changed(self, event=None):
        self._save_current_extensions_from_textbox()

    def _on_add_category(self):
        dialog = ctk.CTkInputDialog(text="Nombre de la nueva categoria:", title="Nueva Categoria")
        name = dialog.get_input()
        if name and name.strip():
            clean_name = name.strip()
            if clean_name in self.working_categories:
                messagebox.showwarning("Atencion", "Ya existe una categoria con ese nombre.")
                return
            self._save_current_extensions_from_textbox()
            self.working_categories[clean_name] = []
            self.selected_category = clean_name
            self._refresh_categories_list()

    def _on_delete_category(self):
        if not self.selected_category:
            return
        if len(self.working_categories) <= 1:
            messagebox.showwarning("Atencion", "Debe existir al menos una categoria.")
            return

        confirm = messagebox.askyesno(
            "Eliminar Categoria",
            f"Deseas eliminar la categoria '{self.selected_category}'?",
        )
        if confirm:
            del self.working_categories[self.selected_category]
            self.selected_category = next(iter(self.working_categories), "")
            self._refresh_categories_list()

    # ----------------------------------------------------
    # TAB 2: Archivos Ignorados
    # ----------------------------------------------------
    def _build_tab_ignored(self, parent):
        lbl_info = ctk.CTkLabel(
            parent,
            text=(
                "Lista de nombres exactos de archivos o carpetas que FilesPy ignorara al escanear.\n"
                "Escribe un nombre o patron por linea:"
            ),
            font=ctk.CTkFont(size=11),
            justify="left",
            text_color="gray",
        )
        lbl_info.pack(anchor="w", padx=10, pady=(10, 6))

        self.ignored_textbox = ctk.CTkTextbox(parent, font=ctk.CTkFont(family="Courier", size=12))
        self.ignored_textbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        current_ignored = self.working_settings.get("ignored_patterns", [])
        self.ignored_textbox.insert("1.0", "\n".join(current_ignored))

    # ----------------------------------------------------
    # TAB 3: Opciones Generales
    # ----------------------------------------------------
    def _build_tab_general(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=8)

        # Section: Nombres de carpetas
        lbl_sec1 = ctk.CTkLabel(scroll, text="Nombres de Carpetas de Destino:", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_sec1.pack(anchor="w", pady=(4, 6))

        # Folder: Unorganized
        f1 = ctk.CTkFrame(scroll, fg_color="transparent")
        f1.pack(fill="x", pady=3)
        ctk.CTkLabel(f1, text="Carpeta para archivos sin clasificar:", width=260, anchor="w").pack(side="left")
        self.entry_unorg = ctk.CTkEntry(f1, width=180)
        self.entry_unorg.insert(0, self.working_settings.get("unorganized_folder", "Otros"))
        self.entry_unorg.pack(side="left")

        # Folder: No extension
        f2 = ctk.CTkFrame(scroll, fg_color="transparent")
        f2.pack(fill="x", pady=3)
        ctk.CTkLabel(f2, text="Carpeta para archivos sin extension:", width=260, anchor="w").pack(side="left")
        self.entry_no_ext = ctk.CTkEntry(f2, width=180)
        self.entry_no_ext.insert(0, self.working_settings.get("no_extension_folder", "SIN_EXTENSION"))
        self.entry_no_ext.pack(side="left")

        # Folder: Duplicates
        f3 = ctk.CTkFrame(scroll, fg_color="transparent")
        f3.pack(fill="x", pady=3)
        ctk.CTkLabel(f3, text="Carpeta para copias duplicadas:", width=260, anchor="w").pack(side="left")
        self.entry_dup = ctk.CTkEntry(f3, width=180)
        self.entry_dup.insert(0, self.working_settings.get("duplicates_folder", "_Duplicados"))
        self.entry_dup.pack(side="left")

        # Section: Seguridad
        lbl_sec2 = ctk.CTkLabel(scroll, text="Seguridad y Confirmaciones:", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_sec2.pack(anchor="w", pady=(14, 6))

        self.confirm_var = ctk.BooleanVar(value=bool(self.working_settings.get("confirm_before_apply", True)))
        self.chk_confirm = ctk.CTkCheckBox(
            scroll,
            text="Solicitar confirmacion antes de aplicar cambios en el disco",
            variable=self.confirm_var,
        )
        self.chk_confirm.pack(anchor="w", pady=3)

        # Section: Limite de visualizacion
        lbl_sec3 = ctk.CTkLabel(scroll, text="Visor e Inspeccion:", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_sec3.pack(anchor="w", pady=(14, 6))

        f4 = ctk.CTkFrame(scroll, fg_color="transparent")
        f4.pack(fill="x", pady=3)
        ctk.CTkLabel(f4, text="Tamano maximo de vista previa de texto (KB):", width=260, anchor="w").pack(side="left")
        self.entry_max_txt = ctk.CTkEntry(f4, width=80)
        self.entry_max_txt.insert(0, str(self.working_settings.get("max_text_preview_size_kb", 512)))
        self.entry_max_txt.pack(side="left")

    # ----------------------------------------------------
    # Bottom Actions
    # ----------------------------------------------------
    def _on_reset(self):
        confirm = messagebox.askyesno(
            "Restablecer Valores",
            "Deseas restaurar todas las opciones y categorias a los valores iniciales predeterminados?",
        )
        if confirm:
            raw_cats = DEFAULT_SETTINGS.get("categories", {})
            self.working_categories = {k: list(v) for k, v in raw_cats.items()}
            self.selected_category = next(iter(self.working_categories), "Documentos")
            self._refresh_categories_list()

            self.ignored_textbox.delete("1.0", "end")
            self.ignored_textbox.insert("1.0", "\n".join(DEFAULT_SETTINGS.get("ignored_patterns", [])))

            self.entry_unorg.delete(0, "end")
            self.entry_unorg.insert(0, DEFAULT_SETTINGS.get("unorganized_folder", "Otros"))

            self.entry_no_ext.delete(0, "end")
            self.entry_no_ext.insert(0, DEFAULT_SETTINGS.get("no_extension_folder", "SIN_EXTENSION"))

            self.entry_dup.delete(0, "end")
            self.entry_dup.insert(0, DEFAULT_SETTINGS.get("duplicates_folder", "_Duplicados"))

            self.confirm_var.set(DEFAULT_SETTINGS.get("confirm_before_apply", True))

            self.entry_max_txt.delete(0, "end")
            self.entry_max_txt.insert(0, str(DEFAULT_SETTINGS.get("max_text_preview_size_kb", 512)))

    def _on_save(self):
        self._save_current_extensions_from_textbox()

        # Parse ignored patterns
        raw_ignored = self.ignored_textbox.get("1.0", "end").strip().splitlines()
        clean_ignored = [p.strip() for p in raw_ignored if p.strip()]

        # Parse text preview size limit
        try:
            max_txt_kb = max(10, int(self.entry_max_txt.get().strip()))
        except ValueError:
            max_txt_kb = 512

        new_settings = {
            "categories": self.working_categories,
            "ignored_patterns": clean_ignored,
            "no_extension_folder": self.entry_no_ext.get().strip() or "SIN_EXTENSION",
            "unorganized_folder": self.entry_unorg.get().strip() or "Otros",
            "duplicates_folder": self.entry_dup.get().strip() or "_Duplicados",
            "confirm_before_apply": self.confirm_var.get(),
            "max_text_preview_size_kb": max_txt_kb,
        }

        self.config_manager.save_settings(new_settings)
        self.on_saved()
        self.destroy()
