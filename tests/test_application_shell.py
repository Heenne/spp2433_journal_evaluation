import json
import os
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from src.ui.main_window import MainWindow


class ApplicationShellTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_main_window_keeps_plot_visible_with_project_sidebar_and_workflow_sections(self):
        window = MainWindow()
        try:
            self.assertEqual(window.windowTitle(), "3D Point Cloud Data Viewer")
            self.assertEqual(
                [window.control_panel.tabs.tabText(i) for i in range(window.control_panel.tabs.count())],
                ["Data", "Prepare", "Align", "Evaluate", "Export"],
            )
            self.assertIsNotNone(window.plot_canvas.parent())
            self.assertEqual(window.sidebar_open_data_button.text(), "Load point cloud")
            self.assertEqual(window.sidebar_open_project_button.text(), "Open project")
            self.assertIsNot(window.control_panel.dataset_group.parent(), window.control_panel)
        finally:
            window.deleteLater()

    def test_theme_selection_is_applied_to_plot_and_persisted(self):
        original_stylesheet = self.app.styleSheet()
        with tempfile.TemporaryDirectory() as directory:
            settings_path = os.path.join(directory, "settings.json")
            with patch("src.utils.app_settings.SETTINGS_FILE", settings_path):
                window = MainWindow()
                try:
                    window.set_theme("dark")
                    self.assertEqual(window.theme, "dark")
                    self.assertEqual(window.plot_canvas.theme, "dark")
                    self.assertTrue(window.dark_theme_action.isChecked())
                    with open(settings_path, encoding="utf-8") as settings_file:
                        self.assertEqual(json.load(settings_file)["theme"], "dark")

                    window.set_theme("light")
                    self.assertEqual(window.plot_canvas.theme, "light")
                    self.assertTrue(window.light_theme_action.isChecked())
                    self.assertIn("#f4f6fa", self.app.styleSheet())
                finally:
                    window.deleteLater()
        self.app.setStyleSheet(original_stylesheet)


if __name__ == "__main__":
    unittest.main()
