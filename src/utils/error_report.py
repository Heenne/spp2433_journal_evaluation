"""Derived surface-deviation statistics and consistent report formatting."""
import math


def update_report_metrics(report, axial_range=None):
    """Normalize the sample SD without changing the evaluated deviations."""
    value = report.get("axial_range") if axial_range is None else axial_range
    value = float(value or 0.0)
    if not math.isfinite(value) or value < 0:
        raise ValueError("Axial range must be a finite, nonnegative span in the error distance unit.")
    report["axial_range"] = value or None
    sd = report.get("standard_deviation")
    report["normalized_standard_deviation_percent"] = 100.0 * sd / value if sd is not None and value > 0 else None
    for probability, low, high in ((90, "p5", "p95"), (95, "p2_5", "p97_5")):
        report[f"coverage_interval_{probability}"] = (
            [report[low], report[high]] if report.get(low) is not None and report.get(high) is not None else None
        )


def report_method(report):
    return report.get("error_method", "signed_normal" if str(report.get("metric", "")).startswith("signed") else "unsigned")


def report_status(report, options=None):
    if not isinstance(report, dict):
        return "No results — calculate surface error", False, "empty"
    if options:
        method = report_method(report)
        previous = {
            **({"reference_filepath": report["reference_filepath"]} if "reference_filepath" in report else {}),
            **({"edge_margin": report["reference_edge_margin_setting"]} if "reference_edge_margin_setting" in report else {}),
            **report.get("calculation_settings", {}),
        }
        keys = ["reference_filepath", "edge_margin", "max_analysis_points", "error_method"]
        if method == "signed_normal":
            keys += ["normal_radius", "normal_neighbours", "normal_orientation"]
        changed = options.get("error_method", method) != method
        changed |= any(key in previous and key in options and previous[key] != options[key] for key in keys)
        if changed:
            return "Previous results available — settings changed; recalculate", True, "warning"
    if report.get("evaluated_points", 0) == 0:
        return "Report available — no valid comparison points", True, "warning"
    if "standard_deviation" not in report or report.get("p5") is None:
        return "Saved report available — missing statistics; recalculate", True, "warning"
    if report.get("standard_deviation") is None:
        return "Results available — SD requires at least two points", True, "warning"
    if not report.get("axial_range"):
        return "Results available — set axial range for normalized SD", True, "warning"
    return "Results available", True, "ready"


def number(value):
    return f"{value:.6g}" if value is not None else "—"


def interval(report, low="p5", high="p95"):
    if report.get(low) is None or report.get(high) is None:
        return "—"
    return f"[{number(report[low])}; {number(report[high])}] {report.get('unit', 'mm')}"


def headline_rows(report):
    unit = report.get("unit", "mm")
    point_fraction = report.get("system_points_within_reference_area_fraction", report.get("overlap_fraction"))
    area_fraction = report.get("reference_area_covered_fraction")
    sd = report.get("standard_deviation")
    return [
        ("System-point fraction", f"{100*point_fraction:.1f} %" if point_fraction is not None else "—"),
        ("Reference-area coverage", f"{100*area_fraction:.1f} %" if area_fraction is not None else "—"),
        ("[P5; P95] — central 90%", interval(report)),
        ("Standard deviation", f"{number(sd)} {unit}" if sd is not None else "—"),
        ("Normalized SD / axial range", f"{number(report.get('normalized_standard_deviation_percent'))} %"
         if report.get("normalized_standard_deviation_percent") is not None else "— (set axial range)"
         if sd is not None and not report.get("axial_range") else "—"),
    ]
