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
            ["Data", "Prepare", "Align", "Evaluate", "Export"],
        )
        self.assertEqual(
            [panel.alignment_tabs.tabText(index) for index in range(panel.alignment_tabs.count())],
            ["Manual transform", "Global alignment"],
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
        panel.comparison_source_combo.setCurrentIndex(0)
        panel.comparison_target_combo.setCurrentIndex(1)
        received = []
        panel.calculate_error_requested.connect(lambda *values: received.append(values))

        panel._on_calculate_error_clicked()

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0][:4], (0, 1, 1.0, 0))
        self.assertEqual(received[0][4:], (True, False, "closest_distance"))
        panel.comparison_colour_mode_combo.setCurrentIndex(1)
        panel._on_calculate_error_clicked()
        self.assertEqual(received[1][-1], "difference_from_mean")
        panel.deleteLater()

    def test_heatmap_max_can_be_set_after_surface_error(self):
        panel = ControlPanel()
        received = []
        panel.error_map_max_changed.connect(received.append)
        panel.add_dataset_to_list("project")
        panel.add_dataset_to_list("reference")
        self.assertTrue(panel.error_map_max_spin.isEnabled())
        self.assertEqual(panel.error_map_max_spin.value(), 0.0)
        panel.set_error_map_display_state(True, True, heatmap_max=2.5)
        self.assertEqual(panel.error_map_max_spin.value(), 2.5)
        self.assertEqual(received, [])
        panel.error_map_max_spin.setValue(3.0)
        self.assertEqual(received, [3.0])
        panel.deleteLater()

    def test_surface_error_has_separate_source_and_reference_selectors(self):
        panel = ControlPanel()
        panel.add_dataset_to_list("project")
        panel.add_dataset_to_list("reference")

        self.assertEqual(panel.comparison_source_combo.currentIndex(), 0)
        self.assertEqual(panel.comparison_target_combo.currentIndex(), 1)
        self.assertTrue(panel.comparison_target_combo.model().item(0).isEnabled())
        self.assertTrue(panel.comparison_source_combo.model().item(1).isEnabled())

        panel.comparison_source_combo.setCurrentIndex(1)
        self.assertEqual(panel.comparison_source_combo.currentIndex(), 1)
        self.assertEqual(panel.comparison_target_combo.currentIndex(), 0)
        panel.comparison_target_combo.setCurrentIndex(1)
        self.assertEqual(panel.comparison_source_combo.currentIndex(), 0)
        self.assertEqual(panel.comparison_target_combo.currentIndex(), 1)
        panel.deleteLater()

    def test_distance_unit_defaults_to_mm_and_is_saved_with_dataset_settings(self):
        panel = ControlPanel()
        self.assertEqual(panel.distance_unit_combo.currentText(), "mm")
        panel.distance_unit_combo.setCurrentText("m")

        self.assertEqual(panel.get_current_settings()["distance_unit"], "m")
        self.assertEqual(panel.tx_label.text(), "Translate X (m):")
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

    def test_error_map_colour_mode_emits_the_selected_metric(self):
        panel = ControlPanel()
        panel.add_dataset_to_list("project")
        panel.dataset_list.setCurrentRow(0)
        panel.set_error_map_display_state(True, True)
        received = []
        panel.error_map_colour_mode_changed.connect(received.append)

        panel.error_map_colour_mode_combo.setCurrentIndex(1)

        self.assertEqual(received, ["difference_from_mean"])
        panel.deleteLater()

    def test_camera_angle_controls_read_and_emit_explicit_orientation(self):
        panel = ControlPanel()
        panel.set_camera_angles(12.5, -34.0, 7.5)
        received = []
        panel.camera_angles_requested.connect(lambda *angles: received.append(angles))

        panel._on_apply_camera_angles_clicked()

        self.assertEqual(received, [(12.5, -34.0, 7.5)])
        panel.deleteLater()

    def test_export_options_collect_heatmap_axis_and_legend_settings(self):
        panel = ControlPanel()
        panel.export_heatmap_check.setChecked(False)
        panel.export_heightmap_check.setChecked(True)
        panel.export_heatmap_colormap_combo.setCurrentText("magma")
        panel.export_heightmap_colormap_combo.setCurrentText("cividis")
        panel.export_colourbar_height_spin.setValue(0.65)
        panel.export_colourbar_decimals_spin.setValue(4)
        panel.export_point_size_spin.setValue(0.4)
        panel.export_x_axis_name.setText("Chord (mm)")
        panel.export_legend_point_size_spin.setValue(25.0)
        panel.export_legend_title.setText("Measurements")
        panel.export_legend_labels.setPlainText("raw = Reference\nscan = Project scan")
        panel.export_legend_position_combo.setCurrentIndex(
            panel.export_legend_position_combo.findData("lower left")
        )
        panel.export_legend_placement_combo.setCurrentIndex(
            panel.export_legend_placement_combo.findData("outside")
        )

        options = panel.get_export_options()

        self.assertFalse(options["use_heatmap"])
        self.assertTrue(options["use_heightmap"])
        self.assertEqual(options["heatmap_colormap"], "magma")
        self.assertEqual(options["heightmap_colormap"], "cividis")
        self.assertEqual(options["colourbar_decimals"], 4)
        self.assertEqual(options["point_size"], 0.4)
        self.assertEqual(options["x_label"], "Chord (mm)")
        self.assertEqual(options["legend_title"], "Measurements")
        self.assertEqual(options["legend_point_size"], 25.0)
        self.assertEqual(options["legend_position"], "lower left")
        self.assertEqual(options["legend_placement"], "outside")
        self.assertEqual(options["legend_labels"], {"raw": "Reference", "scan": "Project scan"})
        restored = ControlPanel()
        restored.apply_export_options(options)
        self.assertEqual(restored.export_colourbar_decimals_spin.value(), 4)
        restored.deleteLater()
        panel.deleteLater()

    def test_error_and_height_export_maps_are_mutually_exclusive(self):
        panel = ControlPanel()
        panel.export_heightmap_check.setChecked(True)
        self.assertFalse(panel.export_heatmap_check.isChecked())
        panel.export_heatmap_check.setChecked(True)
        self.assertFalse(panel.export_heightmap_check.isChecked())
        panel.deleteLater()

    def test_z_axis_export_spacing_and_tick_count_are_saved_and_restored(self):
        import json
        panel = ControlPanel()
        restored = ControlPanel()
        try:
            panel.export_z_label_spacing_spin.setValue(18.0)
            panel.export_z_tick_label_gap_spin.setValue(30.0)
            panel.export_z_ticks_spin.setValue(5)
            panel.export_z_tick_interval_spin.setValue(10)
            options = json.loads(json.dumps(panel.get_export_options()))
            self.assertEqual(options["z_axis_ticks"], 5)
            self.assertEqual(options["z_axis_tick_interval"], 10)
            self.assertEqual(options["z_axis_tick_label_gap"], 30)
            restored.apply_export_options(options)
            self.assertEqual(restored.export_z_label_spacing_spin.value(), 18.0)
            self.assertEqual(restored.export_z_tick_label_gap_spin.value(), 30.0)
            self.assertEqual(restored.export_z_ticks_spin.value(), 5)
            self.assertEqual(restored.export_z_tick_interval_spin.value(), 10)
            self.assertFalse(restored.export_z_ticks_spin.isEnabled())
            restored.apply_export_options({"z_axis_max_ticks": 4})
            self.assertEqual(restored.export_z_ticks_spin.value(), 4)
            self.assertEqual(restored.export_z_tick_interval_spin.value(), 0)
            self.assertEqual(restored.export_z_tick_label_gap_spin.value(), 0)
            self.assertTrue(restored.export_z_ticks_spin.isEnabled())
            restored.apply_export_options({"z_axis_ticks": 7, "z_axis_max_ticks": 4})
            self.assertEqual(restored.export_z_ticks_spin.value(), 7)
            restored.apply_export_options({})
            self.assertEqual(restored.export_z_label_spacing_spin.value(), 0)
            self.assertEqual(restored.export_z_ticks_spin.value(), 0)
        finally:
            panel.deleteLater()
            restored.deleteLater()

    def test_plain_export_legend_labels_follow_visible_cloud_order(self):
        panel = ControlPanel()
        panel.add_dataset_to_list("reference")
        panel.add_dataset_to_list("scan")
        panel.export_legend_labels.setPlainText("Reference surface\nMeasured cloud")

        self.assertEqual(
            panel.get_export_options()["legend_labels"],
            {"reference": "Reference surface", "scan": "Measured cloud"},
        )
        panel.deleteLater()

    def test_export_settings_restore_every_legend_label_line(self):
        import json

        panel = ControlPanel()
        panel.add_dataset_to_list("source")
        original_text = "Source surface\nOutside reference range\nreference = Reference scan"
        panel.export_legend_labels.setPlainText(original_text)
        saved_options = json.loads(json.dumps(panel.get_export_options()))
        self.assertEqual(saved_options["legend_labels_text"], original_text)

        restored = ControlPanel()
        restored.apply_export_options(saved_options)
        self.assertEqual(restored.export_legend_labels.toPlainText(), original_text)

        old_options = dict(saved_options)
        old_options.pop("legend_labels_text")
        restored.apply_export_options(old_options)
        self.assertEqual(
            restored.export_legend_labels.toPlainText(),
            original_text,
        )
        restored.deleteLater()
        panel.deleteLater()

    def test_loading_clouds_adds_editable_legend_label_rows(self):
        panel = ControlPanel()
        panel.add_dataset_to_list("reference.csv")
        panel.add_dataset_to_list("scan.csv")

        panel.export_legend_labels.setPlainText(
            "Reference surface\nMeasured surface"
        )
        self.assertEqual(
            panel.get_export_options()["legend_labels"],
            {"reference.csv": "Reference surface", "scan.csv": "Measured surface"},
        )
        self.assertEqual(
            panel.get_export_options()["legend_label_lines"],
            ["Reference surface", "Measured surface"],
        )
        panel.deleteLater()

    def test_move_controls_emit_a_list_reorder_and_keep_reference_selectors_in_sync(self):
        panel = ControlPanel()
        panel.add_dataset_to_list("project")
        panel.add_dataset_to_list("reference")
        panel.add_dataset_to_list("check")
        panel.dataset_list.setCurrentRow(1)
        received = []
        panel.move_dataset_requested.connect(lambda *values: received.append(values))

        panel._on_move_up_clicked()
        panel.move_dataset_in_list(1, 0)

        self.assertEqual(received, [(1, 0)])
        self.assertEqual(
            [panel.dataset_list.item(index).text() for index in range(panel.dataset_list.count())],
            ["reference", "project", "check"],
        )
        self.assertEqual(
            [panel.comparison_target_combo.itemText(index) for index in range(panel.comparison_target_combo.count())],
            ["reference", "project", "check"],
        )
        panel.deleteLater()


if __name__ == "__main__":
    unittest.main()
