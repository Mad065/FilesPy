"""Preview table component showing customizable file properties, destinations, and status in Flet."""
from typing import Callable, Dict, List, Optional
import flet as ft

from core.config_manager import (
    COLUMN_DEFINITIONS,
    ConfigManager,
    DEFAULT_VISIBLE_COLUMNS,
)
from core.models import FileItem, FileStatus
from core.organizer import get_category_for_extension
from ui.theme import (
    COLOR_BORDER_DARK,
    COLOR_CARD_DARK,
    COLOR_DANGER,
    COLOR_PRIMARY,
    COLOR_SUCCESS,
    COLOR_SURFACE_DARK,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_WARNING,
    format_bytes,
    format_timestamp,
    safe_update,
)

GROUP_LABELS: Dict[str, str] = {
    "basicas": "Propiedades Principales",
    "ubicacion": "Ubicación, Rutas y Nombres",
    "fechas": "Fechas y Tiempos",
    "sistema": "Sistema y Formato Técnico",
    "multimedia": "Contenido Multimedia",
}


class PreviewTable(ft.Container):
    """Scrollable table displaying user-selected file properties, target paths, and status badges."""

    def __init__(
        self,
        on_item_inspected: Callable[[FileItem], None],
        on_selection_toggled: Callable[[], None],
        page: Optional[ft.Page] = None,
        config_manager: Optional[ConfigManager] = None,
    ):
        super().__init__()
        self._page_ref = page
        self.config_manager = config_manager or ConfigManager()
        self.on_item_inspected = on_item_inspected
        self.on_selection_toggled = on_selection_toggled
        self.items: List[FileItem] = []
        self.visible_columns: List[str] = self.config_manager.get_visible_columns()

        self._build_toolbar()
        self._build_header()
        self._build_table_view()

    def _calculate_table_width(self) -> int:
        """Computes total width required for currently visible columns."""
        active_defs = [c for c in COLUMN_DEFINITIONS if c["id"] in self.visible_columns]
        cols_width = sum(int(c["default_width"]) for c in active_defs)
        has_arrow = ("original_name" in self.visible_columns and "new_name" in self.visible_columns)
        arrow_width = 20 if has_arrow else 0
        num_controls = 1 + len(active_defs) + (1 if has_arrow else 0)
        computed = 40 + 20 + cols_width + arrow_width + max(0, (num_controls - 1) * 6)
        return max(680, computed)

    def _build_toolbar(self):
        self.lbl_cols_summary = ft.Text(
            f"{len(self.visible_columns)} de {len(COLUMN_DEFINITIONS)} propiedades visibles",
            size=11,
            color=COLOR_TEXT_MUTED,
        )

        self.btn_columns = ft.OutlinedButton(
            "Elegir Propiedades / Columnas",
            icon=ft.Icons.VIEW_COLUMN_ROUNDED,
            tooltip="Personalizar qué propiedades de los archivos se muestran en la lista",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=6),
                 bgcolor=COLOR_CARD_DARK,
                side=ft.BorderSide(1, COLOR_BORDER_DARK),
                color=COLOR_TEXT_PRIMARY,
                padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                text_style=ft.TextStyle(size=11, weight=ft.FontWeight.W_600),
            ),
            on_click=lambda _: self.open_column_selector_dialog(),
        )

        self.toolbar_row = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.TABLE_CHART_OUTLINED, size=15, color=COLOR_PRIMARY),
                            ft.Text("Lista de Archivos", size=12, weight=ft.FontWeight.W_600, color=COLOR_TEXT_PRIMARY),
                            ft.Text("•", size=12, color=COLOR_TEXT_MUTED),
                            self.lbl_cols_summary,
                        ],
                        spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    self.btn_columns,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.only(left=2, right=2, bottom=2),
        )

    def _get_text_align(self, align_str: str) -> ft.TextAlign:
        if align_str == "right":
            return ft.TextAlign.RIGHT
        if align_str == "center":
            return ft.TextAlign.CENTER
        return ft.TextAlign.LEFT

    def _build_header(self):
        self.chk_all = ft.Checkbox(
            value=True,
            active_color=COLOR_PRIMARY,
            on_change=self._on_toggle_all,
        )

        self.header_controls_row = ft.Row(
            controls=[],
            spacing=6,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        table_width = self._calculate_table_width()
        self.header_row = ft.Container(
            content=self.header_controls_row,
            bgcolor=COLOR_CARD_DARK,
            padding=ft.Padding.symmetric(horizontal=10, vertical=6),
            border_radius=8,
            border=ft.Border.all(1, COLOR_BORDER_DARK),
            width=table_width,
        )
        self._populate_header_controls()

    def _populate_header_controls(self):
        controls: List[ft.Control] = [self.chk_all]
        has_both_names = ("original_name" in self.visible_columns and "new_name" in self.visible_columns)

        for col_def in COLUMN_DEFINITIONS:
            col_id = col_def["id"]
            if col_id not in self.visible_columns:
                continue

            if col_id == "new_name" and has_both_names:
                controls.append(ft.Container(width=20))

            align = self._get_text_align(col_def.get("align", "left"))
            controls.append(
                ft.Container(
                    content=ft.Text(
                        col_def["label"],
                        weight=ft.FontWeight.W_600,
                        size=11,
                        color=COLOR_TEXT_MUTED,
                        text_align=align,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    width=int(col_def["default_width"]),
                    tooltip=col_def.get("description", ""),
                )
            )

        self.header_controls_row.controls = controls

    def _build_table_view(self):
        self.empty_view = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.FOLDER_OPEN_OUTLINED, size=40, color=COLOR_TEXT_MUTED),
                    ft.Text(
                        value="Ningun archivo cargado.\nSelecciona una carpeta arriba para comenzar.",
                        size=12,
                        color=COLOR_TEXT_MUTED,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            alignment=ft.Alignment.CENTER,
            expand=True,
        )

        self.list_view = ft.ListView(
            expand=True,
            spacing=4,
            padding=ft.Padding.symmetric(vertical=4),
        )

        table_width = self._calculate_table_width()
        self.table_column = ft.Column(
            controls=[
                self.header_row,
                ft.Container(content=self.empty_view, expand=True),
            ],
            spacing=4,
            expand=True,
            width=table_width,
        )

        self.expand = True
        self.content = ft.Column(
            controls=[
                self.toolbar_row,
                ft.Row(
                    controls=[self.table_column],
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                ),
            ],
            spacing=4,
            expand=True,
        )

    def update_visible_columns(self, columns: List[str]):
        """Updates the active visible columns and refreshes the header and rows."""
        valid_ids = {c["id"] for c in COLUMN_DEFINITIONS}
        filtered = [c for c in columns if c in valid_ids]
        self.visible_columns = filtered or list(DEFAULT_VISIBLE_COLUMNS)

        table_width = self._calculate_table_width()
        self.header_row.width = table_width
        self.table_column.width = table_width
        self._populate_header_controls()

        self.lbl_cols_summary.value = (
            f"{len(self.visible_columns)} de {len(COLUMN_DEFINITIONS)} propiedades visibles"
        )
        self.set_items(self.items)

    def set_items(self, items: List[FileItem]):
        self.items = items
        self.list_view.controls.clear()

        if not items:
            self.table_column.controls[1] = ft.Container(content=self.empty_view, expand=True)
            safe_update(self)
            return

        for idx, item in enumerate(items):
            row_ctrl = self._create_row(idx, item)
            self.list_view.controls.append(row_ctrl)

        self.table_column.controls[1] = ft.Container(content=self.list_view, expand=True)
        safe_update(self)

    def _create_cell_for_column(self, col_id: str, width: int, item: FileItem) -> ft.Control:
        """Creates the formatted Flet cell control for a given column ID and FileItem."""
        if col_id == "original_name":
            return ft.Container(
                content=ft.Text(
                    item.original_name,
                    size=11,
                    color=COLOR_TEXT_PRIMARY,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                width=width,
                tooltip=item.original_name,
            )

        if col_id == "new_name":
            if item.has_conflict:
                new_name_color = COLOR_DANGER
                new_name_weight = ft.FontWeight.W_600
            elif item.is_modified:
                new_name_color = COLOR_PRIMARY
                new_name_weight = ft.FontWeight.W_600
            else:
                new_name_color = COLOR_TEXT_MUTED
                new_name_weight = ft.FontWeight.NORMAL

            return ft.Container(
                content=ft.Text(
                    item.new_name,
                    size=11,
                    color=new_name_color,
                    weight=new_name_weight,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                width=width,
                tooltip=item.new_name,
            )

        if col_id == "target_folder":
            folder_display = item.target_folder.name or "/"
            return ft.Container(
                content=ft.Text(
                    folder_display,
                    size=11,
                    color=COLOR_TEXT_MUTED,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                width=width,
                tooltip=str(item.target_folder),
            )

        if col_id == "original_folder":
            return ft.Container(
                content=ft.Text(
                    item.original_folder,
                    size=11,
                    color=COLOR_TEXT_MUTED,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                width=width,
                tooltip=str(item.original_path.parent),
            )

        if col_id == "original_full_path":
            return ft.Container(
                content=ft.Text(
                    item.original_full_path,
                    size=10.5,
                    color=COLOR_TEXT_MUTED,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                width=width,
                tooltip=item.original_full_path,
            )

        if col_id == "target_full_path":
            return ft.Container(
                content=ft.Text(
                    item.target_full_path,
                    size=10.5,
                    color=COLOR_TEXT_MUTED,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                width=width,
                tooltip=item.target_full_path,
            )

        if col_id == "stem":
            return ft.Container(
                content=ft.Text(
                    item.stem,
                    size=11,
                    color=COLOR_TEXT_SECONDARY,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                width=width,
                tooltip=item.stem,
            )

        if col_id == "size":
            return ft.Container(
                content=ft.Text(
                    format_bytes(item.size_bytes),
                    size=10.5,
                    color=COLOR_TEXT_MUTED,
                    text_align=ft.TextAlign.RIGHT,
                ),
                width=width,
            )

        if col_id == "extension":
            return ft.Container(
                content=ft.Text(
                    item.extension or "-",
                    size=10.5,
                    color=COLOR_TEXT_MUTED,
                    text_align=ft.TextAlign.CENTER,
                ),
                width=width,
            )

        if col_id == "category":
            cats = self.config_manager.get_categories_dict() if self.config_manager else None
            unorg = self.config_manager.unorganized_folder if self.config_manager else "Otros"
            cat_name = get_category_for_extension(item.extension, cats, default_category=unorg)
            return ft.Container(
                content=ft.Text(
                    cat_name,
                    size=10.5,
                    color=COLOR_TEXT_SECONDARY,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                width=width,
                tooltip=cat_name,
            )

        if col_id == "mime_type":
            mime = item.mime_type
            return ft.Container(
                content=ft.Text(
                    mime,
                    size=10.5,
                    color=COLOR_TEXT_MUTED,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                width=width,
                tooltip=mime,
            )

        if col_id == "permissions":
            return ft.Container(
                content=ft.Text(
                    item.permissions_str,
                    size=10.5,
                    color=COLOR_TEXT_MUTED,
                    text_align=ft.TextAlign.CENTER,
                ),
                width=width,
            )

        if col_id == "is_hidden":
            hidden_text = "Sí" if item.is_hidden else "No"
            hidden_color = COLOR_WARNING if item.is_hidden else COLOR_TEXT_MUTED
            return ft.Container(
                content=ft.Text(
                    hidden_text,
                    size=10.5,
                    color=hidden_color,
                    text_align=ft.TextAlign.CENTER,
                ),
                width=width,
            )

        if col_id == "dimensions":
            dims = item.get_dimensions()
            return ft.Container(
                content=ft.Text(
                    dims,
                    size=10.5,
                    color=COLOR_TEXT_MUTED,
                    text_align=ft.TextAlign.CENTER,
                ),
                width=width,
            )

        if col_id == "modified_time":
            return ft.Container(
                content=ft.Text(
                    format_timestamp(item.modified_time),
                    size=10.5,
                    color=COLOR_TEXT_MUTED,
                    text_align=ft.TextAlign.CENTER,
                ),
                width=width,
            )

        if col_id == "created_time":
            return ft.Container(
                content=ft.Text(
                    format_timestamp(item.created_time),
                    size=10.5,
                    color=COLOR_TEXT_MUTED,
                    text_align=ft.TextAlign.CENTER,
                ),
                width=width,
            )

        if col_id == "access_time":
            return ft.Container(
                content=ft.Text(
                    format_timestamp(item.access_time),
                    size=10.5,
                    color=COLOR_TEXT_MUTED,
                    text_align=ft.TextAlign.CENTER,
                ),
                width=width,
            )

        if col_id == "status":
            badge_text, badge_bg, badge_fg = self._get_status_badge(item)
            return ft.Container(
                content=ft.Text(badge_text, size=9.5, weight=ft.FontWeight.W_600, color=badge_fg),
                bgcolor=badge_bg,
                border_radius=6,
                padding=ft.Padding.symmetric(horizontal=6, vertical=3),
                alignment=ft.Alignment.CENTER,
                width=width,
            )

        return ft.Container(width=width)

    def _create_row(self, idx: int, item: FileItem) -> ft.Container:
        chk = ft.Checkbox(
            value=item.selected,
            active_color=COLOR_PRIMARY,
            on_change=lambda e, it=item: self._on_item_checked(it, e.control.value),
        )

        row_controls: List[ft.Control] = [chk]
        has_both_names = ("original_name" in self.visible_columns and "new_name" in self.visible_columns)

        for col_def in COLUMN_DEFINITIONS:
            col_id = col_def["id"]
            if col_id not in self.visible_columns:
                continue

            if col_id == "new_name" and has_both_names:
                row_controls.append(
                    ft.Container(
                        content=ft.Text("->", size=10, color=COLOR_PRIMARY if item.is_modified else COLOR_TEXT_MUTED),
                        width=20,
                        alignment=ft.Alignment.CENTER,
                    )
                )

            cell_ctrl = self._create_cell_for_column(col_id, int(col_def["default_width"]), item)
            row_controls.append(cell_ctrl)

        row_content = ft.Row(
            controls=row_controls,
            spacing=6,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        table_width = self._calculate_table_width()
        row_container = ft.Container(
            content=row_content,
            bgcolor=COLOR_SURFACE_DARK if idx % 2 == 0 else COLOR_CARD_DARK,
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            width=table_width,
            on_click=lambda _, it=item: self.on_item_inspected(it),
            ink=True,
        )
        return row_container

    def open_column_selector_dialog(self):
        """Opens a modal dialog allowing the user to toggle which file properties are shown."""
        active_page = self._page_ref or getattr(self, "page", None)
        if not active_page:
            return

        checkbox_map: Dict[str, ft.Checkbox] = {}
        lbl_warning = ft.Text(
            "",
            size=11,
            color=COLOR_DANGER,
            weight=ft.FontWeight.W_600,
        )

        # Group columns by category for a structured presentation
        grouped_defs: Dict[str, List[dict]] = {}
        for col_def in COLUMN_DEFINITIONS:
            grp = col_def.get("group", "basicas")
            grouped_defs.setdefault(grp, []).append(col_def)

        groups_column = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

        for grp_key, grp_title in GROUP_LABELS.items():
            defs_in_grp = grouped_defs.get(grp_key, [])
            if not defs_in_grp:
                continue

            grp_items_col = ft.Column(spacing=4)
            for col_def in defs_in_grp:
                cid = col_def["id"]
                chk = ft.Checkbox(
                    value=(cid in self.visible_columns),
                    active_color=COLOR_PRIMARY,
                )
                checkbox_map[cid] = chk

                item_row = ft.Container(
                    content=ft.Row(
                        controls=[
                            chk,
                            ft.Column(
                                controls=[
                                    ft.Text(col_def["label"], size=12, weight=ft.FontWeight.W_600, color=COLOR_TEXT_PRIMARY),
                                    ft.Text(col_def.get("description", ""), size=10.5, color=COLOR_TEXT_MUTED),
                                ],
                                spacing=1,
                                expand=True,
                            ),
                        ],
                        spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                    bgcolor=COLOR_CARD_DARK,
                    border_radius=6,
                    border=ft.Border.all(1, COLOR_BORDER_DARK),
                    on_click=lambda _, c=chk: self._toggle_dialog_checkbox(c),
                    ink=True,
                )
                grp_items_col.controls.append(item_row)

            groups_column.controls.append(
                ft.Column(
                    controls=[
                        ft.Text(grp_title, size=11.5, weight=ft.FontWeight.W_600, color=COLOR_PRIMARY),
                        grp_items_col,
                    ],
                    spacing=4,
                )
            )

        def on_select_all(_):
            for chk in checkbox_map.values():
                chk.value = True
            lbl_warning.value = ""
            safe_update(dialog)

        def on_reset_defaults(_):
            for cid, chk in checkbox_map.items():
                chk.value = cid in DEFAULT_VISIBLE_COLUMNS
            lbl_warning.value = ""
            safe_update(dialog)

        def on_save(_):
            selected_ids = [
                c["id"] for c in COLUMN_DEFINITIONS if checkbox_map[c["id"]].value
            ]
            if not selected_ids:
                lbl_warning.value = "Debes seleccionar al menos una propiedad para mostrar en la lista."
                safe_update(lbl_warning)
                return

            self.config_manager.save_visible_columns(selected_ids)
            self.update_visible_columns(selected_ids)
            active_page.pop_dialog()

        dialog = ft.AlertDialog(
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.VIEW_COLUMN_ROUNDED, color=COLOR_PRIMARY, size=20),
                    ft.Text("Propiedades de Archivos a Mostrar", weight=ft.FontWeight.W_600, size=15),
                ],
                spacing=8,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(
                                    "Marca las propiedades que deseas visualizar en la tabla:",
                                    size=11.5,
                                    color=COLOR_TEXT_SECONDARY,
                                    expand=True,
                                ),
                                ft.TextButton("Todas", on_click=on_select_all),
                                ft.TextButton("Por defecto", on_click=on_reset_defaults),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Divider(height=1, color=COLOR_BORDER_DARK),
                        groups_column,
                        lbl_warning,
                    ],
                    spacing=6,
                    expand=True,
                ),
                width=540,
                height=440,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: active_page.pop_dialog()),
                ft.FilledButton(
                    "Guardar Columnas",
                    icon=ft.Icons.CHECK,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8),
                        bgcolor=COLOR_PRIMARY,
                        color="#FFFFFF",
                    ),
                    on_click=on_save,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        active_page.show_dialog(dialog)

    def _toggle_dialog_checkbox(self, chk: ft.Checkbox):
        chk.value = not bool(chk.value)
        safe_update(chk)

    def _get_status_badge(self, item: FileItem):
        if item.has_conflict:
            return "Conflicto", "#380f12", COLOR_DANGER
        elif item.status == FileStatus.READY or item.is_modified:
            return "Listo", "#0d3320", COLOR_SUCCESS
        else:
            return "Sin cambio", "#1e2433", COLOR_TEXT_MUTED

    def _on_item_checked(self, item: FileItem, checked: bool):
        item.selected = checked
        self.on_selection_toggled()

    def _on_toggle_all(self, e):
        val = bool(self.chk_all.value)
        for it in self.items:
            it.selected = val
        self.set_items(self.items)
        self.on_selection_toggled()
