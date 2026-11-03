"""Automation and Folder Monitoring Engine for FilesPy."""
import re
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Tuple

from core.config_manager import ConfigManager, normalize_extension
from core.conflicts import validate_conflicts
from core.models import (
    AutomationEvent,
    FileItem,
    FileStatus,
    FolderMonitorStatus,
    MonitoredFolderRule,
    OrganizeConfig,
    RenameConfig,
)
from core.organizer import apply_organization_rules
from core.renamer import transform_case
from core.scanner import scan_directory
from core.undo import UndoManager

DATE_PREFIX_REGEX = re.compile(r"^\d{8}_")


def parse_extension_filter(ext_filter: str) -> Set[str]:
    """Parses a comma/space separated string of extensions into normalized '.ext' strings."""
    if not ext_filter or not ext_filter.strip():
        return set()
    parts = re.split(r"[,;\s]+", ext_filter.strip())
    return {normalize_extension(p) for p in parts if normalize_extension(p)}


def apply_rule_rename(item: FileItem, rule: MonitoredFolderRule) -> str:
    """Computes the target filename for a FileItem according to a MonitoredFolderRule.

    Idempotent with respect to prefixes, suffixes, casing, and date prefixes so files
    staying in the same folder are not renamed repeatedly.
    """
    if not rule.rename_enabled:
        return item.original_name

    orig_path = item.original_path
    stem = orig_path.stem
    ext = orig_path.suffix

    # Extract existing prefix/date/suffix (case-insensitively) so case transforms only affect the core stem
    pfx = rule.rename_prefix or ""
    sfx = rule.rename_suffix or ""

    if pfx and stem.lower().startswith(pfx.lower()):
        stem = stem[len(pfx):]

    existing_date_pfx = ""
    if rule.rename_date_prefix:
        m = DATE_PREFIX_REGEX.match(stem)
        if m:
            existing_date_pfx = m.group(0)
            stem = stem[len(existing_date_pfx):]

    if sfx and stem.lower().endswith(sfx.lower()) and len(stem) > len(sfx):
        stem = stem[:-len(sfx)]

    # 1. Find & Replace on core stem
    if rule.rename_find:
        pattern = re.compile(re.escape(rule.rename_find), re.IGNORECASE)
        stem = pattern.sub(rule.rename_replace or "", stem)

    # 2. Case Transformation on core stem
    if rule.rename_case_mode and rule.rename_case_mode != "original":
        stem = transform_case(stem, rule.rename_case_mode)

    # 3. Date prefix YYYYMMDD_
    if rule.rename_date_prefix:
        if existing_date_pfx:
            stem = f"{existing_date_pfx}{stem}"
        else:
            try:
                date_str = datetime.fromtimestamp(item.modified_time).strftime("%Y%m%d")
            except (ValueError, OSError):
                date_str = datetime.now().strftime("%Y%m%d")
            stem = f"{date_str}_{stem}"

    # 4. Prefix & Suffix
    if pfx:
        stem = f"{pfx}{stem}"
    if sfx:
        stem = f"{stem}{sfx}"

    return f"{stem}{ext}"


def resolve_collision_free_name(target_folder: Path, desired_name: str, source_path: Path) -> str:
    """Ensures destination path does not collide with an existing different file."""
    candidate_path = (target_folder / desired_name).resolve()
    if not candidate_path.exists() or candidate_path == source_path.resolve():
        return desired_name

    p = Path(desired_name)
    stem = p.stem
    suffix = p.suffix
    counter = 1
    while True:
        alt_name = f"{stem}_{counter}{suffix}"
        alt_path = (target_folder / alt_name).resolve()
        if not alt_path.exists() or alt_path == source_path.resolve():
            return alt_name
        counter += 1


