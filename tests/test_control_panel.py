import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from src.ui.control_panel import ControlPanel


class ManualFineAlignmentControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_manual_fine_alignment_emits_bounded_pose_parameters(self):
        panel = ControlPanel()
        self.assertEqual(
            [panel.tabs.tabText(index) for index in range(panel.tabs.count())],
            ["Data & Display", "Filtering", "Manual Transform", "Legacy Alignment", "Fine Align & Error"],
        )
        panel.add_dataset_to_list("project")
        panel.add_dataset_to_list("reference")
        panel.dataset_list.setCurrentRow(0)
        panel.legacy_global_target_combo.setCurrentIndex(1)
        panel.auto_target_combo.setCurrentIndex(1)
        received = []
        received_global = []
        panel.run_auto_alignment_requested.connect(lambda *values: received.append(values))
        panel.run_legacy_global_alignment_requested.connect(lambda *values: received_global.append(values))

        panel._on_run_legacy_global_alignment_clicked()
        panel._on_run_auto_alignment_clicked()

        self.assertEqual(received_global, [(0, 1, 30_000)])
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0][:3], (0, 1, 30_000))
        self.assertEqual(received[0][3:], (10.0, 10.0, 10.0, 5.0, 5.0, 5.0))
        self.assertFalse(hasattr(panel, "auto_global_check"))
        panel.deleteLater()

    def test_surface_error_requests_a_pointwise_colour_map_by_default(self):
        panel = ControlPanel()
        panel.add_dataset_to_list("project")
        panel.add_dataset_to_list("reference")
        panel.dataset_list.setCurrentRow(0)
        panel.comparison_target_combo.setCurrentIndex(1)
        received = []
        panel.calculate_error_requested.connect(lambda *values: received.append(values))

        panel._on_calculate_error_clicked()

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0][:4], (0, 1, 1.0, 250_000))
        self.assertEqual(received[0][4:], (True, False))
        panel.deleteLater()

    def test_error_map_display_switch_is_disabled_until_a_map_exists(self):
        panel = ControlPanel()
        panel.add_dataset_to_list("project")
        panel.dataset_list.setCurrentRow(0)
        panel.set_error_map_display_state(False)
        self.assertFalse(panel.analysis_display_group.isEnabled())

        received = []
        panel.error_map_display_changed.connect(received.append)
        panel.set_error_map_display_state(True, True)
        self.assertTrue(panel.analysis_display_group.isEnabled())
        self.assertTrue(panel.show_error_map_check.isChecked())
        self.assertEqual(received, [])
        panel.show_error_map_check.setChecked(False)
        self.assertEqual(received, [False])
        panel.deleteLater()


if __name__ == "__main__":
    unittest.main()
