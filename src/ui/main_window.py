import os
import pandas as pd
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFileDialog, 
    QMessageBox, QMenuBar, QMenu
)
from PyQt6.QtGui import QAction
from src.ui.plot_canvas import PlotCanvas
from src.ui.control_panel import ControlPanel
from src.data.parser import parse_point_cloud_file
from src.data.filter import (
    filter_by_stride, filter_by_random_percentage, check_cached_filtered_files, 
    save_filtered_data, load_filter_config, save_filter_config,
    filter_by_zscore, filter_by_bounding_box, filter_by_sor
)
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
            # We handle the first selected file for simplicity in loading initially.
            # Multi-file support can be extended, but let's load the first one.
            filepath = filepaths[0]
            
            # Check for cached files
            cached_files = check_cached_filtered_files(filepath)
            if cached_files:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Question)
                msg.setWindowTitle("Cached Data Found")
                msg.setText("Filtered versions of this dataset exist. Load a cached version?")
                msg.setInformativeText("This can be much faster for large files.")
                
                # We'll just list the first cached file as an option for simplicity, or we can build a custom dialog.
                # Here we just offer yes/no to load the first available cached file.
                btn_yes = msg.addButton("Yes, load cached", QMessageBox.ButtonRole.YesRole)
                btn_no = msg.addButton("No, load original", QMessageBox.ButtonRole.NoRole)
                msg.exec()
                
                if msg.clickedButton() == btn_yes:
                    filepath = cached_files[0]
            
            self.load_file(filepath)
            
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
            config = {
                "stride": 1,
                "rand_pct": 1.0,
                "base_color": cycle_colors[idx],
                "color_col": None,
                "invert_x": False,
                "invert_y": False,
                "invert_z": False,
                "zscore_enabled": False,
                "zscore_threshold": 3.0,
                "sor_enabled": False,
                "sor_k": 50,
                "sor_std": 1.0,
                "bbox_enabled": False,
                "bbox_zmin": -1000.0,
                "bbox_zmax": 1000.0
            }
            if len(df) > 100000:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setWindowTitle("Massive Dataset Detected")
                msg.setText(f"This dataset has {len(df)} points. Would you like to automatically apply a strict 10% random sample filter before rendering?")
                btn_yes = msg.addButton("Yes, apply strict filter", QMessageBox.ButtonRole.YesRole)
                btn_no = msg.addButton("No, render anyway", QMessageBox.ButtonRole.NoRole)
                msg.exec()
                
                if msg.clickedButton() == btn_yes:
                    config["rand_pct"] = 0.1
                    
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
        # add_dataset_to_list automatically selects it, triggering on_selection_changed
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
            
            # Save config
            save_filter_config(self.datasets[idx]["filepath"], st)
            self.update_plot()
            
    def update_plot(self):
        for d in self.datasets:
            if not d["visible"]:
                continue
                
            df = d["df"]
            st = d["settings"]
            
            df_filtered = df
            
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
            
            if st["stride"] > 1:
                df_filtered = filter_by_stride(df_filtered, st["stride"])
            if st["rand_pct"] < 1.0:
                df_filtered = filter_by_random_percentage(df_filtered, st["rand_pct"])
                
            d["df_filtered"] = df_filtered
            
        self.plot_canvas.plot_datasets(self.datasets)
        
        # Calculate total points shown
        total_points = sum([len(d["df_filtered"]) for d in self.datasets if d["visible"] and "df_filtered" in d])
        self.statusBar().showMessage(f"Showing {total_points} total points across {sum(1 for d in self.datasets if d['visible'])} dataset(s).")
        
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
        
        df_filtered = df
        
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
            
        if st["stride"] > 1:
            df_filtered = filter_by_stride(df_filtered, st["stride"])
        if st["rand_pct"] < 1.0:
            df_filtered = filter_by_random_percentage(df_filtered, st["rand_pct"])
            
        filter_str = f"s{st['stride']}_r{int(st['rand_pct']*100)}"
        
        try:
            new_fp = save_filtered_data(df_filtered, dataset["filepath"], "downsample", filter_str)
            QMessageBox.information(self, "Success", f"Filtered dataset saved to:\n{new_fp}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save data: {str(e)}")
