from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QSlider, QComboBox, 
    QCheckBox, QPushButton, QGroupBox, QHBoxLayout, QFileDialog, QListWidget, QListWidgetItem
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
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # --- Dataset List Group ---
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
        
        # --- Selected Dataset Settings Group ---
        self.settings_group = QGroupBox("Selected Settings")
        settings_layout = QVBoxLayout()
        
        self.stride_label = QLabel("Stride (keep 1 in N): 1")
        self.stride_slider = QSlider(Qt.Orientation.Horizontal)
        self.stride_slider.setMinimum(1)
        self.stride_slider.setMaximum(100)
        self.stride_slider.setValue(1)
        self.stride_slider.valueChanged.connect(self._on_settings_changed)
        
        self.rand_label = QLabel("Random Sample %: 100")
        self.rand_slider = QSlider(Qt.Orientation.Horizontal)
        self.rand_slider.setMinimum(1)
        self.rand_slider.setMaximum(100)
        self.rand_slider.setValue(100)
        self.rand_slider.valueChanged.connect(self._on_settings_changed)
        
        settings_layout.addWidget(self.stride_label)
        settings_layout.addWidget(self.stride_slider)
        settings_layout.addWidget(self.rand_label)
        settings_layout.addWidget(self.rand_slider)
        
        # Colors
        settings_layout.addWidget(QLabel("Base Color:"))
        self.base_color_combo = QComboBox()
        self.base_color_combo.addItems(["C0", "C1", "C2", "C3", "C4", "C5", "red", "green", "blue", "gray", "black", "orange", "purple"])
        self.base_color_combo.currentIndexChanged.connect(self._on_settings_changed)
        settings_layout.addWidget(self.base_color_combo)
        
        settings_layout.addWidget(QLabel("Color Mapping Column (Overrides Base Color):"))
        self.color_combo = QComboBox()
        self.color_combo.addItem("None")
        self.color_combo.currentIndexChanged.connect(self._on_settings_changed)
        settings_layout.addWidget(self.color_combo)
        
        # Axis Inversion
        invert_layout = QHBoxLayout()
        self.invert_x_check = QCheckBox("Invert X")
        self.invert_y_check = QCheckBox("Invert Y")
        self.invert_z_check = QCheckBox("Invert Z")
        self.invert_x_check.stateChanged.connect(self._on_settings_changed)
        self.invert_y_check.stateChanged.connect(self._on_settings_changed)
        self.invert_z_check.stateChanged.connect(self._on_settings_changed)
        invert_layout.addWidget(self.invert_x_check)
        invert_layout.addWidget(self.invert_y_check)
        invert_layout.addWidget(self.invert_z_check)
        settings_layout.addLayout(invert_layout)
        
        self.btn_save_data = QPushButton("Save Filtered Data")
        self.btn_save_data.clicked.connect(self.save_data_requested.emit)
        settings_layout.addWidget(self.btn_save_data)
        
        self.settings_group.setLayout(settings_layout)
        self.settings_group.setEnabled(False) # Disabled until selection made
        layout.addWidget(self.settings_group)
        
        # --- Export ---
        export_group = QGroupBox("Export")
        export_layout = QVBoxLayout()
        self.btn_export = QPushButton("Export Plot")
        self.btn_export.clicked.connect(self._on_export_clicked)
        export_layout.addWidget(self.btn_export)
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def add_dataset_to_list(self, name: str, checked: bool = True):
        item = QListWidgetItem(name)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        self.dataset_list.addItem(item)
        self.dataset_list.setCurrentItem(item)
        
    def remove_dataset_from_list(self, idx: int):
        self.dataset_list.takeItem(idx)
        
    def _on_selection_changed(self):
        idx = self.dataset_list.currentRow()
        self.settings_group.setEnabled(idx >= 0)
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
        self.stride_label.setText(f"Stride (keep 1 in N): {self.stride_slider.value()}")
        self.rand_label.setText(f"Random Sample %: {self.rand_slider.value()}")
        self.settings_changed.emit()
        
    def _on_export_clicked(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Export Plot", "", "PNG Image (*.png);;JPEG Image (*.jpg);;SVG Vector (*.svg)")
        if filepath:
            self.export_requested.emit(filepath)
            
    def update_columns(self, columns: list):
        self.color_combo.blockSignals(True)
        self.color_combo.clear()
        self.color_combo.addItem("None")
        for col in columns:
            self.color_combo.addItem(col)
        self.color_combo.blockSignals(False)
        
    def apply_config(self, config: dict):
        self.blockSignals(True)
        self.stride_slider.blockSignals(True)
        self.rand_slider.blockSignals(True)
        self.base_color_combo.blockSignals(True)
        self.color_combo.blockSignals(True)
        self.invert_x_check.blockSignals(True)
        self.invert_y_check.blockSignals(True)
        self.invert_z_check.blockSignals(True)
        
        if "stride" in config:
            val = config["stride"]
            self.stride_slider.setValue(val)
            self.stride_label.setText(f"Stride (keep 1 in N): {val}")
            
        if "rand_pct" in config:
            val = int(config["rand_pct"] * 100)
            self.rand_slider.setValue(val)
            self.rand_label.setText(f"Random Sample %: {val}")
            
        if "base_color" in config and config["base_color"]:
            idx = self.base_color_combo.findText(config["base_color"])
            if idx >= 0:
                self.base_color_combo.setCurrentIndex(idx)
                
        if "color_col" in config and config["color_col"]:
            idx = self.color_combo.findText(config["color_col"])
            if idx >= 0:
                self.color_combo.setCurrentIndex(idx)
        else:
            self.color_combo.setCurrentIndex(0)
            
        self.invert_x_check.setChecked(config.get("invert_x", False))
        self.invert_y_check.setChecked(config.get("invert_y", False))
        self.invert_z_check.setChecked(config.get("invert_z", False))
            
        self.stride_slider.blockSignals(False)
        self.rand_slider.blockSignals(False)
        self.base_color_combo.blockSignals(False)
        self.color_combo.blockSignals(False)
        self.invert_x_check.blockSignals(False)
        self.invert_y_check.blockSignals(False)
        self.invert_z_check.blockSignals(False)
        self.blockSignals(False)
        
    def get_current_settings(self) -> dict:
        return {
            "stride": self.stride_slider.value(),
            "rand_pct": self.rand_slider.value() / 100.0,
            "base_color": self.base_color_combo.currentText(),
            "color_col": self.color_combo.currentText() if self.color_combo.currentText() != "None" else None,
            "invert_x": self.invert_x_check.isChecked(),
            "invert_y": self.invert_y_check.isChecked(),
            "invert_z": self.invert_z_check.isChecked()
        }
