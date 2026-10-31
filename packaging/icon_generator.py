#!/usr/bin/env python3
"""Generador de iconos oficiales FilesPy para Windows (.ico), macOS (.icns) y Linux (.png).

Crea un diseno moderno y minimalista con el color de marca #f40048 sobre fondo oscuro,
generando las resoluciones necesarias para instaladores y ejecutables de escritorio.
"""
import os
import sys
from PIL import Image, ImageDraw


def generate_icons(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    size = 512
    # Create 512x512 canvas with transparent background
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded rectangle background: dark luxury charcoal #141418
    # with smooth rounded corners
    corner_radius = 110
    draw.rounded_rectangle(
        [(24, 24), (size - 24, size - 24)],
        radius=corner_radius,
        fill=(20, 20, 24, 255),
        outline=(50, 50, 58, 255),
        width=4,
    )

    # Modern folder / organizer geometry
    # Back folder tab
    draw.rounded_rectangle(
        [(90, 110), (240, 190)],
        radius=20,
        fill=(180, 0, 50, 255),
    )

    # Main folder body: #f40048
    draw.rounded_rectangle(
        [(90, 160), (422, 390)],
        radius=36,
        fill=(244, 0, 72, 255),
    )

    # Inner document sheet peeking out: crisp white/silver
    draw.rounded_rectangle(
        [(150, 115), (362, 260)],
        radius=18,
        fill=(248, 249, 250, 255),
    )
    # Sheet fold corner or text lines
    draw.line([(190, 160), (320, 160)], fill=(200, 202, 210, 255), width=8)
    draw.line([(190, 190), (280, 190)], fill=(200, 202, 210, 255), width=8)

    # Front folder flap with subtle gradient overlay/accent
    draw.rounded_rectangle(
        [(90, 210), (422, 390)],
        radius=36,
        fill=(220, 0, 64, 255),
        outline=(255, 60, 110, 180),
        width=4,
    )

    # Lighting highlight inside folder body
    draw.arc(
        [(100, 220), (412, 380)],
        start=180,
        end=360,
        fill=(255, 100, 140, 120),
        width=3,
    )

    # Save PNG
    png_path = os.path.join(output_dir, "app_icon.png")
    img.save(png_path, format="PNG")
    print(f"Generated: {png_path}")

    # Save Windows ICO (containing multi-resolutions: 16, 24, 32, 48, 64, 128, 256)
    ico_path = os.path.join(output_dir, "app_icon.ico")
    icon_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(ico_path, format="ICO", sizes=icon_sizes)
    print(f"Generated: {ico_path}")

    # Generate macOS ICNS if supported or iconset
    icns_path = os.path.join(output_dir, "app_icon.icns")
    try:
        img.save(icns_path, format="ICNS")
        print(f"Generated: {icns_path}")
    except Exception as e:
        print(f"ICNS direct save note: {e}")
        # On macOS, sips or iconutil can also convert if needed
        pass

    return png_path, ico_path


if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "icons"))
    generate_icons(base_dir)
