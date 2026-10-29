"""UI Theme constants, colors, and formatting utilities."""
from datetime import datetime

# Color Palette
COLOR_SUCCESS = "#10B981"  # Emerald green
COLOR_SUCCESS_HOVER = "#059669"
COLOR_DANGER = "#EF4444"   # Red
COLOR_DANGER_HOVER = "#DC2626"
COLOR_WARNING = "#F59E0B"  # Amber
COLOR_MUTED = "#6B7280"    # Gray
COLOR_PRIMARY = "#2563EB"  # Royal blue
COLOR_PRIMARY_HOVER = "#1D4ED8"
COLOR_SURFACE_DARK = "#1E293B"
COLOR_SURFACE_LIGHT = "#F1F5F9"


def format_bytes(num_bytes: int) -> str:
    """Formats bytes into human readable format (KB, MB, GB)."""
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
