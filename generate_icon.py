#!/usr/bin/env python3
"""
Generate app icon assets for QR Code Generator.

Produces:
  assets/icon.png   — 512×512 source PNG (Tkinter window icon, Linux)
  assets/icon.ico   — multi-resolution Windows icon (16/32/48/256 px)
  assets/icon.icns  — macOS icon bundle (macOS only; requires built-in iconutil)

Run once from the project root with the virtual environment active:
  python generate_icon.py
"""

import os
import random
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

# Colour scheme
_BG   = (30, 27, 75, 255)    # deep indigo background
_DARK = (255, 255, 255, 255)  # white QR modules
_LITE = _BG                   # "light" modules show background through


def _draw_finder(draw, x, y, m, dark, light):
    """Draw a standard 7×7 QR finder pattern at pixel position (x, y)."""
    draw.rectangle([x,       y,       x+7*m-1, y+7*m-1], fill=dark)   # outer
    draw.rectangle([x+m,     y+m,     x+6*m-1, y+6*m-1], fill=light)  # ring gap
    draw.rectangle([x+2*m,   y+2*m,   x+5*m-1, y+5*m-1], fill=dark)   # inner


def _make_image(size: int) -> Image.Image:
    """Render the icon at the requested pixel size."""
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded-rectangle background
    draw.rounded_rectangle([0, 0, size-1, size-1], radius=size // 8, fill=_BG)

    margin = size // 12
    mod    = (size - 2 * margin) // 21   # map onto a 21-module virtual QR grid
    if mod < 1:
        mod = 1

    # Three finder patterns (top-left, top-right, bottom-left)
    _draw_finder(draw, margin,          margin,          mod, _DARK, _LITE)
    _draw_finder(draw, margin + 14*mod, margin,          mod, _DARK, _LITE)
    _draw_finder(draw, margin,          margin + 14*mod, mod, _DARK, _LITE)

    # Timing strips (row 6 and column 6, between finder patterns)
    for i in range(8, 13):
        if i % 2 == 0:
            # horizontal strip
            draw.rectangle(
                [margin+i*mod, margin+6*mod, margin+(i+1)*mod-1, margin+7*mod-1],
                fill=_DARK)
            # vertical strip
            draw.rectangle(
                [margin+6*mod, margin+i*mod, margin+7*mod-1, margin+(i+1)*mod-1],
                fill=_DARK)

    # Deterministic data dots (seeded so the icon is always the same)
    rng = random.Random(42)
    for row in range(21):
        for col in range(21):
            # Skip finder + separator zones (8×8 corners) and timing strips
            if (row < 9 and col < 9) or (row < 9 and col > 11) or (row > 11 and col < 9):
                continue
            if row == 6 or col == 6:
                continue
            if rng.random() < 0.45:
                px = margin + col * mod
                py = margin + row * mod
                draw.rectangle([px, py, px+mod-1, py+mod-1], fill=_DARK)

    return img


def _save_png():
    path = os.path.join(ASSETS_DIR, "icon.png")
    _make_image(512).save(path, format="PNG")
    print(f"Saved  {path}")


def _save_ico():
    """Save a multi-resolution .ico containing 16, 32, 48, and 256 px layers."""
    sizes  = [16, 32, 48, 256]
    frames = [_make_image(s) for s in sizes]
    path   = os.path.join(ASSETS_DIR, "icon.ico")
    frames[0].save(
        path, format="ICO",
        append_images=frames[1:],
        sizes=[(s, s) for s in sizes],
    )
    print(f"Saved  {path}")


def _save_icns():
    """Use macOS iconutil to assemble a .icns from multiple PNG resolutions."""
    if sys.platform != "darwin":
        print("Skipped icon.icns — macOS only (run this script on macOS to generate it).")
        return

    # iconutil requires a directory named *.iconset
    iconset = tempfile.mkdtemp(suffix=".iconset")
    try:
        for filename, px in [
            ("icon_16x16.png",      16),
            ("icon_16x16@2x.png",   32),
            ("icon_32x32.png",      32),
            ("icon_32x32@2x.png",   64),
            ("icon_128x128.png",    128),
            ("icon_128x128@2x.png", 256),
            ("icon_256x256.png",    256),
            ("icon_256x256@2x.png", 512),
            ("icon_512x512.png",    512),
            ("icon_512x512@2x.png", 1024),
        ]:
            _make_image(px).save(os.path.join(iconset, filename), format="PNG")

        out = os.path.join(ASSETS_DIR, "icon.icns")
        subprocess.run(["iconutil", "-c", "icns", iconset, "-o", out], check=True)
        print(f"Saved  {out}")
    finally:
        shutil.rmtree(iconset, ignore_errors=True)


def main():
    os.makedirs(ASSETS_DIR, exist_ok=True)
    _save_png()
    _save_ico()
    _save_icns()


if __name__ == "__main__":
    main()
