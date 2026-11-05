"""A spotlight walkthrough that points out the main application areas."""

from PyQt6.QtCore import QEvent, QPoint, QRect, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)


_COPY = {
    "en": {
        "window_title": "New user guide",
        "step": "Step {current} of {total}  ·  {area}",
        "back": "Back",
        "skip": "Skip guide",
        "next": "Next",
        "finish": "Finish",
        "steps": [
            (
                "Welcome to Point Cloud Evaluation",
                "This short tour shows where to load data, inspect point clouds, align them, and compare results. Use Next to continue, or skip the guide at any time. Reopen it later with the ? button.",
                "Main toolbar",
                "welcome",
            ),
            (
                "Load a point cloud",
                "Use the plus button above the Point Clouds list to open CSV or PLY files. You can add a reference cloud and the measurement you want to evaluate.",
                "Add point cloud",
                "load_cloud",
            ),
            (
                "Select and show clouds",
                "The Point Clouds list is on the left. Select a row to edit that cloud's settings; use its checkbox to show or hide it in the plot. Add both a reference and the measurement you want to evaluate.",
                "Point Clouds list",
                "cloud_list",
            ),
            (
                "Inspect the point cloud",
                "The plot is in the middle. Rotate, pan, zoom, or reset the view using the controls directly above it. The camera shortcuts are below the cloud list.",
                "Center plot",
                "plot",
            ),
            (
                "Find the workspace tools",
                "The tabs on the right contain settings for the selected cloud. Use the arrows at the ends of the tab row to reveal more tools, including Filter, Align, Evaluate, and Export.",
                "Workspace tabs",
                "tools",
            ),
            (
                "Align the measurement",
                "Open Manual Align for scale, rotation, and translation. Use Auto Align for a registration method. Choose the measurement as the selected cloud and keep the reference fixed. Check units before aligning.",
                "Manual Align tab",
                "manual_align",
            ),
            (
                "Compare against a reference",
                "Open Evaluate, choose the measurement as Source and the fixed cloud as Reference, then calculate the surface error. Inspect the colour map and open the results for the numeric metrics.",
                "Evaluate tab",
                "evaluate",
            ),
            (
                "Save your project",
                "Save and Save as are in the top toolbar. The project file keeps your settings and results and points to the original cloud files, so keep those files available when reopening it.",
                "Main toolbar",
                "save_project",
            ),
            (
                "Export your results",
                "Use Export Point Cloud in the top toolbar for filtered or centered point-cloud data. Use the Export tab on the right for plot appearance and figure export.",
                "Export Point Cloud",
                "export",
            ),
        ],
    },
    "de": {
        "window_title": "Einführung",
        "step": "Schritt {current} von {total}  ·  {area}",
        "back": "Zurück",
        "skip": "Einführung überspringen",
        "next": "Weiter",
        "finish": "Fertig",
        "steps": [
            (
                "Willkommen bei Point Cloud Evaluation",
                "Dieser kurze Rundgang zeigt, wo Sie Punktwolken laden, ansehen, ausrichten und vergleichen. Mit Weiter geht es zum nächsten Schritt; Sie können jederzeit überspringen. Über das ?-Symbol lässt sich die Einführung später erneut öffnen.",
                "Hauptwerkzeugleiste",
                "welcome",
            ),
            (
                "Punktwolke laden",
                "Wählen Sie das Plus über der Punktwolkenliste, um CSV- oder PLY-Dateien zu öffnen. Fügen Sie die Referenz und die auszuwertende Messung hinzu.",
                "Punktwolke hinzufügen",
                "load_cloud",
            ),
            (
                "Punktwolken auswählen und anzeigen",
                "Links befindet sich die Liste der Punktwolken. Wählen Sie eine Zeile, um deren Einstellungen zu bearbeiten. Mit dem Häkchen blenden Sie die Wolke im Plot ein oder aus. Fügen Sie eine Referenz und die auszuwertende Messung hinzu.",
                "Punktwolkenliste",
                "cloud_list",
            ),
            (
                "Punktwolke ansehen",
                "Der Plot befindet sich in der Mitte. Mit den Steuerelementen direkt darüber können Sie drehen, verschieben, zoomen oder die Ansicht zurücksetzen. Kamera-Schnellansichten stehen unter der Punktwolkenliste.",
                "Plot in der Mitte",
                "plot",
            ),
            (
                "Werkzeuge finden",
                "Die Tabs rechts enthalten Einstellungen für die ausgewählte Punktwolke. Mit den Pfeilen an den Enden der Tab-Leiste erreichen Sie weitere Werkzeuge wie Filter, Ausrichten, Auswerten und Export.",
                "Werkzeug-Tabs",
                "tools",
            ),
            (
                "Messung ausrichten",
                "Unter Manuell ausrichten können Sie Skalierung, Drehung und Verschiebung einstellen. Automatisch ausrichten bietet Registrierungsverfahren. Wählen Sie die Messung als ausgewählte Wolke und lassen Sie die Referenz fest. Prüfen Sie vor dem Ausrichten die Einheiten.",
                "Tab Manuell ausrichten",
                "manual_align",
            ),
            (
                "Mit einer Referenz vergleichen",
                "Öffnen Sie Auswerten, wählen Sie die Messung als Quelle und die feste Punktwolke als Referenz und berechnen Sie den Oberflächenfehler. Prüfen Sie die Farbkarte und öffnen Sie die Ergebnisse für Kennzahlen.",
                "Tab Auswerten",
                "evaluate",
            ),
            (
                "Projekt speichern",
                "Speichern und Speichern unter befinden sich in der oberen Werkzeugleiste. Die Projektdatei sichert Einstellungen und Ergebnisse und verweist auf die ursprünglichen Punktwolkendateien. Diese Dateien müssen zum erneuten Öffnen verfügbar bleiben.",
                "Hauptwerkzeugleiste",
                "save_project",
            ),
            (
                "Ergebnisse exportieren",
                "Punktwolke exportieren in der oberen Werkzeugleiste bietet den Export gefilterter oder zentrierter Daten. Im Export-Tab rechts finden Sie die Einstellungen für die Plotdarstellung und den Export von Abbildungen.",
                "Punktwolke exportieren",
                "export",
            ),
        ],
    },
}


