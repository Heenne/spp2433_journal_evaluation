import json
import os
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QRect

from src.ui.main_window import MainWindow


class ApplicationShellTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_main_window_keeps_plot_visible_with_project_sidebar_and_workflow_sections(self):
        window = MainWindow()
        try:
            self.assertEqual(window.windowTitle(), "SPP 2433 - Point Cloud Evaluation")
            self.assertEqual(
                [window.control_panel.tabs.tabText(index) for index in range(window.control_panel.tabs.count())],
                ["Data", "Preview Plot", "Filter", "Manual Align", "Auto Align", "Evaluate", "Export"],
            )
            self.assertIsNotNone(window.plot_canvas.parent())
            self.assertEqual(window.control_panel.dataset_group.title(), "Point Clouds")
            self.assertEqual(window.control_panel.btn_add.toolTip(), "Add point cloud")
            self.assertIsNot(window.control_panel.dataset_group.parent(), window.control_panel)
            self.assertEqual(window.workspace_splitter.handleWidth(), 6)
            self.assertEqual(
                [action.text() for action in window.export_menu.actions() if not action.isSeparator()],
                ["Export filtered", "Export centered"],
            )
            window.set_language("de", persist=False)
            self.assertTrue(window.language_actions["de"].isChecked())
            self.assertFalse(window.language_actions["en"].isChecked())
            self.assertEqual(window.export_button.text(), "Punktwolke exportieren")
            self.assertEqual(window.control_panel.tab_buttons[0].text(), "Daten")
            self.assertTrue(window.control_panel.btn_apply_camera_angles.icon().isNull())
        finally:
            window.deleteLater()

    def test_initial_window_is_centred_with_space_around_it(self):
        available = QRect(1920, 40, 1536, 824)
        geometry = MainWindow._initial_geometry(available)
        self.assertLess(geometry.width(), available.width())
        self.assertLess(geometry.height(), available.height())
        self.assertAlmostEqual(geometry.center().x(), available.center().x(), delta=1)
        self.assertAlmostEqual(geometry.center().y(), available.center().y(), delta=1)
        self.assertGreaterEqual(geometry.left(), available.left())
        self.assertLessEqual(geometry.right(), available.right())

    def test_theme_selection_is_applied_to_plot_and_persisted(self):
        original_stylesheet = self.app.styleSheet()
        with tempfile.TemporaryDirectory() as directory:
            settings_path = os.path.join(directory, "settings.json")
            with patch("src.utils.app_settings.SETTINGS_FILE", settings_path):
                window = MainWindow()
                try:
                    window.set_theme("dark")
                    self.assertEqual(window.theme, "dark")
                    self.assertEqual(window.plot_canvas.theme, "dark")
                    self.assertTrue(window.dark_theme_action.isChecked())
                    with open(settings_path, encoding="utf-8") as settings_file:
                        self.assertEqual(json.load(settings_file)["theme"], "dark")

                    window.set_theme("light")
                    self.assertEqual(window.plot_canvas.theme, "light")
                    self.assertTrue(window.light_theme_action.isChecked())
                    self.assertIn("#f7f8fa", self.app.styleSheet())
                finally:
                    window.deleteLater()
        self.app.setStyleSheet(original_stylesheet)

    def test_workspace_tabs_have_usable_scroll_arrows(self):
        window = MainWindow()
        try:
            window.resize(1280, 800)
            window.show()
            self.app.processEvents()
            panel = window.control_panel
            left = panel.tab_scroll_left
            right = panel.tab_scroll_right
            self.assertEqual(left.size().width(), 44)
            self.assertEqual(right.size().width(), 44)
            self.assertLess(left.mapTo(panel.tab_navigation, left.rect().topLeft()).x(),
                            right.mapTo(panel.tab_navigation, right.rect().topLeft()).x())
            scrollbar = panel.tab_strip_scroll.horizontalScrollBar()
            before = scrollbar.value()
            active = panel.tabs.currentIndex()
            right.click()
            self.app.processEvents()
            self.assertGreater(scrollbar.value(), before)
            self.assertEqual(panel.tabs.currentIndex(), active)
            panel.tab_buttons[-1].click()
            self.app.processEvents()
            self.assertEqual(panel.tabs.currentIndex(), panel.tabs.count() - 1)
            last = panel.tab_buttons[-1]
            self.assertLessEqual(last.x() + last.width(),
                                 scrollbar.value() + panel.tab_strip_scroll.viewport().width())
        finally:
            window.deleteLater()

    def test_workspace_pages_fit_the_available_width_in_both_languages(self):
        window = MainWindow()
        try:
            window.resize(1280, 800)
            window.show()
            panel = window.control_panel
            panel.add_dataset_to_list("Source")
            panel.add_dataset_to_list("Reference")
            for language in ("en", "de"):
                window.set_language(language, persist=False)
                for index in range(panel.tabs.count()):
                    with self.subTest(language=language, tab=panel.tabs.tabText(index)):
                        panel.tabs.setCurrentIndex(index)
                        self.app.processEvents()
                        scroll = panel.tabs.widget(index)
                        self.assertLessEqual(scroll.widget().width(), scroll.viewport().width())
                        if index == 3:
                            for method in range(panel.alignment_method_combo.count()):
                                panel.alignment_method_combo.setCurrentIndex(method)
                                self.app.processEvents()
                                self.assertLessEqual(scroll.widget().width(), scroll.viewport().width())
        finally:
            window.deleteLater()


if __name__ == "__main__":
    unittest.main()
