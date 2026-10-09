"""Readable surface-error overview, with explicit missing results."""
import csv
import io
import os
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QDialog, QDialogButtonBox, QHeaderView, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout,
)
from src.utils.error_report import headline_rows, interval, number, report_method, report_status


class ErrorReportDialog(QDialog):
    def __init__(self, datasets, selected_source_path=None, format_report=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Surface Error Results")
        self.resize(1120, 660)
        layout = QVBoxLayout(self)
        title = QLabel("Point-cloud comparison with the reference")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        description = QLabel("Stored results for each source cloud. Missing values are shown as —; unsigned and signed results are identified separately.")
        description.setWordWrap(True)
        layout.addWidget(description)
        self.table = QTableWidget(len(datasets), 7)
        self.table.setObjectName("surface_error_report_table")
        headers = ["System / reference", "Error method", "System-point\nfraction (%)",
                   "Reference-area\ncoverage (%)", "[P5; P95]\n90% interval",
                   "Standard\ndeviation", "Normalized SD\n(% of axial range)"]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.verticalHeader().hide()
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setMinimumHeight(48)
        selected_row = 0
        for row, dataset in enumerate(datasets):
            report = dataset.get("last_comparison")
            name = dataset.get("name", os.path.basename(dataset["filepath"]))
            if isinstance(report, dict):
                name += f" → {report.get('reference_name', os.path.basename(report.get('reference_filepath', '') or ''))}"
                values = [value for _, value in headline_rows(report)]
                cells = [name, "Signed normal" if report_method(report) == "signed_normal" else "Unsigned nearest point",
                         *[value.removesuffix(" %") for value in values[:2]], values[2], values[3], values[4]]
                status = report_status(report, dataset.get("surface_error_settings"))[0]
            else:
                cells = [name, "Not calculated", "—", "—", "—", "—", "—"]
                status = "No saved comparison results"
            for column, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setToolTip(status)
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | (Qt.AlignmentFlag.AlignLeft if column < 2 else Qt.AlignmentFlag.AlignRight))
                self.table.setItem(row, column, item)
            if dataset["filepath"] == selected_source_path:
                selected_row = row
        layout.addWidget(self.table, 1)
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.details.setMaximumHeight(190)
        layout.addWidget(self.details)

        def show_details():
            row = self.table.currentRow()
            if not (0 <= row < len(datasets)):
                self.details.clear()
                return
            dataset = datasets[row]
            report = dataset.get("last_comparison")
            if not isinstance(report, dict):
                self.details.setPlainText("No report available for this cloud. Select it as the source and calculate surface error.")
                return
            status = report_status(report, dataset.get("surface_error_settings"))[0]
            unit = report.get("unit", "mm")
            extra = (f"Axial measurement range: {number(report.get('axial_range'))} {unit}\n"
                     f"[P2.5; P97.5] — central 95% empirical interval: {interval(report, 'p2_5', 'p97_5')}\n")
            try:
                detail = format_report(report) if format_report is not None else extra
            except KeyError:
                detail = "This saved report is incomplete; recalculate to obtain missing statistics."
            self.details.setPlainText(status + "\n" + detail)

        self.table.itemSelectionChanged.connect(show_details)
        if datasets:
            self.table.selectRow(selected_row)
        note = QLabel("Normalized SD = 100 × sample SD / axial measurement span (in the same unit). "
                      "Enter each system's axial range from Table 3; this is the percentage requested for the dynamic-range column. "
                      "Intervals describe the empirical point deviations; they are not a complete measurement-uncertainty evaluation.")
        note.setWordWrap(True)
        layout.addWidget(note)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        copy_button = QPushButton("Copy table (TSV)")

        def copy_table():
            output = io.StringIO()
            writer = csv.writer(output, delimiter="\t", lineterminator="\n")
            writer.writerow([header.replace("\n", " ") for header in headers])
            writer.writerows([[self.table.item(row, column).text() for column in range(self.table.columnCount())]
                             for row in range(self.table.rowCount())])
            QApplication.clipboard().setText(output.getvalue())

        copy_button.clicked.connect(copy_table)
        buttons.addButton(copy_button, QDialogButtonBox.ButtonRole.ActionRole)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def prepare_for_display(self):
        """Lay out and render the populated report while its window is hidden."""
        self.ensurePolished()
        self.layout().activate()
        self.table.resizeColumnsToContents()
        self.grab()
