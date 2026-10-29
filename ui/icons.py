"""Icon generation and management for FilesPy.

Provides crisp, modern, vector-drawn line icons for both Light and Dark themes
using Pillow and CustomTkinter CTkImage. No emojis are used.
"""
import math
from pathlib import Path
from typing import Dict, Tuple
import customtkinter as ctk
from PIL import Image, ImageDraw

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "icons"

# Colors for theme adaptability
# In CustomTkinter, 'light_image' is shown when appearance is Light (needs dark icon)
# and 'dark_image' is shown when appearance is Dark (needs light icon).
COLOR_FOR_LIGHT_THEME = (30, 41, 59, 255)   # Slate 800 (dark gray)
COLOR_FOR_DARK_THEME = (241, 245, 249, 255)  # Slate 100 (light gray/white)

_ICON_CACHE: Dict[Tuple[str, int, int], ctk.CTkImage] = {}


def _create_canvas(size: int = 128) -> Image.Image:
    """Creates a transparent high-resolution RGBA canvas."""
    return Image.new("RGBA", (size, size), (0, 0, 0, 0))


def _draw_folder(draw: ImageDraw.ImageDraw, color: Tuple[int, int, int, int]):
    # Folder tab and body
    draw.polygon(
        [(16, 36), (16, 24), (48, 24), (60, 36), (112, 36), (112, 104), (16, 104)],
        outline=color,
        width=8,
    )
    draw.line([(16, 42), (112, 42)], fill=color, width=8)


def _draw_settings(draw: ImageDraw.ImageDraw, color: Tuple[int, int, int, int]):
    cx, cy = 64, 64
    r_out, r_in = 46, 34
    draw.ellipse([cx - r_out, cy - r_out, cx + r_out, cy + r_out], outline=color, width=7)
    draw.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], outline=color, width=8)
    for i in range(8):
        ang = i * (math.pi / 4)
        x1 = cx + (r_out - 2) * math.cos(ang)
        y1 = cy + (r_out - 2) * math.sin(ang)
        x2 = cx + (r_out + 12) * math.cos(ang)
        y2 = cy + (r_out + 12) * math.sin(ang)
        draw.line([(x1, y1), (x2, y2)], fill=color, width=12)


def _draw_edit(draw: ImageDraw.ImageDraw, color: Tuple[int, int, int, int]):
    # Pencil / edit icon
    # Tip
    draw.polygon([(24, 104), (24, 86), (42, 104)], outline=color, fill=color)
    # Shaft
    draw.polygon([(32, 78), (78, 32), (96, 50), (50, 96)], outline=color, width=8)
    # Eraser top
    draw.line([(78, 32), (92, 18), (110, 36), (96, 50)], fill=color, width=8)


def _draw_organize(draw: ImageDraw.ImageDraw, color: Tuple[int, int, int, int]):
    # 2x2 grid / layout squares
    r = 6
    draw.rounded_rectangle([18, 18, 56, 56], radius=r, outline=color, width=8)
    draw.rounded_rectangle([72, 18, 110, 56], radius=r, outline=color, width=8)
    draw.rounded_rectangle([18, 72, 56, 110], radius=r, outline=color, width=8)
    draw.rounded_rectangle([72, 72, 110, 110], radius=r, outline=color, width=8)


def _draw_duplicate(draw: ImageDraw.ImageDraw, color: Tuple[int, int, int, int]):
    # Two overlapping document cards
    r = 8
    # Back card
    draw.rounded_rectangle([42, 18, 108, 86], radius=r, outline=color, width=8)
    # Front card
    draw.rounded_rectangle([20, 42, 86, 110], radius=r, outline=color, width=8)


def _draw_search(draw: ImageDraw.ImageDraw, color: Tuple[int, int, int, int]):
    # Magnifying glass
    draw.ellipse([20, 20, 78, 78], outline=color, width=8)
    draw.line([(72, 72), (108, 108)], fill=color, width=10)


