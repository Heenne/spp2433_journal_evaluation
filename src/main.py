import sys
import os
from pathlib import Path
from PyQt6.QtCore import Qt, QTimer, QRect, QSize
from PyQt6.QtGui import QCursor, QGuiApplication, QPixmap
from PyQt6.QtWidgets import QApplication, QLabel, QMessageBox, QProgressBar, QVBoxLayout, QWidget
from src.ui.application_identity import application_icon, set_windows_app_id


def _initial_window_geometry(app):
    screen = QGuiApplication.screenAt(QCursor.pos()) or app.primaryScreen()
    if screen is None:
        return QRect(0, 0, 1280, 800)
    available = screen.availableGeometry()
    minimum_width = min(1050, max(1, available.width() - 32))
    minimum_height = min(700, max(1, available.height() - 32))
    width = max(minimum_width, min(1500, round(available.width() * 0.9)))
    height = max(minimum_height, min(900, round(available.height() * 0.9)))
    return QRect(
        available.x() + (available.width() - width) // 2,
        available.y() + (available.height() - height) // 2,
        width,
        height,
    )


class StartupSplash(QWidget):
    """Full-window startup splash with phase-based loading progress."""

    def __init__(self, app):
        super().__init__(None, Qt.WindowType.Window)
        self.app = app
        self.setWindowTitle("SPP 2433 - Point Cloud Evaluation")
        self.setWindowIcon(app.windowIcon())
        self.setGeometry(_initial_window_geometry(app))
        self.setStyleSheet("background: #f7f8fa; color: #202938;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.addStretch(1)

        self.logo = QLabel()
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_path = Path(__file__).resolve().parent / "assets" / "app_icon.png"
        logo_pixmap = QPixmap(str(logo_path))
        if logo_pixmap.isNull():
            logo_pixmap = app.windowIcon().pixmap(QSize(128, 128))
        self.logo.setPixmap(logo_pixmap.scaled(
            QSize(128, 128), Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation))
        self.logo.setStyleSheet("background: transparent;")
        layout.addWidget(self.logo)

        self.name = QLabel("SPP 2433")
        self.name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name.setStyleSheet("font-size: 24pt; font-weight: 700; background: transparent;")
        layout.addWidget(self.name)

        self.product = QLabel("Point Cloud Evaluation")
        self.product.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.product.setStyleSheet("font-size: 14pt; color: #526174; background: transparent;")
        layout.addWidget(self.product)

        layout.addSpacing(34)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("%p%")
        self.progress.setFixedSize(520, 18)
        self.progress.setStyleSheet(
            "QProgressBar { border: 0; background: #e1e6ed; border-radius: 9px; "
            "text-align: center; color: #344054; font-size: 9pt; }"
            "QProgressBar::chunk { background: #4d7fe0; border-radius: 9px; }"
        )
        layout.addWidget(self.progress, 0, Qt.AlignmentFlag.AlignHCenter)

        self.status = QLabel("Preparing application…")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setStyleSheet("font-size: 10pt; color: #667085; background: transparent;")
        layout.addWidget(self.status)
        layout.addStretch(1)

    def set_progress(self, value: int, message: str):
        self.progress.setValue(value)
        self.status.setText(message)
        self.app.processEvents()


def main():
    set_windows_app_id()
    app = QApplication(sys.argv)
    app.setOrganizationName("SPP2433")
    app.setApplicationName("SPP2433PointCloudEvaluation")
    app.setApplicationDisplayName("SPP 2433 - Point Cloud Evaluation")
    app.setWindowIcon(application_icon())
    app.setStyle("Fusion")

    try:
        progress_base = max(0, min(60, int(os.environ.pop("SPP2433_STARTUP_PROGRESS", "0"))))
    except ValueError:
        progress_base = 0
    progress_span = 100 - progress_base
    splash = StartupSplash(app)
    splash.set_progress(progress_base, "Preparing application…")
    splash.show()
    app.processEvents()

    def load_main_window():
        try:
            splash.set_progress(progress_base + max(1, round(progress_span * 0.05)),
                                "Loading application modules…")
            from src.ui.main_window import MainWindow

            splash.set_progress(progress_base + round(progress_span * 0.35),
                                "Preparing the workspace…")
            window = MainWindow()
            app._main_window = window
            splash.set_progress(progress_base + round(progress_span * 0.85),
                                "Opening the workspace…")
            window.show()
            splash.set_progress(100, "Ready")
            splash.close()
        except Exception as error:
            splash.close()
            QMessageBox.critical(
                None,
                "SPP 2433 - Point Cloud Evaluation",
                f"Die App konnte nicht gestartet werden.\n\n{error}\n\nDie Anwendung wird beendet.",
                QMessageBox.StandardButton.Ok,
            )
            app.quit()

    QTimer.singleShot(50, load_main_window)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
