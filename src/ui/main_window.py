import os
import pandas as pd
import numpy as np
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFileDialog, 
    QMessageBox, QMenu, QApplication, QProgressBar, QPushButton, QSplitter,
    QToolBar, QToolButton, QStyle
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from src.ui.plot_canvas import PlotCanvas
from src.ui.control_panel import ControlPanel
from src.data.parser import parse_point_cloud_file
from src.data.filter import (
    check_cached_filtered_files, 
    save_filtered_data, load_filter_config, save_filter_config,
    filter_by_zscore, filter_by_bounding_box, filter_by_sor, filter_by_voxel_grid
)
from src.data.centering import centre_point_cloud, save_centred_point_cloud
from src.utils.registration import (
    run_icp, automatic_registration, global_automatic_registration, calculate_cloud_error,
    euler_translation_to_matrix, matrix_to_euler_translation,
)
from src.utils.worker import WorkerThread
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar


class PointCloudNavigationToolbar(NavigationToolbar):
    """Make the standard Home button fit all plotted point-cloud data."""

    def home(self, *args):
        self.canvas.reset_view_to_data()
        self.push_current()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Point Cloud Data Viewer")
        self.resize(1100, 750)
        
        self.datasets = []
        self.project_filepath = None
        self.project_dirty = False
        
        self.init_ui()
        
    def init_ui(self):
        # Main app actions live in an icon toolbar rather than a traditional
        # menu bar. Text remains available through tooltips and accessible
        # action names.
        self.menuBar().hide()
        self.app_toolbar = QToolBar("Project", self)
        self.app_toolbar.setMovable(False)
        self.app_toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.app_toolbar)

        def toolbar_action(icon, text, callback, shortcut=None):
            action = QAction(icon, text, self)
            action.setToolTip(text)
            action.setStatusTip(text)
            if shortcut:
                action.setShortcut(shortcut)
            action.triggered.connect(callback)
            self.app_toolbar.addAction(action)
            return action

        style = self.style()
        self.open_data_action = toolbar_action(
            style.standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton), "Open point cloud…", self.open_file_dialog,
            "Ctrl+O",
        )
        self.open_project_action = toolbar_action(
            style.standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon), "Open project…", self.open_project_dialog,
            "Ctrl+Shift+O",
        )
        self.save_project_action = toolbar_action(
            style.standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton), "Save project", self.save_project,
            "Ctrl+S",
        )
        self.save_as_project_action = toolbar_action(
            style.standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder), "Save project as…",
            self.save_project_as_dialog, "Ctrl+Shift+S",
        )
        self.app_toolbar.addSeparator()
        toolbar_action(
            style.standardIcon(QStyle.StandardPixmap.SP_FileIcon), "Convert TXT to CSV…", self.open_convert_dialog
        )
        toolbar_action(
            style.standardIcon(QStyle.StandardPixmap.SP_ComputerIcon), "Select quick reference file…",
            self.select_quick_reference,
        )
        self.recent_projects_button = QToolButton(self)
        self.recent_projects_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        self.recent_projects_button.setToolTip("Recent projects")
        self.recent_projects_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.recent_projects_menu = QMenu(self.recent_projects_button)
        self.recent_projects_button.setMenu(self.recent_projects_menu)
        self.app_toolbar.addWidget(self.recent_projects_button)
        self.update_recent_projects_menu()
        
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Status Bar with Progress Bar and Cancel Button
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0) # Indeterminate
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        self.statusBar().addPermanentWidget(self.progress_bar)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.cancel_workers)
        self.btn_cancel.hide()
        self.statusBar().addPermanentWidget(self.btn_cancel)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Control Panel
        self.control_panel = ControlPanel()
        self.control_panel.add_dataset_requested.connect(self.open_file_dialog)
        self.control_panel.add_quick_ref_requested.connect(self.add_quick_reference)
        self.control_panel.remove_dataset_requested.connect(self.remove_dataset)
        self.control_panel.move_dataset_requested.connect(self.move_dataset)
        self.control_panel.selection_changed.connect(self.on_selection_changed)
        self.control_panel.visibility_toggled.connect(self.on_visibility_toggled)
        self.control_panel.settings_changed.connect(self.on_settings_changed)
        self.control_panel.export_requested.connect(self.export_plot)
        self.control_panel.save_data_requested.connect(self.save_filtered_dataset)
        self.control_panel.centre_data_requested.connect(self.create_centred_copy)
        self.control_panel.run_icp_requested.connect(self.on_run_icp)
        self.control_panel.run_legacy_global_alignment_requested.connect(self.on_run_legacy_global_alignment)
        self.control_panel.run_auto_alignment_requested.connect(self.on_run_auto_alignment)
        self.control_panel.calculate_error_requested.connect(self.on_calculate_error)
        self.control_panel.error_map_display_changed.connect(self.on_error_map_display_changed)
        self.control_panel.error_map_colour_mode_changed.connect(self.on_error_map_colour_mode_changed)
        self.control_panel.camera_view_requested.connect(self.on_camera_view_requested)
        self.control_panel.camera_rotate_requested.connect(self.on_camera_rotate_requested)
        
        # Plot Canvas
        plot_layout = QVBoxLayout()
        self.plot_canvas = PlotCanvas(self)
        self.toolbar = PointCloudNavigationToolbar(self.plot_canvas, self)
        
        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.plot_canvas)
        
        plot_widget = QWidget()
        plot_widget.setLayout(plot_layout)
        
        splitter.addWidget(self.control_panel)
        splitter.addWidget(plot_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        
        layout.addWidget(splitter)
        
        central_widget.setLayout(layout)

    def set_project_dirty(self, dirty: bool = True):
        """Track project-owned changes and expose them in the window title."""
        self.project_dirty = bool(dirty)
        suffix = os.path.basename(self.project_filepath) if self.project_filepath else "Untitled project"
        marker = " *" if self.project_dirty else ""
        self.setWindowTitle(f"3D Point Cloud Data Viewer — {suffix}{marker}")
        
    def set_loading_state(self, is_loading: bool, message: str = ""):
        from PyQt6.QtCore import Qt
        if is_loading:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            self.progress_bar.show()
            self.btn_cancel.show()
            self.statusBar().showMessage(message)
            self.control_panel.setEnabled(False)
            self.app_toolbar.setEnabled(False)
        else:
            QApplication.restoreOverrideCursor()
            self.progress_bar.hide()
            self.btn_cancel.hide()
            self.control_panel.setEnabled(True)
            self.app_toolbar.setEnabled(True)
            self.statusBar().showMessage(message if message else "Ready.")
            
    def cancel_workers(self):
        if hasattr(self, 'load_worker') and self.load_worker.isRunning():
            self.load_worker.cancel()
        if hasattr(self, 'update_worker') and self.update_worker.isRunning():
            self.update_worker.cancel()
        if hasattr(self, 'icp_worker') and self.icp_worker.isRunning():
            self.icp_worker.cancel()
        if hasattr(self, 'legacy_global_alignment_worker') and self.legacy_global_alignment_worker.isRunning():
            self.legacy_global_alignment_worker.cancel()
        if hasattr(self, 'auto_alignment_worker') and self.auto_alignment_worker.isRunning():
            self.auto_alignment_worker.cancel()
        if hasattr(self, 'comparison_worker') and self.comparison_worker.isRunning():
            self.comparison_worker.cancel()
        if hasattr(self, 'save_worker') and self.save_worker.isRunning():
            self.save_worker.cancel()
        if hasattr(self, 'centre_worker') and self.centre_worker.isRunning():
            self.centre_worker.cancel()
        self.statusBar().showMessage("Cancelling... (Waiting for worker to abort)")
        
    def open_convert_dialog(self):
        filepaths, _ = QFileDialog.getOpenFileNames(
            self, "Select TXT files to convert", "", "Text Files (*.txt);;All Files (*)"
        )
        
        if filepaths:
            from src.data.converter import convert_txt_to_csv
            
            success_count = 0
            last_csv = None
            
            for fp in filepaths:
                base, _ = os.path.splitext(fp)
                out_csv = f"{base}.csv"
                count, err = convert_txt_to_csv(fp, out_csv)
                if err:
                    QMessageBox.warning(self, "Conversion Error", f"Failed to convert {os.path.basename(fp)}:\n{err}")
                else:
                    success_count += 1
                    last_csv = out_csv
                    
            if success_count > 0:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setWindowTitle("Conversion Complete")
                msg.setText(f"Successfully converted {success_count} file(s) to CSV.")
                
                if success_count == 1 and last_csv:
                    msg.setInformativeText("Would you like to load the converted file now?")
                    btn_yes = msg.addButton("Yes, load it", QMessageBox.ButtonRole.YesRole)
                    btn_no = msg.addButton("No", QMessageBox.ButtonRole.NoRole)
                    msg.exec()
                    if msg.clickedButton() == btn_yes:
                        self.load_file(last_csv)
                else:
                    msg.exec()
                    
    def select_quick_reference(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select Quick Reference CSV", "", "CSV Files (*.csv);;All Files (*)"
        )
        if filepath:
            from src.utils.app_settings import load_app_settings, save_app_settings
            settings = load_app_settings()
            settings["quick_reference_file"] = filepath
            save_app_settings(settings)
            QMessageBox.information(self, "Success", f"Quick reference file set to:\n{filepath}")
            
    def add_quick_reference(self):
        from src.utils.app_settings import load_app_settings
        settings = load_app_settings()
        ref_file = settings.get("quick_reference_file")
        
        if not ref_file or not os.path.exists(ref_file):
            QMessageBox.warning(self, "Not Configured", "Please select a quick reference file first in Settings -> Select Quick Reference File...")
            return
            
        self.load_file(ref_file)
        
    def open_file_dialog(self):
        filepaths, _ = QFileDialog.getOpenFileNames(
            self, "Open Point Cloud File", "", "Point Cloud Files (*.csv *.ply);;CSV Files (*.csv);;PLY Files (*.ply);;All Files (*)"
        )
        
        if filepaths:
            for filepath in filepaths:
                cached_files = check_cached_filtered_files(filepath)
                if cached_files:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Icon.Question)
                    msg.setWindowTitle("Cached Data Found")
                    msg.setText(f"Filtered versions of {os.path.basename(filepath)} exist. Load a cached version?")
                    msg.setInformativeText("This can be much faster for large files.")
                    
                    btn_yes = msg.addButton("Yes, load cached", QMessageBox.ButtonRole.YesRole)
                    btn_no = msg.addButton("No, load original", QMessageBox.ButtonRole.NoRole)
                    msg.exec()
                    
                    if msg.clickedButton() == btn_yes:
                        filepath = cached_files[0]
                
                self.load_file(filepath)
            
    def update_recent_projects_menu(self):
        self.recent_projects_menu.clear()
        from src.utils.app_settings import load_app_settings
        settings = load_app_settings()
        recent = settings.get("recent_projects", [])
        
        if not recent:
            empty_action = QAction("No recent projects", self)
            empty_action.setEnabled(False)
            self.recent_projects_menu.addAction(empty_action)
            return
            
        for fp in recent:
            if os.path.exists(fp):
                action = QAction(os.path.basename(fp), self)
                action.setToolTip(fp)
                action.triggered.connect(lambda checked, path=fp: self.open_specific_project(path))
                self.recent_projects_menu.addAction(action)

    def add_recent_project(self, filepath: str):
        from src.utils.app_settings import load_app_settings, save_app_settings
        settings = load_app_settings()
        recent = settings.get("recent_projects", [])
        
        if filepath in recent:
            recent.remove(filepath)
        recent.insert(0, filepath)
        
        # Keep top 5
        recent = recent[:5]
        settings["recent_projects"] = recent
        save_app_settings(settings)
        self.update_recent_projects_menu()

    def open_specific_project(self, filepath: str):
        if len(self.datasets) > 0:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Clear Existing Data")
            msg.setText("Opening a project will remove all currently loaded point clouds.")
            msg.setInformativeText("Are you sure you want to proceed?")
            btn_yes = msg.addButton("Yes, open project", QMessageBox.ButtonRole.YesRole)
            btn_no = msg.addButton("Cancel", QMessageBox.ButtonRole.NoRole)
            msg.exec()
            
            if msg.clickedButton() != btn_yes:
                return
                
        try:
            import json
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            entries = data.get("datasets", [])
            # Older project files stored a plain list of paths. New project
            # files also preserve visibility alongside every path.
            normalized_entries = []
            for entry in entries:
                if isinstance(entry, str):
                    normalized_entries.append({"filepath": entry, "visible": True})
                elif isinstance(entry, dict) and entry.get("filepath"):
                    normalized_entries.append({
                        "filepath": entry["filepath"],
                        "visible": bool(entry.get("visible", True)),
                    })

            # Clear existing datasets.
            for i in range(len(self.datasets) - 1, -1, -1):
                self.remove_dataset(i)
            
            # Load all files in the project
            for entry in normalized_entries:
                fp = entry["filepath"]
                if os.path.exists(fp):
                    self.load_file(fp, visible=entry["visible"], mark_project_dirty=False)
                else:
                    QMessageBox.warning(self, "Missing File", f"Could not find dataset file:\n{fp}")
                    
            self.project_filepath = filepath
            self.set_project_dirty(False)
            self.statusBar().showMessage(f"Loaded project: {filepath}")
            self.add_recent_project(filepath)
        except Exception as e:
            QMessageBox.critical(self, "Project Load Error", f"Failed to load project:\n{str(e)}")

    def open_project_dialog(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "", "Project Files (*.json);;All Files (*)"
        )
        if filepath:
            self.open_specific_project(filepath)

    def _project_data(self):
        """Serialize project-owned state, including layer order and visibility."""
        return {
            "format_version": 2,
            "datasets": [
                {"filepath": dataset["filepath"], "visible": bool(dataset.get("visible", True))}
                for dataset in self.datasets
            ],
        }

    def _save_project_to_file(self, filepath: str) -> bool:
        try:
            import json
            with open(filepath, 'w') as f:
                json.dump(self._project_data(), f, indent=4)
            self.project_filepath = filepath
            self.set_project_dirty(False)
            self.statusBar().showMessage(f"Project saved to {filepath}")
            self.add_recent_project(filepath)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Project Save Error", f"Failed to save project:\n{str(e)}")
            return False

    def save_project(self) -> bool:
        """Save in place, or request a path when this is an unsaved project."""
        if self.project_filepath:
            return self._save_project_to_file(self.project_filepath)
        return self.save_project_as_dialog()

    def save_project_as_dialog(self) -> bool:
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Project", "", "Project Files (*.json)"
        )
        if not filepath:
            return False
        if not filepath.lower().endswith(".json"):
            filepath += ".json"
        return self._save_project_to_file(filepath)

    # Kept for callers from earlier versions of the UI.
    def save_project_dialog(self):
        return self.save_project_as_dialog()
            
    def load_file(self, filepath: str, visible: bool = True, mark_project_dirty: bool = True):
        if not hasattr(self, 'load_queue'):
            self.load_queue = []
        self.load_queue.append({
            "filepath": filepath,
            "visible": bool(visible),
            "mark_project_dirty": bool(mark_project_dirty),
        })
        self.process_load_queue()

    def process_load_queue(self):
        if hasattr(self, 'load_worker') and self.load_worker.isRunning():
            return
            
        if not hasattr(self, 'load_queue') or not self.load_queue:
            return
            
        load_request = self.load_queue.pop(0)
        filepath = load_request["filepath"]
        self.set_loading_state(True, f"Loading {os.path.basename(filepath)}...")
        
        self.load_worker = WorkerThread(parse_point_cloud_file, filepath)
        
        def on_finished(result):
            df, add_cols, err = result
            if err:
                QMessageBox.critical(self, "Error", err)
                if self.load_queue:
                    self.process_load_queue()
                else:
                    self.set_loading_state(False, "Error loading file.")
                return
                
            name = os.path.basename(filepath)
            
            config = load_filter_config(filepath)
            if not config:
                cycle_colors = ["C0", "C1", "C2", "C3", "C4", "C5"]
                idx = len(self.datasets) % len(cycle_colors)
                
                if not df.empty:
                    p5_x, p95_x = np.percentile(df['X'], [5, 95])
                    p5_y, p95_y = np.percentile(df['Y'], [5, 95])
                    p5_z, p95_z = np.percentile(df['Z'], [5, 95])
                    max_dim = max(p95_x - p5_x, p95_y - p5_y, p95_z - p5_z)
                    auto_voxel_size = max_dim * 0.01
                    if auto_voxel_size <= 0:
                        auto_voxel_size = 0.1
                else:
                    auto_voxel_size = 0.1
                    
                config = {
                    "base_color": cycle_colors[idx], "color_col": None,
                    "invert_x": False, "invert_y": False, "invert_z": False,
                    "zscore_enabled": False, "zscore_threshold": 3.0,
                    "sor_enabled": False, "sor_k": 50, "sor_std": 1.0,
                    "bbox_enabled": False, "bbox_zmin": -1000.0, "bbox_zmax": 1000.0,
                    "voxel_enabled": False, "voxel_size": auto_voxel_size,
                    "scale": 1.0,
                    "tx": 0.0, "ty": 0.0, "tz": 0.0, "rx": 0.0, "ry": 0.0, "rz": 0.0
                }
                if len(df) > 100000:
                    config["voxel_enabled"] = True
                    QMessageBox.information(
                        self, 
                        "Auto-Filter Activated", 
                        f"Dataset {name} has {len(df):,} points which could cause lag.\n\n"
                        f"A Voxel Downsample filter has been automatically enabled with a size of {auto_voxel_size:.3f} units."
                    )
                        
            dataset = {
                "filepath": filepath,
                "name": name,
                "df": df,
                "settings": config,
                "visible": load_request["visible"],
                "add_cols": add_cols
            }
            
            self.datasets.append(dataset)
            self.control_panel.add_dataset_to_list(name, checked=load_request["visible"])
            if load_request["mark_project_dirty"]:
                self.set_project_dirty(True)
            
            if self.load_queue:
                self.process_load_queue()
            else:
                self.set_loading_state(False)
                self.update_plot()
            
        def on_error(err_str):
            QMessageBox.critical(self, "Error", f"Failed to load file: {err_str}")
            if self.load_queue:
                self.process_load_queue()
            else:
                self.set_loading_state(False, "Error loading file.")
            
        self.load_worker.finished.connect(on_finished)
        self.load_worker.error.connect(on_error)
        self.load_worker.start()
        
    def remove_dataset(self, idx: int):
        if 0 <= idx < len(self.datasets):
            del self.datasets[idx]
            self.control_panel.remove_dataset_from_list(idx)
            self.set_project_dirty(True)
            self.update_plot()

    def move_dataset(self, old_idx: int, new_idx: int):
        """Reorder data and selectors; the first list entry is the top render layer."""
        if not (0 <= old_idx < len(self.datasets) and 0 <= new_idx < len(self.datasets)):
            return
        dataset = self.datasets.pop(old_idx)
        self.datasets.insert(new_idx, dataset)
        self.control_panel.move_dataset_in_list(old_idx, new_idx)
        self.set_project_dirty(True)
        self.update_plot()
            
    def on_selection_changed(self, idx: int):
        if 0 <= idx < len(self.datasets):
            dataset = self.datasets[idx]
            self.control_panel.update_columns(dataset["add_cols"])
            self.control_panel.apply_config(dataset["settings"])
            self.control_panel.set_error_map_display_state(
                "error_visualization" in dataset,
                dataset.get("show_error_visualization", False),
                dataset.get("error_visualization", {}).get("colour_mode", "closest_distance"),
            )
            
    def on_visibility_toggled(self, idx: int, is_visible: bool):
        if 0 <= idx < len(self.datasets):
            self.datasets[idx]["visible"] = is_visible
            self.set_project_dirty(True)
            self.update_plot()
            
    def on_settings_changed(self):
        idx = self.control_panel.dataset_list.currentRow()
        if 0 <= idx < len(self.datasets):
            # A distance map is valid only for the exact source/reference
            # transforms and quality filters that were used to calculate it.
            # Any settings edit can change either cloud, so discard stale maps.
            for dataset in self.datasets:
                dataset.pop("error_visualization", None)
                dataset.pop("show_error_visualization", None)
            st = self.control_panel.get_current_settings()
            self.datasets[idx]["settings"] = st
            save_filter_config(self.datasets[idx]["filepath"], st)
            self.set_project_dirty(True)
            self.control_panel.set_error_map_display_state(False)
            self.update_plot()

    def on_error_map_display_changed(self, shown: bool):
        """Toggle the selected cloud's already calculated error-map rendering."""
        idx = self.control_panel.dataset_list.currentRow()
        if not (0 <= idx < len(self.datasets)):
            return
        dataset = self.datasets[idx]
        if "error_visualization" not in dataset:
            return
        dataset["show_error_visualization"] = shown
        self.plot_canvas.plot_datasets(self.datasets)

    def on_error_map_colour_mode_changed(self, colour_mode: str):
        """Switch between absolute nearest-reference error and mean-centred display."""
        idx = self.control_panel.dataset_list.currentRow()
        if not (0 <= idx < len(self.datasets)):
            return
        error_map = self.datasets[idx].get("error_visualization")
        if error_map is None:
            return
        error_map["colour_mode"] = colour_mode
        if self.datasets[idx].get("show_error_visualization", False):
            self.plot_canvas.plot_datasets(self.datasets)

    def on_camera_view_requested(self, view_name: str):
        self.plot_canvas.set_standard_view(view_name)

    def on_camera_rotate_requested(self, degrees: float):
        self.plot_canvas.rotate_camera_around_vertical(float(degrees))
            
    def apply_transform(self, df: pd.DataFrame, settings: dict) -> pd.DataFrame:
        """Apply axis convention, uniform scale, then manual rotation and translation."""
        tx, ty, tz = settings.get("tx", 0.0), settings.get("ty", 0.0), settings.get("tz", 0.0)
        rx, ry, rz = settings.get("rx", 0.0), settings.get("ry", 0.0), settings.get("rz", 0.0)
        scale = settings.get("scale", 1.0)
        
        invert_x = settings.get("invert_x", False)
        invert_y = settings.get("invert_y", False)
        invert_z = settings.get("invert_z", False)
        if (scale == 1.0 and tx == 0.0 and ty == 0.0 and tz == 0.0 and rx == 0.0 and ry == 0.0 and rz == 0.0
                and not invert_x and not invert_y and not invert_z):
            return df
            
        mat = euler_translation_to_matrix(tx, ty, tz, rx, ry, rz)
        
        points = df[['X', 'Y', 'Z']].to_numpy(dtype=float, copy=True)
        if invert_x:
            points[:, 0] *= -1
        if invert_y:
            points[:, 1] *= -1
        if invert_z:
            points[:, 2] *= -1
        points *= scale
        transformed_points = points @ mat[:3, :3].T + mat[:3, 3]
        
        df_out = df.copy()
        df_out['X'] = transformed_points[:, 0]
        df_out['Y'] = transformed_points[:, 1]
        df_out['Z'] = transformed_points[:, 2]
        return df_out
            
    def process_filters_background(self, datasets):
        results = []
        for d in datasets:
            if not d["visible"]:
                results.append((None, d, False))
                continue
                
            df = d["df"]
            st = d["settings"]
            
            # Skip reprocessing if settings are unchanged
            if d.get("last_settings") == st and "df_filtered" in d:
                results.append((d["df_filtered"], d, True))
                continue
            
            df_filtered = self.apply_transform(df, st)
            
            if st.get("bbox_enabled"):
                df_filtered = filter_by_bounding_box(df_filtered, z_min=st.get("bbox_zmin"), z_max=st.get("bbox_zmax"))
            if st.get("zscore_enabled"):
                df_filtered = filter_by_zscore(df_filtered, st.get("zscore_threshold", 3.0))
            if st.get("sor_enabled"):
                df_filtered = filter_by_sor(df_filtered, st.get("sor_k", 50), st.get("sor_std", 1.0))
            if st.get("voxel_enabled"):
                df_filtered = filter_by_voxel_grid(df_filtered, st.get("voxel_size", 0.1))
                
            results.append((df_filtered, d, False))
        return results

    def update_plot(self):
        if hasattr(self, 'update_worker') and self.update_worker.isRunning():
            return
            
        self.set_loading_state(True, "Updating plot (processing filters)...")
        
        self.update_worker = WorkerThread(self.process_filters_background, self.datasets)
        
        def on_finished(results):
            import copy
            for df_filtered, d, unchanged in results:
                if df_filtered is not None:
                    if not unchanged:
                        d["df_filtered"] = df_filtered
                        d["last_settings"] = copy.deepcopy(d["settings"])
                    
            self.plot_canvas.plot_datasets(self.datasets)
            total_points = sum([len(d["df_filtered"]) for d in self.datasets if d["visible"] and "df_filtered" in d])
            msg = f"Showing {total_points} total points across {sum(1 for d in self.datasets if d['visible'])} dataset(s)."
            self.set_loading_state(False, msg)
            
        def on_error(err_str):
            self.set_loading_state(False, "Error updating plot.")
            QMessageBox.critical(self, "Plot Error", f"Failed to filter data: {err_str}")
            
        self.update_worker.finished.connect(on_finished)
        self.update_worker.error.connect(on_error)
        self.update_worker.start()

    def run_icp_background(self, source_dataset, target_dataset, max_corr_dist, method, progress_callback=None, is_cancelled_callback=None):
        if progress_callback:
            progress_callback("Applying initial transforms to data...")
            
        source_df = self.apply_transform(source_dataset["df"], source_dataset["settings"])
        target_df = self.apply_transform(target_dataset["df"], target_dataset["settings"])
        
        if len(source_df) > 50000:
            if progress_callback:
                progress_callback("Downsampling source cloud for performance...")
            source_df = filter_by_voxel_grid(source_df, 0.5)
            
        if len(target_df) > 50000:
            if progress_callback:
                progress_callback("Downsampling target cloud for performance...")
            target_df = filter_by_voxel_grid(target_df, 0.5)
            
        result, fitness = run_icp(source_df, target_df, max_correspondence_distance=max_corr_dist, method=method, progress_callback=progress_callback, is_cancelled_callback=is_cancelled_callback)
        return result, fitness, source_dataset

    def run_legacy_global_alignment_background(self, source_dataset, target_dataset, max_registration_points,
                                               progress_callback=None, is_cancelled_callback=None):
        if progress_callback:
            progress_callback(
                "Applying the selected axis inversions, scale, and manual transforms before global alignment..."
            )
        source_df = self._apply_quality_filters(source_dataset)
        target_df = self._apply_quality_filters(target_dataset)
        result = global_automatic_registration(
            source_df,
            target_df,
            max_registration_points=max_registration_points,
            progress_callback=progress_callback,
            is_cancelled_callback=is_cancelled_callback,
        )
        return result, source_dataset, target_dataset

    def _apply_quality_filters(self, dataset):
        """Apply the user's non-display filters before registration/comparison.

        The interactive voxel setting is deliberately not applied here. The
        automatic registration chooses its own adaptive voxel size, and the
        comparison should use the retained measurement density (or its explicit
        analysis sample limit), rather than the coarse display resolution.
        """
        df = self.apply_transform(dataset["df"], dataset["settings"])
        st = dataset["settings"]
        if st.get("bbox_enabled"):
            df = filter_by_bounding_box(df, z_min=st.get("bbox_zmin"), z_max=st.get("bbox_zmax"))
        if st.get("zscore_enabled"):
            df = filter_by_zscore(df, st.get("zscore_threshold", 3.0))
        if st.get("sor_enabled"):
            df = filter_by_sor(df, st.get("sor_k", 50), st.get("sor_std", 1.0))
        return df

    def _save_alignment_transform(self, source_idx, target_dataset, delta_transform, label, details):
        """Compose an alignment delta with the source's existing manual pose."""
        source_dataset = self.datasets[source_idx]
        st = source_dataset["settings"]
        current_transform = euler_translation_to_matrix(
            st.get("tx", 0.0), st.get("ty", 0.0), st.get("tz", 0.0),
            st.get("rx", 0.0), st.get("ry", 0.0), st.get("rz", 0.0),
        )
        final_transform = np.asarray(delta_transform) @ current_transform
        ftx, fty, ftz, frx, fry, frz = matrix_to_euler_translation(final_transform)

        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        preset_name = f"{label} ({timestamp})"
        saved = st.get("saved_transforms", {"Initial": {
            "scale": st.get("scale", 1.0),
            "tx": st.get("tx", 0.0), "ty": st.get("ty", 0.0), "tz": st.get("tz", 0.0),
            "rx": st.get("rx", 0.0), "ry": st.get("ry", 0.0), "rz": st.get("rz", 0.0),
        }})
        saved[preset_name] = {
            "scale": st.get("scale", 1.0),
            "tx": ftx, "ty": fty, "tz": ftz, "rx": frx, "ry": fry, "rz": frz,
        }
        st.update({
            "saved_transforms": saved,
            "current_transform_name": preset_name,
            "tx": ftx, "ty": fty, "tz": ftz, "rx": frx, "ry": fry, "rz": frz,
            "last_registration": {
                **details,
                "reference": target_dataset["name"],
                "preset": preset_name,
            },
        })
        save_filter_config(source_dataset["filepath"], st)
        self.set_project_dirty(True)
        if self.control_panel.dataset_list.currentRow() == source_idx:
            self.control_panel.apply_config(st)
        return preset_name

    def run_auto_alignment_background(self, source_dataset, target_dataset, max_registration_points,
                                      translation_x_limit, translation_y_limit, translation_z_limit,
                                      rotation_x_limit, rotation_y_limit, rotation_z_limit,
                                      progress_callback=None,
                                      is_cancelled_callback=None):
        if progress_callback:
            progress_callback("Preparing point clouds for bounded manual fine alignment...")
        source_df = self._apply_quality_filters(source_dataset)
        target_df = self._apply_quality_filters(target_dataset)
        result = automatic_registration(
            source_df,
            target_df,
            max_registration_points=max_registration_points,
            use_global_registration=False,
            translation_limits=(translation_x_limit, translation_y_limit, translation_z_limit),
            rotation_limits_degrees=(rotation_x_limit, rotation_y_limit, rotation_z_limit),
            progress_callback=progress_callback,
            is_cancelled_callback=is_cancelled_callback,
        )
        return result, source_dataset, target_dataset

    def on_run_legacy_global_alignment(self, source_idx: int, target_idx: int, max_registration_points: int):
        if hasattr(self, 'legacy_global_alignment_worker') and self.legacy_global_alignment_worker.isRunning():
            return
        source_dataset = self.datasets[source_idx]
        target_dataset = self.datasets[target_idx]
        self.set_loading_state(True, "Running previous global auto alignment with the transformed point clouds...")
        self.legacy_global_alignment_worker = WorkerThread(
            self.run_legacy_global_alignment_background,
            source_dataset,
            target_dataset,
            max_registration_points,
            inject_progress=True,
            inject_cancelled=True,
        )
        self.legacy_global_alignment_worker.progress.connect(lambda msg: self.statusBar().showMessage(msg))

        def on_finished(result):
            alignment, source, target = result
            details = {
                "method": "previous global PCA / centre-of-gravity / FPFH alignment",
                "initialization": alignment["initialization"],
                "source_overlap": alignment["source_overlap"],
                "reference_overlap": alignment["reference_overlap"],
                "symmetric_overlap": alignment["symmetric_overlap"],
                "inlier_rmse": alignment["inlier_rmse"],
                "voxel_size": alignment["voxel_size"],
                "final_tolerance": alignment["final_tolerance"],
                "source_registration_points": alignment["source_registration_points"],
                "target_registration_points": alignment["target_registration_points"],
                "candidate_count": alignment["candidate_count"],
                "axis_inversions_applied": True,
            }
            preset_name = self._save_alignment_transform(
                source_idx, target, alignment["transformation"], "Previous Global Align", details
            )
            self.control_panel.set_comparison_summary(
                f"Previous global alignment to {target['name']}: {alignment['source_overlap']:.1%} source overlap, "
                f"trimmed RMSE {alignment['inlier_rmse']:.6g}."
            )
            self.set_loading_state(False)
            self.update_plot()
            QMessageBox.information(
                self,
                "Previous Global Alignment Complete",
                f"Saved as preset: '{preset_name}'.\n\n"
                f"Initialisation selected: {alignment['initialization']}\n"
                f"Source overlap: {alignment['source_overlap']:.1%}\n"
                f"Reference overlap: {alignment['reference_overlap']:.1%}\n"
                f"Symmetric overlap: {alignment['symmetric_overlap']:.1%}\n"
                f"Trimmed RMSE: {alignment['inlier_rmse']:.6g}\n\n"
                "The selected Invert X/Y/Z settings were applied to both clouds before this alignment. "
                "Inspect the overlay before calculating surface error; this restored global method can still select "
                "a visually similar but wrong blade area.",
            )

        def on_error(err_str):
            self.set_loading_state(False)
            if "Cancelled by User" in err_str:
                QMessageBox.information(self, "Cancelled", "Previous global alignment was cancelled.")
            else:
                QMessageBox.critical(self, "Previous Global Alignment Error", f"Alignment failed:\n{err_str}")

        self.legacy_global_alignment_worker.finished.connect(on_finished)
        self.legacy_global_alignment_worker.error.connect(on_error)
        self.legacy_global_alignment_worker.start()

    def on_run_auto_alignment(self, source_idx: int, target_idx: int,
                              max_registration_points: int,
                              translation_x_limit: float, translation_y_limit: float, translation_z_limit: float,
                              rotation_x_limit: float, rotation_y_limit: float, rotation_z_limit: float):
        if hasattr(self, 'auto_alignment_worker') and self.auto_alignment_worker.isRunning():
            return
        source_dataset = self.datasets[source_idx]
        target_dataset = self.datasets[target_idx]
        self.set_loading_state(True, "Optimising the manual point-cloud alignment...")
        self.auto_alignment_worker = WorkerThread(
            self.run_auto_alignment_background,
            source_dataset,
            target_dataset,
            max_registration_points,
            translation_x_limit,
            translation_y_limit,
            translation_z_limit,
            rotation_x_limit,
            rotation_y_limit,
            rotation_z_limit,
            inject_progress=True,
            inject_cancelled=True,
        )
        self.auto_alignment_worker.progress.connect(lambda msg: self.statusBar().showMessage(msg))

        def on_finished(result):
            alignment, source, target = result
            baseline = alignment["baseline"]
            optimizer = alignment["optimizer"]
            baseline_summary = (
                f"manual anchored overlap {baseline['fitness']:.1%}, "
                f"trimmed RMSE {baseline['rmse']:.6g}"
            )
            final_summary = (
                f"final anchored overlap {alignment['fitness']:.1%}, "
                f"trimmed RMSE {alignment['inlier_rmse']:.6g}"
            )
            if not optimizer["accepted"]:
                self.control_panel.set_comparison_summary(
                    "Manual pose retained: the bounded local optimizer did not provide a safe measurable improvement. "
                    f"{baseline_summary}."
                )
                self.set_loading_state(False)
                QMessageBox.information(
                    self,
                    "Manual Alignment Retained",
                    "No transform was saved because the optimizer could not improve the manual pose safely.\n\n"
                    f"Initial: {baseline_summary}\n"
                    f"Candidate: {final_summary}\n\n"
                    "The plotted manual pose is unchanged. Reduce the correction limits to match your confidence, "
                    "or improve the manual placement and try again.",
                )
                return
            details = {
                "method": "bounded bidirectional closest-point optimizer",
                "initialization": alignment["initialization"],
                "fitness": alignment["fitness"],
                "inlier_rmse": alignment["inlier_rmse"],
                "voxel_size": alignment["voxel_size"],
                "source_registration_points": alignment["source_registration_points"],
                "target_registration_points": alignment["target_registration_points"],
                "translation_limits": alignment["translation_limits"],
                "rotation_limits_degrees": alignment["rotation_limits_degrees"],
                "capture_distance": alignment["capture_distance"],
                "source_anchor_points": alignment["source_anchor_points"],
                "reference_anchor_points": alignment["reference_anchor_points"],
                "baseline": baseline,
                "optimizer": optimizer,
            }
            preset_name = self._save_alignment_transform(
                source_idx, target, alignment["transformation"], "Fine Align", details
            )
            summary = (
                f"Fine alignment to {target['name']}: {final_summary} (from {baseline_summary})."
            )
            self.control_panel.set_comparison_summary(summary)
            self.set_loading_state(False)
            self.update_plot()
            QMessageBox.information(
                self,
                "Fine Alignment Complete",
                f"Saved as preset: '{preset_name}'.\n\n"
                f"Initial: {baseline_summary}\n"
                f"Final: {final_summary}\n"
                f"Anchor points: {alignment['source_anchor_points']:,} source / "
                f"{alignment['reference_anchor_points']:,} reference\n"
                f"Translation limits (+/-): ({alignment['translation_limits'][0]:.6g}, "
                f"{alignment['translation_limits'][1]:.6g}, {alignment['translation_limits'][2]:.6g})\n"
                f"Rotation limits (+/-): ({alignment['rotation_limits_degrees'][0]:.2f}, "
                f"{alignment['rotation_limits_degrees'][1]:.2f}, "
                f"{alignment['rotation_limits_degrees'][2]:.2f}) degrees\n"
                f"Capture distance: {alignment['capture_distance']:.6g}\n\n"
                f"Correction at overlap pivot: {optimizer['translation_correction']:.6g} units "
                f"({optimizer['translation_correction_vector'][0]:.6g}, "
                f"{optimizer['translation_correction_vector'][1]:.6g}, "
                f"{optimizer['translation_correction_vector'][2]:.6g}); "
                f"rotation XYZ ({optimizer['rotation_correction_vector_degrees'][0]:.2f}, "
                f"{optimizer['rotation_correction_vector_degrees'][1]:.2f}, "
                f"{optimizer['rotation_correction_vector_degrees'][2]:.2f}) degrees "
                f"(total {optimizer['rotation_correction_degrees']:.2f} degrees)\n\n"
                "The result was constrained around the manual pose. Check the plot before calculating surface error.",
            )

        def on_error(err_str):
            self.set_loading_state(False)
            if "Cancelled by User" in err_str:
                QMessageBox.information(self, "Cancelled", "Manual fine alignment was cancelled.")
            else:
                QMessageBox.critical(self, "Fine Alignment Error", f"Manual fine alignment failed:\n{err_str}")

        self.auto_alignment_worker.finished.connect(on_finished)
        self.auto_alignment_worker.error.connect(on_error)
        self.auto_alignment_worker.start()

    @staticmethod
    def _format_error_report(report):
        overlap = f"{report['overlap_fraction']:.1%} ({report['overlap_points']:,} points)"
        sampled = "yes" if report["source_points_sampled"] else "no"
        if report["overlap_points"] == 0:
            return (
                f"Overlap: {overlap}\nNo points were within the cutoff of {report['overlap_cutoff']:.6g}. "
                "Increase the cutoff or inspect the alignment."
            )
        return (
            f"Overlap: {overlap}; outside overlap: {report['non_overlap_points']:,}\n"
            f"Mean: {report['mean']:.6g}; median: {report['median']:.6g}; "
            f"RMSE: {report['rmse']:.6g}; P95: {report['p95']:.6g}; max: {report['maximum']:.6g}\n"
            f"Analysed {report['source_points_analysed']:,} source points (sampled: {sampled}); "
            f"indexed {report['reference_points_indexed']:,} reference points."
        )

    def run_comparison_background(self, source_dataset, target_dataset, cutoff, max_analysis_points,
                                  progress_callback=None, is_cancelled_callback=None):
        if progress_callback:
            progress_callback("Preparing point clouds for surface-error calculation...")
        source_df = self._apply_quality_filters(source_dataset)
        target_df = self._apply_quality_filters(target_dataset)
        report, pointwise = calculate_cloud_error(
            source_df,
            target_df,
            max_distance=cutoff,
            max_analysis_points=max_analysis_points,
            progress_callback=progress_callback,
            is_cancelled_callback=is_cancelled_callback,
            include_pointwise=True,
        )
        return report, pointwise, source_dataset, target_dataset

    def on_calculate_error(self, source_idx: int, target_idx: int, cutoff: float, max_analysis_points: int,
                           show_error_map: bool = True, highlight_above_mean: bool = False):
        if hasattr(self, 'comparison_worker') and self.comparison_worker.isRunning():
            return
        source_dataset = self.datasets[source_idx]
        target_dataset = self.datasets[target_idx]
        self.set_loading_state(True, "Calculating surface error to reference...")
        self.comparison_worker = WorkerThread(
            self.run_comparison_background,
            source_dataset,
            target_dataset,
            cutoff,
            max_analysis_points,
            inject_progress=True,
            inject_cancelled=True,
        )
        self.comparison_worker.progress.connect(lambda msg: self.statusBar().showMessage(msg))

        def on_finished(result):
            report, pointwise, source, target = result
            report["source_name"] = source["name"]
            report["reference_name"] = target["name"]
            source["last_comparison"] = report
            for dataset in self.datasets:
                dataset.pop("error_visualization", None)
                dataset.pop("show_error_visualization", None)
            source["error_visualization"] = {
                **pointwise,
                "reference_name": target["name"],
                "cutoff": report["overlap_cutoff"],
                "mean": report["mean"],
                "highlight_above_mean": highlight_above_mean,
                "colour_mode": "closest_distance",
            }
            source["show_error_visualization"] = show_error_map
            summary = self._format_error_report(report)
            self.control_panel.set_comparison_summary(summary)
            self.set_loading_state(False, "Surface-error comparison complete.")
            self.plot_canvas.plot_datasets(self.datasets)
            if self.control_panel.dataset_list.currentRow() == source_idx:
                self.control_panel.set_error_map_display_state(True, show_error_map, "closest_distance")
            QMessageBox.information(
                self,
                "Surface Error Report",
                f"{source['name']} -> {target['name']}\n\n{summary}\n\n"
                "Errors are unsigned nearest-reference distances in the data coordinate units. "
                "Points beyond the cutoff are treated as non-overlap and are excluded from the statistics."
                + (" The plot now shows the analysed source points coloured by this distance; grey means outside the cutoff."
                   if show_error_map else ""),
            )

        def on_error(err_str):
            self.set_loading_state(False)
            if "Cancelled by User" in err_str:
                QMessageBox.information(self, "Cancelled", "Surface-error calculation was cancelled.")
            else:
                QMessageBox.critical(self, "Surface Error", f"Surface-error calculation failed:\n{err_str}")

        self.comparison_worker.finished.connect(on_finished)
        self.comparison_worker.error.connect(on_error)
        self.comparison_worker.start()

    def on_run_icp(self, source_idx: int, target_idx: int, max_corr_dist: float, method: str):
        if hasattr(self, 'icp_worker') and self.icp_worker.isRunning():
            return
            
        self.set_loading_state(True, "Running ICP Alignment...")
        
        source_dataset = self.datasets[source_idx]
        target_dataset = self.datasets[target_idx]
        
        self.icp_worker = WorkerThread(self.run_icp_background, source_dataset, target_dataset, max_corr_dist, method, inject_progress=True, inject_cancelled=True)
        self.icp_worker.progress.connect(lambda msg: self.statusBar().showMessage(msg))
        
        def on_finished(res):
            result, fitness, s_dataset = res
            self.set_loading_state(False)
            
            if result:
                new_tx, new_ty, new_tz, new_rx, new_ry, new_rz = result
                st = s_dataset["settings"]
                mat_current = euler_translation_to_matrix(st.get("tx", 0.0), st.get("ty", 0.0), st.get("tz", 0.0),
                                                          st.get("rx", 0.0), st.get("ry", 0.0), st.get("rz", 0.0))
                mat_icp = euler_translation_to_matrix(new_tx, new_ty, new_tz, new_rx, new_ry, new_rz)
                
                mat_final = mat_icp @ mat_current
                from src.utils.registration import matrix_to_euler_translation
                ftx, fty, ftz, frx, fry, frz = matrix_to_euler_translation(mat_final)
                
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_preset_name = f"ICP Result ({timestamp})"
                
                saved = st.get("saved_transforms", {"Initial": {
                    "scale": st.get("scale", 1.0),
                    "tx": st.get("tx", 0.0), "ty": st.get("ty", 0.0), "tz": st.get("tz", 0.0),
                    "rx": st.get("rx", 0.0), "ry": st.get("ry", 0.0), "rz": st.get("rz", 0.0)
                }})
                
                saved[new_preset_name] = {
                    "scale": st.get("scale", 1.0),
                    "tx": ftx, "ty": fty, "tz": ftz,
                    "rx": frx, "ry": fry, "rz": frz
                }
                
                st["saved_transforms"] = saved
                st["current_transform_name"] = new_preset_name
                st["tx"] = ftx
                st["ty"] = fty
                st["tz"] = ftz
                st["rx"] = frx
                st["ry"] = fry
                st["rz"] = frz
                
                save_filter_config(s_dataset["filepath"], st)
                self.set_project_dirty(True)
                
                if self.control_panel.dataset_list.currentRow() == source_idx:
                    self.control_panel.apply_config(st)
                    
                self.update_plot()
                QMessageBox.information(self, "ICP Complete", f"Alignment finished.\nSaved as preset: '{new_preset_name}'.\nFitness score: {fitness:.4f}")
            else:
                QMessageBox.warning(self, "ICP Failed", "ICP Alignment failed or open3d is missing.")
                
        def on_error(err_str):
            self.set_loading_state(False)
            if "Cancelled by User" in err_str:
                QMessageBox.information(self, "Cancelled", "ICP Alignment was cancelled.")
            else:
                QMessageBox.critical(self, "ICP Error", f"An error occurred during ICP:\n{err_str}")
            
        self.icp_worker.finished.connect(on_finished)
        self.icp_worker.error.connect(on_error)
        self.icp_worker.start()
        
    def export_plot(self, filepath: str):
        try:
            self.plot_canvas.export_plot(filepath)
            self.statusBar().showMessage(f"Plot exported to {filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export plot: {str(e)}")
            
    def save_data_background(self, dataset):
        df = dataset["df"]
        st = dataset["settings"]
        
        df_filtered = self.apply_transform(df, st)
        if st.get("bbox_enabled"):
            df_filtered = filter_by_bounding_box(df_filtered, z_min=st.get("bbox_zmin"), z_max=st.get("bbox_zmax"))
        if st.get("zscore_enabled"):
            df_filtered = filter_by_zscore(df_filtered, st.get("zscore_threshold", 3.0))
        if st.get("sor_enabled"):
            df_filtered = filter_by_sor(df_filtered, st.get("sor_k", 50), st.get("sor_std", 1.0))
        if st.get("voxel_enabled"):
            df_filtered = filter_by_voxel_grid(df_filtered, st.get("voxel_size", 0.1))
            
        new_fp = save_filtered_data(df_filtered, dataset["filepath"], "downsample", "transformed")
        return new_fp

    def save_filtered_dataset(self):
        idx = self.control_panel.dataset_list.currentRow()
        if idx < 0 or idx >= len(self.datasets):
            return
            
        if hasattr(self, 'save_worker') and self.save_worker.isRunning():
            return
            
        dataset = self.datasets[idx]
        self.set_loading_state(True, "Saving dataset...")
        
        self.save_worker = WorkerThread(self.save_data_background, dataset)
        
        def on_finished(new_fp):
            self.set_loading_state(False, "Ready.")
            QMessageBox.information(self, "Success", f"Filtered dataset saved to:\n{new_fp}")
            
        def on_error(err_str):
            self.set_loading_state(False, "Ready.")
            QMessageBox.critical(self, "Save Error", f"Failed to save data: {err_str}")
            
        self.save_worker.finished.connect(on_finished)
        self.save_worker.error.connect(on_error)
        self.save_worker.start()

    def create_centred_copy(self):
        """Save a translated copy of the selected source cloud without altering it."""
        idx = self.control_panel.dataset_list.currentRow()
        if idx < 0 or idx >= len(self.datasets):
            return
        if hasattr(self, "centre_worker") and self.centre_worker.isRunning():
            return

        dataset = self.datasets[idx]
        self.set_loading_state(True, "Creating centred point-cloud copy...")

        def centre_and_save():
            centred, centroid = centre_point_cloud(dataset["df"])
            filepath = save_centred_point_cloud(centred, dataset["filepath"], centroid)
            return filepath, centroid

        self.centre_worker = WorkerThread(centre_and_save)

        def on_finished(result):
            filepath, centroid = result
            self.set_loading_state(False, "Ready.")
            QMessageBox.information(
                self,
                "Centred Copy Created",
                "The original file was not changed.\n\n"
                f"Saved copy:\n{filepath}\n\n"
                "Original centroid subtracted (data units):\n"
                f"X={centroid[0]:.3f}, Y={centroid[1]:.3f}, Z={centroid[2]:.3f}",
            )

        def on_error(error):
            self.set_loading_state(False, "Could not create centred copy.")
            QMessageBox.critical(self, "Centred Copy Error", str(error))

        self.centre_worker.finished.connect(on_finished)
        self.centre_worker.error.connect(on_error)
        self.centre_worker.start()

    def closeEvent(self, event):
        """Offer Save / Discard / Cancel when project-owned state changed."""
        if not self.project_dirty:
            event.accept()
            return

        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Warning)
        dialog.setWindowTitle("Unsaved Project Changes")
        dialog.setText("The project has unsaved changes.")
        dialog.setInformativeText("Save before closing?")
        dialog.setStandardButtons(
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel
        )
        dialog.setDefaultButton(QMessageBox.StandardButton.Save)
        choice = dialog.exec()
        if choice == QMessageBox.StandardButton.Save:
            if self.save_project():
                event.accept()
            else:
                event.ignore()
        elif choice == QMessageBox.StandardButton.Discard:
            event.accept()
        else:
            event.ignore()
