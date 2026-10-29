"""Theme constants, colors, and formatting utilities for FilesPy (Flet)."""
from datetime import datetime

# Primary Brand Accent (#f40048)
COLOR_PRIMARY = "#f40048"
COLOR_PRIMARY_HOVER = "#d0003e"
COLOR_PRIMARY_LIGHT = "#ff336f"
COLOR_PRIMARY_MUTED = "#2d000d"
COLOR_PRIMARY_TRANSPARENT = "#20f40048"

# Surfaces and Backgrounds (Ultra-minimal Dark Palette)
COLOR_BG_DARK = "#0F1117"
COLOR_SURFACE_DARK = "#161922"
COLOR_CARD_DARK = "#1B1F2B"
COLOR_BORDER_DARK = "#272D3D"

# Text Colors
COLOR_TEXT_PRIMARY = "#F8FAFC"
COLOR_TEXT_SECONDARY = "#94A3B8"
COLOR_TEXT_MUTED = "#64748B"

# Semantic Status Colors
COLOR_SUCCESS = "#10B981"
COLOR_DANGER = "#EF4444"
COLOR_WARNING = "#F59E0B"
COLOR_INFO = "#38BDF8"


def format_bytes(num_bytes: int) -> str:
    """Formats bytes into human readable format (B, KB, MB, GB)."""
    if num_bytes < 1024:
        return f"{num_bytes} B"
    elif num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    elif num_bytes < 1024 * 1024 * 1024:
        return f"{num_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{num_bytes / (1024 * 1024 * 1024):.2f} GB"


def format_timestamp(ts: float) -> str:
    """Formats timestamp into YYYY-MM-DD HH:MM format."""
    if not ts:
        return "-"
    try:
        dt = datetime.fromtimestamp(ts)
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, OSError):
        return "-"


def safe_update(control) -> None:
    """Safely updates a Flet control if it is mounted to a page."""
    try:
        control.update()
    except (RuntimeError, AttributeError):
        pass

