import os
import tempfile
import unittest

import pandas as pd
from pandas.testing import assert_frame_equal

from src.data.pixel_scaling import pixels_to_millimetres, save_pixel_scaled_copy


class PixelScalingTests(unittest.TestCase):
    def test_xy_conversion_uses_inverse_pixels_per_mm_and_preserves_z(self):
        original = pd.DataFrame({"X": [2.1, 4.2], "Y": [-4.2, 0.0], "Z": [12.5, 13.0], "quality": [1, 2]})

        converted = pixels_to_millimetres(original, 2.1)

        assert_frame_equal(converted, pd.DataFrame({
            "X": [1.0, 2.0], "Y": [-2.0, 0.0], "Z": [12.5, 13.0], "quality": [1, 2]
        }))
        self.assertEqual(original.loc[0, "X"], 2.1)
        self.assertAlmostEqual(pixels_to_millimetres(original, 2.1, scale_z=True).loc[0, "Z"], 12.5 / 2.1)

    def test_saved_copy_round_trips_without_changing_source(self):
        original = pd.DataFrame({"X": [2.1], "Y": [4.2], "Z": [8.0]})
        with tempfile.TemporaryDirectory() as directory:
            filepath = os.path.join(directory, "converted.csv")
            save_pixel_scaled_copy(original, filepath, 2.1)
            saved = pd.read_csv(filepath)
        assert_frame_equal(saved, pd.DataFrame({"X": [1.0], "Y": [2.0], "Z": [8.0]}))
        self.assertEqual(original.loc[0, "X"], 2.1)

    def test_invalid_pixels_per_mm_is_rejected(self):
        original = pd.DataFrame({"X": [1.0], "Y": [1.0], "Z": [1.0]})
        for value in (0, -2.1, float("nan")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                pixels_to_millimetres(original, value)
