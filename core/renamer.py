"""Batch renaming engine modeled after Apple macOS Finder (Replace Text, Add Text, Format) plus advanced rules."""
from datetime import datetime
import re
from pathlib import Path
from typing import List, Optional
from core.models import FileItem, RenameConfig, FileStatus


def transform_case(text: str, mode: str) -> str:
    """Transforms the casing of the given text."""
    if mode == "lower":
        return text.lower()
    elif mode == "upper":
        return text.upper()
    elif mode == "title":
        return text.title()
    elif mode == "snake":
        clean = re.sub(r"[\s\-]+", "_", text.strip())
        return clean.lower()
    elif mode == "kebab":
        clean = re.sub(r"[\s_]+", "-", text.strip())
        return clean.lower()
    return text


def _compute_renamed_filename(
    stem: str,
    ext: str,
    mtime: float,
    index: int,
    config: RenameConfig,
) -> str:
    """Computes the target filename for a single item at sequence position `index`."""
    mode = config.mode or "replace"

    if mode == "add_text":
        if config.add_text:
            if config.add_location == "before":
                stem = f"{config.add_text}{stem}"
            else:
                stem = f"{stem}{config.add_text}"

    elif mode == "format":
        start_num = config.counter_start if config.counter_start is not None else 1
        current_num = start_num + index
        base = (config.custom_format or "").strip()

        if config.format_style == "name_index":
            token = f"{current_num}"
        elif config.format_style == "name_date":
            try:
                dt = datetime.fromtimestamp(mtime) if mtime else datetime.now()
            except (ValueError, OSError, OverflowError):
                dt = datetime.now()
            token = dt.strftime("%Y-%m-%d a las %H.%M.%S")
        else:
            # Default: "name_counter" (5-digit zero-padded like macOS Finder: 00001)
            token = f"{current_num:05d}"

        if base:
            if config.format_location == "before":
                stem = f"{token} {base}"
            else:
                stem = f"{base} {token}"
        else:
            stem = token

    else:
        # Mode: "replace" (Reemplazar texto)
        if config.find_text:
            if config.use_regex:
                try:
                    flags = 0 if config.match_case else re.IGNORECASE
                    stem = re.sub(config.find_text, config.replace_text, stem, flags=flags)
                except re.error:
                    pass
            else:
                if config.match_case:
                    stem = stem.replace(config.find_text, config.replace_text)
                else:
                    pattern = re.compile(re.escape(config.find_text), re.IGNORECASE)
                    stem = pattern.sub(config.replace_text, stem)

    # Additional / Legacy rules (case, prefix/suffix, numbering, extension)
    if config.case_mode and config.case_mode != "original":
        stem = transform_case(stem, config.case_mode)

    if config.prefix:
        stem = f"{config.prefix}{stem}"
    if config.suffix:
        stem = f"{stem}{config.suffix}"

    if config.numbering_enabled and mode != "format":
        current_num = config.numbering_start + index
        digits = max(1, config.numbering_digits)
        formatted_num = f"{current_num:0{digits}d}"
        stem = f"{stem}_{formatted_num}"

    final_ext = ext
    if config.custom_extension:
        custom = config.custom_extension.strip()
        if not custom.startswith("."):
            custom = f".{custom}"
        final_ext = custom
    elif not config.preserve_extension:
        final_ext = ""

    return f"{stem}{final_ext}"


def apply_rename_rules(items: List[FileItem], config: RenameConfig) -> List[FileItem]:
    """Applies renaming rules to the given list of FileItem objects.

    Returns the updated items (new_name calculated).
    """
    seq_index = 0
    for item in items:
        if not item.selected:
            item.new_name = item.original_name
            continue

        orig_path = item.original_path
        stem = orig_path.stem
        ext = orig_path.suffix

        item.new_name = _compute_renamed_filename(
            stem=stem,
            ext=ext,
            mtime=item.modified_time,
            index=seq_index,
            config=config,
        )
        seq_index += 1

    return items


def generate_example_name(
    config: RenameConfig,
    sample_name: str = "Captura de pantalla 2022-12-21 a las 15.3.png",
    sample_mtime: Optional[float] = None,
) -> str:
    """Generates a live preview filename string for the macOS-style 'Ejemplo:' label."""
    p = Path(sample_name)
    stem = p.stem if p.stem else "Archivo"
    ext = p.suffix if p.suffix else ".png"
    mtime = sample_mtime if sample_mtime is not None else 1671658230.0
    return _compute_renamed_filename(
        stem=stem,
        ext=ext,
        mtime=mtime,
        index=0,
        config=config,
    )


def has_active_rename_rules(config: Optional[RenameConfig]) -> bool:
    """Returns True if the given RenameConfig has any active transformation rule."""
    if not config:
        return False
    mode = config.mode or "replace"
    if mode == "format":
        return True
    if mode == "add_text" and bool(config.add_text):
        return True
    if mode == "replace" and bool(config.find_text):
        return True
    return (
        bool(config.find_text)
        or (config.case_mode != "original")
        or bool(config.prefix)
        or bool(config.suffix)
        or config.numbering_enabled
        or bool(config.custom_extension)
        or (not config.preserve_extension)
    )


def generate_single_auto_name(
    item: FileItem,
    config: Optional[RenameConfig] = None,
    index: int = 0,
) -> str:
    """Generates an automatic new name for a single FileItem based on RenameConfig.

    If config is None or has no active transformations, normalizes the stem cleanly.
    """
    orig_path = item.original_path
    stem = orig_path.stem
    ext = orig_path.suffix

    cfg = config or RenameConfig()

    if has_active_rename_rules(cfg):
        return _compute_renamed_filename(
            stem=stem,
            ext=ext,
            mtime=item.modified_time,
            index=index,
            config=cfg,
        )

    # Default fallback: clean spacing and normalize to clean snake_case
    clean_stem = re.sub(r"[\s\-]+", "_", stem.strip()).strip("_")
    return f"{clean_stem.lower()}{ext.lower()}"


def clean_to_snake_case(filename: str) -> str:
    """Converts a filename's stem to snake_case while preserving its extension."""
    p = Path(filename)
    stem = p.stem
    ext = p.suffix
    clean_stem = re.sub(r"[\s\-]+", "_", stem.strip()).strip("_")
    return f"{clean_stem.lower()}{ext}"


def add_date_prefix(filename: str, mtime: float, date_format: str = "%Y%m%d") -> str:
    """Prepends a formatted modification date to the filename."""
    try:
        date_str = datetime.fromtimestamp(mtime).strftime(date_format)
    except Exception:
        date_str = "FECHA"
    p = Path(filename)
    return f"{date_str}_{p.name}"