class NewUserGuideDialog(QDialog):
    """A modal, nine-step tour with a dimmed scrim and a spotlight target."""

    def __init__(self, language: str, parent=None):
        super().__init__(parent)
        self.copy = _COPY[language if language in _COPY else "en"]
        self.current_step = 0
        self.highlight_rect = QRect()
        self.target_key = ""

        self.setWindowTitle(self.copy["window_title"])
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(480, 300)

        self.card = QFrame(self)
        self.card.setObjectName("guideCallout")
        self.card.setFixedWidth(410)
        self.card.setStyleSheet(
            "QFrame#guideCallout { background: #ffffff; color: #202938; "
            "border: 1px solid #d9dee7; border-radius: 14px; }"
            "QLabel { border: none; background: transparent; color: #202938; }"
            "QLabel#guideStepLabel { color: #58677b; font-size: 9pt; font-weight: 600; }"
            "QLabel#guideHeading { font-size: 15pt; font-weight: 700; }"
            "QLabel#guideBody { color: #485467; font-size: 10pt; }"
            "QPushButton { min-height: 34px; padding: 0 13px; border-radius: 7px; "
            "background: #f1f3f6; color: #202938; border: 1px solid #d9dee7; }"
            "QPushButton:hover { background: #e7ebf1; }"
            "QPushButton#primaryAction { background: #315fbb; color: white; "
            "border: 1px solid #315fbb; font-weight: 600; }"
            "QPushButton#primaryAction:hover { background: #244e9e; }"
            "QProgressBar { border: none; background: #e9edf3; border-radius: 3px; }"
            "QProgressBar::chunk { background: #4d7fe0; border-radius: 3px; }"
        )

        layout = QVBoxLayout(self.card)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(11)

        self.step_label = QLabel()
        self.step_label.setObjectName("guideStepLabel")
        layout.addWidget(self.step_label)

        self.heading = QLabel()
        self.heading.setObjectName("guideHeading")
        self.heading.setWordWrap(True)
        layout.addWidget(self.heading)

        self.description = QLabel()
        self.description.setObjectName("guideBody")
        self.description.setWordWrap(True)
        self.description.setMinimumHeight(76)
        self.description.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.description)

        self.progress = QProgressBar()
        self.progress.setObjectName("guideProgress")
        self.progress.setRange(0, len(self.copy["steps"]))
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)
        layout.addWidget(self.progress)

        buttons = QHBoxLayout()
        self.back_button = QPushButton(self.copy["back"])
        self.back_button.clicked.connect(self._previous)
        buttons.addWidget(self.back_button)
        buttons.addStretch(1)
        self.skip_button = QPushButton(self.copy["skip"])
        self.skip_button.clicked.connect(self.reject)
        buttons.addWidget(self.skip_button)
        self.next_button = QPushButton()
        self.next_button.setObjectName("primaryAction")
        self.next_button.clicked.connect(self._next)
        buttons.addWidget(self.next_button)
        layout.addLayout(buttons)

        if parent is not None:
            parent.installEventFilter(self)
        self._show_step()

    def eventFilter(self, watched, event):
        if watched is self.parentWidget() and event.type() in {
            QEvent.Type.Move,
            QEvent.Type.Resize,
        }:
            self._sync_geometry()
        return super().eventFilter(watched, event)

    def showEvent(self, event):
        self._sync_geometry()
        super().showEvent(event)

    def _sync_geometry(self):
        parent = self.parentWidget()
        if parent is None:
            return
        top_left = parent.mapToGlobal(QPoint(0, 0))
        self.setGeometry(QRect(top_left, parent.size()))
        self._update_highlight()

    def _show_step(self):
        total = len(self.copy["steps"])
        title, description, area, self.target_key = self.copy["steps"][self.current_step]
        self.step_label.setText(self.copy["step"].format(
            current=self.current_step + 1,
            total=total,
            area=area,
        ))
        self.heading.setText(title)
        self.description.setText(description)
        self.progress.setValue(self.current_step + 1)
        self.back_button.setEnabled(self.current_step > 0)
        self.next_button.setText(
            self.copy["finish"] if self.current_step == total - 1 else self.copy["next"]
        )
        self._update_highlight()

    def _update_highlight(self):
        parent = self.parentWidget()
        target = parent.guide_target(self.target_key) if parent is not None else None
        if target is None or not target.isVisible():
            self.highlight_rect = QRect()
        else:
            top_left = self.mapFromGlobal(target.mapToGlobal(QPoint(0, 0)))
            self.highlight_rect = QRect(top_left, target.size()).adjusted(-8, -8, 8, 8)
            self.highlight_rect = self.highlight_rect.intersected(self.rect())
        self._position_card()
        self.update()

    def _position_card(self):
        if not hasattr(self, "card"):
            return
        self.card.adjustSize()
        card_size = self.card.sizeHint()
        card_width = self.card.width()
        card_height = card_size.height()
        margin = 18
        highlight = self.highlight_rect

        if highlight.isNull():
            position = QPoint((self.width() - card_width) // 2,
                              (self.height() - card_height) // 2)
        else:
            candidates = [
                QPoint(highlight.right() + margin, highlight.top()),
                QPoint(highlight.left() - card_width - margin, highlight.top()),
                QPoint(highlight.left(), highlight.bottom() + margin),
                QPoint(highlight.left(), highlight.top() - card_height - margin),
            ]
            position = next((
                candidate for candidate in candidates
                if candidate.x() >= margin
                and candidate.y() >= margin
                and candidate.x() + card_width <= self.width() - margin
                and candidate.y() + card_height <= self.height() - margin
            ), QPoint(self.width() - card_width - margin,
                      self.height() - card_height - margin))

        x = min(max(margin, position.x()), max(margin, self.width() - card_width - margin))
        y = min(max(margin, position.y()), max(margin, self.height() - card_height - margin))
        self.card.move(x, y)

    def paintEvent(self, event):
        if self.highlight_rect.isNull():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        mask = QPainterPath()
        mask.setFillRule(Qt.FillRule.OddEvenFill)
        mask.addRect(QRectF(self.rect()))
        mask.addRoundedRect(QRectF(self.highlight_rect), 10, 10)
        painter.fillPath(mask, QColor(22, 28, 38, 174))
        painter.setPen(QPen(QColor(105, 160, 255, 110), 7))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(QRectF(self.highlight_rect), 10, 10)
        painter.setPen(QPen(QColor("#78aaff"), 2))
        painter.drawRoundedRect(QRectF(self.highlight_rect), 10, 10)

    def _previous(self):
        if self.current_step > 0:
            self.current_step -= 1
            self._show_step()

    def _next(self):
        if self.current_step == len(self.copy["steps"]) - 1:
            self.accept()
            return
        self.current_step += 1
        self._show_step()

    def closeEvent(self, event):
        parent = self.parentWidget()
        if parent is not None:
            parent.removeEventFilter(self)
        super().closeEvent(event)
