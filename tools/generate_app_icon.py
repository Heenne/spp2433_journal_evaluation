"""Build the app icon from the supplied SPP logo and a multi-resolution Windows ICO.

Run with the project's environment: python tools/generate_app_icon.py
"""
import shutil
from pathlib import Path

from PIL import Image
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtSvg import QSvgRenderer


def generate():
    assets = Path(__file__).resolve().parents[1] / "src" / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    source = assets / "brand_logo.svg"
    icon_svg = assets / "app_icon.svg"
    shutil.copyfile(source, icon_svg)
    image = QImage(512, 512, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer = QSvgRenderer(str(source))
    size = renderer.defaultSize()
    scale = min(512 / size.width(), 512 / size.height())
    width, height = size.width() * scale, size.height() * scale
    renderer.render(painter, QRectF((512 - width) / 2, (512 - height) / 2, width, height))
    painter.end()
    png = assets / "app_icon.png"
    if not image.save(str(png)):
        raise RuntimeError("Could not write app_icon.png")
    with Image.open(png) as bitmap:
        bitmap.save(assets / "app_icon.ico", format="ICO",
                    sizes=[(size, size) for size in (16, 20, 24, 32, 40, 48, 64, 128, 256)])


if __name__ == "__main__":
    generate()
