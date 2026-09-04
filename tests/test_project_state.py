import json
import os
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from src.ui.main_window import MainWindow


class ProjectStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

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
