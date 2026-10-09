import os
import unittest
import time
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import pandas as pd
from PyQt6.QtWidgets import QApplication, QPushButton
from PyQt6.QtCore import QThread, QTimer
from PyQt6.QtTest import QTest
from src.utils.registration import calculate_cloud_error
from src.utils.error_report import update_report_metrics, report_status
from src.ui.control_panel import ControlPanel
from src.ui.error_report_dialog import ErrorReportDialog
from src.ui.main_window import MainWindow
from src.ui import main_window as main_window_module


class ErrorReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    @staticmethod
    def calculate(offsets, method="signed_normal", axial_range=200):
        x, y = np.meshgrid(np.arange(-4., 5.), np.arange(-4., 5.))
        reference = pd.DataFrame({"X": x.ravel(), "Y": y.ravel(), "Z": np.zeros(x.size)})
        source = pd.DataFrame({"X": np.zeros(len(offsets)), "Y": np.zeros(len(offsets)), "Z": offsets})
        return calculate_cloud_error(source, reference, 0.01, error_method=method,
                                     normal_radius=2, axial_range=axial_range)

    def test_statistics_use_the_selected_signed_or_unsigned_deviations(self):
        offsets = np.array([-0.8, -0.3, 0.1, 0.7, 2.])
        for method in ("signed_normal", "unsigned"):
            with self.subTest(method=method):
                report = self.calculate(offsets, method)
                expected = offsets if method == "signed_normal" else np.abs(offsets)
                self.assertAlmostEqual(report["standard_deviation"], np.std(expected, ddof=1))
                self.assertAlmostEqual(report["normalized_standard_deviation_percent"], 100*np.std(expected, ddof=1)/200)
                np.testing.assert_allclose(report["coverage_interval_90"], np.percentile(expected, [5, 95]))
                np.testing.assert_allclose(report["coverage_interval_95"], np.percentile(expected, [2.5, 97.5]))

    def test_missing_range_and_small_samples_do_not_produce_fake_zero_statistics(self):
        report = self.calculate([-0.1, 0.4], axial_range=0)
        self.assertIsNone(report["normalized_standard_deviation_percent"])
        self.assertIn("set axial range", report_status(report)[0])
        single = self.calculate([0.1])
        self.assertIsNone(single["standard_deviation"])
        self.assertIsNone(single["normalized_standard_deviation_percent"])
        np.testing.assert_allclose(single["coverage_interval_90"], [0.1, 0.1])
        zero = self.calculate([0., 0.])
        self.assertEqual(zero["normalized_standard_deviation_percent"], 0.)
        empty = self.calculate([0.1], method="signed_normal")
        empty.update(evaluated_points=0, p5=None, p95=None, p2_5=None, p97_5=None, standard_deviation=None)
        update_report_metrics(empty)
        self.assertIsNone(empty["coverage_interval_90"])
        self.assertIsNone(empty["normalized_standard_deviation_percent"])
        for span in (-1, np.nan, np.inf):
            with self.assertRaises(ValueError):
                self.calculate([0.1, 0.2], axial_range=span)

    def test_panel_reports_availability_and_stale_calculation_settings(self):
        panel = ControlPanel()
        try:
            panel.add_dataset_to_list("source")
            panel.add_dataset_to_list("reference")
            panel.set_comparison_report(None)
            self.assertFalse(panel.btn_comparison_report.isEnabled())
            report = self.calculate([-0.1, 0.4])
            panel.set_comparison_report(report, report["calculation_settings"])
            self.assertTrue(panel.btn_comparison_report.isEnabled())
            requests = []
            panel.comparison_report_requested.connect(lambda: requests.append(True))
            panel.btn_comparison_report.click()
            self.assertEqual(requests, [True])
            self.assertEqual(panel.comparison_status.text(), "Results available")
            self.assertIn("[P5; P95]", panel.comparison_summary.text())
            self.assertNotIn("Median", panel.comparison_summary.text())
            changed = dict(report["calculation_settings"], normal_orientation="-Z")
            panel.set_comparison_report(report, changed)
            self.assertIn("recalculate", panel.comparison_status.text())
            panel.set_comparison_report(report, dict(report["calculation_settings"], axial_range=100))
            self.assertEqual(panel.comparison_status.text(), "Results available")
        finally:
            panel.deleteLater()

    def test_editing_axial_span_updates_report_without_recalculating_geometry(self):
        window = MainWindow()
        try:
            report = self.calculate([-0.1, 0.4])
            window.datasets = [{"name": "source", "filepath": "source.csv", "last_comparison": report},
                               {"name": "reference", "filepath": "reference.csv"}]
            for dataset in window.datasets:
                dataset.update(settings={}, add_cols=[])
            for name in ("source", "reference"):
                window.control_panel.add_dataset_to_list(name)
            window.control_panel.comparison_source_combo.setCurrentIndex(0)
            window.control_panel.apply_surface_error_options({**report["calculation_settings"], "axial_range": 200}, 1)
            before = report["normalized_standard_deviation_percent"]
            interval_before = report["coverage_interval_90"][:]
            window.control_panel.comparison_axial_range_spin.setValue(100)
            self.assertAlmostEqual(report["normalized_standard_deviation_percent"], 2*before)
            self.assertEqual(report["coverage_interval_90"], interval_before)
            self.assertEqual(window.datasets[0]["surface_error_settings"]["axial_range"], 100)
            self.assertTrue(window.project_dirty)
            self.assertFalse(hasattr(window, "comparison_worker"))
        finally:
            window.deleteLater()

    def test_popup_lists_missing_results_and_copies_journal_columns(self):
        report = self.calculate([-0.1, 0.4])
        report["reference_name"] = "reference"
        datasets = [{"filepath": "source.csv", "name": "A2", "last_comparison": report},
                    {"filepath": "reference.csv", "name": "reference"}]
        dialog = ErrorReportDialog(datasets, "source.csv", MainWindow._format_error_report)
        try:
            self.assertEqual(dialog.table.item(0, 1).text(), "Signed normal")
            self.assertEqual(dialog.table.item(1, 5).text(), "—")
            self.assertIn("Axial measurement span: 200 mm", dialog.details.toPlainText())
            next(button for button in dialog.findChildren(QPushButton) if button.text() == "Copy table (TSV)").click()
            text = QApplication.clipboard().text()
            self.assertIn("Normalized SD", text)
            self.assertIn("[P5; P95]", text)
            self.assertIn("A2", text)
        finally:
            dialog.deleteLater()

    def test_report_is_painted_and_pending_plot_draw_finishes_before_opening(self):
        window = MainWindow()
        points = pd.DataFrame(np.random.default_rng(1).normal(size=(100_000, 3)), columns=["X", "Y", "Z"])
        window.datasets = [{"filepath": "source.csv", "name": "A2",
                            "last_comparison": self.calculate([-0.1, 0.4]),
                            "visible": True, "settings": {}, "df_filtered": points}]
        observations = []

        class ObservedDialog(ErrorReportDialog):
            def paintEvent(self, event):
                observations.append((self.isVisible(), self.table.item(0, 1).text(),
                                     bool(self.details.toPlainText())))
                super().paintEvent(event)

        try:
            window.show()
            QApplication.processEvents()
            with patch.object(window.plot_canvas.fig, "draw", wraps=window.plot_canvas.fig.draw) as draw, \
                    patch.object(main_window_module, "ErrorReportDialog", ObservedDialog):
                window.plot_canvas.plot_datasets(window.datasets)
                self.assertTrue(window.plot_canvas._draw_pending)
                window.show_surface_error_report("source.csv")
                dialog = window._surface_error_dialog
                self.assertTrue(dialog.isVisible())
                self.assertIn((False, "Signed normal", True), observations)
                draw_count = draw.call_count
                self.assertGreater(draw_count, 0)
                heartbeats = []
                # Reproduce draws arriving *after* the report opens: parent
                # resize, queued repaint, and a background filter result.
                QTimer.singleShot(0, lambda: window.resize(1150, 780))
                QTimer.singleShot(0, window.plot_canvas.draw_idle)
                QTimer.singleShot(0, lambda: window.plot_canvas.plot_datasets(window.datasets))
                QTimer.singleShot(0, lambda: heartbeats.append(True))
                QTest.qWait(50)
                self.assertTrue(any(visible for visible, _, _ in observations))
                self.assertEqual(heartbeats, [True])
                self.assertEqual(draw.call_count, draw_count)
                dialog.reject()
                QTest.qWait(30)
                self.assertGreater(draw.call_count, draw_count)
                self.assertIsNone(window._surface_error_dialog)
                self.assertFalse(window.plot_canvas._rendering_suspended)
        finally:
            dialog = getattr(window, "_surface_error_dialog", None)
            if dialog is not None:
                dialog.reject()
            window.close()
            window.deleteLater()

    def test_real_comparison_worker_finishes_and_report_stays_responsive(self):
        window = MainWindow()
        z = np.linspace(-0.5, 0.5, 12_000)
        source_points = pd.DataFrame({"X": np.zeros(len(z)), "Y": np.zeros(len(z)), "Z": z})
        reference_points = pd.DataFrame([(x, y, 0.) for x in range(-4, 5) for y in range(-4, 5)],
                                        columns=["X", "Y", "Z"])
        for name, frame in (("source", source_points), ("reference", reference_points)):
            window.datasets.append({"name": name, "filepath": name + ".csv", "df": frame,
                                    "df_filtered": frame, "settings": {}, "add_cols": [], "visible": True})
            window.control_panel.add_dataset_to_list(name)
        window.control_panel.comparison_source_combo.setCurrentIndex(0)
        window.control_panel.comparison_method_combo.setCurrentIndex(1)
        window._comparison_input_signature = lambda *_: {}
        original_show = window.show_surface_error_report
        gui_threads = []

        def show_report(path):
            gui_threads.append(QThread.currentThread() == self.app.thread())
            original_show(path)

        window.show_surface_error_report = show_report
        try:
            window.show()
            QApplication.processEvents()
            window.on_calculate_error(0, 1, 0.01, 0)
            deadline = time.monotonic() + 10
            while getattr(window, "_surface_error_dialog", None) is None and time.monotonic() < deadline:
                QTest.qWait(20)
            dialog = window._surface_error_dialog
            self.assertEqual(gui_threads, [True])
            self.assertTrue(dialog.isVisible())
            self.assertIn("Signed normal", dialog.table.item(0, 1).text())
            QTest.qWait(40)
            self.assertFalse(window.comparison_worker.isRunning())
            heartbeat = []
            QTimer.singleShot(0, lambda: heartbeat.append(True))
            QTest.qWait(20)
            self.assertEqual(heartbeat, [True])
            dialog.reject()
        finally:
            worker = getattr(window, "comparison_worker", None)
            if worker is not None and worker.isRunning():
                worker.cancel()
                worker.wait()
            dialog = getattr(window, "_surface_error_dialog", None)
            if dialog is not None:
                dialog.reject()
            window.set_project_dirty(False)
            window.close()
            window.deleteLater()

    def test_no_result_window_opens_without_a_saved_report(self):
        window = MainWindow()
        try:
            with patch.object(main_window_module, "ErrorReportDialog") as dialog:
                window.show_surface_error_report()
                dialog.assert_not_called()
        finally:
            window.deleteLater()


if __name__ == "__main__":
    unittest.main()
