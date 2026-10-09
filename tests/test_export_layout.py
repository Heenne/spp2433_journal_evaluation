import unittest
from io import BytesIO
import numpy as np
from unittest.mock import patch
from matplotlib.figure import Figure
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from src.utils.export_layout import layout_export_z_axis, z_tick_boxes, z_tick_label_separation


class ExportLayoutTests(unittest.TestCase):
    def figure(self, font=22, azimuth=45):
        figure = Figure(figsize=(10, 6.5), dpi=150, constrained_layout=True)
        axes = figure.add_subplot(111, projection="3d")
        axes.set_box_aspect((250, 250, 45))
        axes.set_xlim(0, 250)
        axes.set_ylim(0, 250)
        axes.set_zlim(-10, 35)
        axes.view_init(elev=25, azim=azimuth)
        axes.tick_params(labelsize=font)
        figure.colorbar(ScalarMappable(norm=Normalize(-1, 1), cmap="bwr"), ax=axes, shrink=.7)
        return figure, axes

    def test_large_z_labels_do_not_overlap_ticks_on_either_axis_side(self):
        for font in (10, 22, 36):
            for angle in (45, -45, 135, -135):
                with self.subTest(font=font, angle=angle):
                    figure, axes = self.figure(font, angle)
                    title = layout_export_z_axis(figure, axes, "Z in mm", font)
                    figure.canvas.draw()
                    renderer = figure.canvas.get_renderer()
                    boxes = z_tick_boxes(axes, renderer)
                    self.assertTrue(boxes)
                    extent = title.get_window_extent(renderer)
                    self.assertFalse(any(extent.overlaps(box) for box in boxes))
                    self.assertFalse(any(first.overlaps(second) for index, first in enumerate(boxes)
                                         for second in boxes[index + 1:]))

    def test_spacing_and_tick_count_without_rendering_scatter_during_layout(self):
        figure, axes = self.figure()
        scatter = axes.scatter([0, 50, 250], [0, 50, 250], [0, 5, 30])
        original_draw = scatter.draw

        def check_hidden(*args, **kwargs):
            self.assertFalse(scatter.get_visible())
            return original_draw(*args, **kwargs)

        with patch.object(scatter, "draw", check_hidden), \
                patch.object(scatter, "do_3d_projection", side_effect=AssertionError("Layout projected scatter points")):
            title = layout_export_z_axis(figure, axes, "Z in mm", 22, spacing=24, tick_count=5)
        self.assertTrue(scatter.get_visible())
        figure.canvas.draw()
        renderer = figure.canvas.get_renderer()
        boxes = z_tick_boxes(axes, renderer)
        self.assertEqual(len(boxes), 5)
        extent = title.get_window_extent(renderer)
        self.assertGreaterEqual(min(box.x0 for box in boxes) - extent.x1, 24 * figure.dpi / 72 - 1)

    def test_manual_tick_count_is_not_reduced_for_large_fonts_or_reversed_limits(self):
        for count in (1, 3, 4, 7):
            for reverse in (False, True):
                with self.subTest(count=count, reverse=reverse):
                    figure, axes = self.figure(font=36)
                    if reverse:
                        axes.set_zlim(35, -10)
                    title = layout_export_z_axis(figure, axes, "Z in mm", 36, tick_count=count)
                    figure.canvas.draw()
                    renderer = figure.canvas.get_renderer()
                    boxes = z_tick_boxes(axes, renderer)
                    self.assertEqual(len(boxes), count)
                    expected = np.linspace(-10, 35, count) if count > 1 else [12.5]
                    np.testing.assert_allclose(axes.get_zticks(), expected)
                    self.assertFalse(any(title.get_window_extent(renderer).overlaps(box) for box in boxes))

    def test_tick_interval_uses_multiples_without_changing_limits_or_reducing_ticks(self):
        cases = (
            ((-32.71, 38.18), 10, [-30, -20, -10, 0, 10, 20, 30]),
            ((-9.08, -32.71), 10, [-30, -20, -10]),
            ((0.0, 0.3), 0.1, [0.0, 0.1, 0.2, 0.3]),
            ((13, 17), 10, []),
        )
        for limits, interval, expected in cases:
            with self.subTest(limits=limits, interval=interval):
                figure, axes = self.figure(font=22)
                axes.set_zlim(*limits)
                title = layout_export_z_axis(figure, axes, "Z in mm", 22, tick_count=2, tick_interval=interval)
                figure.canvas.draw()
                renderer = figure.canvas.get_renderer()
                np.testing.assert_allclose(axes.get_zticks(), expected)
                self.assertEqual(axes.get_zlim3d(), limits)
                boxes = z_tick_boxes(axes, renderer)
                self.assertEqual(len(boxes), len(expected))
                self.assertFalse(any(title.get_window_extent(renderer).overlaps(box) for box in boxes))
                if interval == 10:
                    self.assertTrue(all("." not in tick.get_text() for tick in axes.get_zticklabels()))

    def test_tick_label_gap_expands_z_height_and_survives_tight_export(self):
        for angle in (45, -45):
            with self.subTest(angle=angle):
                figure, axes = self.figure(font=16, azimuth=angle)
                axes.set_zlim(-32.71, 14.55)
                original_aspect = axes.get_box_aspect().copy()
                title = layout_export_z_axis(figure, axes, "Z in mm", 16, spacing=12,
                    tick_interval=10, tick_label_gap=30)
                np.testing.assert_allclose(axes.get_zticks(), [-30, -20, -10, 0, 10])
                self.assertEqual(axes.get_zlim3d(), (-32.71, 14.55))
                self.assertGreater(axes.get_box_aspect()[2] / axes.get_box_aspect()[0],
                    original_aspect[2] / original_aspect[0])
                measured_gaps = []

                def measure(event):
                    boxes = z_tick_boxes(axes, event.renderer)
                    measured_gaps.append(z_tick_label_separation(axes, boxes)[0] * 72 / figure.dpi)
                    self.assertFalse(any(title.get_window_extent(event.renderer).overlaps(box) for box in boxes))

                figure.canvas.mpl_connect("draw_event", measure)
                figure.savefig(BytesIO(), format="png", bbox_inches="tight")
                self.assertTrue(measured_gaps)
                self.assertTrue(all(gap >= 29.75 for gap in measured_gaps))


if __name__ == "__main__":
    unittest.main()
