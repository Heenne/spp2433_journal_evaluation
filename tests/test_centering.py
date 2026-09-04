import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from src.data.centering import centre_point_cloud, save_centred_point_cloud
from src.data.parser import parse_point_cloud_file


class CentringTests(unittest.TestCase):
    def test_centre_point_cloud_moves_xyz_centroid_to_origin_and_keeps_attributes(self):
        source = pd.DataFrame({
            "X": np.array([10.0, 12.0], dtype=np.float32),
            "Y": np.array([-5.0, -1.0], dtype=np.float32),
            "Z": np.array([2700.0, 2720.0], dtype=np.float32),
            "red": np.array([2, 9], dtype=np.uint8),
        })
        centred, centroid = centre_point_cloud(source)

        np.testing.assert_allclose(centroid, [11.0, -3.0, 2710.0])
        np.testing.assert_allclose(centred[["X", "Y", "Z"]].mean(), [0.0, 0.0, 0.0])
        np.testing.assert_array_equal(centred["red"], source["red"])
        np.testing.assert_allclose(source["Z"], [2700.0, 2720.0])

    def test_save_centred_ply_can_be_loaded_again(self):
        source = pd.DataFrame({
            "X": np.array([10.0, 12.0], dtype=np.float32),
            "Y": np.array([-5.0, -1.0], dtype=np.float32),
            "Z": np.array([2700.0, 2720.0], dtype=np.float32),
            "red": np.array([2, 9], dtype=np.uint8),
        })
        centred, centroid = centre_point_cloud(source)
        with tempfile.TemporaryDirectory() as directory:
            original = Path(directory) / "source.ply"
            original.touch()
            saved = save_centred_point_cloud(centred, str(original), centroid)
            loaded, attributes, error = parse_point_cloud_file(saved)

        self.assertEqual(error, "")
        self.assertEqual(attributes, ["red"])
        np.testing.assert_allclose(loaded[["X", "Y", "Z"]].mean(), [0.0, 0.0, 0.0])
        np.testing.assert_array_equal(loaded["red"], [2, 9])
