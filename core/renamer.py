"""Batch renaming engine for applying pattern, text replacement, prefix, suffix, and sequence rules."""
import re
from pathlib import Path
from typing import List
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
