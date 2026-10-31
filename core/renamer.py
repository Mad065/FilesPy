"""Batch renaming engine for applying pattern, text replacement, prefix, suffix, and sequence rules."""
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


def apply_rename_rules(items: List[FileItem], config: RenameConfig) -> List[FileItem]:
    """Applies renaming rules to the given list of FileItem objects.
    
    Returns the updated items (new_name calculated).
    """
    for index, item in enumerate(items):
        if not item.selected:
            item.new_name = item.original_name
            continue

        orig_path = item.original_path
        stem = orig_path.stem
        ext = orig_path.suffix

        # 1. Text Replacement
        if config.find_text:
            if config.use_regex:
                try:
                    flags = 0 if config.match_case else re.IGNORECASE
                    stem = re.sub(config.find_text, config.replace_text, stem, flags=flags)
                except re.error:
                    # Ignore invalid regex or preserve stem
                    pass
            else:
                if config.match_case:
                    stem = stem.replace(config.find_text, config.replace_text)
                else:
                    pattern = re.compile(re.escape(config.find_text), re.IGNORECASE)
                    stem = pattern.sub(config.replace_text, stem)

        # 2. Case transformation
        if config.case_mode != "original":
            stem = transform_case(stem, config.case_mode)

        # 3. Prefix & Suffix
        if config.prefix:
            stem = f"{config.prefix}{stem}"
        if config.suffix:
            stem = f"{stem}{config.suffix}"

        # 4. Numbering / Sequence
        if config.numbering_enabled:
            current_num = config.numbering_start + index
            digits = max(1, config.numbering_digits)
            formatted_num = f"{current_num:0{digits}d}"
            stem = f"{stem}_{formatted_num}"

        # 5. Extension handling
        final_ext = ext
        if config.custom_extension:
            custom = config.custom_extension.strip()
            if not custom.startswith("."):
                custom = f".{custom}"
            final_ext = custom
        elif not config.preserve_extension:
            final_ext = ""

        item.new_name = f"{stem}{final_ext}"

    return items


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

    has_active_rules = (
        bool(cfg.find_text)
        or (cfg.case_mode != "original")
        or bool(cfg.prefix)
        or bool(cfg.suffix)
        or cfg.numbering_enabled
        or bool(cfg.custom_extension)
        or (not cfg.preserve_extension)
    )

    if has_active_rules:
        # 1. Text Replacement
        if cfg.find_text:
            if cfg.use_regex:
                try:
                    flags = 0 if cfg.match_case else re.IGNORECASE
                    stem = re.sub(cfg.find_text, cfg.replace_text, stem, flags=flags)
                except re.error:
                    pass
            else:
                if cfg.match_case:
                    stem = stem.replace(cfg.find_text, cfg.replace_text)
                else:
                    pattern = re.compile(re.escape(cfg.find_text), re.IGNORECASE)
                    stem = pattern.sub(cfg.replace_text, stem)

        # 2. Case transformation
        if cfg.case_mode != "original":
            stem = transform_case(stem, cfg.case_mode)

        # 3. Prefix & Suffix
        if cfg.prefix:
            stem = f"{cfg.prefix}{stem}"
        if cfg.suffix:
            stem = f"{stem}{cfg.suffix}"

        # 4. Numbering
        if cfg.numbering_enabled:
            current_num = cfg.numbering_start + index
            digits = max(1, cfg.numbering_digits)
            stem = f"{stem}_{current_num:0{digits}d}"

        # 5. Extension
        final_ext = ext
        if cfg.custom_extension:
            custom = cfg.custom_extension.strip()
            if not custom.startswith("."):
                custom = f".{custom}"
            final_ext = custom
        elif not cfg.preserve_extension:
            final_ext = ""

        return f"{stem}{final_ext}"

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
    from datetime import datetime
    try:
        date_str = datetime.fromtimestamp(mtime).strftime(date_format)
    except Exception:
        date_str = "FECHA"
    p = Path(filename)
    return f"{date_str}_{p.name}"
