"""Create centred, self-contained copies of point clouds."""

import os
from typing import Tuple

import numpy as np
import pandas as pd


def centre_point_cloud(df: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray]:
    """Return a copy translated so its finite XYZ centroid is at the origin."""
    points = df[["X", "Y", "Z"]].to_numpy(dtype=np.float64, copy=False)
    finite = np.isfinite(points).all(axis=1)
    if not finite.any():
        raise ValueError("The point cloud does not contain any finite XYZ points.")

    centroid = points[finite].mean(axis=0)
    centred = df.copy()
    for index, column in enumerate(("X", "Y", "Z")):
        # Keep the compact float32 representation used by the supplied PLYs.
        centred[column] = (centred[column].astype(np.float32) - centroid[index]).astype(np.float32)
    return centred, centroid


def get_centred_filename(original_filepath: str) -> str:
    """Return a sibling output path without changing the source file."""
    directory = os.path.join(os.path.dirname(original_filepath), "centered")
    os.makedirs(directory, exist_ok=True)
    name, extension = os.path.splitext(os.path.basename(original_filepath))
    return os.path.join(directory, f"{name}_centered{extension.lower()}")


def _ply_property_type(dtype: np.dtype) -> Tuple[str, np.dtype]:
    """Map a dataframe numeric dtype to the PLY types this app can read."""
    dtype = np.dtype(dtype)
    if dtype.kind == "f":
        return "float", np.dtype("<f4")
    if dtype.kind == "u" and dtype.itemsize == 1:
        return "uchar", np.dtype("u1")
    if dtype.kind in {"i", "u", "b"}:
        return "int", np.dtype("<i4")
    raise ValueError(f"PLY export does not support non-numeric column dtype {dtype}.")


def save_centred_point_cloud(df: pd.DataFrame, original_filepath: str, centroid: np.ndarray,
                             distance_unit: str = "mm") -> str:
    """Save a centred copy in the source format, preserving extra numeric PLY columns."""
    output_filepath = get_centred_filename(original_filepath)
    extension = os.path.splitext(original_filepath)[1].lower()

    if extension == ".csv":
        df.to_csv(output_filepath, index=False)
        return output_filepath
    if extension != ".ply":
        raise ValueError(f"Unsupported point-cloud format: {extension}")

    fields = []
    properties = []
    for column in df.columns:
        property_name = column.lower() if column in {"X", "Y", "Z"} else column
        property_type, dtype = _ply_property_type(df[column].dtype)
        fields.append((property_name, dtype))
        properties.append((property_type, property_name, column))

    records = np.empty(len(df), dtype=np.dtype(fields))
    for _, property_name, column in properties:
        records[property_name] = df[column].to_numpy(dtype=records.dtype[property_name], copy=False)

    header = [
        "ply",
        "format binary_little_endian 1.0",
        f"comment centred copy; original XYZ centroid ({str(distance_unit).strip() or 'mm'}): "
        + " ".join(f"{value:.9g}" for value in centroid),
        f"element vertex {len(records)}",
    ]
    header.extend(f"property {property_type} {property_name}" for property_type, property_name, _ in properties)
    header.append("end_header")

    with open(output_filepath, "wb") as output:
        output.write(("\n".join(header) + "\n").encode("ascii"))
        records.tofile(output)
    return output_filepath
