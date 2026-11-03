"""Application-wide light and dark visual themes."""


LIGHT_STYLESHEET = """
QMainWindow, QWidget { background: #f4f6fa; color: #202938; font-family: "Segoe UI"; font-size: 10pt; }
QToolBar#projectToolbar { background: #ffffff; border: 0; border-bottom: 1px solid #dce3ed; spacing: 5px; padding: 8px 12px; }
QToolBar#projectToolbar::separator { width: 1px; background: #dce3ed; margin: 6px 8px; }
QToolBar#projectToolbar QToolButton { background: transparent; border: 1px solid transparent; border-radius: 8px; padding: 7px 10px; font-weight: 600; }
QToolBar#projectToolbar QToolButton:hover { background: #eef3fb; }
QToolBar#projectToolbar QToolButton#themeChoice { background: #f0f3f8; border: 1px solid #dce3ed; padding: 6px 12px; }
QToolBar#projectToolbar QToolButton#themeChoice:checked { background: #dbeafe; border-color: #8bb6f6; color: #174ea6; }
QWidget#projectSidebar { background: #f8fafd; border-right: 1px solid #dce3ed; }
QWidget#pointViewer { background: #ffffff; border: 1px solid #dce3ed; border-radius: 10px; }
QLabel#sectionHeading, QLabel#sidebarHeading { font-size: 15px; font-weight: 700; color: #17243a; }
QLabel#sectionHint, QLabel#sidebarHint { color: #64748b; font-size: 9pt; }
QToolBar#viewerToolbar { background: #ffffff; border: 0; spacing: 2px; padding: 0; }
QToolBar#viewerToolbar QToolButton { background: #f3f6fa; border: 1px solid transparent; border-radius: 6px; padding: 4px; }
QToolBar#viewerToolbar QToolButton:hover, QToolBar#viewerToolbar QToolButton:checked { background: #dbeafe; border-color: #a5c6f6; }
QStatusBar { background: #ffffff; border-top: 1px solid #dce3ed; }
QGroupBox { background: #ffffff; border: 1px solid #dce3ed; border-radius: 9px; margin-top: 15px; padding: 12px 9px 9px; font-weight: 600; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; color: #334155; }
QTabWidget::pane { background: #ffffff; border: 1px solid #dce3ed; border-radius: 8px; top: -1px; }
QTabBar::tab { background: transparent; color: #64748b; border: 0; border-bottom: 2px solid transparent; padding: 9px 11px; }
QTabBar::tab:hover { color: #2563eb; background: #eef3fb; }
QTabBar::tab:selected { color: #1d4ed8; background: #ffffff; border-bottom: 2px solid #2563eb; font-weight: 700; }
QPushButton, QToolButton { background: #f8fafd; border: 1px solid #cbd5e1; border-radius: 7px; padding: 7px 10px; }
QPushButton:hover, QToolButton:hover { background: #eef3fb; border-color: #8bb6f6; }
QPushButton:disabled, QToolButton:disabled { color: #94a3b8; background: #f3f5f8; border-color: #e3e8ef; }
QPushButton#primaryAction { background: #2563eb; color: #ffffff; border-color: #2563eb; font-weight: 700; }
QPushButton#primaryAction:hover { background: #1d4ed8; }
QListWidget, QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox { background: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; padding: 5px; }
QListWidget::item:selected { background: #dbeafe; color: #173b73; }
QMenu { background: #ffffff; border: 1px solid #dce3ed; padding: 5px; }
QMenu::item { padding: 7px 18px; border-radius: 5px; }
QMenu::item:selected { background: #e7f0ff; color: #174ea6; }
"""

DARK_STYLESHEET = """
QMainWindow, QWidget { background: #171d27; color: #e6edf7; font-family: "Segoe UI"; font-size: 10pt; }
QToolBar#projectToolbar { background: #202938; border: 0; border-bottom: 1px solid #354154; spacing: 5px; padding: 8px 12px; }
QToolBar#projectToolbar::separator { width: 1px; background: #45536a; margin: 6px 8px; }
QToolBar#projectToolbar QToolButton { background: transparent; border: 1px solid transparent; border-radius: 8px; padding: 7px 10px; font-weight: 600; }
QToolBar#projectToolbar QToolButton:hover { background: #34445c; }
QToolBar#projectToolbar QToolButton#themeChoice { background: #293548; border: 1px solid #45536a; padding: 6px 12px; }
QToolBar#projectToolbar QToolButton#themeChoice:checked { background: #2b4c7c; border-color: #6da2ed; color: #ffffff; }
QWidget#projectSidebar { background: #1b2430; border-right: 1px solid #354154; }
QWidget#pointViewer { background: #202938; border: 1px solid #354154; border-radius: 10px; }
QLabel#sectionHeading, QLabel#sidebarHeading { font-size: 15px; font-weight: 700; color: #f1f5fb; }
QLabel#sectionHint, QLabel#sidebarHint { color: #a8b4c6; font-size: 9pt; }
QToolBar#viewerToolbar { background: #202938; border: 0; spacing: 2px; padding: 0; }
QToolBar#viewerToolbar QToolButton { background: #2b3749; border: 1px solid transparent; border-radius: 6px; padding: 4px; }
QToolBar#viewerToolbar QToolButton:hover, QToolBar#viewerToolbar QToolButton:checked { background: #344f72; border-color: #6b91c5; }
QStatusBar { background: #202938; border-top: 1px solid #354154; }
QGroupBox { background: #202938; border: 1px solid #354154; border-radius: 9px; margin-top: 15px; padding: 12px 9px 9px; font-weight: 600; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; color: #cbd5e1; }
QTabWidget::pane { background: #202938; border: 1px solid #354154; border-radius: 8px; top: -1px; }
QTabBar::tab { background: transparent; color: #a8b4c6; border: 0; border-bottom: 2px solid transparent; padding: 9px 11px; }
QTabBar::tab:hover { color: #bfdbfe; background: #2b3749; }
QTabBar::tab:selected { color: #93c5fd; background: #202938; border-bottom: 2px solid #60a5fa; font-weight: 700; }
QPushButton, QToolButton { background: #2b3749; border: 1px solid #45536a; border-radius: 7px; padding: 7px 10px; }
QPushButton:hover, QToolButton:hover { background: #34445c; border-color: #7194c9; }
QPushButton:disabled, QToolButton:disabled { color: #77859a; background: #253040; border-color: #354154; }
QPushButton#primaryAction { background: #2563eb; color: #ffffff; border-color: #2563eb; font-weight: 700; }
QPushButton#primaryAction:hover { background: #3b82f6; }
QListWidget, QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox { background: #151b24; color: #e6edf7; border: 1px solid #45536a; border-radius: 6px; padding: 5px; }
QListWidget::item:selected { background: #2b4c7c; color: #ffffff; }
QMenu { background: #202938; border: 1px solid #45536a; padding: 5px; }
QMenu::item { padding: 7px 18px; border-radius: 5px; }
QMenu::item:selected { background: #2b4c7c; color: #ffffff; }
"""


def apply_theme(application, theme: str) -> None:
    """Apply a named theme to a QApplication instance."""
    application.setStyleSheet(DARK_STYLESHEET if theme == "dark" else LIGHT_STYLESHEET)
