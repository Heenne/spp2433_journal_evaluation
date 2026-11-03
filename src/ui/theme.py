"""Application-wide light and dark visual themes."""


LIGHT_STYLESHEET = """
QMainWindow, QWidget { background: #f4f6fa; color: #202938; }
QToolBar { background: #ffffff; border: 0; border-bottom: 1px solid #d9e0ea; spacing: 6px; padding: 5px; }
QStatusBar { background: #ffffff; border-top: 1px solid #d9e0ea; }
QGroupBox { background: #ffffff; border: 1px solid #d9e0ea; border-radius: 8px; margin-top: 12px; padding: 10px 8px 8px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; font-weight: 600; }
QTabWidget::pane { background: #ffffff; border: 1px solid #d9e0ea; border-radius: 7px; top: -1px; }
QTabBar::tab { background: #e9edf4; border: 1px solid #d9e0ea; padding: 8px 12px; margin-right: 3px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
QTabBar::tab:selected { background: #ffffff; color: #174ea6; font-weight: 600; border-bottom-color: #ffffff; }
QPushButton, QToolButton { background: #ffffff; border: 1px solid #cbd4e1; border-radius: 6px; padding: 6px 10px; }
QPushButton:hover, QToolButton:hover { background: #edf3ff; border-color: #82a9e8; }
QPushButton#primaryAction { background: #2563eb; color: #ffffff; border-color: #2563eb; font-weight: 600; }
QPushButton#primaryAction:hover { background: #1d4ed8; }
QListWidget, QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QSlider { background: #ffffff; border: 1px solid #cbd4e1; border-radius: 5px; padding: 4px; }
QListWidget::item:selected { background: #dbeafe; color: #173b73; }
QLabel#sidebarHeading { font-size: 16px; font-weight: 700; }
QLabel#sidebarHint { color: #596579; }
"""


DARK_STYLESHEET = """
QMainWindow, QWidget { background: #171d27; color: #e6edf7; }
QToolBar { background: #202938; border: 0; border-bottom: 1px solid #354154; spacing: 6px; padding: 5px; }
QStatusBar { background: #202938; border-top: 1px solid #354154; }
QGroupBox { background: #1e2633; border: 1px solid #354154; border-radius: 8px; margin-top: 12px; padding: 10px 8px 8px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; font-weight: 600; }
QTabWidget::pane { background: #1e2633; border: 1px solid #354154; border-radius: 7px; top: -1px; }
QTabBar::tab { background: #252f3e; color: #d6deeb; border: 1px solid #354154; padding: 8px 12px; margin-right: 3px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
QTabBar::tab:selected { background: #1e2633; color: #93c5fd; font-weight: 600; border-bottom-color: #1e2633; }
QPushButton, QToolButton { background: #263244; border: 1px solid #45536a; border-radius: 6px; padding: 6px 10px; }
QPushButton:hover, QToolButton:hover { background: #34445c; border-color: #7194c9; }
QPushButton#primaryAction { background: #2563eb; color: #ffffff; border-color: #2563eb; font-weight: 600; }
QPushButton#primaryAction:hover { background: #3b82f6; }
QListWidget, QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QSlider { background: #151b24; color: #e6edf7; border: 1px solid #45536a; border-radius: 5px; padding: 4px; }
QListWidget::item:selected { background: #2b4c7c; color: #ffffff; }
QLabel#sidebarHeading { font-size: 16px; font-weight: 700; }
QLabel#sidebarHint { color: #a8b4c6; }
"""


def apply_theme(application, theme: str) -> None:
    """Apply a named theme to a QApplication instance."""
    application.setStyleSheet(DARK_STYLESHEET if theme == "dark" else LIGHT_STYLESHEET)
