"""Registration and surface-deviation helpers for point-cloud comparison.

The functions in this module deliberately keep the expensive work off the Qt
thread. Registration is done on adaptively voxel-downsampled clouds, while the
final comparison uses a chunked KD-tree query for large drone surveys.
"""

from __future__ import annotations

from itertools import permutations, product
from typing import Callable, Optional

import numpy as np
import pandas as pd


ProgressCallback = Optional[Callable[[str], None]]
CancelledCallback = Optional[Callable[[], bool]]


def euler_translation_to_matrix(tx: float, ty: float, tz: float,
                                rx: float, ry: float, rz: float) -> np.ndarray:
    """Convert translation and XYZ Euler angles in degrees to a 4x4 matrix."""
    from scipy.spatial.transform import Rotation as rotation

    transform = np.eye(4)
    transform[:3, :3] = rotation.from_euler("xyz", [rx, ry, rz], degrees=True).as_matrix()
    transform[:3, 3] = [tx, ty, tz]
    return transform


def matrix_to_euler_translation(matrix: np.ndarray) -> tuple:
    """Convert a rigid 4x4 matrix to ``(tx, ty, tz, rx, ry, rz)``."""
    from scipy.spatial.transform import Rotation as rotation

    tx, ty, tz = matrix[:3, 3]
    rx, ry, rz = rotation.from_matrix(matrix[:3, :3]).as_euler("xyz", degrees=True)
    return float(tx), float(ty), float(tz), float(rx), float(ry), float(rz)


def transform_points(points: np.ndarray, transform: np.ndarray) -> np.ndarray:
    """Apply a homogeneous transformation without building a 4D copy."""
    return np.asarray(points, dtype=np.float64) @ transform[:3, :3].T + transform[:3, 3]


def _points_from_dataframe(df: pd.DataFrame) -> np.ndarray:
    if df is None or df.empty:
        return np.empty((0, 3), dtype=np.float64)
    points = df[["X", "Y", "Z"]].to_numpy(dtype=np.float64, copy=False)
    return points[np.isfinite(points).all(axis=1)]


def _emit(progress_callback: ProgressCallback, message: str) -> None:
    if progress_callback:
        progress_callback(message)


def _check_cancelled(is_cancelled_callback: CancelledCallback) -> None:
    if is_cancelled_callback and is_cancelled_callback():
        raise RuntimeError("Cancelled by User")


def _require_open3d():
    try:
        import open3d as o3d
    except ImportError as exc:  # pragma: no cover - declared in pixi.toml
        raise RuntimeError("Open3D is required for automatic alignment.") from exc
    return o3d


def _estimate_point_spacing(points: np.ndarray) -> float:
    """Estimate typical sample spacing from a bounded deterministic subset."""
    from scipy.spatial import cKDTree

    if len(points) < 3:
        return 0.0
    sample_size = min(len(points), 20_000)
    if sample_size < len(points):
        sample_indices = np.linspace(0, len(points) - 1, sample_size, dtype=np.int64)
        sample = points[sample_indices]
    else:
        sample = points
    distances, _ = cKDTree(sample).query(sample, k=2, workers=-1)
    nearest = distances[:, 1]
    nearest = nearest[np.isfinite(nearest) & (nearest > 0)]
    return float(np.median(nearest)) if len(nearest) else 0.0


def _initial_voxel_size(source_points: np.ndarray, target_points: np.ndarray) -> float:
    """Choose a stable common voxel size from density and scan extent."""
    # Never derive a scale from the combined bounds: clouds can initially be
    # kilometres apart simply because their coordinate origins differ.
    source_extent = float(np.max(np.percentile(source_points, 95, axis=0) - np.percentile(source_points, 5, axis=0)))
    target_extent = float(np.max(np.percentile(target_points, 95, axis=0) - np.percentile(target_points, 5, axis=0)))
    extents = [value for value in (source_extent, target_extent) if value > 0]
    extent_scale = min(extents) if extents else 0.0
    spacings = [
        value for value in (_estimate_point_spacing(source_points), _estimate_point_spacing(target_points))
        if value > 0
    ]
    spacing = min(spacings) if spacings else 0.0
    # Preserve the smaller (often partial) measurement. The loop in
    # _downsample_for_registration enlarges this as needed to respect the cap.
    return max(spacing * 2.5, extent_scale / 1500.0, 1e-6)


def _crop_reference_near_current_source(source_points: np.ndarray, target_points: np.ndarray,
                                        progress_callback: ProgressCallback) -> np.ndarray:
    """Use the rough manual pose to avoid indexing an entire reference scan.

    The crop is attempted only when the transformed source already falls near
    the transformed reference. If it does not, the full target is retained so
    the caller can report that the manual overlap is insufficient.
    """
    source_low = np.percentile(source_points, 1, axis=0)
    source_high = np.percentile(source_points, 99, axis=0)
    source_extent = float(np.max(source_high - source_low))
    if source_extent <= 0:
        return target_points
    padding = max(source_extent * 0.5, _estimate_point_spacing(source_points) * 20.0)
    mask = np.all((target_points >= source_low - padding) & (target_points <= source_high + padding), axis=1)
    cropped = target_points[mask]
    if len(cropped) >= 100 and len(cropped) < len(target_points) * 0.9:
        _emit(progress_callback,
              f"Using {len(cropped):,} nearby reference points from the rough manual pose "
              f"(of {len(target_points):,} total).")
        return cropped
    return target_points


