"""Shared display/export normalization; never changes error statistics."""
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, Normalize, TwoSlopeNorm


def error_map_colours(distances, error_map, colormap=None, *, normalization_distances=None):
    """Colour rendered points using optional full-data automatic scale limits."""
    values = np.asarray(distances, dtype=float)
    scale_values = values if normalization_distances is None else np.asarray(normalization_distances, dtype=float)
    signed = error_map.get("error_method", "unsigned") == "signed_normal"
    centred = error_map.get("colour_mode") == "difference_from_mean"
    mean = error_map.get("mean")
    if centred and mean is not None and np.isfinite(mean):
        values = values - mean
        scale_values = values if normalization_distances is None else scale_values - mean
    else:
        centred = False
    divergent = signed or centred
    maximum = float(error_map.get("heatmap_max", 0.0))
    mode = error_map.get("scale_mode", "auto")
    if mode == "manual":
        lower, upper = float(error_map.get("heatmap_min", -1.0)), maximum
        if not np.isfinite([lower, upper]).all() or lower >= upper:
            raise ValueError("Heatmap minimum must be smaller than its maximum.")
    elif mode == "symmetric" or divergent:
        if maximum < 0:
            raise ValueError("A symmetric heatmap maximum must be nonnegative.")
        limit = max(maximum or float(np.percentile(np.abs(scale_values), 95)), np.finfo(float).eps)
        lower, upper = -limit, limit
    else:
        if maximum < 0:
            raise ValueError("An automatic heatmap maximum must be nonnegative.")
        upper = max(maximum or float(error_map.get("p95") or np.percentile(scale_values, 95)), np.finfo(float).eps)
        lower = 0.0
    cmap = colormap or "auto"
    if cmap == "auto":
        cmap = "blue_white_red" if divergent else "turbo"
    if cmap in ("blue_white_red", "blue_beige_red"):
        if cmap == "blue_beige_red":
            base = LinearSegmentedColormap.from_list(
                "blue_beige_red",
                [(0.00, "#2166AC"), (0.25, "#87B5D3"), (0.50, "#C9BFB0"),
                 (0.75, "#DB9494"), (1.00, "#B2182B")],
                N=256,
            )
        else:
            base = LinearSegmentedColormap.from_list("signed_blue_white_red", ["blue", "white", "red"], N=257)
        if lower < 0 < upper:
            norm = TwoSlopeNorm(vcenter=0.0, vmin=lower, vmax=upper)
            cmap = base
        else:
            # One-sided ranges retain the appropriate half of the diverging palette.
            extent = max(abs(lower), abs(upper))
            colours = base((np.linspace(lower, upper, 257) / extent + 1.0) / 2.0)
            cmap = LinearSegmentedColormap.from_list("one_sided_signed", colours, N=257)
            norm = Normalize(vmin=lower, vmax=upper)
    else:
        norm = Normalize(vmin=lower, vmax=upper)
    label = "Signed normal deviation" if signed else "Unsigned distance to reference"
    if centred:
        label += " minus mean"
    label += f" ({error_map.get('unit', 'mm')}; colours clipped)"
    return values, {"cmap": cmap, "norm": norm}, label, (0.0 if centred else mean)
