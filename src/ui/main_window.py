import os
import pandas as pd
import numpy as np
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFileDialog, 
    QMessageBox, QMenuBar, QMenu, QApplication
)
from PyQt6.QtGui import QAction
from src.ui.plot_canvas import PlotCanvas
from src.ui.control_panel import ControlPanel
from src.data.parser import parse_point_cloud_file
from src.data.filter import (
    check_cached_filtered_files, 
    save_filtered_data, load_filter_config, save_filter_config,
    filter_by_zscore, filter_by_bounding_box, filter_by_sor, filter_by_voxel_grid
)
from src.utils.registration import run_icp, euler_translation_to_matrix
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Point Cloud Data Viewer")
        self.resize(1100, 750)
        
        self.datasets = []
        
        self.init_ui()
        
    def init_ui(self):
        # Menu Bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        
        open_action = QAction("Open File...", self)
        open_action.triggered.connect(self.open_file_dialog)
        file_menu.addAction(open_action)
        
        open_proj_action = QAction("Open Project...", self)
        open_proj_action.triggered.connect(self.open_project_dialog)
        file_menu.addAction(open_proj_action)
        
        save_proj_action = QAction("Save Project...", self)
        save_proj_action.triggered.connect(self.save_project_dialog)
        file_menu.addAction(save_proj_action)
        
        # Tools Menu
        tools_menu = menu_bar.addMenu("Tools")
        convert_action = QAction("Convert TXT to CSV...", self)
        convert_action.triggered.connect(self.open_convert_dialog)
        tools_menu.addAction(convert_action)
        
        # Settings Menu
        settings_menu = menu_bar.addMenu("Settings")
        set_ref_action = QAction("Select Quick Reference File...", self)
        set_ref_action.triggered.connect(self.select_quick_reference)
        settings_menu.addAction(set_ref_action)
        
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout()
        
        # Control Panel
        self.control_panel = ControlPanel()
        self.control_panel.add_dataset_requested.connect(self.open_file_dialog)
        self.control_panel.add_quick_ref_requested.connect(self.add_quick_reference)
        self.control_panel.remove_dataset_requested.connect(self.remove_dataset)
        self.control_panel.selection_changed.connect(self.on_selection_changed)
        self.control_panel.visibility_toggled.connect(self.on_visibility_toggled)
        self.control_panel.settings_changed.connect(self.on_settings_changed)
        self.control_panel.export_requested.connect(self.export_plot)
        self.control_panel.save_data_requested.connect(self.save_filtered_dataset)
        self.control_panel.run_icp_requested.connect(self.on_run_icp)
        
        # Plot Canvas
        plot_layout = QVBoxLayout()
        self.plot_canvas = PlotCanvas(self)
        self.toolbar = NavigationToolbar(self.plot_canvas, self)
        
        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.plot_canvas)
        
        plot_widget = QWidget()
        plot_widget.setLayout(plot_layout)
        
        layout.addWidget(self.control_panel, 1) # proportion 1
        layout.addWidget(plot_widget, 3) # proportion 3
        
        central_widget.setLayout(layout)
        
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
            filepath = filepaths[0]
            
            cached_files = check_cached_filtered_files(filepath)
            if cached_files:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Question)
                msg.setWindowTitle("Cached Data Found")
                msg.setText("Filtered versions of this dataset exist. Load a cached version?")
                msg.setInformativeText("This can be much faster for large files.")
                
                btn_yes = msg.addButton("Yes, load cached", QMessageBox.ButtonRole.YesRole)
                btn_no = msg.addButton("No, load original", QMessageBox.ButtonRole.NoRole)
                msg.exec()
                
                if msg.clickedButton() == btn_yes:
                    filepath = cached_files[0]
            
            self.load_file(filepath)
            
    def open_project_dialog(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "", "Project Files (*.json);;All Files (*)"
        )
        if filepath:
            try:
                import json
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                # Load all files in the project
                for fp in data.get("datasets", []):
                    if os.path.exists(fp):
                        self.load_file(fp)
                    else:
                        QMessageBox.warning(self, "Missing File", f"Could not find dataset file:\n{fp}")
                        
                self.statusBar().showMessage(f"Loaded project: {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Project Load Error", f"Failed to load project:\n{str(e)}")

    def save_project_dialog(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Project", "", "Project Files (*.json)"
        )
        if filepath:
            try:
                import json
                data = {
                    "datasets": [d["filepath"] for d in self.datasets]
                }
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=4)
                self.statusBar().showMessage(f"Project saved to {filepath}")
                QMessageBox.information(self, "Success", "Project saved successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Project Save Error", f"Failed to save project:\n{str(e)}")
            
    def load_file(self, filepath: str):
        self.statusBar().showMessage(f"Loading {filepath}...")
        
        df, add_cols, err = parse_point_cloud_file(filepath)
        if err:
            QMessageBox.critical(self, "Error", err)
            self.statusBar().showMessage("Error loading file.")
            return
            
        name = os.path.basename(filepath)
        self.statusBar().showMessage(f"Loaded {len(df)} points from {name}")
        
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
                "tx": 0.0, "ty": 0.0, "tz": 0.0, "rx": 0.0, "ry": 0.0, "rz": 0.0
            }
            if len(df) > 100000:
                config["voxel_enabled"] = True
                QMessageBox.information(
                    self, 
                    "Auto-Filter Activated", 
                    f"This dataset has {len(df):,} points which could cause lag.\n\n"
                    f"A Voxel Downsample filter has been automatically enabled with a size of {auto_voxel_size:.3f} units."
                )
                    
        dataset = {
            "filepath": filepath,
            "name": name,
            "df": df,
            "settings": config,
            "visible": True,
            "add_cols": add_cols
        }
        
        self.datasets.append(dataset)
        self.control_panel.add_dataset_to_list(name, checked=True)
        self.update_plot()
        
    def remove_dataset(self, idx: int):
        if 0 <= idx < len(self.datasets):
            del self.datasets[idx]
            self.control_panel.remove_dataset_from_list(idx)
            self.update_plot()
            
    def on_selection_changed(self, idx: int):
        if 0 <= idx < len(self.datasets):
            dataset = self.datasets[idx]
            self.control_panel.update_columns(dataset["add_cols"])
            self.control_panel.apply_config(dataset["settings"])
            
    def on_visibility_toggled(self, idx: int, is_visible: bool):
        if 0 <= idx < len(self.datasets):
            self.datasets[idx]["visible"] = is_visible
            self.update_plot()
            
    def on_settings_changed(self):
        idx = self.control_panel.dataset_list.currentRow()
        if 0 <= idx < len(self.datasets):
            st = self.control_panel.get_current_settings()
            self.datasets[idx]["settings"] = st
            save_filter_config(self.datasets[idx]["filepath"], st)
            self.update_plot()
            
    def apply_transform(self, df: pd.DataFrame, settings: dict) -> pd.DataFrame:
        """Applies manual translation and rotation to the DataFrame coordinates."""
        tx, ty, tz = settings.get("tx", 0.0), settings.get("ty", 0.0), settings.get("tz", 0.0)
        rx, ry, rz = settings.get("rx", 0.0), settings.get("ry", 0.0), settings.get("rz", 0.0)
        
        if tx == 0.0 and ty == 0.0 and tz == 0.0 and rx == 0.0 and ry == 0.0 and rz == 0.0:
            return df
            
        mat = euler_translation_to_matrix(tx, ty, tz, rx, ry, rz)
        
        points = df[['X', 'Y', 'Z']].values
        # Apply 4x4 matrix
        ones = np.ones((points.shape[0], 1))
        points_4d = np.hstack([points, ones])
        transformed_points = (mat @ points_4d.T).T[:, :3]
        
        df_out = df.copy()
        df_out['X'] = transformed_points[:, 0]
        df_out['Y'] = transformed_points[:, 1]
        df_out['Z'] = transformed_points[:, 2]
        return df_out
            
    def update_plot(self):
        from PyQt6.QtCore import Qt
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.statusBar().showMessage("Updating plot (processing filters)...")
        QApplication.processEvents()
        
        try:
            for d in self.datasets:
                if not d["visible"]:
                    continue
                    
                df = d["df"]
                st = d["settings"]
                
                # Apply Spatial Transformation first
                df_filtered = self.apply_transform(df, st)
                
                if st.get("bbox_enabled"):
                    df_filtered = filter_by_bounding_box(
                        df_filtered, 
                        z_min=st.get("bbox_zmin"), 
                        z_max=st.get("bbox_zmax")
                    )
                
                if st.get("zscore_enabled"):
                    df_filtered = filter_by_zscore(df_filtered, st.get("zscore_threshold", 3.0))
                    
                if st.get("sor_enabled"):
                    df_filtered = filter_by_sor(df_filtered, st.get("sor_k", 50), st.get("sor_std", 1.0))
                    
                if st.get("voxel_enabled"):
                    df_filtered = filter_by_voxel_grid(df_filtered, st.get("voxel_size", 0.1))
                    
                d["df_filtered"] = df_filtered
                
            self.plot_canvas.plot_datasets(self.datasets)
            
            total_points = sum([len(d["df_filtered"]) for d in self.datasets if d["visible"] and "df_filtered" in d])
            self.statusBar().showMessage(f"Showing {total_points} total points across {sum(1 for d in self.datasets if d['visible'])} dataset(s).")
        finally:
            QApplication.restoreOverrideCursor()

    def on_run_icp(self, source_idx: int, target_idx: int, max_corr_dist: float):
        from PyQt6.QtCore import Qt
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.statusBar().showMessage("Running ICP Alignment...")
        QApplication.processEvents()
        
        try:
            source_dataset = self.datasets[source_idx]
            target_dataset = self.datasets[target_idx]
            
            source_df = self.apply_transform(source_dataset["df"], source_dataset["settings"])
            target_df = self.apply_transform(target_dataset["df"], target_dataset["settings"])
            
            # Optional: Downsample for ICP to speed it up
            if len(source_df) > 50000:
                source_df = filter_by_voxel_grid(source_df, 0.5)
            if len(target_df) > 50000:
                target_df = filter_by_voxel_grid(target_df, 0.5)
                
            result, fitness = run_icp(source_df, target_df, max_correspondence_distance=max_corr_dist)
            if result:
                new_tx, new_ty, new_tz, new_rx, new_ry, new_rz = result
                
                # Combine the current transform with the new ICP result
                st = source_dataset["settings"]
                mat_current = euler_translation_to_matrix(st.get("tx", 0.0), st.get("ty", 0.0), st.get("tz", 0.0),
                                                          st.get("rx", 0.0), st.get("ry", 0.0), st.get("rz", 0.0))
                mat_icp = euler_translation_to_matrix(new_tx, new_ty, new_tz, new_rx, new_ry, new_rz)
                
                mat_final = mat_icp @ mat_current
                from src.utils.registration import matrix_to_euler_translation
                ftx, fty, ftz, frx, fry, frz = matrix_to_euler_translation(mat_final)
                
                st["tx"] = ftx
                st["ty"] = fty
                st["tz"] = ftz
                st["rx"] = frx
                st["ry"] = fry
                st["rz"] = frz
                
                save_filter_config(source_dataset["filepath"], st)
                
                # Update UI
                if self.control_panel.dataset_list.currentRow() == source_idx:
                    self.control_panel.apply_config(st)
                    
                self.update_plot()
                QMessageBox.information(self, "ICP Complete", f"Alignment finished.\nFitness score: {fitness:.4f}")
            else:
                QMessageBox.warning(self, "ICP Failed", "ICP Alignment failed or open3d is missing.")
        except Exception as e:
            QMessageBox.critical(self, "ICP Error", f"An error occurred during ICP:\n{str(e)}")
        finally:
            QApplication.restoreOverrideCursor()
            self.statusBar().showMessage("Ready.")
        
    def export_plot(self, filepath: str):
        try:
            self.plot_canvas.export_plot(filepath)
            self.statusBar().showMessage(f"Plot exported to {filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export plot: {str(e)}")
            
    def save_filtered_dataset(self):
        idx = self.control_panel.dataset_list.currentRow()
        if idx < 0 or idx >= len(self.datasets):
            return
            
        dataset = self.datasets[idx]
        df = dataset["df"]
        st = dataset["settings"]
        
        from PyQt6.QtCore import Qt
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.statusBar().showMessage("Saving dataset...")
        QApplication.processEvents()
        
        try:
            df_filtered = self.apply_transform(df, st)
            
            if st.get("bbox_enabled"):
                df_filtered = filter_by_bounding_box(df_filtered, z_min=st.get("bbox_zmin"), z_max=st.get("bbox_zmax"))
            if st.get("zscore_enabled"):
                df_filtered = filter_by_zscore(df_filtered, st.get("zscore_threshold", 3.0))
            if st.get("sor_enabled"):
                df_filtered = filter_by_sor(df_filtered, st.get("sor_k", 50), st.get("sor_std", 1.0))
                
            if st.get("voxel_enabled"):
                df_filtered = filter_by_voxel_grid(df_filtered, st.get("voxel_size", 0.1))
                
            filter_str = "transformed"
            
            new_fp = save_filtered_data(df_filtered, dataset["filepath"], "downsample", filter_str)
            QMessageBox.information(self, "Success", f"Filtered dataset saved to:\n{new_fp}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save data: {str(e)}")
        finally:
            QApplication.restoreOverrideCursor()
            self.statusBar().showMessage("Ready.")