def _downsample_for_registration(source_points: np.ndarray, target_points: np.ndarray,
                                 max_points: int, progress_callback: ProgressCallback,
                                 is_cancelled_callback: CancelledCallback):
    """Return two feature-sized Open3D clouds and their shared voxel size."""
    o3d = _require_open3d()
    max_points = max(1_000, int(max_points))

    def bounded_sample(points: np.ndarray, label: str, seed: int) -> np.ndarray:
        # Avoid creating a second full Open3D copy of a multi-million-point
        # survey just to estimate a rigid transform. The later comparison can
        # still use the dense source cloud.
        cap = min(max_points * 10, 1_000_000)
        if len(points) <= cap:
            return points
        indices = np.random.default_rng(seed).choice(len(points), cap, replace=False)
        _emit(progress_callback, f"Pre-sampling {label} from {len(points):,} to {cap:,} points for registration.")
        return points[indices]

    source_points = bounded_sample(source_points, "source", 20260820)
    target_points = bounded_sample(target_points, "reference", 20260821)
    source = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(source_points))
    target = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(target_points))
    voxel_size = _initial_voxel_size(source_points, target_points)

    _emit(progress_callback, "Selecting a resolution for automatic registration...")
    for _ in range(16):
        _check_cancelled(is_cancelled_callback)
        source_down = source.voxel_down_sample(voxel_size)
        target_down = target.voxel_down_sample(voxel_size)
        if len(source_down.points) <= max_points and len(target_down.points) <= max_points:
            break
        voxel_size *= 1.6
    else:
        source_down = source.voxel_down_sample(voxel_size)
        target_down = target.voxel_down_sample(voxel_size)

    if min(len(source_down.points), len(target_down.points)) < 20:
        raise ValueError(
            "Too few points remain after downsampling. Check that both clouds use the same units "
            "(set the manual Uniform scale if needed) and make a rough manual placement before retrying."
        )
    _emit(progress_callback,
          f"Registration resolution: {voxel_size:.6g}; using "
          f"{len(source_down.points):,} source and {len(target_down.points):,} reference points.")
    return source_down, target_down, voxel_size


def _estimate_global_normals(point_cloud, voxel_size: float, progress_callback: ProgressCallback,
                             label: str, is_cancelled_callback: CancelledCallback) -> None:
    """Estimate normals once for the restored global alignment pipeline."""
    o3d = _require_open3d()
    _check_cancelled(is_cancelled_callback)
    _emit(progress_callback, f"Estimating normals for global alignment ({label})...")
    point_cloud.estimate_normals(
        o3d.geometry.KDTreeSearchParamHybrid(radius=voxel_size * 2.5, max_nn=40)
    )


def _global_fpfh_features(point_cloud, voxel_size: float, progress_callback: ProgressCallback,
                          label: str, is_cancelled_callback: CancelledCallback):
    """Compute FPFH descriptors for the legacy broad pose search."""
    o3d = _require_open3d()
    _check_cancelled(is_cancelled_callback)
    _emit(progress_callback, f"Computing FPFH features for global alignment ({label})...")
    return o3d.pipelines.registration.compute_fpfh_feature(
        point_cloud,
        o3d.geometry.KDTreeSearchParamHybrid(radius=voxel_size * 6.0, max_nn=100),
    )


def _centre_of_gravity_transform(source, target) -> np.ndarray:
    """Return a global translation that aligns the two point-cloud centroids."""
    source_centre = np.asarray(source.points).mean(axis=0)
    target_centre = np.asarray(target.points).mean(axis=0)
    transform = np.eye(4)
    transform[:3, 3] = target_centre - source_centre
    return transform


def _pca_centre_of_gravity_candidates(source, target) -> list[np.ndarray]:
    """Return all proper PCA orientation candidates with centroid translation."""
    source_points = np.asarray(source.points)
    target_points = np.asarray(target.points)
    source_centre = source_points.mean(axis=0)
    target_centre = target_points.mean(axis=0)
    _, source_axes = np.linalg.eigh(np.cov((source_points - source_centre).T))
    _, target_axes = np.linalg.eigh(np.cov((target_points - target_centre).T))
    source_axes = source_axes[:, ::-1]
    target_axes = target_axes[:, ::-1]
    candidates = []
    for axis_order in permutations(range(3)):
        for signs in product((-1.0, 1.0), repeat=3):
            basis_mapping = np.zeros((3, 3))
            for source_axis, target_axis in enumerate(axis_order):
                basis_mapping[target_axis, source_axis] = signs[source_axis]
            rotation = target_axes @ basis_mapping @ source_axes.T
            if np.linalg.det(rotation) <= 0:
                continue
            transform = np.eye(4)
            transform[:3, :3] = rotation
            transform[:3, 3] = target_centre - rotation @ source_centre
            candidates.append(transform)
    return candidates


def _best_global_pca_candidates(source, target, voxel_size: float, max_candidates: int = 3) -> list[np.ndarray]:
    """Keep only the promising PCA candidates before expensive ICP refinement."""
    registration = _require_open3d().pipelines.registration
    radius = voxel_size * 8.0
    scored = []
    for transform in _pca_centre_of_gravity_candidates(source, target):
        evaluation = registration.evaluate_registration(source, target, radius, transform)
        rmse = float(evaluation.inlier_rmse)
        scored.append((float(evaluation.fitness), rmse if np.isfinite(rmse) else float("inf"), transform))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [item[2] for item in scored[:max_candidates]]


def _robust_global_icp(source, target, initial_transform: np.ndarray, voxel_size: float,
                       progress_callback: ProgressCallback, is_cancelled_callback: CancelledCallback,
                       label: str) -> tuple[np.ndarray, float]:
    """Refine one restored global candidate with coarse-to-fine robust ICP."""
    registration = _require_open3d().pipelines.registration
    transform = np.asarray(initial_transform, dtype=np.float64).copy()
    final_radius = max(voxel_size * 1.25, 1e-9)
    radii = (max(voxel_size * 8.0, final_radius), max(voxel_size * 3.0, final_radius), final_radius)
    for stage, radius in enumerate(radii, start=1):
        _check_cancelled(is_cancelled_callback)
        _emit(progress_callback, f"{label}: global robust ICP {stage}/3 (radius {radius:.6g})...")
        result = registration.registration_icp(
            source,
            target,
            radius,
            transform,
            registration.TransformationEstimationPointToPlane(registration.TukeyLoss(k=radius)),
            registration.ICPConvergenceCriteria(max_iteration=80),
        )
        transform = result.transformation
    return transform, final_radius


def _final_alignment_tolerance(voxel_size: float, search_radius: float) -> float:
    """Choose a strict final correspondence tolerance from the requested search range."""
    return max(voxel_size * 0.25, min(search_radius * 0.20, voxel_size))


def _component_limits(limits, fallback: float, label: str, maximum: float | None = None) -> np.ndarray:
    """Normalize one scalar fallback or three non-negative per-axis half-widths."""
    values = np.full(3, float(fallback), dtype=np.float64) if limits is None else np.asarray(limits, dtype=np.float64)
    if values.shape != (3,) or not np.isfinite(values).all() or np.any(values < 0):
        raise ValueError(f"{label} limits must contain exactly three finite values greater than or equal to zero.")
    if maximum is not None and np.any(values > maximum):
        raise ValueError(f"Each {label.lower()} limit must not exceed {maximum:.6g}.")
    return values


