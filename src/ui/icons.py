"""Small, single-colour outline icons used by the application chrome."""

from PyQt6.QtCore import QByteArray, QRectF, Qt
from PyQt6.QtGui import QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer


_PATHS = {
    "folder": '<path d="M3 6.5h6l2 2H21v9.8a1.7 1.7 0 0 1-1.7 1.7H4.7A1.7 1.7 0 0 1 3 18.3z"/><path d="M3 9h18"/>',
    "cloud": '<circle cx="6" cy="8" r="1.3"/><circle cx="12" cy="6" r="1.3"/><circle cx="18" cy="9" r="1.3"/><circle cx="8" cy="14" r="1.3"/><circle cx="14" cy="13" r="1.3"/><circle cx="19" cy="16" r="1.3"/><circle cx="5" cy="18" r="1.3"/><circle cx="11" cy="19" r="1.3"/><circle cx="16" cy="21" r="1.3"/>',
    "save": '<path d="M4 3h13l4 4v14H4z"/><path d="M8 3v6h9V3M8 21v-8h9v8"/>',
    "save_as": '<path d="M4 3h12l4 4v6M4 3v18h9"/><path d="M8 3v6h8V4M8 21v-6h5"/><path d="m14 19 5-5 2 2-5 5-3 1z"/>',
    "convert": '<path d="M4 7h13l-3-3M20 17H7l3 3"/><path d="m17 4 3 3-3 3M7 14l-3 3 3 3"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M2 12h2m16 0h2M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42"/>',
    "moon": '<path d="M20.5 15.5A8.5 8.5 0 0 1 8.5 3.5 8.7 8.7 0 1 0 20.5 15.5Z"/>',
    "chevron_down": '<path d="m6 9 6 6 6-6"/>',
    "chevron_left": '<path d="m15 5-7 7 7 7"/>',
    "chevron_right": '<path d="m9 5 7 7-7 7"/>',
    "home": '<path d="m3 11 9-7 9 7M5 10v10h14V10M9 20v-6h6v6"/>',
    "back": '<path d="m14 5-7 7 7 7M7 12h14"/>',
    "forward": '<path d="m10 5 7 7-7 7M17 12H3"/>',
    "pan": '<path d="M12 3v18m-3-3 3 3 3-3M12 3 9 6m3-3 3 3M3 12h18m-3-3 3 3-3 3M3 12l3-3m-3 3 3 3"/>',
    "zoom": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m15.5 15.5 5 5M10.5 7.5v6m-3-3h6"/>',
    "subplots": '<rect x="3" y="4" width="8" height="7" rx="1"/><rect x="13" y="4" width="8" height="7" rx="1"/><rect x="3" y="13" width="8" height="7" rx="1"/><rect x="13" y="13" width="8" height="7" rx="1"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "edit": '<path d="m4 16.5-.8 4.3 4.3-.8L20 7.5 16.5 4z"/><path d="m14.8 5.7 3.5 3.5"/>',
    "trash": '<path d="M4 7h16M9 7V4h6v3m3 0-1 14H7L6 7m3 3v7m6-7v7"/>',
    "up": '<path d="m6 14 6-6 6 6"/>',
    "down": '<path d="m6 10 6 6 6-6"/>',
    "camera": '<path d="m3 12 9-8 9 8M5 11v9h14v-9M9 20v-6h6v6"/>',
    "data": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v7c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12v7c0 1.7 3.6 3 8 3s8-1.3 8-3v-7"/>',
    "prepare": '<path d="M4 6h16M7 12h10m-7 6h4"/><circle cx="8" cy="6" r="1"/><circle cx="16" cy="12" r="1"/><circle cx="10" cy="18" r="1"/>',
    "align": '<path d="M12 3v18M3 12h18M7 7l10 10m0-10L7 17"/><circle cx="12" cy="12" r="8"/>',
    "evaluate": '<path d="M5 19V5m0 14h14M8 16l3-4 3 2 5-7"/><circle cx="11" cy="12" r="1"/><circle cx="14" cy="14" r="1"/><circle cx="19" cy="7" r="1"/>',
    "export": '<path d="M12 3v12m-5-5 5 5 5-5M5 16v4h14v-4"/>',
    "preview": '<path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z"/><circle cx="12" cy="12" r="2.5"/>',
    "export_display": '<rect x="3.5" y="4" width="17" height="15" rx="1.5"/><path d="m5 16 4.5-4.5 3.2 3.2 2.3-2.3L19 16"/>',
    "export_full": '<path d="M8 4H4v4m12-4h4v4M4 16v4h4m12-4v4h-4"/><path d="M4 4l6 6m10-6-6 6M4 20l6-6m10 6-6-6"/>',
    "help": '<circle cx="12" cy="12" r="9"/><path d="M9.6 9a2.5 2.5 0 1 1 4.3 1.8c-1.1 1.1-1.9 1.4-1.9 3M12 17.5h.01"/>',
}

_GITHUB_MARK = (
    "M12 1C5.93 1 1 5.93 1 12c0 4.87 3.16 8.99 7.55 10.44c.55.1.75-.24.75-.53"
    " 0-.26-.01-.95-.01-1.86-3.07.66-3.71-.74-3.96-1.42-.12-.31-.66-1.42-1.13-1.71"
    "-.39-.21-.94-.72-.01-.73.87-.01 1.49.8 1.7 1.13.99 1.66 2.58 1.19 3.21.9"
    ".1-.72.39-1.19.7-1.46-2.77-.31-5.66-1.39-5.66-6.15 0-1.36.49-2.48"
    "1.29-3.36-.13-.32-.56-1.6.12-3.32 0 0 1.05-.33 3.46 1.28a11.92 11.92 0 0 1"
    "6.3 0c2.4-1.63 3.46-1.28 3.46-1.28.68 1.72.25 3-.12 3.32.81.88 1.29 1.99"
    "1.29 3.36 0 4.77-2.9 5.83-5.67 6.15.37.32.7.94.7 1.9 0 1.37-.01 2.47-.01"
    " 2.81 0 .29.2.63.75.53A11.02 11.02 0 0 0 23 12c0-6.07-4.93-11-11-11Z"
)


def monochrome_icon(name: str, color: str) -> QIcon:
    """Render a crisp, monochrome 24 px outline icon."""
    if name == "github":
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">'
            f'<path fill="{color}" d="{_GITHUB_MARK}"/></svg>'
        )
        renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        renderer.render(painter, QRectF(0, 0, 48, 48))
        painter.end()
        return QIcon(pixmap)

    body = _PATHS[name]
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">'
        f'<g fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" '
        f'stroke-linejoin="round">{body}</g></svg>'
    )
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pixmap = QPixmap(48, 48)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter, QRectF(0, 0, 48, 48))
    painter.end()
    return QIcon(pixmap)


def github_icon(color: str) -> QIcon:
    """Render the filled GitHub mark in the requested theme colour."""
    return monochrome_icon("github", color)
