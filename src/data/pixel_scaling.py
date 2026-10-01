"""One-time conversion of pixel coordinates to millimetres."""

import os
import tempfile

import numpy as np
import pandas as pd


def pixels_to_millimetres(df: pd.DataFrame, pixels_per_mm: float, scale_z: bool = False) -> pd.DataFrame:
    """Convert raw X/Y pixel coordinates, optionally including Z, to mm."""
    pixels_per_mm = float(pixels_per_mm)
    if not np.isfinite(pixels_per_mm) or pixels_per_mm <= 0:
        raise ValueError("Pixels per millimetre must be a finite positive number.")
    columns = ("X", "Y", "Z") if scale_z else ("X", "Y")
    converted = df.copy()
    for column in columns:
        converted[column] = converted[column].astype(float) / pixels_per_mm
    return converted


def save_pixel_scaled_copy(df: pd.DataFrame, filepath: str, pixels_per_mm: float,
                           scale_z: bool = False) -> str:
    """Write a converted CSV copy while leaving the loaded source untouched."""
    if os.path.splitext(filepath)[1].lower() != ".csv":
        raise ValueError("The converted point cloud must be saved as a CSV file.")
    converted = pixels_to_millimetres(df, pixels_per_mm, scale_z)
    directory = os.path.dirname(os.path.abspath(filepath))
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", prefix=".pixel_scale_",
                                         dir=directory, delete=False, encoding="utf-8", newline="") as output:
            temporary_path = output.name
            converted.to_csv(output, index=False)
        os.replace(temporary_path, filepath)
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)
    return filepath
