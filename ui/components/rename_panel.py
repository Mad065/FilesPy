"""Rename rules configuration panel."""
from typing import Callable
import customtkinter as ctk
from core.models import RenameConfig


class RenamePanel(ctk.CTkFrame):
    """Configuration panel for batch file renaming rules."""

    def __init__(self, master, on_change: Callable[[RenameConfig], None], **kwargs):
        super().__init__(master, **kwargs)
        self.on_change = on_change
        self._build_widgets()

    def _build_widgets(self):
        # Section 1: Text Replacement
        replace_frame = ctk.CTkFrame(self, fg_color="transparent")
        replace_frame.pack(fill="x", padx=10, pady=(10, 5))

        lbl_find = ctk.CTkLabel(replace_frame, text="Buscar texto:", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_find.pack(anchor="w")

        self.find_entry = ctk.CTkEntry(replace_frame, placeholder_text="Texto a buscar...")
        self.find_entry.pack(fill="x", pady=(2, 6))
        self.find_entry.bind("<KeyRelease>", self._trigger_change)

        lbl_replace = ctk.CTkLabel(replace_frame, text="Reemplazar con:", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_replace.pack(anchor="w")

        self.replace_entry = ctk.CTkEntry(replace_frame, placeholder_text="Nuevo texto...")
        self.replace_entry.pack(fill="x", pady=(2, 6))
        self.replace_entry.bind("<KeyRelease>", self._trigger_change)

        # Options for replacement
        opts_frame = ctk.CTkFrame(replace_frame, fg_color="transparent")
        opts_frame.pack(fill="x", pady=2)

        self.match_case_var = ctk.BooleanVar(value=False)
        self.chk_match_case = ctk.CTkCheckBox(
            opts_frame, text="Mayús/Minús", variable=self.match_case_var,
            font=ctk.CTkFont(size=11), command=self._trigger_change
        )
        self.chk_match_case.pack(side="left", padx=(0, 10))

        self.regex_var = ctk.BooleanVar(value=False)
        self.chk_regex = ctk.CTkCheckBox(
            opts_frame, text="Regex", variable=self.regex_var,
            font=ctk.CTkFont(size=11), command=self._trigger_change
        )
        self.chk_regex.pack(side="left")

        # Section 2: Prefix and Suffix
        affix_frame = ctk.CTkFrame(self, fg_color="transparent")
        affix_frame.pack(fill="x", padx=10, pady=5)

        lbl_prefix = ctk.CTkLabel(affix_frame, text="Prefijo (al inicio):", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_prefix.pack(anchor="w")
        self.prefix_entry = ctk.CTkEntry(affix_frame, placeholder_text="ej. Foto_ o 2026_")
        self.prefix_entry.pack(fill="x", pady=(2, 6))
        self.prefix_entry.bind("<KeyRelease>", self._trigger_change)

        lbl_suffix = ctk.CTkLabel(affix_frame, text="Sufijo (al final):", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_suffix.pack(anchor="w")
        self.suffix_entry = ctk.CTkEntry(affix_frame, placeholder_text="ej. _FINAL o _v1")
        self.suffix_entry.pack(fill="x", pady=(2, 6))
        self.suffix_entry.bind("<KeyRelease>", self._trigger_change)

        # Section 3: Sequential Numbering
        num_frame = ctk.CTkFrame(self, fg_color="transparent")
        num_frame.pack(fill="x", padx=10, pady=5)

        self.numbering_var = ctk.BooleanVar(value=False)
        self.chk_numbering = ctk.CTkCheckBox(
            num_frame, text="Numeración Secuencial", variable=self.numbering_var,
            font=ctk.CTkFont(size=12, weight="bold"), command=self._trigger_change
        )
        self.chk_numbering.pack(anchor="w", pady=(0, 4))

        num_sub_frame = ctk.CTkFrame(num_frame, fg_color="transparent")
        num_sub_frame.pack(fill="x", pady=2)

        lbl_start = ctk.CTkLabel(num_sub_frame, text="Inicio:", font=ctk.CTkFont(size=11))
        lbl_start.pack(side="left", padx=(0, 4))
        self.num_start_entry = ctk.CTkEntry(num_sub_frame, width=50)
        self.num_start_entry.insert(0, "1")
        self.num_start_entry.pack(side="left", padx=(0, 10))
        self.num_start_entry.bind("<KeyRelease>", self._trigger_change)

        lbl_digits = ctk.CTkLabel(num_sub_frame, text="Dígitos:", font=ctk.CTkFont(size=11))
        lbl_digits.pack(side="left", padx=(0, 4))
        self.digits_menu = ctk.CTkOptionMenu(
            num_sub_frame, values=["1", "2", "3", "4", "5"], width=65,
            command=lambda _: self._trigger_change()
        )
        self.digits_menu.set("3")
        self.digits_menu.pack(side="left")

        # Section 4: Case & Extensions
        extra_frame = ctk.CTkFrame(self, fg_color="transparent")
        extra_frame.pack(fill="x", padx=10, pady=5)

        lbl_case = ctk.CTkLabel(extra_frame, text="Formato de Mayúsculas:", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_case.pack(anchor="w")

        self.case_map = {
            "Original (Sin cambio)": "original",
            "minúsculas": "lower",
            "MAYÚSCULAS": "upper",
            "Título (Capitalize)": "title",
            "snake_case": "snake",
            "kebab-case": "kebab",
        }
        self.case_menu = ctk.CTkOptionMenu(
            extra_frame,
            values=list(self.case_map.keys()),
            command=lambda _: self._trigger_change(),
        )
        self.case_menu.set("Original (Sin cambio)")
        self.case_menu.pack(fill="x", pady=(2, 6))

        lbl_ext = ctk.CTkLabel(extra_frame, text="Cambiar Extensión (opcional):", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_ext.pack(anchor="w")
        self.ext_entry = ctk.CTkEntry(extra_frame, placeholder_text="ej. jpg o png (dejar vacío para mantener)")
        self.ext_entry.pack(fill="x", pady=(2, 6))
        self.ext_entry.bind("<KeyRelease>", self._trigger_change)

        # Reset button
        btn_reset = ctk.CTkButton(
            self, text="Restablecer Reglas", fg_color="transparent",
            border_width=1, text_color=("gray10", "gray90"),
            command=self.reset_rules, height=28
        )
        btn_reset.pack(fill="x", padx=10, pady=(10, 10))

    def _trigger_change(self, event=None):
        config = self.get_config()
        self.on_change(config)

    def get_config(self) -> RenameConfig:
        start_val = 1
        try:
            start_val = int(self.num_start_entry.get().strip())
        except ValueError:
            start_val = 1

        digits_val = 3
        try:
            digits_val = int(self.digits_menu.get())
        except ValueError:
            digits_val = 3

        selected_case = self.case_map.get(self.case_menu.get(), "original")

        return RenameConfig(
            find_text=self.find_entry.get(),
            replace_text=self.replace_entry.get(),
            match_case=self.match_case_var.get(),
            use_regex=self.regex_var.get(),
            prefix=self.prefix_entry.get(),
            suffix=self.suffix_entry.get(),
            numbering_enabled=self.numbering_var.get(),
            numbering_start=start_val,
            numbering_digits=digits_val,
            case_mode=selected_case,
            preserve_extension=True,
            custom_extension=self.ext_entry.get().strip(),
        )

    def reset_rules(self):
        self.find_entry.delete(0, "end")
        self.replace_entry.delete(0, "end")
        self.match_case_var.set(False)
        self.regex_var.set(False)
        self.prefix_entry.delete(0, "end")
        self.suffix_entry.delete(0, "end")
        self.numbering_var.set(False)
        self.num_start_entry.delete(0, "end")
        self.num_start_entry.insert(0, "1")
        self.digits_menu.set("3")
        self.case_menu.set("Original (Sin cambio)")
        self.ext_entry.delete(0, "end")
        self._trigger_change()
