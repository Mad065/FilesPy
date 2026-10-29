"""Settings modal dialog for Flet."""
from typing import Callable, Dict, List
import flet as ft

from core.config_manager import ConfigManager, DEFAULT_SETTINGS, normalize_extension
from ui.theme import (
    COLOR_BORDER_DARK,
    COLOR_CARD_DARK,
    COLOR_PRIMARY,
    COLOR_SURFACE_DARK,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    safe_update,
)


class SettingsDialog:
    """Modal dialog for editing app configuration in Flet."""

    def __init__(
        self,
        page: ft.Page,
        config_manager: ConfigManager,
        on_saved: Callable[[], None],
    ):
        self.page = page
        self.config_manager = config_manager
        self.on_saved = on_saved

        self.working_settings = dict(self.config_manager.settings)
        raw_cats = self.working_settings.get("categories", {})
        self.working_categories: Dict[str, List[str]] = {
            k: list(v) for k, v in raw_cats.items()
        }
        self.selected_category: str = next(iter(self.working_categories), "Documentos")

        self._build_dialog()

    def _build_dialog(self):
        # TAB 1: Categories & Extensions
        self.cat_list_col = ft.Column(spacing=2, scroll=ft.ScrollMode.AUTO)
        self.lbl_selected_cat = ft.Text(f"Categoria: {self.selected_category}", weight=ft.FontWeight.W_600, size=12)
        self.ext_field = ft.TextField(
            multiline=True,
            min_lines=6,
            max_lines=6,
            dense=True,
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            text_size=12,
            on_change=lambda _: self._save_current_extensions_from_textbox(),
        )

        btn_new_cat = ft.Button(
            "Nueva Categoria",
            icon=ft.Icons.ADD,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=6),
                bgcolor=COLOR_CARD_DARK,
                color=COLOR_TEXT_PRIMARY,
            ),
            on_click=self._on_add_category_prompt,
        )

        btn_del_cat = ft.OutlinedButton(
            "Eliminar",
            icon=ft.Icons.DELETE_OUTLINE,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=6),
                side=ft.BorderSide(1, COLOR_BORDER_DARK),
                color=COLOR_TEXT_MUTED,
            ),
            on_click=lambda _: self._on_delete_category(),
        )

        tab_ext_content = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Categorias:", weight=ft.FontWeight.W_600, size=12),
                            ft.Container(content=self.cat_list_col, height=170),
                            ft.Row([btn_new_cat, btn_del_cat], spacing=4),
                        ],
                        spacing=6,
                    ),
                    width=230,
                    padding=8,
                    bgcolor=COLOR_CARD_DARK,
                    border_radius=8,
                    border=ft.Border.all(1, COLOR_BORDER_DARK),
                ),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            self.lbl_selected_cat,
                            ft.Text(
                                "Extensiones reconocidas (separadas por comas o saltos de linea):",
                                size=11,
                                color=COLOR_TEXT_MUTED,
                            ),
                            self.ext_field,
                            ft.Text("Ejemplo: .pdf, .docx, .xlsx, .txt, .epub", size=10, color=COLOR_TEXT_MUTED),
                        ],
                        spacing=6,
                    ),
                    expand=True,
                    padding=8,
                ),
            ],
            spacing=10,
        )

        # TAB 2: Ignored files
        self.ignored_field = ft.TextField(
            multiline=True,
            min_lines=9,
            max_lines=9,
            dense=True,
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            text_size=12,
            value="\n".join(self.working_settings.get("ignored_patterns", [])),
        )

        tab_ignored_content = ft.Column(
            controls=[
                ft.Text(
                    "Nombres de archivos o carpetas que FilesPy ignorara al escanear (uno por linea):",
                    size=11,
                    color=COLOR_TEXT_MUTED,
                ),
                self.ignored_field,
            ],
            spacing=8,
        )

        # TAB 3: General Options
        self.entry_unorg = ft.TextField(
            label="Archivos sin clasificar",
            value=self.working_settings.get("unorganized_folder", "Otros"),
            dense=True,
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
        )

        self.entry_no_ext = ft.TextField(
            label="Archivos sin extension",
            value=self.working_settings.get("no_extension_folder", "SIN_EXTENSION"),
            dense=True,
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
        )

        self.entry_dup = ft.TextField(
            label="Copias duplicadas",
            value=self.working_settings.get("duplicates_folder", "_Duplicados"),
            dense=True,
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
        )

        self.switch_confirm = ft.Switch(
            label="Solicitar confirmacion antes de aplicar cambios en disco",
            value=bool(self.working_settings.get("confirm_before_apply", True)),
            active_color=COLOR_PRIMARY,
        )

        tab_general_content = ft.Column(
            controls=[
                self.entry_unorg,
                self.entry_no_ext,
                self.entry_dup,
                ft.Container(height=6),
                self.switch_confirm,
            ],
            spacing=10,
        )

        # Settings Content Switcher (SegmentedButton)
        self.settings_content = ft.Container(content=tab_ext_content, expand=True)

        def on_settings_nav_changed(e):
            sel = e.control.selected
            val = list(sel)[0] if sel else "categories"
            if val == "categories":
                self.settings_content.content = tab_ext_content
            elif val == "ignored":
                self.settings_content.content = tab_ignored_content
            elif val == "general":
                self.settings_content.content = tab_general_content
            safe_update(self.settings_content)

        self.settings_nav = ft.SegmentedButton(
            selected=["categories"],
            allow_empty_selection=False,
            segments=[
                ft.Segment(value="categories", label=ft.Text("Categorias y Extensiones", size=11), icon=ft.Icons.CATEGORY_OUTLINED),
                ft.Segment(value="ignored", label=ft.Text("Archivos Ignorados", size=11), icon=ft.Icons.BLOCK_OUTLINED),
                ft.Segment(value="general", label=ft.Text("Opciones Generales", size=11), icon=ft.Icons.TUNE_OUTLINED),
            ],
            on_change=on_settings_nav_changed,
        )

        self._refresh_categories_list()

        # Dialog
        self.dialog = ft.AlertDialog(
            title=ft.Text("Configuracion", weight=ft.FontWeight.W_600, size=16),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        self.settings_nav,
                        ft.Divider(height=1, color=COLOR_BORDER_DARK),
                        self.settings_content,
                    ],
                    spacing=6,
                    expand=True,
                ),
                width=640,
                height=360,
            ),
            actions=[
                ft.TextButton("Restablecer Valores", on_click=lambda _: self._on_reset()),
                ft.TextButton("Cancelar", on_click=lambda _: self.page.pop_dialog()),
                ft.FilledButton(
                    "Guardar",
                    icon=ft.Icons.CHECK,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8),
                        bgcolor=COLOR_PRIMARY,
                        color="#FFFFFF",
                    ),
                    on_click=lambda _: self._on_save(),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def show(self):
        self.page.show_dialog(self.dialog)

    def _refresh_categories_list(self):
        self.cat_list_col.controls.clear()
        if self.selected_category not in self.working_categories:
            self.selected_category = next(iter(self.working_categories), "")

        for cat_name in list(self.working_categories.keys()):
            is_active = (cat_name == self.selected_category)

            def select_cat(e, name=cat_name):
                self._save_current_extensions_from_textbox()
                self.selected_category = name
                self._refresh_categories_list()
                safe_update(self.cat_list_col)
                safe_update(self.lbl_selected_cat)
                safe_update(self.ext_field)

            item_btn = ft.Container(
                content=ft.Text(
                    cat_name,
                    size=12,
                    weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.NORMAL,
                    color=COLOR_PRIMARY if is_active else COLOR_TEXT_PRIMARY,
                ),
                padding=ft.Padding.symmetric(horizontal=8, vertical=5),
                bgcolor=COLOR_SURFACE_DARK if is_active else None,
                border_radius=6,
                on_click=select_cat,
                ink=True,
            )
            self.cat_list_col.controls.append(item_btn)

        if self.selected_category:
            self.lbl_selected_cat.value = f"Categoria: {self.selected_category}"
            exts = self.working_categories.get(self.selected_category, [])
            self.ext_field.value = ", ".join(exts)
        else:
            self.lbl_selected_cat.value = "Sin categorias"
            self.ext_field.value = ""

    def _save_current_extensions_from_textbox(self):
        if not self.selected_category:
            return
        content = self.ext_field.value or ""
        tokens = [t.strip() for t in content.replace("\n", ",").split(",") if t.strip()]
        normalized = []
        for t in tokens:
            norm = normalize_extension(t)
            if norm and norm not in normalized:
                normalized.append(norm)
        self.working_categories[self.selected_category] = normalized

    def _on_add_category_prompt(self, e):
        new_name_field = ft.TextField(label="Nombre de categoria", dense=True, autofocus=True)

        def add_cat(ev):
            val = new_name_field.value.strip() if new_name_field.value else ""
            if val and val not in self.working_categories:
                self._save_current_extensions_from_textbox()
                self.working_categories[val] = []
                self.selected_category = val
                self._refresh_categories_list()
                safe_update(self.cat_list_col)
                safe_update(self.lbl_selected_cat)
                safe_update(self.ext_field)
            self.page.pop_dialog()

        prompt_dialog = ft.AlertDialog(
            title=ft.Text("Nueva Categoria"),
            content=new_name_field,
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self.page.pop_dialog()),
                ft.FilledButton("Crear", on_click=add_cat, bgcolor=COLOR_PRIMARY, color="#FFFFFF"),
            ],
        )
        self.page.show_dialog(prompt_dialog)

    def _on_delete_category(self):
        if not self.selected_category or len(self.working_categories) <= 1:
            return
        del self.working_categories[self.selected_category]
        self.selected_category = next(iter(self.working_categories), "")
        self._refresh_categories_list()
        safe_update(self.cat_list_col)
        safe_update(self.lbl_selected_cat)
        safe_update(self.ext_field)

    def _on_reset(self):
        raw_cats = DEFAULT_SETTINGS.get("categories", {})
        self.working_categories = {k: list(v) for k, v in raw_cats.items()}
        self.selected_category = next(iter(self.working_categories), "Documentos")
        self._refresh_categories_list()

        self.ignored_field.value = "\n".join(DEFAULT_SETTINGS.get("ignored_patterns", []))
        self.entry_unorg.value = DEFAULT_SETTINGS.get("unorganized_folder", "Otros")
        self.entry_no_ext.value = DEFAULT_SETTINGS.get("no_extension_folder", "SIN_EXTENSION")
        self.entry_dup.value = DEFAULT_SETTINGS.get("duplicates_folder", "_Duplicados")
        self.switch_confirm.value = bool(DEFAULT_SETTINGS.get("confirm_before_apply", True))

        safe_update(self.dialog)

    def _on_save(self):
        self._save_current_extensions_from_textbox()
        raw_ignored = (self.ignored_field.value or "").strip().splitlines()
        clean_ignored = [p.strip() for p in raw_ignored if p.strip()]

        new_settings = {
            "categories": self.working_categories,
            "ignored_patterns": clean_ignored,
            "no_extension_folder": self.entry_no_ext.value.strip() if self.entry_no_ext.value else "SIN_EXTENSION",
            "unorganized_folder": self.entry_unorg.value.strip() if self.entry_unorg.value else "Otros",
            "duplicates_folder": self.entry_dup.value.strip() if self.entry_dup.value else "_Duplicados",
            "confirm_before_apply": bool(self.switch_confirm.value),
        }
        self.config_manager.save_settings(new_settings)
        self.page.pop_dialog()
        self.on_saved()
