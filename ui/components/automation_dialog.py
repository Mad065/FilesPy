"""Automation and Folder Monitoring Window/Dialog for FilesPy (Flet)."""
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional
import uuid
import flet as ft

from core.automation import AutomationManager
from core.models import FolderMonitorStatus, MonitoredFolderRule
from ui.theme import (
    COLOR_BG_DARK,
    COLOR_BORDER_DARK,
    COLOR_CARD_DARK,
    COLOR_DANGER,
    COLOR_INFO,
    COLOR_PRIMARY,
    COLOR_SUCCESS,
    COLOR_SURFACE_DARK,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_WARNING,
    safe_update,
)


class FolderRuleEditorDialog:
    """Modal sub-dialog to add or edit a MonitoredFolderRule."""

    def __init__(
        self,
        page: ft.Page,
        file_picker: ft.FilePicker,
        on_save: Callable[[MonitoredFolderRule], None],
        existing_rule: Optional[MonitoredFolderRule] = None,
        default_folder: Optional[Path] = None,
        default_manual_folders: Optional[List[str]] = None,
    ):
        self.page = page
        self.file_picker = file_picker
        self.on_save = on_save
        self.existing_rule = existing_rule

        if existing_rule:
            self.rule_id = existing_rule.id
            init_path = existing_rule.path
            init_name = existing_rule.name
            init_auto = "auto" if existing_rule.auto_apply else "on_demand"
            init_org_mode = existing_rule.organize_mode
            init_custom_sub = existing_rule.custom_subfolder
            init_ext_filter = existing_rule.extension_filter
            init_ren_enabled = existing_rule.rename_enabled
            init_prefix = existing_rule.rename_prefix
            init_suffix = existing_rule.rename_suffix
            init_date_pfx = existing_rule.rename_date_prefix
            init_find = existing_rule.rename_find
            init_replace = existing_rule.rename_replace
            init_case = existing_rule.rename_case_mode or "original"
            self.manual_folders = list(existing_rule.manual_folders)
        else:
            self.rule_id = str(uuid.uuid4())
            init_path = str(default_folder) if default_folder else ""
            init_name = default_folder.name if default_folder else ""
            init_auto = "auto"
            init_org_mode = "by_category"
            init_custom_sub = "Clasificados"
            init_ext_filter = ""
            init_ren_enabled = False
            init_prefix = ""
            init_suffix = ""
            init_date_pfx = False
            init_find = ""
            init_replace = ""
            init_case = "original"
            self.manual_folders = list(
                default_manual_folders or ["Documentos", "Imágenes", "Facturas", "Trabajo", "Personal"]
            )

        self._build_ui(
            init_path=init_path,
            init_name=init_name,
            init_auto=init_auto,
            init_org_mode=init_org_mode,
            init_custom_sub=init_custom_sub,
            init_ext_filter=init_ext_filter,
            init_ren_enabled=init_ren_enabled,
            init_prefix=init_prefix,
            init_suffix=init_suffix,
            init_date_pfx=init_date_pfx,
            init_find=init_find,
            init_replace=init_replace,
            init_case=init_case,
        )

    def _build_ui(
        self,
        init_path: str,
        init_name: str,
        init_auto: str,
        init_org_mode: str,
        init_custom_sub: str,
        init_ext_filter: str,
        init_ren_enabled: bool,
        init_prefix: str,
        init_suffix: str,
        init_date_pfx: bool,
        init_find: str,
        init_replace: str,
        init_case: str,
    ):
        # 1. Folder selection
        self.txt_path = ft.TextField(
            label="Carpeta a monitorear",
            hint_text="/Users/.../Descargas",
            value=init_path,
            dense=True,
            text_size=11.5,
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            expand=True,
        )

        self.btn_browse = ft.OutlinedButton(
            "Explorar...",
            icon=ft.Icons.FOLDER_OPEN_OUTLINED,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(1, COLOR_BORDER_DARK),
                color=COLOR_TEXT_PRIMARY,
            ),
            on_click=self._on_browse_click,
        )

        self.txt_name = ft.TextField(
            label="Nombre / Alias (opcional)",
            hint_text="Ej. Descargas Diarias",
            value=init_name,
            dense=True,
            text_size=11,
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            expand=True,
        )

        self.txt_ext_filter = ft.TextField(
            label="Filtrar extensiones (opcional)",
            hint_text="Ej. .pdf, .jpg (vacío = todos)",
            value=init_ext_filter,
            dense=True,
            text_size=11,
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            expand=True,
        )

        # 2. Trigger Mode & Organization Action
        self.dd_trigger = ft.Dropdown(
            label="¿Cuándo ejecutar las acciones?",
            value=init_auto,
            dense=True,
            text_size=11,
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            expand=True,
            options=[
                ft.dropdown.Option(
                    "auto",
                    "⚡ Automático (al detectar archivos) y también cuando yo lo diga",
                ),
                ft.dropdown.Option(
                    "on_demand",
                    "👆 Solo cuando yo lo diga (monitorear estatus y ordenar con clic)",
                ),
            ],
        )

        self.dd_org_mode = ft.Dropdown(
            label="Acción de Carpeta / Subcarpeta",
            value=init_org_mode,
            dense=True,
            text_size=11,
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            expand=True,
            options=[
                ft.dropdown.Option("by_category", "📂 Guardar en subcarpeta por Categoría (Documentos, Imágenes...)"),
                ft.dropdown.Option("by_extension", "📄 Guardar en subcarpeta por Extensión (/PDF, /JPG, /TXT...)"),
                ft.dropdown.Option("by_date", "📅 Guardar en subcarpeta por Fecha (Año/Mes, ej. 2026/11)"),
                ft.dropdown.Option("custom_subfolder", "📁 Guardar en una Subcarpeta Específica (personalizada)"),
                ft.dropdown.Option("manual", "🖐️ Orden Manual Interactivo (permitir ordenarla haciendo clic)"),
                ft.dropdown.Option("none", "📍 No mover a subcarpeta (solo aplicar cambio de nombre)"),
            ],
            on_select=self._on_org_mode_changed,
        )

        # Custom subfolder box
        self.txt_custom_subfolder = ft.TextField(
            label="Nombre de la subcarpeta destino",
            hint_text="Ej. Clasificados o Recibidos/2026",
            value=init_custom_sub,
            dense=True,
            text_size=11,
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
        )
        self.custom_subfolder_box = ft.Container(
            content=self.txt_custom_subfolder,
            visible=(init_org_mode == "custom_subfolder"),
        )

        # Manual folders configuration box
        self.txt_new_manual_folder = ft.TextField(
            hint_text="Agregar carpeta destino rápida (ej. Facturas)...",
            dense=True,
            text_size=11,
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            expand=True,
            on_submit=lambda _: self._on_add_manual_folder(),
        )
        self.btn_add_manual_folder = ft.IconButton(
            icon=ft.Icons.ADD,
            icon_color=COLOR_PRIMARY,
            tooltip="Agregar carpeta",
            on_click=lambda _: self._on_add_manual_folder(),
        )
        self.manual_chips_row = ft.Row(wrap=True, spacing=6, run_spacing=6)
        self._render_manual_chips()

        self.manual_folders_box = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Carpetas disponibles al ordenar manualmente haciendo clic:",
                        size=10.5,
                        weight=ft.FontWeight.W_600,
                        color=COLOR_TEXT_SECONDARY,
                    ),
                    ft.Row([self.txt_new_manual_folder, self.btn_add_manual_folder], spacing=4),
                    self.manual_chips_row,
                ],
                spacing=6,
            ),
            bgcolor=COLOR_CARD_DARK,
            border_radius=8,
            padding=8,
            border=ft.Border.all(1, COLOR_BORDER_DARK),
            visible=(init_org_mode == "manual"),
        )

        # 3. Rename Action
        self.sw_rename = ft.Switch(
            label="Automatizar cambio de nombre del archivo",
            value=init_ren_enabled,
            active_color=COLOR_PRIMARY,
            on_change=self._on_rename_toggled,
        )

        self.txt_prefix = ft.TextField(
            label="Prefijo (al inicio)",
            hint_text="Ej. DOC_",
            value=init_prefix,
            dense=True,
            text_size=11,
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            expand=True,
        )

        self.txt_suffix = ft.TextField(
            label="Sufijo (al final)",
            hint_text="Ej. _ok",
            value=init_suffix,
            dense=True,
            text_size=11,
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            expand=True,
        )

        self.chk_date_prefix = ft.Checkbox(
            label="Anteponer fecha (YYYYMMDD_)",
            value=init_date_pfx,
            active_color=COLOR_PRIMARY,
            label_style=ft.TextStyle(size=11, color=COLOR_TEXT_PRIMARY),
        )

        self.dd_case = ft.Dropdown(
            label="Formato de Mayúsculas / Minúsculas",
            value=init_case,
            dense=True,
            text_size=11,
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            expand=True,
            options=[
                ft.dropdown.Option("original", "Original (Sin cambio)"),
                ft.dropdown.Option("snake", "snake_case (guiones_bajos)"),
                ft.dropdown.Option("kebab", "kebab-case (guiones-medios)"),
                ft.dropdown.Option("lower", "minúsculas"),
                ft.dropdown.Option("upper", "MAYÚSCULAS"),
                ft.dropdown.Option("title", "Título (Capitalize)"),
            ],
        )

        self.txt_find = ft.TextField(
            label="Buscar texto en el nombre",
            value=init_find,
            dense=True,
            text_size=11,
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            expand=True,
        )

        self.txt_replace = ft.TextField(
            label="Reemplazar con",
            value=init_replace,
            dense=True,
            text_size=11,
            border_radius=8,
            border_color=COLOR_BORDER_DARK,
            focused_border_color=COLOR_PRIMARY,
            expand=True,
        )

        self.rename_options_box = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row([self.txt_prefix, self.txt_suffix], spacing=8),
                    ft.Row([self.chk_date_prefix, self.dd_case], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Row([self.txt_find, self.txt_replace], spacing=8),
                ],
                spacing=8,
            ),
            bgcolor=COLOR_CARD_DARK,
            border_radius=8,
            padding=10,
            border=ft.Border.all(1, COLOR_BORDER_DARK),
            visible=init_ren_enabled,
        )

        self.lbl_error = ft.Text("", size=11, color=COLOR_DANGER, visible=False)

        form_col = ft.Column(
            controls=[
                ft.Text("1. Carpeta a Monitorear", size=12, weight=ft.FontWeight.W_600, color=COLOR_PRIMARY),
                ft.Row([self.txt_path, self.btn_browse], spacing=8),
                ft.Row([self.txt_name, self.txt_ext_filter], spacing=8),
                ft.Divider(height=1, color=COLOR_BORDER_DARK),
                ft.Text("2. Modo de Ejecución y Subcarpetas", size=12, weight=ft.FontWeight.W_600, color=COLOR_PRIMARY),
                self.dd_trigger,
                self.dd_org_mode,
                self.custom_subfolder_box,
                self.manual_folders_box,
                ft.Divider(height=1, color=COLOR_BORDER_DARK),
                ft.Text("3. Acciones de Cambio de Nombre", size=12, weight=ft.FontWeight.W_600, color=COLOR_PRIMARY),
                self.sw_rename,
                self.rename_options_box,
                self.lbl_error,
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )

        title_str = "Editar Carpeta Monitoreada" if self.existing_rule else "Agregar Carpeta a Monitorear"
        self.dialog = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CREATE_NEW_FOLDER_ROUNDED, color=COLOR_PRIMARY, size=20),
                    ft.Text(title_str, weight=ft.FontWeight.W_600, size=15),
                ],
                spacing=8,
            ),
            content=ft.Container(
                content=form_col,
                width=640,
                height=440,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self.page.pop_dialog()),
                ft.FilledButton(
                    "Guardar Regla",
                    icon=ft.Icons.CHECK,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8),
                        bgcolor=COLOR_PRIMARY,
                        color="#FFFFFF",
                    ),
                    on_click=lambda _: self._on_save_clicked(),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    async def _on_browse_click(self, e):
        path = await self.file_picker.get_directory_path(
            dialog_title="Seleccionar Carpeta para Monitorear"
        )
        if path:
            resolved = Path(path).resolve()
            self.txt_path.value = str(resolved)
            if not (self.txt_name.value or "").strip():
                self.txt_name.value = resolved.name
            safe_update(self.txt_path)
            safe_update(self.txt_name)

    def _on_org_mode_changed(self, e):
        mode = self.dd_org_mode.value or "by_category"
        self.custom_subfolder_box.visible = (mode == "custom_subfolder")
        self.manual_folders_box.visible = (mode == "manual")
        safe_update(self.custom_subfolder_box)
        safe_update(self.manual_folders_box)

    def _on_rename_toggled(self, e):
        self.rename_options_box.visible = bool(self.sw_rename.value)
        safe_update(self.rename_options_box)

    def _render_manual_chips(self):
        chips: List[ft.Control] = []
        for f in self.manual_folders:
            def make_chip(fname=f):
                return ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.FOLDER_OUTLINED, size=12, color=COLOR_PRIMARY),
                            ft.Text(fname, size=10.5, color=COLOR_TEXT_PRIMARY),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_size=11,
                                icon_color=COLOR_TEXT_MUTED,
                                on_click=lambda _: self._remove_manual_folder(fname),
                            ),
                        ],
                        spacing=2,
                        tight=True,
                    ),
                    bgcolor=COLOR_SURFACE_DARK,
                    border_radius=12,
                    padding=ft.Padding.only(left=8, right=2, top=1, bottom=1),
                    border=ft.Border.all(1, COLOR_BORDER_DARK),
                )
            chips.append(make_chip())
        self.manual_chips_row.controls = chips

    def _on_add_manual_folder(self):
        val = (self.txt_new_manual_folder.value or "").strip().strip("/\\")
        if val and val not in self.manual_folders:
            self.manual_folders.append(val)
            self._render_manual_chips()
            safe_update(self.manual_folders_box)
        self.txt_new_manual_folder.value = ""
        safe_update(self.txt_new_manual_folder)

    def _remove_manual_folder(self, fname: str):
        if fname in self.manual_folders:
            self.manual_folders.remove(fname)
            self._render_manual_chips()
            safe_update(self.manual_folders_box)

    def _on_save_clicked(self):
        raw_path = (self.txt_path.value or "").strip()
        if not raw_path:
            self.lbl_error.value = "Por favor indica la ruta de la carpeta a monitorear."
            self.lbl_error.visible = True
            safe_update(self.lbl_error)
            return

        folder_path = Path(raw_path).expanduser().resolve()
        if not folder_path.exists() or not folder_path.is_dir():
            self.lbl_error.value = f"La ruta indicada no existe o no es una carpeta válida: {folder_path}"
            self.lbl_error.visible = True
            safe_update(self.lbl_error)
            return

        org_mode = self.dd_org_mode.value or "by_category"
        ren_enabled = bool(self.sw_rename.value)

        if org_mode == "none" and not ren_enabled:
            self.lbl_error.value = (
                "Selecciona una acción de subcarpeta o activa el cambio de nombre para que la regla tenga efecto."
            )
            self.lbl_error.visible = True
            safe_update(self.lbl_error)
            return

        custom_sub = (self.txt_custom_subfolder.value or "").strip().strip("/\\")
        if org_mode == "custom_subfolder" and not custom_sub:
            self.lbl_error.value = "Indica el nombre de la subcarpeta personalizada."
            self.lbl_error.visible = True
            safe_update(self.lbl_error)
            return

        rule = MonitoredFolderRule(
            id=self.rule_id,
            path=str(folder_path),
            name=(self.txt_name.value or "").strip() or folder_path.name,
            enabled=self.existing_rule.enabled if self.existing_rule else True,
            auto_apply=(self.dd_trigger.value == "auto"),
            organize_mode=org_mode,
            custom_subfolder=custom_sub,
            extension_filter=(self.txt_ext_filter.value or "").strip(),
            rename_enabled=ren_enabled,
            rename_prefix=(self.txt_prefix.value or ""),
            rename_suffix=(self.txt_suffix.value or ""),
            rename_date_prefix=bool(self.chk_date_prefix.value),
            rename_find=(self.txt_find.value or ""),
            rename_replace=(self.txt_replace.value or ""),
            rename_case_mode=self.dd_case.value or "original",
            manual_folders=list(self.manual_folders) or ["Documentos", "Imágenes", "Facturas"],
        )

        self.page.pop_dialog()
        self.on_save(rule)

    def show(self):
        self.page.show_dialog(self.dialog)


