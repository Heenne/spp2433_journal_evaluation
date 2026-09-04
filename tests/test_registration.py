import unittest

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation

from src.utils.registration import (
    _projected_xy_overlap_masks,
    automatic_registration,
    calculate_cloud_error,
    global_automatic_registration,
    transform_points,
)


class LocalFineAlignmentTests(unittest.TestCase):
    @staticmethod
    def _source_cloud():
        """Make an asymmetric curved surface far from the world origin."""
        rng = np.random.default_rng(7)
        xy = rng.uniform(-20.0, 20.0, (9_000, 2))
        z = (
            0.02 * xy[:, 0] ** 2 + 0.015 * xy[:, 1] + 0.8 * np.sin(xy[:, 0] / 4.0)
            + 4.0 * np.exp(-((xy[:, 0] - 7.0) ** 2 + (xy[:, 1] + 5.0) ** 2) / 15.0)
            + 2.5 * np.exp(-((xy[:, 0] + 9.0) ** 2 + (xy[:, 1] - 8.0) ** 2) / 8.0)
        )
        return np.column_stack((xy[:, 0] + 400.0, xy[:, 1] - 200.0, z + 50.0))

    @staticmethod
    def _frame(points):
        return pd.DataFrame(points, columns=["X", "Y", "Z"])

    def test_refines_a_small_manual_pose_error_about_the_local_pivot(self):
        source = self._source_cloud()
        pivot = source.mean(axis=0)
        rotation = Rotation.from_rotvec([0.04, -0.025, 0.055]).as_matrix()
        target_full = (source - pivot) @ rotation.T + pivot + np.array([2.0, -1.3, 0.7])
        target_full += np.random.default_rng(8).normal(scale=0.003, size=target_full.shape)
        target = target_full[np.random.default_rng(9).choice(len(target_full), 6_500, replace=False)]

        result = automatic_registration(
            self._frame(source), self._frame(target),
            max_registration_points=12_000,
            maximum_correction_distance=4.0,
            maximum_rotation_degrees=8.0,
        )

        self.assertTrue(result["optimizer"]["accepted"], result)
        aligned = transform_points(source, result["transformation"])
        nearest_rms = float(np.sqrt(np.mean(cKDTree(target).query(aligned)[0] ** 2)))
        correspondence_rms = float(np.sqrt(np.mean(np.sum((aligned - target_full) ** 2, axis=1))))
        self.assertLess(correspondence_rms, 0.10, {**result, "nearest_rms": nearest_rms})
        self.assertLessEqual(result["optimizer"]["translation_correction"], 4.0)
        self.assertLessEqual(result["optimizer"]["rotation_correction_degrees"], 8.0)
        np.testing.assert_allclose(result["optimizer"]["pivot"], source.mean(axis=0))

    def test_keeps_an_already_correct_manual_pose(self):
        source = self._source_cloud()
        result = automatic_registration(
            self._frame(source), self._frame(source),
            max_registration_points=12_000,
            maximum_correction_distance=4.0,
            maximum_rotation_degrees=8.0,
        )

        self.assertFalse(result["optimizer"]["accepted"], result)
        self.assertTrue(result["initialization"].startswith("manual pose retained"))
        np.testing.assert_allclose(result["transformation"], np.eye(4))

    def test_individual_limits_can_lock_five_pose_axes(self):
        source = self._source_cloud()
        target = source + np.array([2.0, 0.0, 0.0])

        result = automatic_registration(
            self._frame(source), self._frame(target),
            max_registration_points=12_000,
            translation_limits=(3.0, 0.0, 0.0),
            rotation_limits_degrees=(0.0, 0.0, 0.0),
        )

        self.assertTrue(result["optimizer"]["accepted"], result)
        correction = result["optimizer"]["translation_correction_vector"]
        self.assertAlmostEqual(correction[0], 2.0, delta=0.1)
        self.assertEqual(correction[1:], [0.0, 0.0])
        self.assertEqual(result["optimizer"]["rotation_correction_vector_degrees"], [0.0, 0.0, 0.0])

    def test_projected_footprint_excludes_scan_extensions_before_3d_matching(self):
        x, y = np.meshgrid(np.linspace(-10.0, 10.0, 101), np.linspace(-5.0, 5.0, 31))
        source = np.column_stack((x.ravel(), y.ravel(), np.zeros(x.size)))
        target = source.copy()
        target[:, 0] += 10.0

        source_mask, target_mask, details = _projected_xy_overlap_masks(source, target, voxel_size=0.1)

        self.assertTrue(details["projected_overlap_used"])
        self.assertLess(source_mask.mean(), 0.6)
        self.assertLess(target_mask.mean(), 0.6)
        self.assertTrue(np.all(source[source_mask, 0] >= -0.3))
        self.assertTrue(np.all(target[target_mask, 0] <= 10.3))

    def test_surface_error_excludes_non_overlapping_source_points(self):
        source = self._frame(np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [10.0, 0.0, 0.0]]))
        reference = self._frame(np.array([[0.1, 0.0, 0.0], [1.2, 0.0, 0.0]]))

        report = calculate_cloud_error(source, reference, max_distance=0.5, max_analysis_points=0)

        self.assertEqual(report["overlap_points"], 2)
        self.assertEqual(report["non_overlap_points"], 1)
        self.assertAlmostEqual(report["minimum"], 0.1)
        self.assertAlmostEqual(report["mean"], 0.15)
        self.assertAlmostEqual(report["rmse"], np.sqrt((0.1 ** 2 + 0.2 ** 2) / 2.0))
        self.assertEqual(report["unit"], "mm")

    def test_surface_error_excludes_partial_scan_extension_from_maximum(self):
        # The points beyond X=89 are close enough to the reference edge to
        # pass a generous distance cutoff, but they are outside the common
        # footprint and must not determine the maximum error.
        source = self._frame(np.column_stack((np.arange(110, dtype=float), np.zeros(110), np.zeros(110))))
        reference = self._frame(np.column_stack((np.arange(90, dtype=float), np.zeros(90), np.zeros(90))))

        report = calculate_cloud_error(source, reference, max_distance=25.0, max_analysis_points=0)

        self.assertTrue(report["projected_footprint_used"])
        self.assertGreaterEqual(report["projected_non_overlap_points"], 2)
        self.assertEqual(report["maximum"], 0.0)

        report_metres = calculate_cloud_error(source, reference, max_distance=0.5, max_analysis_points=0, distance_unit="m")
        self.assertEqual(report_metres["unit"], "m")

    def test_surface_error_can_return_pointwise_colours_for_the_analysed_points(self):
        source = self._frame(np.array([[0.0, 0.0, 0.0], [3.0, 0.0, 0.0]]))
        reference = self._frame(np.array([[0.2, 0.0, 0.0]]))

        report, pointwise = calculate_cloud_error(
            source, reference, max_distance=1.0, max_analysis_points=0, include_pointwise=True
        )

        np.testing.assert_allclose(pointwise["points"], source[["X", "Y", "Z"]].to_numpy())
        np.testing.assert_allclose(pointwise["distances"][:1], [0.2])
        self.assertTrue(np.isinf(pointwise["distances"][1]))
        self.assertEqual(report["overlap_points"], 1)

    def test_fine_alignment_rejects_flip_sized_rotation_limits(self):
        source = self._frame(self._source_cloud())

        with self.assertRaisesRegex(ValueError, "between 0 and 30 degrees"):
            automatic_registration(source, source, maximum_rotation_degrees=180.0)

    def test_previous_global_alignment_uses_axis_corrected_coordinates(self):
        source = self._source_cloud()
        reference_raw = source.copy()
        reference_raw[:, 2] *= -1.0
        reference_after_z_inversion = reference_raw.copy()
        reference_after_z_inversion[:, 2] *= -1.0

        result = global_automatic_registration(
            self._frame(source), self._frame(reference_after_z_inversion), max_registration_points=3_000
        )

        self.assertGreater(result["source_overlap"], 0.95, result)
        self.assertLess(result["inlier_rmse"], 0.02, result)


if __name__ == "__main__":
    unittest.main()