class AutomationManager:
    """Manages watched folders, evaluates their ordering status, and runs automatic/manual actions."""

    def __init__(
        self,
        config_manager: ConfigManager,
        undo_manager: UndoManager,
        on_state_changed: Optional[Callable[[], None]] = None,
        poll_interval: float = 2.0,
    ):
        self.config_manager = config_manager
        self.undo_manager = undo_manager
        self.on_state_changed = on_state_changed
        self.poll_interval = poll_interval

        self.rules: List[MonitoredFolderRule] = self.config_manager.get_monitored_folders()
        self.is_monitoring_active: bool = self.config_manager.automation_active
        self.events: List[AutomationEvent] = []

        # Tracks files explicitly marked as "KEEP" during manual organization per rule_id
        self._manual_kept_paths: Dict[str, Set[Path]] = {}
        # Tracks files restored via Undo so background loop doesn't immediately re-move them
        self._undone_skip_paths: Set[Path] = set()
        # Tracks file sizes across polls to avoid moving files still being written
        self._file_stability_cache: Dict[Path, Tuple[int, float]] = {}

        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None

        # Perform initial status evaluation synchronously
        self.refresh_all_statuses(trigger_auto=False)

    # ------------------------------------------------------------------
    # Lifecycle & Background Thread
    # ------------------------------------------------------------------

    def start_background_monitor(self):
        """Starts the daemon thread that monitors folders periodically."""
        if self._worker_thread and self._worker_thread.is_alive():
            return
        self._stop_event.clear()
        self._worker_thread = threading.Thread(
            target=self._monitor_loop,
            name="FilesPyAutomationMonitor",
            daemon=True,
        )
        self._worker_thread.start()

    def stop_background_monitor(self):
        """Stops the background monitoring thread."""
        self._stop_event.set()

    def set_monitoring_active(self, active: bool):
        """Enables or pauses global real-time automatic execution."""
        with self._lock:
            self.is_monitoring_active = bool(active)
            self.config_manager.set_automation_active(self.is_monitoring_active)
        self.refresh_all_statuses(trigger_auto=self.is_monitoring_active)
        self._notify_listeners()

    def _monitor_loop(self):
        while not self._stop_event.is_set():
            try:
                self.refresh_all_statuses(trigger_auto=self.is_monitoring_active)
            except Exception:
                pass
            self._stop_event.wait(self.poll_interval)

    def _notify_listeners(self):
        if self.on_state_changed:
            try:
                self.on_state_changed()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Rule CRUD Operations
    # ------------------------------------------------------------------

    def get_rules(self) -> List[MonitoredFolderRule]:
        with self._lock:
            return list(self.rules)

    def get_rule_by_id(self, rule_id: str) -> Optional[MonitoredFolderRule]:
        with self._lock:
            return next((r for r in self.rules if r.id == rule_id), None)

    def add_or_update_rule(self, rule: MonitoredFolderRule):
        """Adds a new MonitoredFolderRule or updates an existing one with the same id."""
        with self._lock:
            existing_idx = next((i for i, r in enumerate(self.rules) if r.id == rule.id), None)
            if existing_idx is not None:
                self.rules[existing_idx] = rule
            else:
                self.rules.append(rule)
            # Clear kept cache when rule config is edited
            self._manual_kept_paths.pop(rule.id, None)
            self.config_manager.save_monitored_folders(self.rules)

        self.evaluate_rule_status(rule, trigger_auto=self.is_monitoring_active)
        self._notify_listeners()

    def remove_rule(self, rule_id: str):
        """Removes a monitored folder rule by ID."""
        with self._lock:
            self.rules = [r for r in self.rules if r.id != rule_id]
            self._manual_kept_paths.pop(rule_id, None)
            self.config_manager.save_monitored_folders(self.rules)
        self._notify_listeners()

    def toggle_rule_enabled(self, rule_id: str, enabled: bool):
        rule = self.get_rule_by_id(rule_id)
        if not rule:
            return
        with self._lock:
            rule.enabled = bool(enabled)
            self.config_manager.save_monitored_folders(self.rules)
        self.evaluate_rule_status(rule, trigger_auto=self.is_monitoring_active)
        self._notify_listeners()

    def toggle_rule_auto(self, rule_id: str, auto_apply: bool):
        rule = self.get_rule_by_id(rule_id)
        if not rule:
            return
        with self._lock:
            rule.auto_apply = bool(auto_apply)
            self.config_manager.save_monitored_folders(self.rules)
        self.evaluate_rule_status(rule, trigger_auto=self.is_monitoring_active)
        self._notify_listeners()

    # ------------------------------------------------------------------
    # Scanning, Pipeline Preparation & Status Evaluation
    # ------------------------------------------------------------------

    def build_candidate_items(self, rule: MonitoredFolderRule) -> List[FileItem]:
        """Scans the folder for top-level files matching the rule and calculates target paths."""
        folder_path = Path(rule.path).resolve()
        if not folder_path.exists() or not folder_path.is_dir():
            return []

        ignored = set(self.config_manager.get_ignored_set())
        ignored.add(self.config_manager.trash_folder)
        ignored.add(self.config_manager.duplicates_folder)

        scanned = scan_directory(
            folder_path,
            recursive=False,
            include_hidden=False,
            ignored_names=ignored,
        )

        allowed_exts = parse_extension_filter(rule.extension_filter)
        if allowed_exts:
            scanned = [it for it in scanned if it.extension.lower() in allowed_exts]

        # Apply rename rules
        for it in scanned:
            it.new_name = apply_rule_rename(it, rule)

        # Apply organization rules
        org_config = OrganizeConfig(
            mode=rule.organize_mode,
            custom_subfolder=rule.custom_subfolder,
            custom_category_map=self.config_manager.get_categories_dict(),
            no_extension_folder=self.config_manager.no_extension_folder,
            unorganized_folder=self.config_manager.unorganized_folder,
            manual_folders=list(rule.manual_folders),
        )
        scanned = apply_organization_rules(scanned, folder_path, org_config)
        return scanned

    def get_pending_items_for_rule(self, rule: MonitoredFolderRule) -> List[FileItem]:
        """Returns the list of FileItems that currently need action in this folder."""
        candidates = self.build_candidate_items(rule)
        if rule.organize_mode == "manual":
            kept_set = self._manual_kept_paths.get(rule.id, set())
            return [it for it in candidates if it.original_path.resolve() not in kept_set]
        else:
            return [it for it in candidates if it.is_modified]

    def evaluate_rule_status(self, rule: MonitoredFolderRule, trigger_auto: bool = False) -> FolderMonitorStatus:
        """Evaluates the current status of a single rule and optionally runs auto execution."""
        if rule.status == FolderMonitorStatus.IN_PROGRESS:
            return rule.status

        folder_path = Path(rule.path)
        if not folder_path.exists() or not folder_path.is_dir():
            rule.status = FolderMonitorStatus.ERROR
            rule.pending_count = 0
            rule.last_message = "La carpeta no existe o no está disponible"
            return rule.status

        pending_items = self.get_pending_items_for_rule(rule)
        rule.pending_count = len(pending_items)

        if rule.pending_count == 0:
            rule.status = FolderMonitorStatus.ORDERED
            if not rule.last_message or "pendiente" in rule.last_message.lower() or "no existe" in rule.last_message.lower():
                rule.last_message = "Ya está ordenado (0 pendientes)"
            return rule.status

        # There are pending files
        rule.status = FolderMonitorStatus.PENDING
        if rule.organize_mode == "manual":
            rule.last_message = f"Aún no ordenado ({rule.pending_count} para orden manual)"
        else:
            rule.last_message = f"Aún no ordenado ({rule.pending_count} pendiente(s))"

        # Should we auto-execute?
        if (
            trigger_auto
            and self.is_monitoring_active
            and rule.enabled
            and rule.auto_apply
            and rule.organize_mode != "manual"
        ):
            # Verify file stability and skip files explicitly undone until manual trigger
            now = time.time()
            stable_items = [
                it for it in pending_items
                if (now - it.modified_time) >= 0.5
                and it.original_path.resolve() not in self._undone_skip_paths
            ]
            if stable_items:
                self.execute_rule_now(rule.id, is_automatic=True)

        return rule.status

    def refresh_all_statuses(self, trigger_auto: bool = False):
        """Re-evaluates status for all configured rules."""
        changed = False
        for rule in self.get_rules():
            prev_status = rule.status
            prev_pending = rule.pending_count
            self.evaluate_rule_status(rule, trigger_auto=trigger_auto)
            if rule.status != prev_status or rule.pending_count != prev_pending:
                changed = True
        if changed:
            self._notify_listeners()

    # ------------------------------------------------------------------
    # Execution (Automatic & On-Demand)
    # ------------------------------------------------------------------

    def execute_rule_now(self, rule_id: str, is_automatic: bool = False) -> Tuple[int, List[str]]:
        """Executes the configured automatic/rule-based actions for a folder immediately.

        Returns:
            Tuple of (number of processed files, list of error messages).
        """
        rule = self.get_rule_by_id(rule_id)
        if not rule:
            return 0, ["Regla de carpeta no encontrada."]

        folder_path = Path(rule.path)
        if not folder_path.exists() or not folder_path.is_dir():
            rule.status = FolderMonitorStatus.ERROR
            rule.last_message = "Carpeta no encontrada"
            self._notify_listeners()
            return 0, ["La carpeta seleccionada no existe."]

        with self._lock:
            if rule.status == FolderMonitorStatus.IN_PROGRESS:
                return 0, ["La carpeta ya se encuentra en proceso."]
            rule.status = FolderMonitorStatus.IN_PROGRESS
            rule.last_message = "En proceso de ordenación..."
        self._notify_listeners()

        try:
            pending_items = self.get_pending_items_for_rule(rule)
            if is_automatic:
                pending_items = [
                    it for it in pending_items
                    if it.original_path.resolve() not in self._undone_skip_paths
                ]
            else:
                # Manual / on-demand run clears undone skip status for these items
                for it in pending_items:
                    self._undone_skip_paths.discard(it.original_path.resolve())

            if not pending_items:
                with self._lock:
                    rule.status = FolderMonitorStatus.ORDERED
                    rule.pending_count = 0
                    rule.last_message = "Ya está ordenado (0 pendientes)"
                self._notify_listeners()
                return 0, []

            # Resolve any destination filename collisions safely so automation succeeds cleanly
            used_destinations: Set[Path] = set()
            for item in pending_items:
                safe_name = resolve_collision_free_name(
                    item.target_folder, item.new_name, item.original_path
                )
                candidate_dest = (item.target_folder / safe_name).resolve()
                counter = 1
                base_stem = Path(safe_name).stem
                base_ext = Path(safe_name).suffix
                while candidate_dest in used_destinations:
                    safe_name = f"{base_stem}_{counter}{base_ext}"
                    candidate_dest = (item.target_folder / safe_name).resolve()
                    counter += 1
                item.new_name = safe_name
                used_destinations.add(candidate_dest)

            pending_items = validate_conflicts(pending_items)
            count, errors = self.undo_manager.apply_batch(pending_items)

            now = time.time()
            with self._lock:
                rule.last_run_timestamp = now
                rule.processed_total += count

                if errors:
                    rule.status = FolderMonitorStatus.ERROR
                    rule.last_message = f"Error: {errors[0]}"
                    self._record_event(
                        rule,
                        f"Error al procesar: {errors[0]}",
                        files_count=0,
                        is_error=True,
                    )
                else:
                    mode_tag = "Auto" if is_automatic else "Bajo demanda"
                    summary = f"[{mode_tag}] {count} archivo(s) ordenados ({self.describe_rule_actions(rule)})"
                    self._record_event(rule, summary, files_count=count, is_error=False)

            # Re-evaluate remaining items
            remaining = self.get_pending_items_for_rule(rule)
            with self._lock:
                rule.pending_count = len(remaining)
                if not errors:
                    if rule.pending_count == 0:
                        rule.status = FolderMonitorStatus.ORDERED
                        rule.last_message = f"Ya ordenado • Última acción: {count} archivo(s)"
                    else:
                        rule.status = FolderMonitorStatus.PENDING
                        rule.last_message = f"Aún no ordenado ({rule.pending_count} pendiente(s))"

            self._notify_listeners()
            return count, errors

        except Exception as ex:
            with self._lock:
                rule.status = FolderMonitorStatus.ERROR
                rule.last_message = f"Error inesperado: {str(ex)}"
            self._notify_listeners()
            return 0, [str(ex)]

    def execute_all_pending(self) -> Tuple[int, int]:
        """Executes all non-manual monitored folders that currently have pending items.

        Returns:
            Tuple of (folders_processed, total_files_processed).
        """
        folders_done = 0
        files_done = 0
        for rule in self.get_rules():
            if rule.organize_mode != "manual":
                self.evaluate_rule_status(rule, trigger_auto=False)
                if rule.pending_count > 0:
                    c, errs = self.execute_rule_now(rule.id, is_automatic=False)
                    if c > 0 and not errs:
                        folders_done += 1
                        files_done += c
        return folders_done, files_done

    def mark_manual_run_completed(
        self,
        rule_id: str,
        modified_count: int,
        discarded_count: int,
        kept_paths: Optional[List[Path]] = None,
    ):
        """Updates a manual rule's state and log after ManualOrganizeDialog finishes."""
        rule = self.get_rule_by_id(rule_id)
        if not rule:
            return
        with self._lock:
            if kept_paths:
                kept_set = self._manual_kept_paths.setdefault(rule.id, set())
                for kp in kept_paths:
                    kept_set.add(kp.resolve())
            total_changed = modified_count + discarded_count
            rule.last_run_timestamp = time.time()
            rule.processed_total += total_changed
            summary = (
                f"[Orden Manual] {modified_count} organizado(s), "
                f"{discarded_count} descartado(s)"
            )
            self._record_event(rule, summary, files_count=total_changed, is_error=False)

        self.evaluate_rule_status(rule, trigger_auto=False)
        if rule.pending_count == 0:
            rule.last_message = "Ya está ordenado (Orden manual completado)"
        self._notify_listeners()

    def mark_files_undone(self, restored_paths: List[Path]):
        """Marks restored files so background automatic loop does not immediately re-process them."""
        with self._lock:
            for p in restored_paths:
                self._undone_skip_paths.add(p.resolve())
                # Also remove from manual kept paths so they show as pending again
                for kept_set in self._manual_kept_paths.values():
                    kept_set.discard(p.resolve())
        self.refresh_all_statuses(trigger_auto=False)
        self._notify_listeners()

    def build_rename_config_for_rule(self, rule: MonitoredFolderRule) -> RenameConfig:
        """Converts a MonitoredFolderRule's rename settings into a RenameConfig object."""
        if not rule.rename_enabled:
            return RenameConfig()
        return RenameConfig(
            find_text=rule.rename_find,
            replace_text=rule.rename_replace,
            prefix=rule.rename_prefix,
            suffix=rule.rename_suffix,
            case_mode=rule.rename_case_mode or "original",
        )

    @staticmethod
    def describe_rule_actions(rule: MonitoredFolderRule) -> str:
        """Returns a human-readable summary in Spanish of the rule's configured actions."""
        parts: List[str] = []
        mode_map = {
            "by_category": "Subcarpeta por Categoría",
            "by_extension": "Subcarpeta por Extensión",
            "by_date": "Subcarpeta por Fecha (Año/Mes)",
            "custom_subfolder": f"Subcarpeta '{rule.custom_subfolder or 'Personalizada'}'",
            "manual": "Orden Manual Interactivo (1 clic)",
            "none": "En misma carpeta",
        }
        parts.append(mode_map.get(rule.organize_mode, "Subcarpeta por Categoría"))

        if rule.rename_enabled:
            ren_details: List[str] = []
            if rule.rename_date_prefix:
                ren_details.append("Fecha YYYYMMDD_")
            if rule.rename_prefix:
                ren_details.append(f"Prefijo '{rule.rename_prefix}'")
            if rule.rename_suffix:
                ren_details.append(f"Sufijo '{rule.rename_suffix}'")
            if rule.rename_find:
                ren_details.append(f"Reemplazar '{rule.rename_find}'")
            if rule.rename_case_mode and rule.rename_case_mode != "original":
                ren_details.append(rule.rename_case_mode)
            if ren_details:
                parts.append("Renombrar: " + " + ".join(ren_details))
            else:
                parts.append("Renombrado activo")

        if rule.extension_filter.strip():
            parts.append(f"Filtro: {rule.extension_filter.strip()}")

        return " • ".join(parts)

    def _record_event(
        self,
        rule: MonitoredFolderRule,
        summary: str,
        files_count: int = 0,
        is_error: bool = False,
    ):
        ev = AutomationEvent(
            timestamp=time.time(),
            folder_name=rule.display_name,
            folder_path=rule.path,
            action_summary=summary,
            files_count=files_count,
            is_error=is_error,
        )
        self.events.insert(0, ev)
        if len(self.events) > 50:
            self.events = self.events[:50]
