import os
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from matplotlib.figure import Figure

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from src.ui.plot_canvas import PlotCanvas
from src.ui.main_window import MainWindow


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
        underlay = {
            "name": "reference",
            "visible": True,
            "df_filtered": pd.DataFrame(
                [[0.0, 1.0, 0.0], [1.0, 1.0, 0.0]], columns=["X", "Y", "Z"]
            ),
            "settings": {"base_color": "C1"},
        }
        canvas = PlotCanvas()

        canvas.plot_datasets([cloud, underlay])
        self.assertFalse(canvas.axes.computed_zorder)
        self.assertEqual(canvas.axes.collections[0].get_zorder(), 3)
        self.assertEqual(canvas.axes.collections[-1].get_zorder(), 2)
        canvas.plot_datasets([underlay, cloud])
        self.assertEqual(canvas.axes.collections[0].get_zorder(), 3)
        self.assertEqual(canvas.axes.collections[-1].get_zorder(), 2)
        cloud["error_visualization"]["colour_mode"] = "difference_from_mean"
        canvas.plot_datasets([cloud, underlay])
        cloud["visible"] = False
        canvas.plot_datasets([cloud])

        self.assertEqual(canvas.colorbars, [])
        canvas.deleteLater()

    def test_redraw_preserves_the_3d_camera_view_after_a_manual_transform(self):
        cloud = {
            "name": "project",
            "visible": True,
            "df_filtered": pd.DataFrame(
                [[0.0, 0.0, 0.0], [1.0, 2.0, 3.0]], columns=["X", "Y", "Z"]
            ),
            "settings": {"base_color": "C0"},
        }
        canvas = PlotCanvas()
        canvas.plot_datasets([cloud])
        canvas.axes.view_init(elev=17.0, azim=-43.0)
        canvas.axes.set_xlim3d((-5.0, 5.0))
        canvas.axes.set_ylim3d((-4.0, 6.0))
        canvas.axes.set_zlim3d((-3.0, 7.0))

        cloud["df_filtered"] = cloud["df_filtered"].assign(X=lambda df: df["X"] + 0.2)
        canvas.plot_datasets([cloud])

        self.assertAlmostEqual(canvas.axes.elev, 17.0)
        self.assertAlmostEqual(canvas.axes.azim, -43.0)
        self.assertEqual(canvas.axes.get_xlim3d(), (-5.0, 5.0))
        self.assertEqual(canvas.axes.get_ylim3d(), (-4.0, 6.0))
        self.assertEqual(canvas.axes.get_zlim3d(), (-3.0, 7.0))
        canvas.deleteLater()

    def test_standard_camera_views_and_quarter_turn_keep_the_current_zoom(self):
        canvas = PlotCanvas()
        canvas.axes.set_xlim3d((-5.0, 5.0))
        canvas.axes.set_ylim3d((-4.0, 6.0))
        canvas.axes.set_zlim3d((-3.0, 7.0))

        canvas.set_standard_view("top")
        self.assertAlmostEqual(canvas.axes.elev, 90.0)
        self.assertAlmostEqual(canvas.axes.azim, -90.0)
        self.assertEqual(canvas.axes.get_xlim3d(), (-5.0, 5.0))
        canvas.set_standard_view("positive_x")
        canvas.rotate_camera_around_vertical(90.0)

        self.assertAlmostEqual(canvas.axes.elev, 0.0)
        self.assertAlmostEqual(canvas.axes.azim, 90.0)
        canvas.set_standard_view("diagonal_negative_x_positive_y_positive_z")
        self.assertAlmostEqual(canvas.axes.elev, -30.0)
        self.assertAlmostEqual(canvas.axes.azim, -45.0)
        self.assertAlmostEqual(canvas.axes.roll, 180.0)
        canvas.deleteLater()

    def test_explicit_camera_angles_can_be_set_and_read(self):
        canvas = PlotCanvas()
        canvas.set_camera_angles(21.0, -77.0, 12.0)

        self.assertEqual(canvas.camera_angles(), (21.0, -77.0, 12.0))
        canvas.deleteLater()

    def test_new_visible_cloud_refits_limits_but_refreshing_the_same_one_preserves_them(self):
        first = {
            "name": "first",
            "visible": True,
            "df_filtered": pd.DataFrame([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]], columns=["X", "Y", "Z"]),
            "settings": {"base_color": "C0"},
        }
        second = {
            "name": "second",
            "visible": True,
            "df_filtered": pd.DataFrame([[100.0, 100.0, 100.0], [101.0, 101.0, 101.0]], columns=["X", "Y", "Z"]),
            "settings": {"base_color": "C1"},
        }
        canvas = PlotCanvas()
        canvas.plot_datasets([first])
        canvas.axes.set_xlim3d((-5.0, 5.0))
        canvas.plot_datasets([first])
        self.assertEqual(canvas.axes.get_xlim3d(), (-5.0, 5.0))

        canvas.plot_datasets([second])
        self.assertGreater(canvas.axes.get_xlim3d()[0], 90.0)
        canvas.reset_view_to_data()
        self.assertGreater(canvas.axes.get_xlim3d()[0], 90.0)
        canvas.deleteLater()

    def test_full_resolution_export_renders_offscreen_without_display_voxel_filter(self):
        dataset = {
            "name": "project",
            "visible": True,
            "df": pd.DataFrame(
                [[0.0, 0.0, 0.0], [1.0, 2.0, 3.0]], columns=["X", "Y", "Z"]
            ),
            "settings": {"base_color": "C0", "voxel_enabled": True, "voxel_size": 10.0},
        }
        canvas = PlotCanvas()
        canvas.plot_datasets([{**dataset, "df_filtered": dataset["df"]}])
        window = MainWindow.__new__(MainWindow)
        with tempfile.TemporaryDirectory() as directory:
            output = os.path.join(directory, "full_resolution.png")
            window.export_full_resolution_background([dataset], output, window._export_view_state(canvas))
            self.assertTrue(os.path.exists(output))
            self.assertGreater(os.path.getsize(output), 0)
        canvas.deleteLater()

    def test_full_resolution_export_recalculates_an_active_error_colour_map(self):
        reference = {
            "name": "reference", "filepath": "reference.csv", "visible": True,
            "df": pd.DataFrame([[0.0, 0.0, 0.0]], columns=["X", "Y", "Z"]),
            "settings": {"base_color": "C2"},
        }
        source = {
            "name": "source", "filepath": "source.csv", "visible": True,
            "df": pd.DataFrame([[0.2, 0.0, 0.0], [5.0, 0.0, 0.0]], columns=["X", "Y", "Z"]),
            "settings": {"base_color": "C3", "voxel_enabled": True, "voxel_size": 10.0},
            "show_error_visualization": True,
            "error_visualization": {
                "reference_filepath": "reference.csv", "reference_name": "reference", "cutoff": 1.0,
                "mean": 0.2, "unit": "mm", "colour_mode": "closest_distance",
            },
        }
        canvas = PlotCanvas()
        canvas.plot_datasets([{**source, "df_filtered": source["df"]}, {**reference, "df_filtered": reference["df"]}])
        window = MainWindow.__new__(MainWindow)
        with tempfile.TemporaryDirectory() as directory:
            output = os.path.join(directory, "error_map.png")
            colourbar_formats = []
            original_colorbar = Figure.colorbar

            def record_colorbar(figure, *args, **kwargs):
                colourbar_formats.append(kwargs.get("format"))
                return original_colorbar(figure, *args, **kwargs)

            with patch.object(Figure, "colorbar", record_colorbar):
                result = window.export_full_resolution_background(
                    [source, reference], output, window._export_view_state(canvas),
                    export_options={"colourbar_decimals": 4},
                )
            self.assertEqual(result["error_maps_rendered"], 1)
            self.assertEqual(colourbar_formats, ["%.4f"])
            self.assertTrue(os.path.exists(output))
        canvas.deleteLater()


if __name__ == "__main__":
    unittest.main()
