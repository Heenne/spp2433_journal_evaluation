"""Rebuild the vector point-cloud icon and multi-resolution Windows ICO.

Run with the project's environment: python tools/generate_app_icon.py
"""
import math
from pathlib import Path

from PIL import Image
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtSvg import QSvgRenderer


def generate():
    assets = Path(__file__).resolve().parents[1] / "src" / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">',
           '<defs><linearGradient id="tile" x2="0.7" y2="1"><stop stop-color="#203c63"/><stop offset="1" stop-color="#101f39"/></linearGradient></defs>',
           '<rect x="4" y="4" width="248" height="248" rx="50" fill="url(#tile)"/>',
           '<g fill="none" stroke="#738ba8" stroke-width="5" stroke-linecap="round" stroke-linejoin="round">',
           '<path d="M34 152 L128 205 L222 152 M128 205 V45"/>',
           '<path d="M34 152 L37 166 M34 152 L49 151 M222 152 L207 151 M222 152 L219 166 M128 45 L119 56 M128 45 L137 56"/>',
           '</g>']
    colours = ["#4d91f5", "#6fb1fb", "#a5d6ff", "#eef7ff", "#ffd1c7", "#ffa193", "#ff746b"]
    for row in range(7):
        for column in range(7):
            x = 128 + 16 * (column - row)
            y = 122 + 9 * (column + row - 6) - 13 * math.cos((column - 3) * math.pi / 6)
            svg.append(f'<circle cx="{x}" cy="{y:.2f}" r="5.8" fill="{colours[column]}"/>')
    svg.append('</svg>')
    source = assets / "app_icon.svg"
    source.write_text("\n".join(svg) + "\n", encoding="utf-8")
    image = QImage(512, 512, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    QSvgRenderer(str(source)).render(painter)
    painter.end()
    png = assets / "app_icon.png"
    if not image.save(str(png)):
        raise RuntimeError("Could not write app_icon.png")
    with Image.open(png) as bitmap:
        bitmap.save(assets / "app_icon.ico", format="ICO",
                    sizes=[(size, size) for size in (16, 20, 24, 32, 40, 48, 64, 128, 256)])


if __name__ == "__main__":
    generate()
