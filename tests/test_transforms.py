import os
import unittest

import numpy as np
import pandas as pd

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from src.ui.main_window import MainWindow


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


if __name__ == "__main__":
    unittest.main()
