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
        window.set_project_dirty(True)

        with tempfile.TemporaryDirectory() as directory:
            filepath = os.path.join(directory, "comparison.json")
            self.assertTrue(window._save_project_to_file(filepath))
            with open(filepath, "r") as project_file:
                saved = json.load(project_file)

        self.assertEqual(saved["format_version"], 2)
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


if __name__ == "__main__":
    unittest.main()
