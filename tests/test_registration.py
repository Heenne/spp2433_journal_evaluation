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

        self.assertEqual(report["overlap_points"], 3)
        self.assertEqual(report["evaluated_points"], 3)
        self.assertAlmostEqual(report["minimum"], 0.1)
        self.assertAlmostEqual(report["mean"], (0.1 + 0.2 + 8.8) / 3.0)
        self.assertAlmostEqual(report["maximum"], 8.8)
        self.assertAlmostEqual(report["rmse"], np.sqrt((0.1 ** 2 + 0.2 ** 2 + 8.8 ** 2) / 3.0))
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

    def test_surface_error_keeps_reference_covered_corners(self):
        grid = np.array([(x, y, 0.0) for x in range(21) for y in range(21)], dtype=float)
        extension = np.array([(x, y, 0.0) for x in range(21) for y in range(25, 31)], dtype=float)
        source = self._frame(np.vstack((grid, extension)))
        reference = self._frame(grid)

        report, pointwise = calculate_cloud_error(
            source, reference, max_distance=30.0, max_analysis_points=0, include_pointwise=True
        )

        self.assertTrue(np.all(np.isfinite(pointwise["distances"][:len(grid)])))
        self.assertTrue(np.all(np.isinf(pointwise["distances"][len(grid):])))
        self.assertEqual(report["overlap_points"], len(grid))
        self.assertAlmostEqual(report["overlap_fraction"], len(grid) / (len(grid) + len(extension)))
        self.assertEqual(report["evaluated_points"], len(grid))

    def test_surface_error_keeps_a_hole_within_the_distance_cutoff(self):
        reference_points = np.array(
            [(x, y, 0.0) for x in range(21) for y in range(21)
             if not (8 <= x <= 12 and 8 <= y <= 12)], dtype=float
        )
        source_points = np.vstack((
            [[10.0, 10.0, 0.0], [10.0, 25.0, 0.0]],
            [[x, 0.0, 0.0] for x in range(21)],
        ))

        report, pointwise = calculate_cloud_error(
            self._frame(source_points), self._frame(reference_points),
            max_distance=4.0, max_analysis_points=0, include_pointwise=True,
        )

        self.assertAlmostEqual(pointwise["distances"][0], 3.0)
        self.assertTrue(np.isinf(pointwise["distances"][1]))
        self.assertEqual(report["overlap_points"], len(source_points) - 1)
        self.assertEqual(report["evaluated_points"], len(source_points) - 1)

    def test_surface_error_excludes_a_boundary_band_but_keeps_interior_error(self):
        reference_points = np.array(
            [(x, y, 0.0) for x in range(101) for y in range(101)], dtype=float
        )
        source_points = np.vstack((
            [[50.0, 50.0, 1.8], [99.0, 50.0, 1.8], [101.0, 50.0, 0.0]],
            [[x, 50.0, 0.0] for x in range(20, 41)],
        ))

        report, pointwise = calculate_cloud_error(
            self._frame(source_points), self._frame(reference_points),
            max_distance=2.0, max_analysis_points=0, include_pointwise=True,
        )

        self.assertAlmostEqual(pointwise["distances"][0], 1.8)
        self.assertTrue(np.all(np.isinf(pointwise["distances"][1:3])))
        self.assertEqual(report["overlap_points"], len(source_points) - 1)
        self.assertEqual(report["reference_edge_excluded_points"], 1)
        self.assertEqual(report["evaluated_points"], len(source_points) - 2)

    def test_surface_error_can_return_pointwise_colours_for_the_analysed_points(self):
        source = self._frame(np.array([[0.0, 0.0, 0.0], [3.0, 0.0, 0.0]]))
        reference = self._frame(np.array([[0.2, 0.0, 0.0]]))

        report, pointwise = calculate_cloud_error(
            source, reference, max_distance=1.0, max_analysis_points=0, include_pointwise=True
        )

        np.testing.assert_allclose(pointwise["points"], source[["X", "Y", "Z"]].to_numpy())
        np.testing.assert_allclose(pointwise["distances"][:1], [0.2])
        self.assertAlmostEqual(pointwise["distances"][1], 2.8)
        self.assertEqual(report["overlap_points"], 2)
        self.assertEqual(report["evaluated_points"], 2)

    def test_xy_overlap_is_independent_of_height_error_and_cutoff(self):
        reference_points = np.array(
            [(x, y, 0.0) for x in range(21) for y in range(21)], dtype=float
        )
        source_points = np.array(
            [(x, y, 5.0) for x in range(5, 16) for y in range(5, 16)], dtype=float
        )

        report = calculate_cloud_error(
            self._frame(source_points), self._frame(reference_points),
            max_distance=1.0, max_analysis_points=0,
        )

        self.assertEqual(report["overlap_fraction"], 1.0)
        self.assertEqual(report["overlap_points"], len(source_points))
        self.assertEqual(report["evaluated_points"], len(source_points))
        self.assertAlmostEqual(report["p95"], 5.0)

    def test_surface_error_keeps_large_interior_errors_in_statistics(self):
        reference_points = np.array(
            [(x, y, 0.0) for x in range(21) for y in range(21)], dtype=float
        )
        source_points = np.array(
            [(x, y, 0.0) for x in range(5, 15) for y in range(5, 15)], dtype=float
        )
        source_points[-1, 2] = 10.0

        report, pointwise = calculate_cloud_error(
            self._frame(source_points), self._frame(reference_points),
            max_distance=1.0, max_analysis_points=0, include_pointwise=True,
        )

        self.assertEqual(report["overlap_fraction"], 1.0)
        self.assertEqual(report["evaluated_points"], len(source_points))
        self.assertEqual(report["maximum"], 10.0)
        self.assertEqual(report["p95"], 0.0)
        self.assertEqual(pointwise["distances"][-1], 10.0)

    def test_p5_is_not_determined_by_one_nearly_identical_point(self):
        source_points = np.vstack(([[0.0, 0.0, 0.0]], np.tile([1.0, 0.0, 0.0], (100, 1))))
        report = calculate_cloud_error(
            self._frame(source_points), self._frame(np.array([[0.0, 0.0, 0.0]])),
            max_distance=1.0,
        )
        self.assertEqual(report["minimum"], 0.0)
        self.assertEqual(report["p5"], 1.0)

    def test_xy_overlap_between_reference_samples_does_not_change_with_cutoff(self):
        reference_points = np.array(
            [(x, y, 0.0) for x in range(21) for y in range(21)], dtype=float
        )
        source_points = np.array([[5.5, 5.5, 0.0], [25.0, 5.5, 0.0]], dtype=float)

        for cutoff in (0.1, 2.0):
            report = calculate_cloud_error(
                self._frame(source_points), self._frame(reference_points),
                max_distance=cutoff, max_analysis_points=0,
            )
            self.assertEqual(report["overlap_points"], 1)
            self.assertEqual(report["overlap_fraction"], 0.5)

    def test_xy_overlap_uses_the_full_measurement_when_error_points_are_sampled(self):
        reference_points = np.array(
            [(x, y, 0.0) for x in range(21) for y in range(21)], dtype=float
        )
        extension = np.array(
            [(x, y, 0.0) for x in range(21) for y in range(25, 31)], dtype=float
        )
        source_points = np.vstack((reference_points, extension))

        report = calculate_cloud_error(
            self._frame(source_points), self._frame(reference_points),
            max_distance=1.0, max_analysis_points=25,
        )

        self.assertEqual(report["source_points_analysed"], 25)
        self.assertEqual(report["overlap_points"], len(reference_points))
        self.assertAlmostEqual(report["overlap_fraction"], len(reference_points) / len(source_points))

    def test_large_system_area_has_low_point_fraction_but_full_reference_coverage(self):
        reference = np.array([(x, y, 0.0) for x in range(21) for y in range(21)], dtype=float)
        source = np.array([(x, y, 3.0) for x in range(-20, 41) for y in range(-20, 41)], dtype=float)
        messages = []
        report = calculate_cloud_error(self._frame(source), self._frame(reference), 1.0,
                                       progress_callback=messages.append)
        self.assertAlmostEqual(report["system_points_within_reference_area_fraction"], 441 / 3721)
        self.assertEqual(report["reference_area_covered_fraction"], 1.0)
        self.assertEqual(report["mean"], 3.0)
        self.assertIn("System points within reference area", messages[-1])
        self.assertIn("Reference area covered", messages[-1])

    def test_small_system_area_has_full_point_fraction_but_partial_reference_coverage(self):
        reference = np.array([(x, y, 0.0) for x in range(41) for y in range(41)], dtype=float)
        source = np.array([(x, y, 2.0) for x in range(10, 31) for y in range(10, 31)], dtype=float)
        report = calculate_cloud_error(self._frame(source), self._frame(reference), 1.0)
        self.assertEqual(report["system_points_within_reference_area_fraction"], 1.0)
        # Raster boundaries introduce approximately one cell of uncertainty.
        self.assertAlmostEqual(report["reference_area_covered_fraction"], 0.25, delta=0.02)
        self.assertAlmostEqual(report["reference_area_covered"] / report["reference_area"],
                               report["reference_area_covered_fraction"])

    def test_area_coverage_is_independent_of_density_duplicates_z_and_analysis_sample(self):
        reference = np.array([(x, y, 0.0) for x in range(41) for y in range(41)], dtype=float)
        fractions = []
        for step, repeats, margin, limit in [(1, 1, 0.1, 0), (2, 1, 5.0, 25), (2, 5, 0.1, 0)]:
            source = np.array([(x, y, 8.0) for x in range(0, 41, step)
                               for y in range(0, 41, step)], dtype=float)
            source = np.repeat(source, repeats, axis=0)
            report = calculate_cloud_error(self._frame(source), self._frame(reference), margin,
                                           max_analysis_points=limit)
            fractions.append(report["reference_area_covered_fraction"])
            self.assertEqual(report["system_points_within_reference_area_fraction"], 1.0)
        self.assertEqual(fractions, [1.0, 1.0, 1.0])

    def test_reference_area_coverage_keeps_system_holes_and_disconnected_regions(self):
        reference = np.array([(x, y, 0.0) for x in range(41) for y in range(41)], dtype=float)
        full = calculate_cloud_error(self._frame(reference), self._frame(reference), 1.0)
        hole = reference[~((reference[:, 0] >= 10) & (reference[:, 0] <= 30)
                           & (reference[:, 1] >= 10) & (reference[:, 1] <= 30))]
        strips = reference[(reference[:, 0] < 10) | (reference[:, 0] > 30)]
        hole_report = calculate_cloud_error(self._frame(hole), self._frame(reference), 1.0)
        strip_report = calculate_cloud_error(self._frame(strips), self._frame(reference), 1.0)
        self.assertLess(hole_report["reference_area_covered_fraction"], 0.8)
        self.assertLess(strip_report["reference_area_covered_fraction"], 0.5)
        self.assertEqual(full["reference_area_covered_fraction"], 1.0)

    def test_sparse_irregular_scan_covering_reference_is_not_penalised_for_sample_gaps(self):
        reference = np.array([(x, y, 0.0) for x in range(101) for y in range(101)], dtype=float)
        xy = np.random.default_rng(12).uniform(-10.0, 110.0, (3000, 2))
        source = np.column_stack((xy, np.full(len(xy), 2.0)))
        report = calculate_cloud_error(self._frame(source), self._frame(reference), 1.0)
        # The previous occupied-cell method gave about 62% for this full scan.
        self.assertGreater(report["reference_area_covered_fraction"], 0.99)
        self.assertLess(report["system_points_within_reference_area_fraction"], 0.8)
        self.assertEqual(report["reference_area_coverage_method"], "xy_local_delaunay_cell_centres_v2")
        duplicated = calculate_cloud_error(self._frame(np.repeat(source, 3, axis=0)), self._frame(reference), 1.0)
        self.assertEqual(report["reference_area_covered_fraction"], duplicated["reference_area_covered_fraction"])
        missing = (source[:, 0] > 30) & (source[:, 0] < 70) & (source[:, 1] > 30) & (source[:, 1] < 70)
        hole_report = calculate_cloud_error(self._frame(source[~missing]), self._frame(reference), 1.0)
        self.assertLess(hole_report["reference_area_covered_fraction"], 0.9)
        self.assertGreater(hole_report["reference_area_covered_fraction"], 0.75)

    def test_area_coverage_adapts_to_local_density_without_bridging_disconnected_scans(self):
        reference = np.array([(x, y, 0.0) for x in range(101) for y in range(101)], dtype=float)
        rng = np.random.default_rng(91)
        dense = rng.uniform([-10.0, -10.0], [52.0, 110.0], (12000, 2))
        sparse = rng.uniform([48.0, -10.0], [110.0, 110.0], (1500, 2))
        xy = np.vstack((dense, sparse))
        source = np.column_stack((xy, np.zeros(len(xy))))
        report = calculate_cloud_error(self._frame(source), self._frame(reference), 1.0)
        self.assertGreater(report["reference_area_covered_fraction"], 0.98)
        separated = source[(source[:, 0] < 30.0) | (source[:, 0] > 70.0)]
        gap_report = calculate_cloud_error(self._frame(separated), self._frame(reference), 1.0)
        self.assertLess(gap_report["reference_area_covered_fraction"], 0.7)

    def test_diagonally_collinear_system_has_no_projected_area(self):
        reference = np.array([(x, y, 0.0) for x in range(21) for y in range(21)], dtype=float)
        source = np.array([(x, x, 0.0) for x in range(21)], dtype=float)
        report = calculate_cloud_error(self._frame(source), self._frame(reference), 1.0)
        self.assertEqual(report["reference_area_covered_fraction"], 0.0)
        self.assertEqual(report["system_points_within_reference_area_fraction"], 1.0)
        self.assertEqual(report["mean"], 0.0)

    def test_disjoint_system_has_zero_area_coverage(self):
        reference = np.array([(x, y, 0.0) for x in range(21) for y in range(21)], dtype=float)
        source = reference + [100.0, 0.0, 0.0]
        report = calculate_cloud_error(self._frame(source), self._frame(reference), 1.0)
        self.assertEqual(report["system_points_within_reference_area_fraction"], 0.0)
        self.assertEqual(report["reference_area_covered_fraction"], 0.0)
        self.assertEqual(report["evaluated_points"], 0)
        self.assertIsNone(report["mean"])

    def test_reference_without_2d_area_reports_area_coverage_as_unavailable(self):
        for count in (1, 2, 21):
            reference = np.column_stack((np.arange(count), np.zeros(count), np.zeros(count)))
            report = calculate_cloud_error(self._frame(reference), self._frame(reference), 1.0)
            self.assertIsNone(report["reference_area_covered_fraction"])
            self.assertEqual(report["reference_area_coverage_method"], "unavailable_no_2d_reference_area")
            self.assertEqual(report["mean"], 0.0)

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