class AutomationMonitorDialog:
    """Main window/dialog for Folder Automation and Real-Time Status Monitoring."""

    def __init__(
        self,
        page: ft.Page,
        automation_manager: AutomationManager,
        file_picker: ft.FilePicker,
        on_open_manual_for_rule: Callable[[MonitoredFolderRule], None],
        on_load_folder_in_main: Callable[[Path], None],
        on_undo_requested: Callable[[], None],
        current_folder: Optional[Path] = None,
    ):
        self.page = page
        self.automation_manager = automation_manager
        self.file_picker = file_picker
        self.on_open_manual_for_rule = on_open_manual_for_rule
        self.on_load_folder_in_main = on_load_folder_in_main
        self.on_undo_requested = on_undo_requested
        self.current_folder = current_folder

        self._build_ui()
        self.refresh_view()

    def _build_ui(self):
        # 1. Header controls
        self.sw_global_active = ft.Switch(
            label="Automatización Activa",
            value=self.automation_manager.is_monitoring_active,
            active_color=COLOR_PRIMARY,
            label_text_style=ft.TextStyle(size=11.5, weight=ft.FontWeight.W_600, color=COLOR_TEXT_PRIMARY),
            on_change=self._on_global_switch_changed,
        )

        self.pill_ordered = ft.Container(
            content=ft.Text("🟢 Ordenadas: 0", size=11, weight=ft.FontWeight.W_600, color=COLOR_SUCCESS),
            bgcolor=COLOR_CARD_DARK,
            border_radius=12,
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            border=ft.Border.all(1, COLOR_BORDER_DARK),
        )
        self.pill_progress = ft.Container(
            content=ft.Text("🔵 En proceso: 0", size=11, weight=ft.FontWeight.W_600, color=COLOR_INFO),
            bgcolor=COLOR_CARD_DARK,
            border_radius=12,
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            border=ft.Border.all(1, COLOR_BORDER_DARK),
        )
        self.pill_pending = ft.Container(
            content=ft.Text("🟡 Aún no ordenadas: 0", size=11, weight=ft.FontWeight.W_600, color=COLOR_WARNING),
            bgcolor=COLOR_CARD_DARK,
            border_radius=12,
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            border=ft.Border.all(1, COLOR_BORDER_DARK),
        )

        header_row = ft.Row(
            controls=[
                ft.Icon(ft.Icons.BOLT_ROUNDED, color=COLOR_PRIMARY, size=24),
                ft.Column(
                    controls=[
                        ft.Text(
                            "Automatización y Monitorización de Carpetas",
                            size=15,
                            weight=ft.FontWeight.W_600,
                            color=COLOR_TEXT_PRIMARY,
                        ),
                        ft.Text(
                            "Vigila carpetas en tiempo real, automatiza subcarpetas y renombrado o ejecuta orden manual con un clic.",
                            size=10.5,
                            color=COLOR_TEXT_MUTED,
                        ),
                    ],
                    spacing=1,
                    expand=True,
                ),
                self.sw_global_active,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # 2. Action Toolbar
        btn_add_folder = ft.FilledButton(
            "＋ Agregar Carpeta",
            icon=ft.Icons.CREATE_NEW_FOLDER_OUTLINED,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                bgcolor=COLOR_PRIMARY,
                color="#FFFFFF",
            ),
            on_click=lambda _: self._open_rule_editor(None),
        )

        self.btn_add_current = ft.OutlinedButton(
            "＋ Monitorear Carpeta Actual",
            icon=ft.Icons.FOLDER_SPECIAL_OUTLINED,
            visible=bool(self.current_folder and self.current_folder.is_dir()),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(1, COLOR_PRIMARY),
                color=COLOR_PRIMARY,
            ),
            on_click=lambda _: self._open_rule_editor(None, use_current=True),
        )

        btn_run_all = ft.OutlinedButton(
            "⚡ Ordenar Todas Ahora",
            icon=ft.Icons.PLAY_ARROW_ROUNDED,
            tooltip="Ejecuta inmediatamente todas las carpetas automáticas/bajo demanda que tengan archivos pendientes",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(1, COLOR_BORDER_DARK),
                color=COLOR_TEXT_PRIMARY,
            ),
            on_click=lambda _: self._on_run_all_clicked(),
        )

        btn_refresh = ft.IconButton(
            icon=ft.Icons.REFRESH_ROUNDED,
            tooltip="Actualizar estatus de todas las carpetas ahora",
            icon_color=COLOR_TEXT_PRIMARY,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                bgcolor=COLOR_CARD_DARK,
                side=ft.BorderSide(1, COLOR_BORDER_DARK),
            ),
            on_click=lambda _: self._on_refresh_clicked(),
        )

        toolbar_row = ft.Row(
            controls=[
                btn_add_folder,
                self.btn_add_current,
                btn_run_all,
                btn_refresh,
                ft.Container(expand=True),
                self.pill_ordered,
                self.pill_progress,
                self.pill_pending,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        )

        # 3. Monitored Folders Cards List
        self.folders_col = ft.Column(
            controls=[],
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        folders_container = ft.Container(
            content=self.folders_col,
            bgcolor=COLOR_BG_DARK,
            border_radius=10,
            padding=10,
            border=ft.Border.all(1, COLOR_BORDER_DARK),
            expand=True,
        )

        # 4. Activity Log Panel
        self.events_col = ft.Column(
            controls=[],
            spacing=4,
            scroll=ft.ScrollMode.AUTO,
        )

        self.log_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.HISTORY_ROUNDED, size=15, color=COLOR_TEXT_SECONDARY),
                            ft.Text(
                                "Registro de Actividad Reciente",
                                size=11,
                                weight=ft.FontWeight.W_600,
                                color=COLOR_TEXT_SECONDARY,
                            ),
                            ft.Container(expand=True),
                            ft.TextButton(
                                "↩️ Deshacer Última Operación",
                                on_click=lambda _: self._on_undo_clicked(),
                                style=ft.ButtonStyle(color=COLOR_TEXT_MUTED),
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(content=self.events_col, height=85),
                ],
                spacing=4,
            ),
            bgcolor=COLOR_CARD_DARK,
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=10, vertical=6),
            border=ft.Border.all(1, COLOR_BORDER_DARK),
        )

        self.dialog = ft.AlertDialog(
            title=header_row,
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        toolbar_row,
                        folders_container,
                        self.log_container,
                    ],
                    spacing=10,
                    expand=True,
                ),
                width=860,
                height=540,
            ),
            actions=[
                ft.FilledButton(
                    "Cerrar Ventana",
                    on_click=lambda _: self.close(),
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8),
                        bgcolor=COLOR_CARD_DARK,
                        color=COLOR_TEXT_PRIMARY,
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _build_status_badge(self, rule: MonitoredFolderRule) -> ft.Container:
        """Builds the visual status badge showing if the folder is ordered, in progress, or not yet."""
        if not rule.enabled:
            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.PAUSE_CIRCLE_OUTLINE, size=14, color=COLOR_TEXT_MUTED),
                        ft.Text("PAUSADA", size=10.5, weight=ft.FontWeight.W_600, color=COLOR_TEXT_MUTED),
                    ],
                    spacing=4,
                    tight=True,
                ),
                bgcolor=COLOR_SURFACE_DARK,
                border_radius=12,
                padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                border=ft.Border.all(1, COLOR_BORDER_DARK),
            )

        if rule.status == FolderMonitorStatus.IN_PROGRESS:
            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.SYNC_ROUNDED, size=14, color=COLOR_INFO),
                        ft.Text("EN PROCESO...", size=10.5, weight=ft.FontWeight.W_600, color=COLOR_INFO),
                    ],
                    spacing=4,
                    tight=True,
                ),
                bgcolor="#1538BDF8",
                border_radius=12,
                padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                border=ft.Border.all(1, COLOR_INFO),
            )

        if rule.status == FolderMonitorStatus.ORDERED:
            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, size=14, color=COLOR_SUCCESS),
                        ft.Text("YA ESTÁ ORDENADO", size=10.5, weight=ft.FontWeight.W_600, color=COLOR_SUCCESS),
                    ],
                    spacing=4,
                    tight=True,
                ),
                bgcolor="#1510B981",
                border_radius=12,
                padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                border=ft.Border.all(1, COLOR_SUCCESS),
            )

        if rule.status == FolderMonitorStatus.PENDING:
            label = f"AÚN NO ORDENADO ({rule.pending_count} pendiente{'s' if rule.pending_count != 1 else ''})"
            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.PENDING_ACTIONS_ROUNDED, size=14, color=COLOR_WARNING),
                        ft.Text(label, size=10.5, weight=ft.FontWeight.W_600, color=COLOR_WARNING),
                    ],
                    spacing=4,
                    tight=True,
                ),
                bgcolor="#18F59E0B",
                border_radius=12,
                padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                border=ft.Border.all(1, COLOR_WARNING),
            )

        # ERROR state
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, size=14, color=COLOR_DANGER),
                    ft.Text("ERROR / NO DISPONIBLE", size=10.5, weight=ft.FontWeight.W_600, color=COLOR_DANGER),
                ],
                spacing=4,
                tight=True,
            ),
            bgcolor="#18EF4444",
            border_radius=12,
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            border=ft.Border.all(1, COLOR_DANGER),
        )

    def _build_folder_card(self, rule: MonitoredFolderRule) -> ft.Container:
        """Builds a single monitored folder card with status and 1-click actions."""
        accent_color = COLOR_BORDER_DARK
        if rule.enabled:
            if rule.status == FolderMonitorStatus.ORDERED:
                accent_color = COLOR_SUCCESS
            elif rule.status == FolderMonitorStatus.IN_PROGRESS:
                accent_color = COLOR_INFO
            elif rule.status == FolderMonitorStatus.PENDING:
                accent_color = COLOR_WARNING
            elif rule.status == FolderMonitorStatus.ERROR:
                accent_color = COLOR_DANGER

        sw_enabled = ft.Switch(
            value=rule.enabled,
            active_color=COLOR_PRIMARY,
            tooltip="Activar o pausar el monitoreo de esta carpeta",
            on_change=lambda e, rid=rule.id: self._on_toggle_rule_enabled(rid, bool(e.control.value)),
        )

        status_badge = self._build_status_badge(rule)

        # Execution mode badge / switch
        if rule.organize_mode == "manual":
            exec_mode_widget = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.TOUCH_APP_OUTLINED, size=13, color=COLOR_PRIMARY),
                        ft.Text("Configurada para Orden Manual (1 clic)", size=10.5, weight=ft.FontWeight.W_600, color=COLOR_PRIMARY),
                    ],
                    spacing=4,
                    tight=True,
                ),
                bgcolor=COLOR_SURFACE_DARK,
                border_radius=6,
                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                border=ft.Border.all(1, COLOR_PRIMARY),
                on_click=lambda _, r=rule: self._on_manual_organize_clicked(r),
                tooltip="Haz clic para abrir el recorrido de Orden Manual de esta carpeta",
            )
        else:
            exec_mode_widget = ft.Checkbox(
                label="Automático al agregar archivos",
                value=rule.auto_apply,
                active_color=COLOR_PRIMARY,
                label_style=ft.TextStyle(size=10.5, color=COLOR_TEXT_SECONDARY),
                tooltip="Si está activo, ordena automáticamente en cuanto detecta archivos; si se desmarca, ordena cuando hagas clic en 'Ordenar Ahora'",
                on_change=lambda e, rid=rule.id: self._on_toggle_rule_auto(rid, bool(e.control.value)),
            )

        # Primary action button(s)
        if rule.organize_mode == "manual":
            btn_text = (
                f"🖐️ Ordenar Manualmente ({rule.pending_count})"
                if rule.pending_count > 0
                else "🖐️ Ordenar Manualmente"
            )
            primary_action_btn = ft.FilledButton(
                btn_text,
                icon=ft.Icons.DRIVE_FILE_MOVE_OUTLINED,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=8),
                    bgcolor=COLOR_PRIMARY,
                    color="#FFFFFF",
                ),
                tooltip="Haz clic para ordenar manualmente los archivos de esta carpeta paso a paso",
                on_click=lambda _, r=rule: self._on_manual_organize_clicked(r),
            )
            secondary_action_btn = ft.Container()
        else:
            btn_label = (
                f"▶️ Ordenar Ahora ({rule.pending_count})"
                if rule.pending_count > 0
                else "▶️ Ordenar Ahora"
            )
            primary_action_btn = ft.FilledButton(
                btn_label,
                icon=ft.Icons.BOLT_ROUNDED,
                disabled=(rule.status == FolderMonitorStatus.IN_PROGRESS),
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=8),
                    bgcolor=COLOR_PRIMARY if rule.pending_count > 0 else COLOR_SURFACE_DARK,
                    color="#FFFFFF" if rule.pending_count > 0 else COLOR_TEXT_PRIMARY,
                ),
                tooltip="Ejecutar las reglas de esta carpeta en este momento",
                on_click=lambda _, rid=rule.id: self._on_execute_rule_clicked(rid),
            )
            secondary_action_btn = ft.OutlinedButton(
                "🖐️ Orden Manual",
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=8),
                    side=ft.BorderSide(1, COLOR_BORDER_DARK),
                    color=COLOR_TEXT_SECONDARY,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                ),
                tooltip="Abrir el asistente de Orden Manual para esta carpeta",
                on_click=lambda _, r=rule: self._on_manual_organize_clicked(r),
            )

        btn_open_in_table = ft.IconButton(
            icon=ft.Icons.OPEN_IN_NEW_ROUNDED,
            icon_size=16,
            icon_color=COLOR_TEXT_SECONDARY,
            tooltip="Cargar esta carpeta en la tabla principal de FilesPy",
            on_click=lambda _, p=rule.path: self._on_open_in_main_clicked(p),
        )

        btn_edit = ft.IconButton(
            icon=ft.Icons.TUNE_ROUNDED,
            icon_size=16,
            icon_color=COLOR_TEXT_PRIMARY,
            tooltip="Configurar acciones de esta carpeta",
            on_click=lambda _, r=rule: self._open_rule_editor(r),
        )

        btn_delete = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
            icon_size=16,
            icon_color=COLOR_DANGER,
            tooltip="Dejar de monitorear esta carpeta",
            on_click=lambda _, rid=rule.id: self._on_delete_rule_clicked(rid),
        )

        top_row = ft.Row(
            controls=[
                sw_enabled,
                ft.Icon(ft.Icons.FOLDER_ROUNDED, color=COLOR_PRIMARY, size=20),
                ft.Column(
                    controls=[
                        ft.Text(rule.display_name, size=13, weight=ft.FontWeight.W_600, color=COLOR_TEXT_PRIMARY),
                        ft.Text(
                            rule.path,
                            size=10,
                            color=COLOR_TEXT_MUTED,
                            selectable=True,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ],
                    spacing=1,
                    expand=True,
                ),
                status_badge,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        )

        rules_summary = AutomationManager.describe_rule_actions(rule)
        bottom_row = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text(
                            f"Acciones: {rules_summary}",
                            size=10.5,
                            color=COLOR_TEXT_PRIMARY,
                            weight=ft.FontWeight.W_500,
                        ),
                        ft.Text(
                            f"Estatus: {rule.last_message} • Total procesados: {rule.processed_total}",
                            size=10,
                            color=COLOR_TEXT_MUTED,
                        ),
                    ],
                    spacing=2,
                    expand=True,
                ),
                exec_mode_widget,
                secondary_action_btn,
                primary_action_btn,
                btn_open_in_table,
                btn_edit,
                btn_delete,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    top_row,
                    ft.Divider(height=1, color=COLOR_BORDER_DARK),
                    bottom_row,
                ],
                spacing=6,
            ),
            bgcolor=COLOR_CARD_DARK,
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            border=ft.Border(
                left=ft.BorderSide(4, accent_color),
                top=ft.BorderSide(1, COLOR_BORDER_DARK),
                right=ft.BorderSide(1, COLOR_BORDER_DARK),
                bottom=ft.BorderSide(1, COLOR_BORDER_DARK),
            ),
        )

    def refresh_view(self):
        """Rebuilds the folders list, status counters, and activity log."""
        rules = self.automation_manager.get_rules()

        ordered_count = sum(1 for r in rules if r.enabled and r.status == FolderMonitorStatus.ORDERED)
        progress_count = sum(1 for r in rules if r.enabled and r.status == FolderMonitorStatus.IN_PROGRESS)
        pending_count = sum(1 for r in rules if r.enabled and r.status == FolderMonitorStatus.PENDING)

        self.pill_ordered.content = ft.Text(f"🟢 Ya ordenadas: {ordered_count}", size=11, weight=ft.FontWeight.W_600, color=COLOR_SUCCESS)
        self.pill_progress.content = ft.Text(f"🔵 En proceso: {progress_count}", size=11, weight=ft.FontWeight.W_600, color=COLOR_INFO)
        self.pill_pending.content = ft.Text(f"🟡 Aún no ordenadas: {pending_count}", size=11, weight=ft.FontWeight.W_600, color=COLOR_WARNING)
        self.sw_global_active.value = self.automation_manager.is_monitoring_active

        if not rules:
            self.folders_col.controls = [
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.FOLDER_COPY_OUTLINED, size=42, color=COLOR_TEXT_MUTED),
                            ft.Text(
                                "No hay carpetas monitoreadas todavía",
                                size=13,
                                weight=ft.FontWeight.W_600,
                                color=COLOR_TEXT_PRIMARY,
                            ),
                            ft.Text(
                                "Haz clic en '＋ Agregar Carpeta' para indicar una carpeta y automatizar que al agregar archivos\n"
                                "se guarden en una subcarpeta, cambien de nombre o puedan ordenarse manualmente con un clic.",
                                size=11,
                                color=COLOR_TEXT_MUTED,
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=6,
                    ),
                    padding=40,
                    alignment=ft.Alignment.CENTER,
                )
            ]
        else:
            self.folders_col.controls = [self._build_folder_card(r) for r in rules]

        # Events log
        if not self.automation_manager.events:
            self.events_col.controls = [
                ft.Text(
                    "Sin operaciones registradas en esta sesión. Las acciones automáticas y manuales aparecerán aquí.",
                    size=10.5,
                    color=COLOR_TEXT_MUTED,
                )
            ]
        else:
            ev_controls: List[ft.Control] = []
            for ev in self.automation_manager.events[:15]:
                ts_str = datetime.fromtimestamp(ev.timestamp).strftime("%H:%M:%S")
                color = COLOR_DANGER if ev.is_error else COLOR_TEXT_PRIMARY
                ev_controls.append(
                    ft.Row(
                        controls=[
                            ft.Text(f"[{ts_str}]", size=10, color=COLOR_TEXT_MUTED),
                            ft.Text(f"{ev.folder_name}:", size=10, weight=ft.FontWeight.W_600, color=COLOR_PRIMARY),
                            ft.Text(ev.action_summary, size=10, color=color, expand=True),
                        ],
                        spacing=6,
                    )
                )
            self.events_col.controls = ev_controls

        safe_update(self.dialog)

    # ------------------------------------------------------------------
    # Event Handlers
    # ------------------------------------------------------------------

    def _on_global_switch_changed(self, e):
        self.automation_manager.set_monitoring_active(bool(self.sw_global_active.value))
        self.refresh_view()

    def _on_refresh_clicked(self):
        self.automation_manager.refresh_all_statuses(trigger_auto=self.automation_manager.is_monitoring_active)
        self.refresh_view()

    def _on_run_all_clicked(self):
        self.automation_manager.execute_all_pending()
        self.refresh_view()

    def _on_toggle_rule_enabled(self, rule_id: str, enabled: bool):
        self.automation_manager.toggle_rule_enabled(rule_id, enabled)
        self.refresh_view()

    def _on_toggle_rule_auto(self, rule_id: str, auto_apply: bool):
        self.automation_manager.toggle_rule_auto(rule_id, auto_apply)
        self.refresh_view()

    def _on_execute_rule_clicked(self, rule_id: str):
        self.automation_manager.execute_rule_now(rule_id, is_automatic=False)
        self.refresh_view()

    def _on_delete_rule_clicked(self, rule_id: str):
        self.automation_manager.remove_rule(rule_id)
        self.refresh_view()

    def _on_open_in_main_clicked(self, folder_path_str: str):
        p = Path(folder_path_str)
        if p.exists() and p.is_dir():
            self.close()
            self.on_load_folder_in_main(p)

    def _on_manual_organize_clicked(self, rule: MonitoredFolderRule):
        """Closes this monitor dialog and triggers the interactive ManualOrganizeDialog for the selected rule."""
        self.close()
        self.on_open_manual_for_rule(rule)

    def _on_undo_clicked(self):
        self.close()
        self.on_undo_requested()

    def _open_rule_editor(self, rule: Optional[MonitoredFolderRule], use_current: bool = False):
        default_dir = self.current_folder if use_current else None
        editor = FolderRuleEditorDialog(
            page=self.page,
            file_picker=self.file_picker,
            on_save=self._on_rule_saved,
            existing_rule=rule,
            default_folder=default_dir,
            default_manual_folders=self.automation_manager.config_manager.get_manual_folders(),
        )
        editor.show()

    def _on_rule_saved(self, rule: MonitoredFolderRule):
        self.automation_manager.add_or_update_rule(rule)
        self.refresh_view()

    def show(self):
        self.automation_manager.refresh_all_statuses(trigger_auto=False)
        self.refresh_view()
        self.page.show_dialog(self.dialog)

    def close(self):
        try:
            self.page.pop_dialog()
        except Exception:
            pass
