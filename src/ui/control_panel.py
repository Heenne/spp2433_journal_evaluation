from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QSlider, QComboBox, 
    QCheckBox, QPushButton, QGroupBox, QHBoxLayout, QFileDialog, QListWidget, QListWidgetItem,
    QDoubleSpinBox, QSpinBox, QTabWidget, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal

class ControlPanel(QWidget):
    # Signals
    add_dataset_requested = pyqtSignal()
    add_quick_ref_requested = pyqtSignal()
    remove_dataset_requested = pyqtSignal(int)
    selection_changed = pyqtSignal(int)
    visibility_toggled = pyqtSignal(int, bool)
    settings_changed = pyqtSignal()
    export_requested = pyqtSignal(str)
    save_data_requested = pyqtSignal()
    run_icp_requested = pyqtSignal(int, int, float, str) # source_idx, target_idx, max_dist, method
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # --- Global Dataset List ---
        list_group = QGroupBox("Loaded Point Clouds")
        list_layout = QVBoxLayout()
        
        self.dataset_list = QListWidget()
        self.dataset_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.dataset_list.itemChanged.connect(self._on_item_changed)
        list_layout.addWidget(self.dataset_list)
        
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Add Data...")
        self.btn_add.clicked.connect(self.add_dataset_requested.emit)
        
        self.btn_add_quick_ref = QPushButton("Add Quick Ref")
        self.btn_add_quick_ref.clicked.connect(self.add_quick_ref_requested.emit)
        
        self.btn_remove = QPushButton("Remove Selected")
        self.btn_remove.clicked.connect(self._on_remove_clicked)
        
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_add_quick_ref)
        btn_layout.addWidget(self.btn_remove)
        list_layout.addLayout(btn_layout)
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)
        
        self.tabs = QTabWidget()
        
        # --- Tab 1: Appearance ---
        tab_data = QWidget()
        data_layout = QVBoxLayout()
        
        colors_group = QGroupBox("Color Settings")
        colors_layout = QVBoxLayout()
        colors_layout.addWidget(QLabel("Base Color:"))
        self.base_color_combo = QComboBox()
        self.base_color_combo.addItems(["C0", "C1", "C2", "C3", "C4", "C5", "red", "green", "blue", "gray", "black", "orange", "purple"])
        self.base_color_combo.currentIndexChanged.connect(self._on_settings_changed)
        colors_layout.addWidget(self.base_color_combo)
        
        colors_layout.addWidget(QLabel("Color Mapping Column (Overrides Base Color):"))
        self.color_combo = QComboBox()
        self.color_combo.addItem("None")
        self.color_combo.currentIndexChanged.connect(self._on_settings_changed)
        colors_layout.addWidget(self.color_combo)
        colors_group.setLayout(colors_layout)
        data_layout.addWidget(colors_group)
        
        export_group = QGroupBox("Export")
        export_layout = QVBoxLayout()
        self.btn_export = QPushButton("Export Plot")
        self.btn_export.clicked.connect(self._on_export_clicked)
        export_layout.addWidget(self.btn_export)
        export_group.setLayout(export_layout)
        data_layout.addWidget(export_group)
        
        data_layout.addStretch()
        tab_data.setLayout(data_layout)
        
        # --- Tab 2: Filtering ---
        tab_filter = QWidget()
        filter_layout = QVBoxLayout()
        
        # Voxel Downsampling
        voxel_group = QGroupBox("Voxel Grid Downsampling (Uniform)")
        voxel_layout = QHBoxLayout()
        self.voxel_check = QCheckBox("Enable Voxel Filter")
        self.voxel_check.stateChanged.connect(self._on_settings_changed)
        self.voxel_check.setToolTip("Uniformly downsamples the point cloud by merging points within 3D grid cells (voxels).")
        
        self.voxel_spin = QDoubleSpinBox()
        self.voxel_spin.setRange(0.001, 1000.0)
        self.voxel_spin.setToolTip("Size of the voxel grid cell in data units. Auto-calculated on load based on dataset bounds.")
        self.voxel_spin.setValue(0.1)
        self.voxel_spin.setSingleStep(0.05)
        self.voxel_spin.setDecimals(3)
        self.voxel_spin.valueChanged.connect(self._on_settings_changed)
        voxel_layout.addWidget(self.voxel_check)
        voxel_layout.addWidget(QLabel("Voxel Size:"))
        voxel_layout.addWidget(self.voxel_spin)
        voxel_group.setLayout(voxel_layout)
        filter_layout.addWidget(voxel_group)
        

        
        # Outliers
        outlier_group = QGroupBox("Outlier Filters")
        outlier_layout = QVBoxLayout()
        
        zscore_layout = QHBoxLayout()
        self.zscore_check = QCheckBox("Z-Score")
        self.zscore_check.stateChanged.connect(self._on_settings_changed)
        self.zscore_spin = QDoubleSpinBox()
        self.zscore_spin.setRange(0.1, 10.0)
        self.zscore_spin.setValue(3.0)
        self.zscore_spin.setSingleStep(0.1)
        self.zscore_spin.valueChanged.connect(self._on_settings_changed)
        zscore_layout.addWidget(self.zscore_check)
        zscore_layout.addWidget(self.zscore_spin)
        outlier_layout.addLayout(zscore_layout)
        
        sor_layout = QHBoxLayout()
        self.sor_check = QCheckBox("SOR")
        self.sor_check.stateChanged.connect(self._on_settings_changed)
        self.sor_k_spin = QSpinBox()
        self.sor_k_spin.setRange(1, 1000)
        self.sor_k_spin.setValue(50)
        self.sor_k_spin.valueChanged.connect(self._on_settings_changed)
        self.sor_std_spin = QDoubleSpinBox()
        self.sor_std_spin.setRange(0.1, 10.0)
        self.sor_std_spin.setValue(1.0)
        self.sor_std_spin.valueChanged.connect(self._on_settings_changed)
        sor_layout.addWidget(self.sor_check)
        sor_layout.addWidget(QLabel("k:"))
        sor_layout.addWidget(self.sor_k_spin)
        sor_layout.addWidget(QLabel("Std:"))
        sor_layout.addWidget(self.sor_std_spin)
        outlier_layout.addLayout(sor_layout)
        
        bbox_layout = QVBoxLayout()
        self.bbox_check = QCheckBox("Z-Bounds")
        self.bbox_check.stateChanged.connect(self._on_settings_changed)
        bbox_layout.addWidget(self.bbox_check)
        bbox_grid = QHBoxLayout()
        self.bbox_zmin = QDoubleSpinBox()
        self.bbox_zmin.setRange(-10000, 10000)
        self.bbox_zmin.setValue(-1000)
        self.bbox_zmin.valueChanged.connect(self._on_settings_changed)
        self.bbox_zmax = QDoubleSpinBox()
        self.bbox_zmax.setRange(-10000, 10000)
        self.bbox_zmax.setValue(1000)
        self.bbox_zmax.valueChanged.connect(self._on_settings_changed)
        bbox_grid.addWidget(QLabel("Min:"))
        bbox_grid.addWidget(self.bbox_zmin)
        bbox_grid.addWidget(QLabel("Max:"))
        bbox_grid.addWidget(self.bbox_zmax)
        bbox_layout.addLayout(bbox_grid)
        outlier_layout.addLayout(bbox_layout)
        
        outlier_group.setLayout(outlier_layout)
        filter_layout.addWidget(outlier_group)
        
        self.btn_save_data = QPushButton("Save Filtered Data")
        self.btn_save_data.clicked.connect(self.save_data_requested.emit)
        filter_layout.addWidget(self.btn_save_data)
        
        filter_layout.addStretch()
        tab_filter.setLayout(filter_layout)
        
        # --- Tab 3: Transform & Align ---
        tab_transform = QWidget()
        transform_layout = QVBoxLayout()
        
        # Manual Transform
        manual_group = QGroupBox("Manual Transform (Selected Dataset)")
        manual_form = QFormLayout()
        
        self.tx_spin = QDoubleSpinBox()
        self.ty_spin = QDoubleSpinBox()
        self.tz_spin = QDoubleSpinBox()
        for spin in (self.tx_spin, self.ty_spin, self.tz_spin):
            spin.setRange(-10000.0, 10000.0)
            spin.setDecimals(3)
            spin.setSingleStep(0.1)
            
        self.rx_spin = QDoubleSpinBox()
        self.ry_spin = QDoubleSpinBox()
        self.rz_spin = QDoubleSpinBox()
        for spin in (self.rx_spin, self.ry_spin, self.rz_spin):
            spin.setRange(-180.0, 180.0)
            spin.setDecimals(2)
            spin.setSingleStep(1.0)
            
        manual_form.addRow("Translate X (units):", self.tx_spin)
        manual_form.addRow("Translate Y (units):", self.ty_spin)
        manual_form.addRow("Translate Z (units):", self.tz_spin)
        manual_form.addRow("Rotate X (deg):", self.rx_spin)
        manual_form.addRow("Rotate Y (deg):", self.ry_spin)
        manual_form.addRow("Rotate Z (deg):", self.rz_spin)
        
        # Invert axis options
        invert_layout = QHBoxLayout()
        self.invert_x_check = QCheckBox("Invert X")
        self.invert_y_check = QCheckBox("Invert Y")
        self.invert_z_check = QCheckBox("Invert Z")
        # Apply is now done via button instead of stateChanged
        invert_layout.addWidget(self.invert_x_check)
        invert_layout.addWidget(self.invert_y_check)
        invert_layout.addWidget(self.invert_z_check)
        manual_form.addRow("Invert Axis:", invert_layout)
        
        self.btn_apply_transform = QPushButton("Apply Transform")
        self.btn_apply_transform.clicked.connect(self._on_settings_changed)
        manual_form.addRow("", self.btn_apply_transform)
        
        manual_group.setLayout(manual_form)
        transform_layout.addWidget(manual_group)
        
        # ICP Group
        icp_group = QGroupBox("ICP Alignment")
        icp_layout = QFormLayout()
        self.icp_target_combo = QComboBox()
        
        self.icp_method_combo = QComboBox()
        self.icp_method_combo.addItems(["Standard ICP", "Robust ICP (Partial Overlap)", "SciPy Custom Optimizer"])
        
        self.icp_distance_spin = QDoubleSpinBox()
        self.icp_distance_spin.setRange(0.001, 10000.0)
        self.icp_distance_spin.setValue(1.0)
        self.icp_distance_spin.setDecimals(3)
        self.icp_distance_spin.setToolTip("The search radius for matching points. Set this to your estimated manual alignment error in your data's units. E.g., if you are off by ~2 meters, enter 2.0. Values that are too large cause incorrect matches.")
        
        self.btn_run_icp = QPushButton("Run ICP (Selected -> Target)")
        self.btn_run_icp.clicked.connect(self._on_run_icp_clicked)
        
        icp_layout.addRow("Target (Reference):", self.icp_target_combo)
        icp_layout.addRow("Method:", self.icp_method_combo)
        icp_layout.addRow("Max Distance:", self.icp_distance_spin)
        
        icp_info = QLabel("Tip: Set this to your estimated manual alignment error.\nIf you aligned them to within ~2 units, enter 2.0.\nIf this is too large, the alignment will fail.")
        icp_info.setWordWrap(True)
        icp_info.setStyleSheet("color: #888888; font-size: 11px; font-style: italic;")
        icp_layout.addRow("", icp_info)
        
        icp_layout.addRow("", self.btn_run_icp)
        icp_group.setLayout(icp_layout)
        transform_layout.addWidget(icp_group)
        
        transform_layout.addStretch()
        tab_transform.setLayout(transform_layout)
        
        self.tabs.addTab(tab_data, "Data & Display")
        self.tabs.addTab(tab_filter, "Filtering")
        self.tabs.addTab(tab_transform, "Transform & Align")
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)
        
        # Group parts that require selection
        self.requires_selection_widgets = [
            colors_group, voxel_group, outlier_group,
            self.btn_save_data, manual_group, icp_group
        ]
        self._enable_selection_widgets(False)
        
    def _enable_selection_widgets(self, enable: bool):
        for w in self.requires_selection_widgets:
            w.setEnabled(enable)
            
    def add_dataset_to_list(self, name: str, checked: bool = True):
        item = QListWidgetItem(name)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        self.dataset_list.addItem(item)
        self.dataset_list.setCurrentItem(item)
        
        # Update target combo
        self.icp_target_combo.addItem(name)
        
    def remove_dataset_from_list(self, idx: int):
        self.dataset_list.takeItem(idx)
        self.icp_target_combo.removeItem(idx)
        
    def _on_selection_changed(self):
        idx = self.dataset_list.currentRow()
        self._enable_selection_widgets(idx >= 0)
        if idx >= 0:
            self.selection_changed.emit(idx)
        
    def _on_item_changed(self, item):
        idx = self.dataset_list.row(item)
        is_visible = (item.checkState() == Qt.CheckState.Checked)
        self.visibility_toggled.emit(idx, is_visible)
        
    def _on_remove_clicked(self):
        idx = self.dataset_list.currentRow()
        if idx >= 0:
            self.remove_dataset_requested.emit(idx)
            
    def _on_settings_changed(self):
        if self.signalsBlocked():
            return
        self.settings_changed.emit()
        
    def _on_export_clicked(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Export Plot", "", "PNG Image (*.png);;JPEG Image (*.jpg);;SVG Vector (*.svg)")
        if filepath:
            self.export_requested.emit(filepath)
            
    def _on_run_icp_clicked(self):
        source_idx = self.dataset_list.currentRow()
        target_idx = self.icp_target_combo.currentIndex()
        if source_idx >= 0 and target_idx >= 0 and source_idx != target_idx:
            self.run_icp_requested.emit(source_idx, target_idx, self.icp_distance_spin.value(), self.icp_method_combo.currentText())
            
    def update_columns(self, columns: list):
        self.color_combo.blockSignals(True)
        self.color_combo.clear()
        self.color_combo.addItem("None")
        for col in columns:
            self.color_combo.addItem(col)
        self.color_combo.blockSignals(False)
        
    def apply_config(self, config: dict):
        self.blockSignals(True)
        
        # Block sub-signals
        for w in [self.base_color_combo, self.color_combo,
                  self.invert_x_check, self.invert_y_check, self.invert_z_check,
                  self.zscore_check, self.zscore_spin, self.sor_check, self.sor_k_spin, self.sor_std_spin,
                  self.bbox_check, self.bbox_zmin, self.bbox_zmax, self.voxel_check, self.voxel_spin,
                  self.tx_spin, self.ty_spin, self.tz_spin, self.rx_spin, self.ry_spin, self.rz_spin]:
            w.blockSignals(True)
            
        if "base_color" in config and config["base_color"]:
            idx = self.base_color_combo.findText(config["base_color"])
            if idx >= 0: self.base_color_combo.setCurrentIndex(idx)
        if "color_col" in config and config["color_col"]:
            idx = self.color_combo.findText(config["color_col"])
            if idx >= 0: self.color_combo.setCurrentIndex(idx)
        else:
            self.color_combo.setCurrentIndex(0)
            
        self.invert_x_check.setChecked(config.get("invert_x", False))
        self.invert_y_check.setChecked(config.get("invert_y", False))
        self.invert_z_check.setChecked(config.get("invert_z", False))
        
        self.zscore_check.setChecked(config.get("zscore_enabled", False))
        self.zscore_spin.setValue(config.get("zscore_threshold", 3.0))
        self.sor_check.setChecked(config.get("sor_enabled", False))
        self.sor_k_spin.setValue(config.get("sor_k", 50))
        self.sor_std_spin.setValue(config.get("sor_std", 1.0))
        self.bbox_check.setChecked(config.get("bbox_enabled", False))
        self.bbox_zmin.setValue(config.get("bbox_zmin", -1000.0))
        self.bbox_zmax.setValue(config.get("bbox_zmax", 1000.0))
        
        self.voxel_check.setChecked(config.get("voxel_enabled", False))
        self.voxel_spin.setValue(config.get("voxel_size", 0.1))
        
        self.tx_spin.setValue(config.get("tx", 0.0))
        self.ty_spin.setValue(config.get("ty", 0.0))
        self.tz_spin.setValue(config.get("tz", 0.0))
        self.rx_spin.setValue(config.get("rx", 0.0))
        self.ry_spin.setValue(config.get("ry", 0.0))
        self.rz_spin.setValue(config.get("rz", 0.0))
        
        # Unblock sub-signals
        for w in [self.base_color_combo, self.color_combo,
                  self.invert_x_check, self.invert_y_check, self.invert_z_check,
                  self.zscore_check, self.zscore_spin, self.sor_check, self.sor_k_spin, self.sor_std_spin,
                  self.bbox_check, self.bbox_zmin, self.bbox_zmax, self.voxel_check, self.voxel_spin,
                  self.tx_spin, self.ty_spin, self.tz_spin, self.rx_spin, self.ry_spin, self.rz_spin]:
            w.blockSignals(False)
            
        self.blockSignals(False)
        
    def get_current_settings(self) -> dict:
        return {
            "base_color": self.base_color_combo.currentText(),
            "color_col": self.color_combo.currentText() if self.color_combo.currentText() != "None" else None,
            "invert_x": self.invert_x_check.isChecked(),
            "invert_y": self.invert_y_check.isChecked(),
            "invert_z": self.invert_z_check.isChecked(),
            "zscore_enabled": self.zscore_check.isChecked(),
            "zscore_threshold": self.zscore_spin.value(),
            "sor_enabled": self.sor_check.isChecked(),
            "sor_k": self.sor_k_spin.value(),
            "sor_std": self.sor_std_spin.value(),
            "bbox_enabled": self.bbox_check.isChecked(),
            "bbox_zmin": self.bbox_zmin.value(),
            "bbox_zmax": self.bbox_zmax.value(),
            "voxel_enabled": self.voxel_check.isChecked(),
            "voxel_size": self.voxel_spin.value(),
            "tx": self.tx_spin.value(),
            "ty": self.ty_spin.value(),
            "tz": self.tz_spin.value(),
            "rx": self.rx_spin.value(),
            "ry": self.ry_spin.value(),
            "rz": self.rz_spin.value()
        }
