import os
import unittest

import numpy as np
import pandas as pd

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from src.ui.plot_canvas import PlotCanvas


class PointwiseErrorMapPlotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_hiding_a_cloud_after_an_error_map_removes_its_colourbar_safely(self):
        cloud = {
            "name": "project",
            "visible": True,
            "df_filtered": pd.DataFrame(
                [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]], columns=["X", "Y", "Z"]
            ),
            "settings": {"base_color": "C0"},
            "show_error_visualization": True,
            "error_visualization": {
                "points": np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]),
                "distances": np.array([0.1, 0.2]),
                "cutoff": 1.0,
                "mean": 0.15,
                "highlight_above_mean": False,
            },
        }
        canvas = PlotCanvas()

        canvas.plot_datasets([cloud])
        cloud["visible"] = False
        canvas.plot_datasets([cloud])

        self.assertEqual(canvas.colorbars, [])
        canvas.deleteLater()


if __name__ == "__main__":
    unittest.main()
