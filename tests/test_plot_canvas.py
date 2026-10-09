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
from src.utils.registration import calculate_cloud_error
from src.utils.export_layout import z_tick_boxes, z_tick_label_separation


class PointwiseErrorMapPlotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_preview_budget_preserves_full_error_data_colour_scale_and_extent(self):
        points = np.random.default_rng(2).normal(size=(1000, 3))
        points[123, 0] = 1000.
        distances = np.linspace(-10., 30., 1000)
        distances[0] = np.inf
        original_points, original_distances = points.copy(), distances.copy()
        report = {"standard_deviation": 12.3, "evaluated_points": 999}
        source = {"name": "source", "visible": True, "df_filtered": pd.DataFrame(points, columns=["X", "Y", "Z"]),
                  "settings": {}, "last_comparison": report,
                  "show_error_visualization": True, "error_visualization": {"points": points, "distances": distances,
                  "error_method": "signed_normal", "mean": 10.}}
        reference = {"name": "reference", "visible": True, "df_filtered": source["df_filtered"], "settings": {}}
        canvas = PlotCanvas()
        try:
            canvas.MAX_PREVIEW_POINTS = 20
            canvas.plot_datasets([source, reference])
            self.assertLessEqual(sum(len(collection._offsets3d[0]) for collection in canvas.axes.collections), 20)
            self.assertEqual(canvas.preview_point_counts, [(1000, 10), (1000, 10)])
            expected_limit = np.percentile(np.abs(distances[np.isfinite(distances)]), 95)
            self.assertAlmostEqual(canvas.colorbars[0].norm.vmax, expected_limit)
            self.assertGreater(canvas.axes.get_xlim3d()[1], 1000.)
            np.testing.assert_array_equal(points, original_points)
            np.testing.assert_array_equal(distances, original_distances)
            self.assertEqual(source["last_comparison"], {"standard_deviation": 12.3, "evaluated_points": 999})
            self.assertIn("20 of 2,000", canvas.preview_summary())
            self.assertEqual(canvas._preview_notice.get_text(), canvas.preview_summary())
        finally:
            canvas.deleteLater()

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
        canvas.MAX_PREVIEW_POINTS = 1
        canvas.plot_datasets([{**dataset, "df_filtered": dataset["df"]}])
        self.assertEqual(canvas.preview_point_counts, [(2, 1)])
        window = MainWindow.__new__(MainWindow)
        exported_point_counts = []
        savefig = Figure.savefig

        def record_export(figure, *args, **kwargs):
            exported_point_counts.extend(len(collection._offsets3d[0]) for collection in figure.axes[0].collections)
            np.testing.assert_allclose(figure.axes[0].get_zticks(), [0, 1, 2, 3])
            return savefig(figure, *args, **kwargs)

        with tempfile.TemporaryDirectory() as directory:
            output = os.path.join(directory, "full_resolution.png")
            with patch.object(Figure, "savefig", record_export):
                window.export_full_resolution_background([dataset], output, window._export_view_state(canvas),
                    export_options={"z_axis_tick_interval": 1, "z_axis_ticks": 5})
            self.assertTrue(os.path.exists(output))
            self.assertGreater(os.path.getsize(output), 0)
            self.assertEqual(exported_point_counts, [2])
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

    def test_signed_map_and_both_export_resolutions_preserve_signs_and_white_at_zero(self):
        x, y = np.meshgrid(np.linspace(-3., 3., 21), np.linspace(-3., 3., 21))
        reference_df = pd.DataFrame({"X": x.ravel(), "Y": y.ravel(), "Z": (0.3*x).ravel()})
        interior = reference_df[(reference_df.X.abs() < 2) & (reference_df.Y.abs() < 2)].to_numpy()
        normal = np.array([-0.3, 0., 1.]) / np.sqrt(1.09)
        source_df = pd.DataFrame(np.concatenate((interior - 0.2*normal, interior + 0.4*normal)), columns=["X", "Y", "Z"])
        report, pointwise = calculate_cloud_error(source_df, reference_df, 0.01,
            error_method="signed_normal", normal_radius=1., include_pointwise=True)
        reference = {"name": "reference", "filepath": "reference.csv", "visible": True,
                     "df": reference_df, "df_filtered": reference_df, "settings": {"base_color": "C0"}}
        source = {"name": "source", "filepath": "source.csv", "visible": True,
                  "df": source_df, "df_filtered": source_df, "settings": {"base_color": "C1"},
                  "show_error_visualization": True,
                  "error_visualization": {**pointwise, "reference_filepath": "reference.csv",
                      "error_method": "signed_normal", "normal_radius": 1., "normal_orientation": "+Z",
                      "edge_margin": 0.01, "mean": report["mean"], "unit": "mm",
                      "scale_mode": "manual", "heatmap_min": -0.2, "heatmap_max": 0.4}}
        canvas = PlotCanvas()
        canvas.plot_datasets([source, reference])
        scatter = canvas.axes.collections[0]
        np.testing.assert_allclose(scatter.get_array(), pointwise["distances"], atol=1e-12)
        np.testing.assert_allclose(scatter.cmap(scatter.norm(0.)), [1., 1., 1., 1.])
        rendered = []
        original_savefig = Figure.savefig

        def check_export(figure, *args, **kwargs):
            artist = figure.axes[0].collections[0]
            self.assertEqual(len(figure.axes[0].get_zticks()), 5)
            axes = figure.axes[0]
            gap, _ = z_tick_label_separation(axes, z_tick_boxes(axes, figure.canvas.get_renderer()))
            self.assertGreaterEqual(gap * 72 / figure.dpi, 29.75)
            rendered.append(np.asarray(artist.get_array()))
            np.testing.assert_allclose(artist.cmap(artist.norm(0.)), [1., 1., 1., 1.])
            self.assertEqual((artist.norm.vmin, artist.norm.vmax), (-0.2, 0.4))
            return original_savefig(figure, *args, **kwargs)

        window = MainWindow.__new__(MainWindow)
        with tempfile.TemporaryDirectory() as directory, patch.object(Figure, "savefig", check_export):
            for display in (False, True):
                window.export_full_resolution_background([source, reference], os.path.join(directory, f"signed_{display}.png"),
                    window._export_view_state(canvas), use_display_points=display,
                    export_options={"heatmap_colormap": "blue_white_red", "z_axis_ticks": 5,
                                    "z_axis_tick_label_gap": 30})
        for values in rendered:
            np.testing.assert_allclose(values, pointwise["distances"], atol=1e-12)
        canvas.deleteLater()


if __name__ == "__main__":
    unittest.main()
