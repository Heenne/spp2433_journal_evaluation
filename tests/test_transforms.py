import os
import unittest

import numpy as np
import pandas as pd
from scipy.spatial.transform import Rotation

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from src.ui.main_window import MainWindow
from src.utils.registration import euler_translation_to_matrix, matrix_to_euler_translation, transform_points


class CoordinateConventionTransformTests(unittest.TestCase):
    def test_axis_inversion_is_applied_before_scale_and_pose(self):
        cloud = pd.DataFrame([[1.0, 2.0, 3.0]], columns=["X", "Y", "Z"])
        settings = {
            "invert_z": True,
            "scale": 2.0,
            "tx": 5.0,
            "ty": -1.0,
            "tz": 0.5,
            "rx": 0.0,
            "ry": 0.0,
            "rz": 0.0,
        }

        transformed = MainWindow.apply_transform(None, cloud, settings)

        np.testing.assert_allclose(transformed[["X", "Y", "Z"]].to_numpy(), [[7.0, 3.0, -5.5]])

    def test_saved_fine_alignment_composes_with_the_current_transformed_pose(self):
        raw = pd.DataFrame(
            [[1.0, 2.0, 3.0], [-2.0, 0.5, 4.0], [3.0, -1.0, -2.0]], columns=["X", "Y", "Z"]
        )
        settings = {
            "invert_z": True, "scale": 2.0,
            "tx": 7.0, "ty": -4.0, "tz": 1.5,
            "rx": 3.0, "ry": -2.0, "rz": 5.0,
        }
        initially_transformed = MainWindow.apply_transform(None, raw, settings)
        initial_points = initially_transformed[["X", "Y", "Z"]].to_numpy()
        pivot = initial_points.mean(axis=0)
        delta_rotation = Rotation.from_euler("xyz", [0.5, -0.3, 0.8], degrees=True).as_matrix()
        delta = np.eye(4)
        delta[:3, :3] = delta_rotation
        delta[:3, 3] = pivot + np.array([0.2, -0.1, 0.3]) - delta_rotation @ pivot

        current = euler_translation_to_matrix(
            settings["tx"], settings["ty"], settings["tz"], settings["rx"], settings["ry"], settings["rz"]
        )
        tx, ty, tz, rx, ry, rz = matrix_to_euler_translation(delta @ current)
        saved_settings = {**settings, "tx": tx, "ty": ty, "tz": tz, "rx": rx, "ry": ry, "rz": rz}

        expected = transform_points(initial_points, delta)
        actual = MainWindow.apply_transform(None, raw, saved_settings)[["X", "Y", "Z"]].to_numpy()
        np.testing.assert_allclose(actual, expected, atol=1e-10)


if __name__ == "__main__":
    unittest.main()