def _draw_refresh(draw: ImageDraw.ImageDraw, color: Tuple[int, int, int, int]):
    # Circular refresh arrow
    draw.arc([22, 22, 106, 106], start=40, end=310, fill=color, width=8)
    # Arrow head
    draw.polygon([(100, 36), (114, 56), (90, 62)], fill=color)


def _draw_undo(draw: ImageDraw.ImageDraw, color: Tuple[int, int, int, int]):
    # Undo curved arrow pointing left
    draw.arc([30, 34, 110, 114], start=180, end=360, fill=color, width=8)
    # Arrow head pointing left
    draw.polygon([(18, 74), (40, 52), (40, 96)], fill=color)


def _draw_check(draw: ImageDraw.ImageDraw, color: Tuple[int, int, int, int]):
    # Checkmark
    draw.line([(24, 66), (50, 92)], fill=color, width=10)
    draw.line([(50, 92), (106, 34)], fill=color, width=10)


def _draw_plus(draw: ImageDraw.ImageDraw, color: Tuple[int, int, int, int]):
    # Plus +
    draw.line([(64, 26), (64, 102)], fill=color, width=10)
    draw.line([(26, 64), (102, 64)], fill=color, width=10)


def _draw_trash(draw: ImageDraw.ImageDraw, color: Tuple[int, int, int, int]):
    # Trash bin
    # Lid & Handle
    draw.line([(22, 36), (106, 36)], fill=color, width=8)
    draw.rounded_rectangle([48, 20, 80, 36], radius=4, outline=color, width=7)
    # Bin body
    draw.polygon([(34, 44), (94, 44), (88, 108), (40, 108)], outline=color, width=8)
    # Vertical ribs
    draw.line([(52, 54), (52, 98)], fill=color, width=6)
    draw.line([(76, 54), (76, 98)], fill=color, width=6)


ICON_BUILDERS = {
    "folder": _draw_folder,
    "settings": _draw_settings,
    "edit": _draw_edit,
    "rename": _draw_edit,
    "organize": _draw_organize,
    "duplicate": _draw_duplicate,
    "search": _draw_search,
    "refresh": _draw_refresh,
    "undo": _draw_undo,
    "check": _draw_check,
    "plus": _draw_plus,
    "trash": _draw_trash,
}


def render_icon_image(name: str, is_dark_theme: bool, render_size: int = 48) -> Image.Image:
    """Renders an icon image at render_size with antialiasing."""
    builder = ICON_BUILDERS.get(name)
    if not builder:
        return Image.new("RGBA", (render_size, render_size), (0, 0, 0, 0))

    canvas = _create_canvas(size=128)
    draw = ImageDraw.Draw(canvas)
    color = COLOR_FOR_DARK_THEME if is_dark_theme else COLOR_FOR_LIGHT_THEME
    builder(draw, color)

    # Downsample with high-quality resampling for anti-aliased edges
    return canvas.resize((render_size, render_size), Image.Resampling.LANCZOS)


def ensure_icons_exported():
    """Exports PNG icons to assets/icons/ for static asset availability."""
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    for name in ICON_BUILDERS.keys():
        light_path = ASSETS_DIR / f"{name}_light.png"
        dark_path = ASSETS_DIR / f"{name}_dark.png"

        if not light_path.exists():
            img_light = render_icon_image(name, is_dark_theme=False, render_size=48)
            img_light.save(light_path, "PNG")

        if not dark_path.exists():
            img_dark = render_icon_image(name, is_dark_theme=True, render_size=48)
            img_dark.save(dark_path, "PNG")


def get_icon(name: str, size: Tuple[int, int] = (16, 16)) -> ctk.CTkImage:
    """Returns a CTkImage for the given icon name that adapts to Light and Dark themes."""
    key = (name, size[0], size[1])
    if key in _ICON_CACHE:
        return _ICON_CACHE[key]

    light_img = render_icon_image(name, is_dark_theme=False, render_size=size[0] * 2)
    dark_img = render_icon_image(name, is_dark_theme=True, render_size=size[0] * 2)

    ctk_img = ctk.CTkImage(
        light_image=light_img,
        dark_image=dark_img,
        size=size,
    )
    _ICON_CACHE[key] = ctk_img
    return ctk_img
