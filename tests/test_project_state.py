import json
import os
import tempfile
import unittest
import pandas as pd
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from src.ui.main_window import MainWindow
from src.ui import main_window as main_window_module
from src.utils.registration import calculate_cloud_error


class ProjectStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_project_data_keeps_saved_surface_error_values(self):
        stub = SimpleNamespace(
            plot_canvas=SimpleNamespace(camera_angles=lambda: (10.0, 20.0, 0.0)),
            datasets=[{
                "filepath": "measurement.csv", "visible": True,
                "last_comparison": {"p95": 0.8, "maximum": 2.4, "heatmap_max": 1.5},
            }],
        )
        saved = MainWindow._project_data(stub)
        self.assertEqual(saved["datasets"][0]["last_comparison"]["p95"], 0.8)
        self.assertEqual(saved["datasets"][0]["last_comparison"]["heatmap_max"], 1.5)

    def test_error_report_separates_coverage_and_handles_old_saved_reports(self):
        points = pd.DataFrame([(x, y, 0.0) for x in range(11) for y in range(11)], columns=["X", "Y", "Z"])
        report = calculate_cloud_error(points, points, 1.0)
        text = MainWindow._format_error_report(report)
        self.assertIn("System points within reference area [%]: 100.0%", text)
        self.assertIn("Reference area covered [%]: 100.0%", text)
        restored = json.loads(json.dumps(report))
        self.assertEqual(MainWindow._format_error_report(restored), text)
        old = {key: value for key, value in report.items()
               if not key.startswith(("system_points_", "reference_area", "coverage_"))}
        self.assertIn("Reference area covered [%]: not saved; recalculate", MainWindow._format_error_report(old))
        self.assertIn("System points within reference area [%]: 100.0%", MainWindow._format_error_report(old))
        line = pd.DataFrame([(x, 0.0, 0.0) for x in range(11)], columns=["X", "Y", "Z"])
        degenerate = calculate_cloud_error(line, line, 1.0)
        self.assertIn("unavailable (no 2-D reference area)", MainWindow._format_error_report(degenerate))

    def test_saved_comparison_restores_only_for_unchanged_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            source_path = os.path.join(directory, "source.csv")
            reference_path = os.path.join(directory, "reference.csv")
            for path in (source_path, reference_path):
                with open(path, "w") as output:
                    output.write("X,Y,Z\n0,0,0\n")
            source = {"filepath": source_path, "settings": {"scale": 1.0}}
            reference = {"filepath": reference_path, "settings": {"scale": 1.0}}
            report = {
                "reference_filepath": reference_path,
                "source_input": MainWindow._comparison_input_signature(source),
                "reference_input": MainWindow._comparison_input_signature(reference),
                "p95": 0.4,
            }
            stub = SimpleNamespace(
                datasets=[source, reference],
                _pending_project_comparisons=[{"filepath": source_path, "last_comparison": report}],
                _comparison_input_signature=MainWindow._comparison_input_signature,
                _show_saved_comparison_for_source=lambda: None,
            )
            MainWindow._restore_saved_comparisons(stub)
            self.assertIs(source["last_comparison"], report)

            source.pop("last_comparison")
            source["settings"]["scale"] = 2.0
            stub._pending_project_comparisons = [{"filepath": source_path, "last_comparison": report}]
            MainWindow._restore_saved_comparisons(stub)
            self.assertNotIn("last_comparison", source)

    def test_surface_error_completion_keeps_requested_heatmap_maximum(self):
        class Signal:
            def connect(self, callback):
                self.callback = callback

        class Worker:
            def __init__(self, *_args, **_kwargs):
                self.progress = Signal()
                self.finished = Signal()
                self.error = Signal()

            def start(self):
                pass

        source = {"name": "source", "filepath": "source.csv"}
        reference = {"name": "reference", "filepath": "reference.csv"}
        panel = SimpleNamespace(
            error_map_max_spin=SimpleNamespace(value=lambda: 2.5),
            dataset_list=SimpleNamespace(currentRow=lambda: 0),
            set_comparison_summary=lambda *_: None,
            set_error_map_display_state=lambda *_: None,
        )
        window = SimpleNamespace(
            datasets=[source, reference], control_panel=panel,
            set_loading_state=lambda *_: None, set_project_dirty=lambda *_: None,
            run_comparison_background=lambda *_: None,
            statusBar=lambda: SimpleNamespace(showMessage=lambda *_: None),
            plot_canvas=SimpleNamespace(plot_datasets=lambda *_: None),
            _comparison_input_signature=lambda *_: {},
            _format_error_report=lambda *_: "report",
        )
        with patch.object(main_window_module, "WorkerThread", Worker), \
                patch.object(main_window_module.QMessageBox, "information"):
            MainWindow.on_calculate_error(window, 0, 1, 1.0, 0)
            report = {"reference_edge_margin_setting": 1.0, "p95": 0.7,
                      "unit": "mm", "mean": 0.3}
            window.comparison_worker.finished.callback((report, {}, source, reference))
        self.assertEqual(report["heatmap_max"], 2.5)
        self.assertEqual(source["error_visualization"]["heatmap_max"], 2.5)

    def test_project_save_keeps_dataset_order_and_visibility(self):
        window = MainWindow()
        window.datasets = [
            {"filepath": "first.csv", "visible": True},
            {"filepath": "second.csv", "visible": False},
        ]
        window.add_recent_project = lambda _: None
        window.plot_canvas.set_camera_angles(-30, -45, 180)
        window.set_project_dirty(True)

        with tempfile.TemporaryDirectory() as directory:
            filepath = os.path.join(directory, "comparison.json")
            self.assertTrue(window._save_project_to_file(filepath))
            with open(filepath, "r") as project_file:
                saved = json.load(project_file)

        self.assertEqual(saved["format_version"], 3)
        self.assertEqual(
            saved["camera_view"],
            {"elevation": -30.0, "azimuth": -45.0, "roll": 180.0},
        )
        self.assertEqual(
            saved["datasets"],
            [
                {"filepath": "first.csv", "visible": True},
                {"filepath": "second.csv", "visible": False},
            ],
        )
        self.assertFalse(window.project_dirty)
        self.assertEqual(window.project_filepath, filepath)
        window.deleteLater()

    def test_saved_camera_view_is_restored_and_updates_controls(self):
        window = MainWindow()
        window._pending_project_camera_view = {
            "elevation": -30,
            "azimuth": -45,
            "roll": 180,
        }

        window._apply_pending_project_camera_view()

        self.assertEqual(window.plot_canvas.camera_angles(), (-30.0, -45.0, 180.0))
        self.assertEqual(window.control_panel.camera_elevation_spin.value(), -30.0)
        self.assertEqual(window.control_panel.camera_azimuth_spin.value(), -45.0)
        self.assertEqual(window.control_panel.camera_roll_spin.value(), 180.0)
        self.assertIsNone(window._pending_project_camera_view)
        window.deleteLater()


if __name__ == "__main__":
    unittest.main()
