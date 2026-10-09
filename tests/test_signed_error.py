import unittest
import numpy as np
import pandas as pd

from src.utils.registration import calculate_cloud_error
from src.utils.error_mapping import error_map_colours


class SignedSurfaceErrorTests(unittest.TestCase):
    @staticmethod
    def frame(points):
        return pd.DataFrame(points, columns=["X", "Y", "Z"])

    def test_tilted_plane_has_correct_signed_normal_offset_and_orientation(self):
        x, y = np.meshgrid(np.linspace(-3, 3, 25), np.linspace(-3, 3, 25))
        reference = np.column_stack((x.ravel(), y.ravel(), (0.4*x - 0.2*y).ravel()))
        interior = reference[(np.abs(reference[:, 0]) < 2) & (np.abs(reference[:, 1]) < 2)]
        normal = np.array([-0.4, 0.2, 1.0])
        normal /= np.linalg.norm(normal)
        source = np.concatenate((interior + 0.2*normal, interior - 0.3*normal))
        report, pointwise = calculate_cloud_error(self.frame(source), self.frame(reference), 0.01,
            error_method="signed_normal", normal_radius=0.8, include_pointwise=True)
        expected = np.r_[np.full(len(interior), 0.2), np.full(len(interior), -0.3)]
        np.testing.assert_allclose(pointwise["distances"], expected, atol=1e-12)
        self.assertAlmostEqual(report["standard_deviation"], np.std(expected, ddof=1))
        reversed_report, reversed_points = calculate_cloud_error(self.frame(source), self.frame(reference), 0.01,
            error_method="signed_normal", normal_radius=0.8, normal_orientation="-Z", include_pointwise=True)
        np.testing.assert_allclose(reversed_points["distances"], -expected, atol=1e-12)
        self.assertAlmostEqual(reversed_report["rmse"], report["rmse"])

    def test_unsigned_point_distance_includes_sampling_offset_but_normal_error_does_not(self):
        x, y = np.meshgrid(np.arange(-3., 4.), np.arange(-3., 4.))
        reference = np.column_stack((x.ravel(), y.ravel(), np.zeros(x.size)))
        source = np.array([[0.1, 0.1, -0.2]])
        unsigned = calculate_cloud_error(self.frame(source), self.frame(reference), 0.01)
        signed = calculate_cloud_error(self.frame(source), self.frame(reference), 0.01,
                                       error_method="signed_normal", normal_radius=2.1)
        self.assertAlmostEqual(unsigned["mean"], np.sqrt(0.06))
        self.assertAlmostEqual(signed["mean"], -0.2)
        self.assertIsNone(signed["standard_deviation"])

    def test_normals_follow_curvature(self):
        x, y = np.meshgrid(np.linspace(-3., 3., 61), np.linspace(-2., 2., 41))
        reference = np.column_stack((x.ravel(), y.ravel(), (0.08*x*x).ravel()))
        interior = reference[(np.abs(reference[:, 0]) < 2) & (np.abs(reference[:, 1]) < 1)]
        normals = np.column_stack((-0.16*interior[:, 0], np.zeros(len(interior)), np.ones(len(interior))))
        normals /= np.linalg.norm(normals, axis=1)[:, None]
        _, points = calculate_cloud_error(self.frame(interior + 0.1*normals), self.frame(reference), 0.01,
            error_method="signed_normal", normal_radius=0.3, include_pointwise=True)
        np.testing.assert_allclose(points["distances"], 0.1, atol=0.005)

    def test_collinear_reference_does_not_produce_fake_normals_or_zero_errors(self):
        reference = self.frame([[float(x), 0., 0.] for x in range(10)])
        report, points = calculate_cloud_error(reference.assign(Z=0.1), reference, 0.01,
            error_method="signed_normal", normal_radius=3., include_pointwise=True)
        self.assertEqual(report["evaluated_points"], 0)
        self.assertIsNone(report["mean"])
        self.assertIsNone(report["standard_deviation"])
        self.assertIsNone(report["normalized_standard_deviation_percent"])
        self.assertIsNone(report["coverage_interval_90"])
        self.assertIsNone(report["coverage_interval_95"])
        self.assertFalse(np.any(np.isfinite(points["distances"])))

    def test_duplicate_reference_points_do_not_break_automatic_radius(self):
        x, y = np.meshgrid(np.arange(-3., 4.), np.arange(-3., 4.))
        points = np.column_stack((x.ravel(), y.ravel(), np.zeros(x.size)))
        source = self.frame([[0., 0., -0.2], [0., 0., 0.3]])
        report, errors = calculate_cloud_error(source, self.frame(np.repeat(points, 10, axis=0)), 0.01,
            error_method="signed_normal", include_pointwise=True)
        self.assertEqual(report["normal_radius_effective"], 3.)
        np.testing.assert_allclose(errors["distances"], [-0.2, 0.3], atol=1e-12)

    def test_asymmetric_colour_range_places_white_at_zero_without_changing_values(self):
        values = np.array([-0.2, 0., 0.8])
        coloured, kwargs, _, _ = error_map_colours(values,
            {"error_method": "signed_normal", "scale_mode": "manual", "heatmap_min": -0.2, "heatmap_max": 0.8},
            "blue_white_red")
        np.testing.assert_array_equal(coloured, values)
        np.testing.assert_allclose(kwargs["cmap"](kwargs["norm"](values)),
                                   [[0, 0, 1, 1], [1, 1, 1, 1], [1, 0, 0, 1]], atol=1e-12)

    def test_symmetric_colour_range_and_invalid_manual_limits(self):
        _, kwargs, _, _ = error_map_colours(np.array([-3., 1.]),
            {"error_method": "signed_normal", "scale_mode": "symmetric", "heatmap_max": 2.})
        self.assertEqual((kwargs["norm"].vmin, kwargs["norm"].vmax), (-2., 2.))
        with self.assertRaises(ValueError):
            error_map_colours(np.array([1.]), {"scale_mode": "manual", "heatmap_min": 2., "heatmap_max": 1.})

    def test_sampled_preview_keeps_full_data_colour_limits(self):
        full = np.linspace(-10., 30., 1000)
        sample = full[[0, 300, 400]]
        for method, centred in (("signed_normal", False), ("signed_normal", True), ("unsigned", False)):
            settings = {"error_method": method, "colour_mode": "difference_from_mean" if centred else "closest_distance",
                        "mean": float(np.mean(full))}
            _, original, _, _ = error_map_colours(full, settings)
            values, preview, _, _ = error_map_colours(sample, settings, normalization_distances=full)
            self.assertEqual(preview["norm"].vmin, original["norm"].vmin)
            self.assertEqual(preview["norm"].vmax, original["norm"].vmax)
            np.testing.assert_array_equal(values, sample - np.mean(full) if centred else sample)

    def test_final_statistics_progress_does_not_claim_display_is_complete(self):
        reference = self.frame([[x, y, 0.] for x in range(5) for y in range(5)])
        progress = []
        calculate_cloud_error(reference, reference, .01, progress_callback=progress.append)
        self.assertTrue(progress[-1].startswith("Error statistics ready:"))
        self.assertNotIn("Comparison complete", progress[-1])


if __name__ == "__main__":
    unittest.main()