def _bounded_sample(points: np.ndarray, maximum_points: int, seed: int) -> np.ndarray:
    """Deterministically sample a cloud for repeated optimizer evaluations."""
    if len(points) <= maximum_points:
        return points
    indices = np.random.default_rng(seed).choice(len(points), maximum_points, replace=False)
    return points[indices]


def _clip_componentwise(vector: np.ndarray, limits: np.ndarray) -> np.ndarray:
    """Keep every coordinate of ``vector`` inside its own symmetric limit."""
    vector = np.asarray(vector, dtype=np.float64)
    limits = np.asarray(limits, dtype=np.float64)
    return np.clip(vector, -limits, limits)


def _bounded_local_parameters(parameters: np.ndarray, translation_limits: np.ndarray,
                              rotation_limits_degrees: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return the pivot correction under independent XYZ translation/rotation limits."""
    translation = _clip_componentwise(parameters[:3], translation_limits)
    rotation_angles = _clip_componentwise(parameters[3:], rotation_limits_degrees)
    return translation, rotation_angles


def _local_delta_transform(parameters: np.ndarray, pivot: np.ndarray,
                           translation_limits: np.ndarray,
                           rotation_limits_degrees: np.ndarray) -> np.ndarray:
    """Build a bounded rigid correction around a local overlap pivot.

    ``parameters[:3]`` is a translation at ``pivot`` and ``parameters[3:]``
    are XYZ Euler angles in degrees, matching the manual transform controls.
    This avoids the misleading, origin-dependent translation that results when
    a small rotation is represented around a distant project-coordinate origin.
    """
    from scipy.spatial.transform import Rotation

    translation, rotation_angles = _bounded_local_parameters(
        parameters, translation_limits, rotation_limits_degrees
    )
    rotation = Rotation.from_euler("xyz", rotation_angles, degrees=True).as_matrix()
    transform = np.eye(4)
    transform[:3, :3] = rotation
    transform[:3, 3] = pivot + translation - rotation @ pivot
    return transform


def _projected_xy_overlap_masks(source_points: np.ndarray, target_points: np.ndarray,
                                voxel_size: float, exclude_partial_extensions: bool = False) -> tuple[np.ndarray, np.ndarray, dict]:
    """Select the common footprint of two already roughly aligned clouds.

    A partial survey frequently contains a valid surface plus areas which are
    simply not present in the reference (and conversely).  A large 3-D
    correspondence gate is useful while refining a small manual error, but is
    a poor way to decide which of those areas are comparable: it can let an
    unmatched edge pull ICP towards the reference.  The current manual pose
    gives a much more reliable answer.  We therefore intersect robust X--Y
    envelopes before making the 3-D anchor sets.

    The small padding protects genuine edge points from voxelisation and minor
    manual error.  It is deliberately based on resolution, not on the allowed
    correction range, so entering a generous bound cannot turn a non-overlap
    region back into an optimizer objective.
    """
    source_xy = np.asarray(source_points, dtype=np.float64)[:, :2]
    target_xy = np.asarray(target_points, dtype=np.float64)[:, :2]
    source_low, source_high = np.percentile(source_xy, (1.0, 99.0), axis=0)
    target_low, target_high = np.percentile(target_xy, (1.0, 99.0), axis=0)
    overlap_low = np.maximum(source_low, target_low)
    overlap_high = np.minimum(source_high, target_high)

    # At most a very small fraction of the current footprint is admitted at
    # an edge.  This keeps the selection stable for scattered/noisy boundary
    # points without admitting a large unmatched scan extension.
    source_span = source_high - source_low
    target_span = target_high - target_low
    smaller_span = np.minimum(source_span, target_span)
    padding = np.maximum(voxel_size * 2.0, smaller_span * 0.01)

    if np.any(overlap_high + padding < overlap_low - padding):
        # Let the normal 3-D overlap validation produce its helpful error
        # message when the rough pose is not close enough for an X--Y crop.
        return np.ones(len(source_points), dtype=bool), np.ones(len(target_points), dtype=bool), {
            "projected_overlap_used": False,
            "projected_source_points": int(len(source_points)),
            "projected_reference_points": int(len(target_points)),
        }

    lower = overlap_low - padding
    upper = overlap_high + padding
    source_mask = np.all((source_xy >= lower) & (source_xy <= upper), axis=1)
    target_mask = np.all((target_xy >= lower) & (target_xy <= upper), axis=1)
    source_fraction = float(np.mean(source_mask))
    target_fraction = float(np.mean(target_mask))
    # Do not discard a thin boundary strip when the scans already cover almost
    # all of one another.  Those edge features can be valuable constraints;
    # footprint cropping is intended for genuinely partial surveys.
    if not exclude_partial_extensions and min(source_fraction, target_fraction) >= 0.9:
        return np.ones(len(source_points), dtype=bool), np.ones(len(target_points), dtype=bool), {
            "projected_overlap_used": False,
            "projected_source_points": int(len(source_points)),
            "projected_reference_points": int(len(target_points)),
            "projected_source_fraction": source_fraction,
            "projected_reference_fraction": target_fraction,
        }
    return source_mask, target_mask, {
        "projected_overlap_used": True,
        "projected_source_points": int(np.count_nonzero(source_mask)),
        "projected_reference_points": int(np.count_nonzero(target_mask)),
        "projected_source_fraction": source_fraction,
        "projected_reference_fraction": target_fraction,
        "projected_xy_padding": float(np.max(padding)),
    }


def _comparison_footprint_masks(source_points: np.ndarray, reference_points: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict]:
    """Keep points inside the reference outline, including measured surface holes."""
    if min(len(source_points), len(reference_points)) < 20:
        # A few isolated samples cannot define a reliable surface footprint.
        return (
            np.ones(len(source_points), dtype=bool),
            np.ones(len(reference_points), dtype=bool),
            {"projected_overlap_used": False},
        )
    from scipy.spatial import ConvexHull, QhullError, cKDTree

    reference_xy = np.asarray(reference_points, dtype=np.float64)[:, :2]
    source_xy = np.asarray(source_points, dtype=np.float64)[:, :2]
    try:
        outline_equations = ConvexHull(reference_xy).equations
    except QhullError:
        # A line-like diagnostic scan has no 2-D outline. For this case only,
        # use local reference support to reject source extensions.
        outline_equations = None
        reference_tree = cKDTree(reference_xy)
        sample = reference_xy[np.linspace(0, len(reference_xy) - 1, min(len(reference_xy), 20_000), dtype=np.int64)]
        neighbour_distances, _ = reference_tree.query(sample, k=2, workers=-1)
        positive_spacings = neighbour_distances[:, 1]
        positive_spacings = positive_spacings[np.isfinite(positive_spacings) & (positive_spacings > 0)]
        spacing = float(np.percentile(positive_spacings, 95)) if len(positive_spacings) else 0.0
        support_radius = max(0.95 * spacing, 1e-6)
    source_mask = np.zeros(len(source_xy), dtype=bool)
    for start in range(0, len(source_xy), 100_000):
        stop = min(start + 100_000, len(source_xy))
        if outline_equations is not None:
            chunk = source_xy[start:stop]
            inside = np.ones(len(chunk), dtype=bool)
            for a, b, c in outline_equations:
                inside &= a * chunk[:, 0] + b * chunk[:, 1] + c <= 1e-9
            source_mask[start:stop] = inside
        else:
            distances, _ = reference_tree.query(
                source_xy[start:stop], k=1, distance_upper_bound=support_radius, workers=-1
            )
            source_mask[start:stop] = np.isfinite(distances)
    return source_mask, np.ones(len(reference_xy), dtype=bool), {
        "projected_overlap_used": True,
        "projected_source_points": int(np.count_nonzero(source_mask)),
        "projected_reference_points": int(len(reference_xy)),
    }


def _manual_overlap_anchor_sets(source_points: np.ndarray, target_points: np.ndarray,
                                capture_distance: float,
                                source_footprint_mask: np.ndarray | None = None,
                                target_footprint_mask: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray, dict]:
    """Freeze the area that already overlaps in the manually placed pose.

    The reference can be much larger than the project scan.  Restricting both
    directions to their initial nearby points means the optimizer cannot obtain
    an attractive score simply by sliding onto another similar blade region.
    """
    from scipy.spatial import cKDTree

    if source_footprint_mask is None:
        source_footprint_mask = np.ones(len(source_points), dtype=bool)
    if target_footprint_mask is None:
        target_footprint_mask = np.ones(len(target_points), dtype=bool)
    source_candidates = source_points[np.asarray(source_footprint_mask, dtype=bool)]
    target_candidates = target_points[np.asarray(target_footprint_mask, dtype=bool)]
    if min(len(source_candidates), len(target_candidates)) < 20:
        raise RuntimeError(
            "The projected X-Y footprints do not contain enough common points for safe fine alignment. "
            "Adjust the scan manually first."
        )

    source_tree = cKDTree(source_candidates)
    target_tree = cKDTree(target_candidates)
    source_distances, _ = target_tree.query(
        source_candidates, k=1, distance_upper_bound=capture_distance, workers=-1
    )
    target_distances, _ = source_tree.query(
        target_candidates, k=1, distance_upper_bound=capture_distance, workers=-1
    )
    source_mask = np.isfinite(source_distances)
    target_mask = np.isfinite(target_distances)
    source_anchors = source_candidates[source_mask]
    target_anchors = target_candidates[target_mask]
    minimum_anchors = max(50, min(500, min(len(source_candidates), len(target_candidates)) // 200))
    if min(len(source_anchors), len(target_anchors)) < minimum_anchors:
        raise RuntimeError(
            "The manual pose does not establish enough nearby overlap for safe fine alignment. "
            "Adjust the scan manually first, or increase the correspondence capture distance slightly."
        )
    return source_anchors, target_anchors, {
        "source_anchor_points": int(len(source_anchors)),
        "reference_anchor_points": int(len(target_anchors)),
        "source_anchor_fraction": float(len(source_anchors) / len(source_candidates)),
        "reference_anchor_fraction": float(len(target_anchors) / len(target_candidates)),
    }


def _anchor_score(source_points: np.ndarray, target_points: np.ndarray,
                  transform: np.ndarray, maximum_distance: float,
                  trim_fraction: float = 0.8) -> dict:
    """Score a frozen overlap footprint in both nearest-neighbour directions."""
    from scipy.spatial import cKDTree

    transformed_source = transform_points(source_points, transform)
    forward, _ = cKDTree(target_points).query(
        transformed_source, k=1, distance_upper_bound=maximum_distance, workers=-1
    )
    reverse, _ = cKDTree(transformed_source).query(
        target_points, k=1, distance_upper_bound=maximum_distance, workers=-1
    )

    def directional_score(distances):
        accepted = distances[np.isfinite(distances)]
        overlap = float(len(accepted) / len(distances))
        if not len(accepted):
            return overlap, float("inf"), 0
        count = max(1, int(np.ceil(len(accepted) * trim_fraction)))
        trimmed = np.partition(accepted, count - 1)[:count]
        return overlap, float(np.sqrt(np.mean(np.square(trimmed)))), int(len(accepted))

    source_overlap, source_rmse, source_matches = directional_score(forward)
    reference_overlap, reference_rmse, reference_matches = directional_score(reverse)
    return {
        "fitness": float(np.sqrt(source_overlap * reference_overlap)),
        "rmse": float(np.sqrt((source_rmse ** 2 + reference_rmse ** 2) / 2.0)),
        "source_overlap": source_overlap,
        "reference_overlap": reference_overlap,
        "source_matches": source_matches,
        "reference_matches": reference_matches,
    }


def _optimize_local_closest_point_pose(source_points: np.ndarray, target_points: np.ndarray,
                                       voxel_size: float, capture_distance: float,
                                       translation_limits: np.ndarray,
                                       rotation_limits_degrees: np.ndarray,
                                       pivot: np.ndarray,
                                       progress_callback: ProgressCallback,
                                       is_cancelled_callback: CancelledCallback):
    """Iteratively refine the manual pose with a bounded bidirectional objective.

    Correspondences are recomputed after every small pose update, much like
    ICP, but the correction is strictly local to the manual pose.  Both anchor
    directions are included in the robust loss so a partial project cloud and
    a large reference are treated fairly.
    """
    from scipy.optimize import least_squares
    from scipy.spatial import cKDTree
    from scipy.spatial.transform import Rotation

    source_points = np.asarray(source_points, dtype=np.float64)
    target_points = np.asarray(target_points, dtype=np.float64)
    source_pivot = np.asarray(pivot, dtype=np.float64)
    if source_pivot.shape != (3,) or not np.isfinite(source_pivot).all():
        raise ValueError("The fine-alignment pivot must contain three finite coordinates.")
    translation_limits = np.asarray(translation_limits, dtype=np.float64)
    rotation_limits_degrees = np.asarray(rotation_limits_degrees, dtype=np.float64)
    translation_search_extent = float(np.max(translation_limits))
    final_tolerance = _final_alignment_tolerance(voxel_size, translation_search_extent)
    lower = -np.concatenate((translation_limits, rotation_limits_degrees))
    upper = -lower
    parameters = np.zeros(6, dtype=np.float64)
    active_parameters = np.flatnonzero(upper - lower > 1e-12)
    stages = (
        (3_000, capture_distance, 45),
        (10_000, max(final_tolerance * 2.0, capture_distance * 0.45), 60),
        (20_000, final_tolerance, 75),
    )
    evaluation_count = 0
    parameter_scale = np.array(
        [max(limit * 0.25, final_tolerance) for limit in translation_limits]
        + [max(limit * 0.25, 0.25) for limit in rotation_limits_degrees],
        dtype=np.float64,
    )

    if not len(active_parameters):
        _emit(progress_callback, "All fine-alignment translation and rotation limits are zero; retaining the manual pose.")

    for stage, (maximum_points, correspondence_limit, max_nfev) in enumerate(stages, start=1):
        if not len(active_parameters):
            break
        _check_cancelled(is_cancelled_callback)
        working_source = _bounded_sample(source_points, min(maximum_points, len(source_points)), 20261000 + stage)
        working_target = _bounded_sample(target_points, min(maximum_points, len(target_points)), 20262000 + stage)
        target_tree = cKDTree(working_target)
        _emit(progress_callback,
              f"Local closest-point optimization {stage}/3: {len(working_source):,} source and "
              f"{len(working_target):,} reference anchor points (capture {correspondence_limit:.6g})...")

        def residuals(candidate_active_parameters):
            nonlocal evaluation_count
            _check_cancelled(is_cancelled_callback)
            evaluation_count += 1
            candidate_parameters = parameters.copy()
            candidate_parameters[active_parameters] = candidate_active_parameters
            delta = _local_delta_transform(
                candidate_parameters, source_pivot, translation_limits, rotation_limits_degrees
            )
            transformed_source = transform_points(working_source, delta)
            forward, _ = target_tree.query(
                transformed_source, k=1, distance_upper_bound=correspondence_limit, workers=1
            )
            source_tree = cKDTree(transformed_source)
            reverse, _ = source_tree.query(
                working_target, k=1, distance_upper_bound=correspondence_limit, workers=1
            )
            # Non-overlap stays at the capture limit. soft_l1 makes those
            # constant residuals resistant to pulling the solution elsewhere.
            return np.concatenate((
                np.minimum(forward, correspondence_limit),
                np.minimum(reverse, correspondence_limit),
            ))

        result = least_squares(
            residuals,
            parameters[active_parameters],
            bounds=(lower[active_parameters], upper[active_parameters]),
            method="trf",
            loss="soft_l1",
            f_scale=max(final_tolerance, correspondence_limit * 0.15),
            x_scale=parameter_scale[active_parameters],
            max_nfev=max_nfev,
            xtol=1e-5,
            ftol=1e-5,
            gtol=1e-5,
        )
        parameters[active_parameters] = result.x
        translation, rotation_vector = _bounded_local_parameters(
            parameters, translation_limits, rotation_limits_degrees
        )
        parameters = np.concatenate((translation, rotation_vector))

    transform = _local_delta_transform(
        parameters, source_pivot, translation_limits, rotation_limits_degrees
    )
    translation, rotation_vector = _bounded_local_parameters(
        parameters, translation_limits, rotation_limits_degrees
    )
    return transform, final_tolerance, {
        "optimizer": "bounded bidirectional closest-point least squares",
        "evaluations": evaluation_count,
        "translation_correction": float(np.linalg.norm(translation)),
        "translation_correction_vector": [float(value) for value in translation],
        "rotation_correction_vector_degrees": [float(value) for value in rotation_vector],
        "rotation_correction_degrees": float(np.degrees(
            Rotation.from_euler("xyz", rotation_vector, degrees=True).magnitude()
        )),
        "pivot": [float(value) for value in source_pivot],
    }


def automatic_registration(source_df: pd.DataFrame, target_df: pd.DataFrame,
                           max_registration_points: int = 30_000,
                           use_global_registration: bool = False,
                           maximum_correction_distance: float = 10.0,
                           maximum_rotation_degrees: float = 15.0,
                           progress_callback: ProgressCallback = None,
                           is_cancelled_callback: CancelledCallback = None,
                           translation_limits=None,
                           rotation_limits_degrees=None) -> dict:
    """Fine-align a manually placed source cloud to a partial reference area.

    The input frames are already in their user-selected coordinate systems and
    carry the manual pose.  This function therefore returns only a small delta
    transform.  It deliberately does *not* call PCA, centre-of-gravity, FPFH,
    or RANSAC: those global initializers are ambiguous for a small blade scan
    against a larger reference and can introduce a 180-degree flip.
    """
    source_points = _points_from_dataframe(source_df)
    target_points = _points_from_dataframe(target_df)
    if len(source_points) < 20 or len(target_points) < 20:
        raise ValueError("Both point clouds need at least 20 finite XYZ points.")
    if translation_limits is None and maximum_correction_distance < 0:
        raise ValueError("The rough-pose translation correction limit must not be negative.")
    if rotation_limits_degrees is None and not 0 <= maximum_rotation_degrees <= 30:
        raise ValueError(
            "The maximum rotation correction must be between 0 and 30 degrees for bounded manual fine alignment. "
            "Use the manual controls first when a larger orientation correction is needed."
        )
    translation_limits = _component_limits(
        translation_limits, maximum_correction_distance, "Translation"
    )
    rotation_limits_degrees = _component_limits(
        rotation_limits_degrees, maximum_rotation_degrees, "Rotation", maximum=30.0
    )

    if use_global_registration:
        # Kept as an accepted argument for callers from older versions.  The
        # fine-align action is explicitly manual-pose local now; silently
        # applying a global candidate here would reintroduce the flip it is
        # designed to prevent.
        _emit(progress_callback,
              "Global candidate search is disabled for safe manual-pose fine alignment.")

    target_points_for_registration = _crop_reference_near_current_source(
        source_points, target_points, progress_callback
    )
    source_down, target_down, voxel_size = _downsample_for_registration(
        source_points, target_points_for_registration, max_registration_points, progress_callback, is_cancelled_callback
    )
    source_down_points = np.asarray(source_down.points)
    target_down_points = np.asarray(target_down.points)
    # Capture the selected cloud's centroid in its *current transformed
    # coordinates* before crops, voxelisation, or correspondence selection.
    # The fine correction therefore rotates around the object the user sees
    # when pressing the button, rather than around the raw-file origin or a
    # centroid that shifts when non-overlap points are excluded.
    optimization_pivot = source_points.mean(axis=0)
    translation_search_extent = float(np.max(translation_limits))
    final_tolerance = _final_alignment_tolerance(voxel_size, translation_search_extent)
    # This is a correspondence gate, not an extra motion allowance.  It is
    # deliberately broad enough to find the manually placed overlap before the
    # optimizer reduces it in its three increasingly strict stages.
    source_pivot = source_down_points.mean(axis=0)
    source_radius = float(np.percentile(np.linalg.norm(source_down_points - source_pivot, axis=1), 95))
    maximum_rotation_sweep = float(2.0 * source_radius * np.sin(
        min(np.linalg.norm(np.radians(rotation_limits_degrees)), np.pi) / 2.0
    ))
    capture_distance = max(float(np.linalg.norm(translation_limits)) + maximum_rotation_sweep, voxel_size * 3.0)
    source_footprint_mask, target_footprint_mask, projected_details = _projected_xy_overlap_masks(
        source_down_points, target_down_points, voxel_size
    )
    if projected_details["projected_overlap_used"]:
        _emit(
            progress_callback,
            "Using shared X-Y footprint: "
            f"{projected_details['projected_source_points']:,} source and "
            f"{projected_details['projected_reference_points']:,} reference points before 3-D matching.",
        )
    source_anchors, target_anchors, anchor_details = _manual_overlap_anchor_sets(
        source_down_points,
        target_down_points,
        capture_distance,
        source_footprint_mask,
        target_footprint_mask,
    )
    anchor_details.update(projected_details)
    # Independently voxelised surveys do not generally have matching voxel
    # centres.  This gate only validates the already frozen footprint; the
    # final optimization stage remains stricter.  It must be wider than one
    # voxel because points on a sloped surface can land in adjacent voxels in
    # each scan even after a good manual placement.
    score_tolerance = max(final_tolerance, voxel_size * 3.0)
    baseline = _anchor_score(source_anchors, target_anchors, np.eye(4), score_tolerance)
    minimum_anchor_overlap = 0.05
    minimum_anchor_matches = max(50, min(500, min(len(source_anchors), len(target_anchors)) // 20))
    baseline_is_valid = (
        np.isfinite(baseline["rmse"])
        and min(baseline["source_overlap"], baseline["reference_overlap"]) >= minimum_anchor_overlap
        and min(baseline["source_matches"], baseline["reference_matches"]) >= minimum_anchor_matches
    )
    _emit(progress_callback,
          f"Frozen manual overlap: {len(source_anchors):,} source and {len(target_anchors):,} reference anchor points.")

    refined, _, optimizer_details = _optimize_local_closest_point_pose(
        source_anchors,
        target_anchors,
        voxel_size,
        capture_distance,
        translation_limits,
        rotation_limits_degrees,
        optimization_pivot,
        progress_callback,
        is_cancelled_callback,
    )
    refined_score = _anchor_score(source_anchors, target_anchors, refined, score_tolerance)
    correction_translation = optimizer_details["translation_correction"]
    correction_rotation = optimizer_details["rotation_correction_degrees"]
    correction_translation_vector = np.asarray(optimizer_details["translation_correction_vector"])
    correction_rotation_vector = np.asarray(optimizer_details["rotation_correction_vector_degrees"])
    candidate_is_valid = (
        np.isfinite(refined_score["rmse"])
        and min(refined_score["source_overlap"], refined_score["reference_overlap"]) >= minimum_anchor_overlap
        and min(refined_score["source_matches"], refined_score["reference_matches"]) >= minimum_anchor_matches
        and np.all(np.abs(correction_translation_vector) <= translation_limits + 1e-9)
        and np.all(np.abs(correction_rotation_vector) <= rotation_limits_degrees + 1e-9)
    )
    if not candidate_is_valid and not baseline_is_valid:
        raise RuntimeError(
            "The local optimizer could not retain enough of the manually selected overlap. "
            "Improve the manual pose, or increase the capture/correction distance only as far as necessary."
        )

    # A small residual reduction on a smooth blade can be a surface slip rather
    # than a better physical pose.  Keep a valid manual placement unless the
    # two-sided anchored score improves by at least two percent and neither
    # directional coverage loses more than two percentage points.
    required_improvement = max(baseline["rmse"] * 0.02, voxel_size * 0.01) if baseline_is_valid else 0.0
    keeps_overlap = (
        refined_score["source_overlap"] >= baseline["source_overlap"] - 0.02
        and refined_score["reference_overlap"] >= baseline["reference_overlap"] - 0.02
    )
    improved = (
        candidate_is_valid
        and baseline_is_valid
        and refined_score["rmse"] <= baseline["rmse"] - required_improvement
        and keeps_overlap
    )

    if improved:
        initialization = "bounded local closest-point optimizer"
        transform = refined
        selected_score = refined_score
        optimizer_details["accepted"] = True
        _emit(progress_callback,
              f"Fine alignment accepted (anchored overlap {selected_score['fitness']:.1%}, "
              f"trimmed RMSE {selected_score['rmse']:.6g}).")
    else:
        initialization = "manual pose retained (no safe measurable improvement)"
        transform = np.eye(4)
        selected_score = baseline
        optimizer_details.update({
            "accepted": False,
            "attempted_translation_correction": correction_translation,
            "attempted_translation_correction_vector": optimizer_details["translation_correction_vector"],
            "attempted_rotation_correction_degrees": correction_rotation,
            "attempted_rotation_correction_vector_degrees": optimizer_details["rotation_correction_vector_degrees"],
            "translation_correction": 0.0,
            "translation_correction_vector": [0.0, 0.0, 0.0],
            "rotation_correction_vector_degrees": [0.0, 0.0, 0.0],
            "rotation_correction_degrees": 0.0,
        })
        _emit(progress_callback,
              "Fine alignment retained the manual pose: the bounded optimization did not improve it safely.")

    baseline_report = {
        **baseline,
        "valid": bool(baseline_is_valid),
    }
    return {
        "transformation": transform,
        "fitness": selected_score["fitness"],
        "inlier_rmse": selected_score["rmse"],
        "voxel_size": voxel_size,
        "source_registration_points": len(source_down_points),
        "target_registration_points": len(target_down_points),
        "target_points_cropped": int(len(target_points_for_registration)),
        "source_anchor_points": int(len(source_anchors)),
        "reference_anchor_points": int(len(target_anchors)),
        "anchor_details": anchor_details,
        "projected_overlap": projected_details,
        "initialization": initialization,
        "candidate_count": 1,
        "search_radius": float(translation_search_extent),
        "translation_limits": [float(value) for value in translation_limits],
        "capture_distance": float(capture_distance),
        "score_tolerance": float(score_tolerance),
        "rotation_limit_degrees": float(np.max(rotation_limits_degrees)),
        "rotation_limits_degrees": [float(value) for value in rotation_limits_degrees],
        "final_tolerance": float(final_tolerance),
        "source_overlap": float(selected_score["source_overlap"]),
        "reference_overlap": float(selected_score["reference_overlap"]),
        "baseline": baseline_report,
        "optimizer": optimizer_details,
    }


def global_automatic_registration(source_df: pd.DataFrame, target_df: pd.DataFrame,
                                  max_registration_points: int = 30_000,
                                  progress_callback: ProgressCallback = None,
                                  is_cancelled_callback: CancelledCallback = None) -> dict:
    """Restore the former broad PCA/centre-of-gravity/FPFH alignment workflow.

    Both data frames are expected to have already passed through the selected
    dataset transforms.  In particular, enabled axis inversions are therefore
    part of the coordinates used for every PCA, feature, ICP, and scoring step.
    This method is intentionally kept separate from bounded manual fine
    alignment because global candidates can be ambiguous on a smooth partial
    blade scan.
    """
    source_points = _points_from_dataframe(source_df)
    target_points = _points_from_dataframe(target_df)
    if len(source_points) < 20 or len(target_points) < 20:
        raise ValueError("Both point clouds need at least 20 finite XYZ points.")

    source_down, target_down, voxel_size = _downsample_for_registration(
        source_points, target_points, max_registration_points, progress_callback, is_cancelled_callback
    )
    _estimate_global_normals(source_down, voxel_size, progress_callback, "source", is_cancelled_callback)
    _estimate_global_normals(target_down, voxel_size, progress_callback, "reference", is_cancelled_callback)

    candidates = [("current manual pose", np.eye(4))]
    candidates.append(("centre-of-gravity translation", _centre_of_gravity_transform(source_down, target_down)))
    for index, transform in enumerate(_best_global_pca_candidates(source_down, target_down, voxel_size), start=1):
        candidates.append((f"PCA orientation + centre of gravity ({index})", transform))

    try:
        source_features = _global_fpfh_features(
            source_down, voxel_size, progress_callback, "source", is_cancelled_callback
        )
        target_features = _global_fpfh_features(
            target_down, voxel_size, progress_callback, "reference", is_cancelled_callback
        )
        _check_cancelled(is_cancelled_callback)
        _emit(progress_callback, "Searching global FPFH correspondences (RANSAC)...")
        registration = _require_open3d().pipelines.registration
        correspondence_distance = voxel_size * 2.5
        ransac = registration.registration_ransac_based_on_feature_matching(
            source_down,
            target_down,
            source_features,
            target_features,
            True,
            correspondence_distance,
            registration.TransformationEstimationPointToPoint(False),
            3,
            [
                registration.CorrespondenceCheckerBasedOnEdgeLength(0.9),
                registration.CorrespondenceCheckerBasedOnDistance(correspondence_distance),
            ],
            registration.RANSACConvergenceCriteria(max_iteration=100_000, confidence=0.999),
        )
        candidates.append(("global FPFH/RANSAC", ransac.transformation))
    except RuntimeError as exc:
        if "Cancelled by User" in str(exc):
            raise
        _emit(progress_callback, f"Skipping FPFH/RANSAC candidate: {exc}")
    except Exception as exc:
        _emit(progress_callback, f"Skipping FPFH/RANSAC candidate: {exc}")

    source_down_points = np.asarray(source_down.points)
    target_down_points = np.asarray(target_down.points)
    results = []
    for name, initial_transform in candidates:
        refined, final_radius = _robust_global_icp(
            source_down,
            target_down,
            initial_transform,
            voxel_size,
            progress_callback,
            is_cancelled_callback,
            name,
        )
        score = _anchor_score(source_down_points, target_down_points, refined, final_radius)
        if np.isfinite(score["rmse"]) and score["source_overlap"] > 0:
            results.append((name, refined, final_radius, score))

    if not results:
        raise RuntimeError("The previous global alignment could not establish any valid closest-point overlap.")

    # Project scans are often smaller than the reference. Prefer coverage of
    # the selected source scan, then residual, while retaining symmetric
    # overlap as a final tie-breaker.
    name, transform, final_radius, score = min(
        results,
        key=lambda item: (-item[3]["source_overlap"], item[3]["rmse"], -item[3]["fitness"]),
    )
    _emit(progress_callback,
          f"Previous global alignment selected {name} (source overlap {score['source_overlap']:.1%}, "
          f"trimmed RMSE {score['rmse']:.6g}).")
    return {
        "transformation": transform,
        "initialization": name,
        "source_overlap": float(score["source_overlap"]),
        "reference_overlap": float(score["reference_overlap"]),
        "symmetric_overlap": float(score["fitness"]),
        "inlier_rmse": float(score["rmse"]),
        "voxel_size": float(voxel_size),
        "final_tolerance": float(final_radius),
        "source_registration_points": int(len(source_down_points)),
        "target_registration_points": int(len(target_down_points)),
        "candidate_count": int(len(results)),
    }


def calculate_cloud_error(source_df: pd.DataFrame, reference_df: pd.DataFrame,
                          max_distance: float, max_analysis_points: int = 250_000,
                          chunk_size: int = 100_000,
                          progress_callback: ProgressCallback = None,
                          is_cancelled_callback: CancelledCallback = None,
                          include_pointwise: bool = False,
                          distance_unit: str = "mm"):
    """Calculate unsigned source-to-reference surface deviations.

    Only source points within ``max_distance`` are included in the error
    statistics. This treats areas outside the partial overlap as non-overlap,
    rather than incorrectly reporting them as a geometric error.
    """
    from scipy.spatial import cKDTree

    source_points = _points_from_dataframe(source_df)
    reference_points = _points_from_dataframe(reference_df)
    if len(source_points) == 0 or len(reference_points) == 0:
        raise ValueError("Both point clouds need finite XYZ points for comparison.")
    if max_distance <= 0:
        raise ValueError("The overlap/error cutoff must be greater than zero.")

    distance_unit = str(distance_unit).strip() or "mm"
    source_total = len(source_points)
    max_analysis_points = int(max_analysis_points)
    sampled = False
    if max_analysis_points > 0 and len(source_points) > max_analysis_points:
        # A fixed seed gives repeatable reports for the same data and settings.
        indices = np.random.default_rng(20260820).choice(len(source_points), max_analysis_points, replace=False)
        source_points = source_points[indices]
        sampled = True

    # A 3-D distance cutoff alone can accept a narrow unsupported scan edge.
    # Check the reference's projected outline first, without cropping valid
    # corners or treating small gaps in the measurement as outside coverage.
    source_footprint, reference_footprint, footprint_details = _comparison_footprint_masks(
        source_points, reference_points
    )
    comparison_reference_points = reference_points[reference_footprint]
    if not len(comparison_reference_points):
        comparison_reference_points = reference_points
        source_footprint = np.zeros(len(source_points), dtype=bool)

    _check_cancelled(is_cancelled_callback)
    _emit(
        progress_callback,
        "Using shared X-Y footprint: "
        f"{int(np.count_nonzero(source_footprint)):,} source and "
        f"{len(comparison_reference_points):,} reference points.",
    )
    _emit(progress_callback, f"Building nearest-neighbour index for {len(comparison_reference_points):,} reference points...")
    reference_tree = cKDTree(comparison_reference_points)
    distances = np.empty(len(source_points), dtype=np.float64)
    distances.fill(np.inf)
    footprint_indices = np.flatnonzero(source_footprint)
    for start in range(0, len(footprint_indices), max(1, int(chunk_size))):
        _check_cancelled(is_cancelled_callback)
        stop = min(start + max(1, int(chunk_size)), len(footprint_indices))
        indices = footprint_indices[start:stop]
        distances[indices], _ = reference_tree.query(
            source_points[indices], k=1, distance_upper_bound=max_distance, workers=-1
        )
        _emit(progress_callback, f"Comparing surface distances: {stop:,} / {len(footprint_indices):,} footprint points...")

    in_overlap = np.isfinite(distances)
    overlap_distances = distances[in_overlap]
    overlap_count = int(len(overlap_distances))
    report = {
        "metric": "unsigned nearest-reference Euclidean distance",
        "unit": distance_unit,
        "source_points_total": int(source_total),
        "source_points_analysed": int(len(source_points)),
        "source_points_sampled": sampled,
        "reference_points_indexed": int(len(comparison_reference_points)),
        "overlap_cutoff": float(max_distance),
        "projected_footprint_used": bool(footprint_details.get("projected_overlap_used", False)),
        "projected_non_overlap_points": int(len(source_points) - np.count_nonzero(source_footprint)),
        "overlap_points": overlap_count,
        "non_overlap_points": int(len(source_points) - overlap_count),
        "overlap_fraction": float(overlap_count / len(source_points)),
    }
    if overlap_count:
        report.update({
            "minimum": float(np.min(overlap_distances)),
            "mean": float(np.mean(overlap_distances)),
            "median": float(np.median(overlap_distances)),
            "rmse": float(np.sqrt(np.mean(np.square(overlap_distances)))),
            "p95": float(np.percentile(overlap_distances, 95)),
            "maximum": float(np.max(overlap_distances)),
        })
    else:
        report.update({"minimum": None, "mean": None, "median": None, "rmse": None, "p95": None, "maximum": None})
    _emit(progress_callback, f"Comparison complete: {report['overlap_fraction']:.1%} overlap.")
    if include_pointwise:
        # Keep the plotting data separate from the compact numeric report. The
        # source points are exactly the ones reported as analysed (including a
        # deterministic analysis sample, when one was requested); ``inf``
        # distances denote non-overlap beyond the cutoff.
        return report, {
            "points": source_points,
            "distances": distances,
        }
    return report


def run_icp(source_df: pd.DataFrame, target_df: pd.DataFrame,
            initial_transform: Optional[np.ndarray] = None,
            max_correspondence_distance: float = 10.0,
            method: str = "Standard ICP", progress_callback: ProgressCallback = None,
            is_cancelled_callback: CancelledCallback = None):
    """Run the legacy manual-hint ICP choices kept for backwards compatibility."""
    o3d = _require_open3d()
    if source_df.empty or target_df.empty:
        return None, 0.0
    _check_cancelled(is_cancelled_callback)
    initial_transform = np.eye(4) if initial_transform is None else initial_transform
    source_points = _points_from_dataframe(source_df)
    target_points = _points_from_dataframe(target_df)
    if len(source_points) == 0 or len(target_points) == 0:
        return None, 0.0

    source_pcd = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(source_points))
    target_pcd = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(target_points))

    if method == "SciPy Custom Optimizer":
        raise ValueError(
            "The unbounded SciPy Custom Optimizer was removed because it can flip a partial cloud. "
            "Use Bounded Manual Fine Alignment instead."
        )
    registration = o3d.pipelines.registration
    if method == "Robust ICP (Partial Overlap)":
        _emit(progress_callback, "Estimating normals for robust ICP...")
        radius = max_correspondence_distance * 5
        source_pcd.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=radius, max_nn=30))
        target_pcd.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=radius, max_nn=30))
        estimation = registration.TransformationEstimationPointToPlane(
            registration.TukeyLoss(k=max_correspondence_distance)
        )
    else:
        estimation = registration.TransformationEstimationPointToPoint()
    _emit(progress_callback, "Running ICP...")
    result = registration.registration_icp(
        source_pcd, target_pcd, max_correspondence_distance, initial_transform,
        estimation, registration.ICPConvergenceCriteria(max_iteration=2_000),
    )
    final_transform = result.transformation
    fitness = float(result.fitness)

    _emit(progress_callback, "ICP complete.")
    return matrix_to_euler_translation(final_transform), fitness
