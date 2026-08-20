from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QSlider, QComboBox, 
    QCheckBox, QPushButton, QGroupBox, QHBoxLayout, QFileDialog, QListWidget, QListWidgetItem,
    QDoubleSpinBox, QSpinBox, QTabWidget, QFormLayout, QInputDialog, QMessageBox, QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal

class ControlPanel(QWidget):
    # Signals
    add_dataset_requested = pyqtSignal()
    add_quick_ref_requested = pyqtSignal()
    remove_dataset_requested = pyqtSignal(int)
    move_dataset_requested = pyqtSignal(int, int)
    selection_changed = pyqtSignal(int)
    visibility_toggled = pyqtSignal(int, bool)
    settings_changed = pyqtSignal()
    export_requested = pyqtSignal(str)
    save_data_requested = pyqtSignal()
    run_icp_requested = pyqtSignal(int, int, float, str) # source_idx, target_idx, max_dist, method
    run_legacy_global_alignment_requested = pyqtSignal(int, int, int) # source, reference, registration points
    run_auto_alignment_requested = pyqtSignal(int, int, int, float, float, float, float, float, float) # source, reference, points, +/- Tx/Ty/Tz, +/- Rx/Ry/Rz
    calculate_error_requested = pyqtSignal(int, int, float, int, bool, bool) # source_idx, reference_idx, cutoff, max_analysis_points, show_map, highlight_above_mean
    error_map_display_changed = pyqtSignal(bool)
    error_map_colour_mode_changed = pyqtSignal(str)
    camera_view_requested = pyqtSignal(str)
    camera_rotate_requested = pyqtSignal(float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_saved_transforms = {"Initial": {"tx": 0.0, "ty": 0.0, "tz": 0.0, "rx": 0.0, "ry": 0.0, "rz": 0.0}}
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

        self.btn_move_up = QPushButton("Move Up")
        self.btn_move_up.setToolTip("Move the selected cloud earlier in the list. Earlier clouds are drawn on top.")
        self.btn_move_up.clicked.connect(self._on_move_up_clicked)

        self.btn_move_down = QPushButton("Move Down")
        self.btn_move_down.setToolTip("Move the selected cloud later in the list. Later clouds are drawn underneath.")
        self.btn_move_down.clicked.connect(self._on_move_down_clicked)
        
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_add_quick_ref)
        btn_layout.addWidget(self.btn_remove)
        btn_layout.addWidget(self.btn_move_up)
        btn_layout.addWidget(self.btn_move_down)
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

        analysis_display_group = QGroupBox("Analysis Display")
        analysis_display_layout = QVBoxLayout()
        self.show_error_map_check = QCheckBox("Show latest pointwise error map")
        self.show_error_map_check.setToolTip(
            "Show or hide the latest calculated per-point distance colours for the selected cloud without "
            "recalculating the surface error."
        )
        self.show_error_map_check.toggled.connect(self.error_map_display_changed.emit)
        analysis_display_layout.addWidget(self.show_error_map_check)
        self.error_map_colour_mode_combo = QComboBox()
        self.error_map_colour_mode_combo.addItem("Closest-reference distance", "closest_distance")
        self.error_map_colour_mode_combo.addItem("Difference from mean distance", "difference_from_mean")
        self.error_map_colour_mode_combo.setToolTip(
            "Closest-reference distance colours each point by its actual nearest-reference error. "
            "Difference from mean distance centres a blue-white-red scale on the calculated mean error."
        )
        self.error_map_colour_mode_combo.currentIndexChanged.connect(
            lambda _: self.error_map_colour_mode_changed.emit(self.error_map_colour_mode_combo.currentData())
        )
        analysis_display_layout.addWidget(QLabel("Error-map colouring:"))
        analysis_display_layout.addWidget(self.error_map_colour_mode_combo)
        error_map_info = QLabel(
            "Available after a surface-error calculation. The normal cloud colours are restored when disabled."
        )
        error_map_info.setWordWrap(True)
        error_map_info.setStyleSheet("color: #888888; font-size: 11px; font-style: italic;")
        analysis_display_layout.addWidget(error_map_info)
        analysis_display_group.setLayout(analysis_display_layout)
        data_layout.addWidget(analysis_display_group)
        self.analysis_display_group = analysis_display_group

        camera_group = QGroupBox("Camera Orientation")
        camera_layout = QGridLayout()

        def camera_button(label, view_name, tooltip):
            button = QPushButton(label)
            button.setToolTip(tooltip)
            button.clicked.connect(lambda: self.camera_view_requested.emit(view_name))
            return button

        camera_layout.addWidget(camera_button("Top (+Z)", "top", "Look down the positive Z axis."), 0, 1)
        camera_layout.addWidget(camera_button("+X", "positive_x", "Look along the positive X axis."), 1, 0)
        camera_layout.addWidget(camera_button("−Y", "negative_y", "Look along the negative Y axis (front view)."), 1, 1)
        camera_layout.addWidget(camera_button("−X", "negative_x", "Look along the negative X axis."), 1, 2)
        camera_layout.addWidget(camera_button("+Y", "positive_y", "Look along the positive Y axis (back view)."), 2, 1)
        camera_layout.addWidget(camera_button("Bottom (−Z)", "bottom", "Look up the negative Z axis."), 3, 1)

        rotate_left = QPushButton("↺ 90°")
        rotate_left.setToolTip("Rotate the camera 90 degrees counter-clockwise around Z.")
        rotate_left.clicked.connect(lambda: self.camera_rotate_requested.emit(-90.0))
        isometric = camera_button("Isometric", "isometric", "Restore a useful 3-D isometric camera angle.")
        rotate_right = QPushButton("↻ 90°")
        rotate_right.setToolTip("Rotate the camera 90 degrees clockwise around Z.")
        rotate_right.clicked.connect(lambda: self.camera_rotate_requested.emit(90.0))
        camera_layout.addWidget(rotate_left, 4, 0)
        camera_layout.addWidget(isometric, 4, 1)
        camera_layout.addWidget(rotate_right, 4, 2)
        camera_group.setLayout(camera_layout)
        data_layout.addWidget(camera_group)
        
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
        
        # --- Tabs 3-5: Manual transform, legacy alignment, and fine alignment ---
        tab_manual_transform = QWidget()
        manual_transform_layout = QVBoxLayout()
        tab_legacy_alignment = QWidget()
        legacy_alignment_layout = QVBoxLayout()
        tab_fine_alignment = QWidget()
        fine_alignment_layout = QVBoxLayout()
        
        # Manual Transform
        manual_group = QGroupBox("Manual Transform (Selected Dataset)")
        manual_form = QFormLayout()
        
        # Transform Presets
        preset_layout = QHBoxLayout()
        self.preset_combo = QComboBox()
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        
        self.btn_preset_save = QPushButton("Save As...")
        self.btn_preset_save.clicked.connect(self._on_preset_save_clicked)
        
        self.btn_preset_rename = QPushButton("Rename...")
        self.btn_preset_rename.clicked.connect(self._on_preset_rename_clicked)
        
        self.btn_preset_delete = QPushButton("Delete")
        self.btn_preset_delete.clicked.connect(self._on_preset_delete_clicked)
        
        preset_layout.addWidget(self.preset_combo, 1)
        preset_layout.addWidget(self.btn_preset_save)
        preset_layout.addWidget(self.btn_preset_rename)
        preset_layout.addWidget(self.btn_preset_delete)
        
        manual_form.addRow("Preset:", preset_layout)
        
        
        self.tx_spin = QDoubleSpinBox()
        self.ty_spin = QDoubleSpinBox()
        self.tz_spin = QDoubleSpinBox()
        for spin in (self.tx_spin, self.ty_spin, self.tz_spin):
            # Drone clouds can use projected/geodetic coordinate origins while
            # the reference is local, so the rough translation may be large.
            spin.setRange(-1_000_000_000.0, 1_000_000_000.0)
            spin.setDecimals(3)
            spin.setSingleStep(0.1)

        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(0.000001, 1_000_000.0)
        self.scale_spin.setValue(1.0)
        self.scale_spin.setDecimals(6)
        self.scale_spin.setSingleStep(0.1)
        self.scale_spin.setToolTip(
            "Uniform scale applied before rotation and translation. Use this when one cloud is in metres "
            "and the reference is in millimetres (for example, 1000), then run bounded manual fine alignment."
        )
            
        self.rx_spin = QDoubleSpinBox()
        self.ry_spin = QDoubleSpinBox()
        self.rz_spin = QDoubleSpinBox()
        for spin in (self.rx_spin, self.ry_spin, self.rz_spin):
            spin.setRange(-180.0, 180.0)
            spin.setDecimals(2)
            spin.setSingleStep(1.0)
            
        manual_form.addRow("Uniform scale:", self.scale_spin)
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
        manual_transform_layout.addWidget(manual_group)
        
        # Legacy ICP remains available for specialised use, but unlike the
        # bounded optimizer below it can make an unrestricted pose change.
        icp_group = QGroupBox("Legacy ICP (unbounded)")
        icp_layout = QFormLayout()
        self.icp_target_combo = QComboBox()
        
        self.icp_method_combo = QComboBox()
        self.icp_method_combo.addItems(["Standard ICP", "Robust ICP (Partial Overlap)"])
        
        self.icp_distance_spin = QDoubleSpinBox()
        self.icp_distance_spin.setRange(0.001, 10000.0)
        self.icp_distance_spin.setValue(1.0)
        self.icp_distance_spin.setDecimals(3)
        self.icp_distance_spin.setToolTip("The search radius for matching points. Set this to your estimated manual alignment error in your data's units. E.g., if you are off by ~2 meters, enter 2.0. Values that are too large cause incorrect matches.")
        
        self.btn_run_icp = QPushButton("Run Legacy ICP (Selected -> Target)")
        self.btn_run_icp.clicked.connect(self._on_run_icp_clicked)
        
        icp_layout.addRow("Target (Reference):", self.icp_target_combo)
        icp_layout.addRow("Method:", self.icp_method_combo)
        icp_layout.addRow("Max Distance:", self.icp_distance_spin)
        
        icp_info = QLabel(
            "For drone scans with partial overlap, use Bounded Manual Fine Alignment below. "
            "Legacy ICP is retained for advanced use and can move to an unintended similar surface."
        )
        icp_info.setWordWrap(True)
        icp_info.setStyleSheet("color: #888888; font-size: 11px; font-style: italic;")
        icp_layout.addRow("", icp_info)
        
        icp_layout.addRow("", self.btn_run_icp)
        icp_group.setLayout(icp_layout)
        legacy_alignment_layout.addWidget(icp_group)

        legacy_global_group = QGroupBox("Previous Global Auto Alignment (PCA / FPFH)")
        legacy_global_layout = QFormLayout()
        self.legacy_global_target_combo = QComboBox()
        self.legacy_global_points_spin = QSpinBox()
        self.legacy_global_points_spin.setRange(1_000, 100_000)
        self.legacy_global_points_spin.setValue(30_000)
        self.legacy_global_points_spin.setSingleStep(5_000)
        self.legacy_global_points_spin.setToolTip(
            "Maximum voxel-downsampled points per cloud used by the previous global PCA/feature alignment."
        )
        self.btn_run_legacy_global_alignment = QPushButton("Run Previous Global Auto Align")
        self.btn_run_legacy_global_alignment.clicked.connect(self._on_run_legacy_global_alignment_clicked)
        legacy_global_info = QLabel(
            "This restores the previous broad PCA / centre-of-gravity / FPFH search. It uses the current "
            "transformed coordinates, including every enabled Invert X/Y/Z setting. It can find a coarse pose "
            "without a close manual placement, but is less safe on a smooth partial blade scan."
        )
        legacy_global_info.setWordWrap(True)
        legacy_global_info.setStyleSheet("color: #888888; font-size: 11px; font-style: italic;")
        legacy_global_layout.addRow("Reference:", self.legacy_global_target_combo)
        legacy_global_layout.addRow("Registration points:", self.legacy_global_points_spin)
        legacy_global_layout.addRow("", self.btn_run_legacy_global_alignment)
        legacy_global_layout.addRow("", legacy_global_info)
        legacy_global_group.setLayout(legacy_global_layout)
        legacy_alignment_layout.addWidget(legacy_global_group)

        # Automatic registration and comparison intentionally have their own
        # reference selectors: an alignment can be inspected before its error
        # is evaluated against the chosen reference cloud.
        auto_group = QGroupBox("Bounded Manual Fine Alignment (Selected -> Reference)")
        auto_layout = QFormLayout()
        self.auto_target_combo = QComboBox()
        self.auto_points_spin = QSpinBox()
        self.auto_points_spin.setRange(1_000, 100_000)
        self.auto_points_spin.setValue(30_000)
        self.auto_points_spin.setSingleStep(5_000)
        self.auto_points_spin.setToolTip(
            "Maximum voxel-downsampled points per cloud used to estimate the pose. "
            "The original clouds are not discarded."
        )

        def component_limit(default, maximum, decimals, suffix, tooltip):
            spin = QDoubleSpinBox()
            spin.setRange(0.0, maximum)
            spin.setValue(default)
            spin.setDecimals(decimals)
            spin.setSuffix(suffix)
            spin.setToolTip(tooltip)
            return spin

        translation_tooltip = (
            "Independent plus/minus correction from the manual pose at the overlap pivot, in data units. "
            "Set this to 0 to lock the axis."
        )
        self.auto_tx_limit_spin = component_limit(10.0, 1_000_000.0, 6, "", translation_tooltip)
        self.auto_ty_limit_spin = component_limit(10.0, 1_000_000.0, 6, "", translation_tooltip)
        self.auto_tz_limit_spin = component_limit(10.0, 1_000_000.0, 6, "", translation_tooltip)
        rotation_tooltip = (
            "Independent plus/minus XYZ Euler-angle correction from the manual pose. "
            "Set this to 0 to lock the axis."
        )
        self.auto_rx_limit_spin = component_limit(5.0, 30.0, 1, " deg", rotation_tooltip)
        self.auto_ry_limit_spin = component_limit(5.0, 30.0, 1, " deg", rotation_tooltip)
        self.auto_rz_limit_spin = component_limit(5.0, 30.0, 1, " deg", rotation_tooltip)
        self.btn_run_auto_alignment = QPushButton("Optimise Manual Alignment")
        self.btn_run_auto_alignment.clicked.connect(self._on_run_auto_alignment_clicked)
        auto_layout.addRow("Reference:", self.auto_target_combo)
        auto_layout.addRow("Registration points:", self.auto_points_spin)
        auto_layout.addRow("Translation X (+/-):", self.auto_tx_limit_spin)
        auto_layout.addRow("Translation Y (+/-):", self.auto_ty_limit_spin)
        auto_layout.addRow("Translation Z (+/-):", self.auto_tz_limit_spin)
        auto_layout.addRow("Rotation X (+/-):", self.auto_rx_limit_spin)
        auto_layout.addRow("Rotation Y (+/-):", self.auto_ry_limit_spin)
        auto_layout.addRow("Rotation Z (+/-):", self.auto_rz_limit_spin)
        auto_layout.addRow("", self.btn_run_auto_alignment)
        auto_info = QLabel(
            "First make a rough manual placement, then optimize it here. The optimizer starts exactly at that pose, "
            "changes only translation and rotation within the six limits above, and retains the manual pose unless the "
            "frozen two-sided overlap improves measurably. Global PCA/centre-of-gravity search is intentionally not used. "
            "Both clouds must use the same units: set Uniform scale first if, for example, one file is in metres "
            "and the reference is in millimetres."
        )
        auto_info.setWordWrap(True)
        auto_info.setStyleSheet("color: #888888; font-size: 11px; font-style: italic;")
        auto_layout.addRow("", auto_info)
        auto_group.setLayout(auto_layout)
        fine_alignment_layout.addWidget(auto_group)

        comparison_group = QGroupBox("Surface Error (Selected -> Reference)")
        comparison_layout = QFormLayout()
        self.comparison_target_combo = QComboBox()
        self.comparison_cutoff_spin = QDoubleSpinBox()
        self.comparison_cutoff_spin.setRange(0.000001, 1_000_000.0)
        self.comparison_cutoff_spin.setValue(1.0)
        self.comparison_cutoff_spin.setDecimals(6)
        self.comparison_cutoff_spin.setToolTip(
            "Only points within this distance of the reference are treated as overlap. "
            "Points outside the common scan area are reported separately, not included in error statistics."
        )
        self.comparison_points_spin = QSpinBox()
        self.comparison_points_spin.setRange(0, 5_000_000)
        self.comparison_points_spin.setValue(250_000)
        self.comparison_points_spin.setSingleStep(50_000)
        self.comparison_points_spin.setSpecialValueText("All source points")
        self.comparison_points_spin.setToolTip(
            "Maximum source points used for the report. A reproducible random sample is used above the limit; set to 0 for all points."
        )
        self.btn_calculate_error = QPushButton("Calculate Surface Error")
        self.btn_calculate_error.clicked.connect(self._on_calculate_error_clicked)
        self.comparison_show_map_check = QCheckBox("Show pointwise error colour map after calculation")
        self.comparison_show_map_check.setChecked(True)
        self.comparison_show_map_check.setToolTip(
            "Colours every analysed selected-cloud point by its distance to the reference. "
            "Points outside the overlap cutoff are shown in grey."
        )
        self.comparison_highlight_mean_check = QCheckBox("Highlight errors above the mean in red")
        self.comparison_highlight_mean_check.setToolTip(
            "Keeps the continuous distance colours below the mean and overlays overlap points above the "
            "reported mean distance in red."
        )
        self.comparison_summary = QLabel("No comparison calculated yet.")
        self.comparison_summary.setWordWrap(True)
        self.comparison_summary.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        comparison_layout.addRow("Reference:", self.comparison_target_combo)
        comparison_layout.addRow("Overlap / error cutoff:", self.comparison_cutoff_spin)
        comparison_layout.addRow("Maximum source points:", self.comparison_points_spin)
        comparison_layout.addRow("", self.btn_calculate_error)
        comparison_layout.addRow("", self.comparison_show_map_check)
        comparison_layout.addRow("", self.comparison_highlight_mean_check)
        comparison_layout.addRow("Last result:", self.comparison_summary)
        comparison_group.setLayout(comparison_layout)
        fine_alignment_layout.addWidget(comparison_group)

        manual_transform_layout.addStretch()
        legacy_alignment_layout.addStretch()
        fine_alignment_layout.addStretch()
        tab_manual_transform.setLayout(manual_transform_layout)
        tab_legacy_alignment.setLayout(legacy_alignment_layout)
        tab_fine_alignment.setLayout(fine_alignment_layout)

        def scrollable_tab(widget):
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(widget)
            return scroll
        
        self.tabs.addTab(tab_data, "Data & Display")
        self.tabs.addTab(tab_filter, "Filtering")
        self.tabs.addTab(scrollable_tab(tab_manual_transform), "Manual Transform")
        self.tabs.addTab(scrollable_tab(tab_legacy_alignment), "Legacy Alignment")
        self.tabs.addTab(scrollable_tab(tab_fine_alignment), "Fine Align & Error")
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)
        
        # Group parts that require selection
        self.requires_selection_widgets = [
            colors_group, analysis_display_group, camera_group, voxel_group, outlier_group,
            self.btn_save_data, manual_group, icp_group, legacy_global_group, auto_group, comparison_group
        ]
        self._enable_selection_widgets(False)
        
    def _enable_selection_widgets(self, enable: bool):
        for w in self.requires_selection_widgets:
            w.setEnabled(enable)

    def set_error_map_display_state(self, available: bool, shown: bool = False, colour_mode: str = "closest_distance"):
        """Synchronise the runtime-only error-map display control for a dataset."""
        self.analysis_display_group.setEnabled(available)
        self.show_error_map_check.blockSignals(True)
        self.show_error_map_check.setChecked(bool(shown) if available else False)
        self.show_error_map_check.blockSignals(False)
        self.error_map_colour_mode_combo.blockSignals(True)
        mode_index = self.error_map_colour_mode_combo.findData(colour_mode)
        self.error_map_colour_mode_combo.setCurrentIndex(mode_index if mode_index >= 0 else 0)
        self.error_map_colour_mode_combo.blockSignals(False)
            
    def add_dataset_to_list(self, name: str, checked: bool = True):
        item = QListWidgetItem(name)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        self.dataset_list.addItem(item)
        self.dataset_list.setCurrentItem(item)
        
        # Update target combo
        self.icp_target_combo.addItem(name)
        self.legacy_global_target_combo.addItem(name)
        self.auto_target_combo.addItem(name)
        self.comparison_target_combo.addItem(name)
        
    def remove_dataset_from_list(self, idx: int):
        self.dataset_list.takeItem(idx)
        self.icp_target_combo.removeItem(idx)
        self.legacy_global_target_combo.removeItem(idx)
        self.auto_target_combo.removeItem(idx)
        self.comparison_target_combo.removeItem(idx)

    def move_dataset_in_list(self, old_idx: int, new_idx: int):
        """Move the list item and every reference selector in the same order."""
        if old_idx == new_idx or not (0 <= old_idx < self.dataset_list.count() and 0 <= new_idx < self.dataset_list.count()):
            return
        item = self.dataset_list.takeItem(old_idx)
        self.dataset_list.insertItem(new_idx, item)
        for combo in (
            self.icp_target_combo,
            self.legacy_global_target_combo,
            self.auto_target_combo,
            self.comparison_target_combo,
        ):
            current_text = combo.currentText()
            moved_text = combo.itemText(old_idx)
            combo.removeItem(old_idx)
            combo.insertItem(new_idx, moved_text)
            combo.setCurrentText(current_text)
        self.dataset_list.setCurrentRow(new_idx)
        
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

    def _on_move_up_clicked(self):
        idx = self.dataset_list.currentRow()
        if idx > 0:
            self.move_dataset_requested.emit(idx, idx - 1)

    def _on_move_down_clicked(self):
        idx = self.dataset_list.currentRow()
        if 0 <= idx < self.dataset_list.count() - 1:
            self.move_dataset_requested.emit(idx, idx + 1)
            
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

    def _on_run_legacy_global_alignment_clicked(self):
        source_idx = self.dataset_list.currentRow()
        target_idx = self.legacy_global_target_combo.currentIndex()
        if source_idx >= 0 and target_idx >= 0 and source_idx != target_idx:
            self.run_legacy_global_alignment_requested.emit(
                source_idx,
                target_idx,
                self.legacy_global_points_spin.value(),
            )

    def _on_run_auto_alignment_clicked(self):
        source_idx = self.dataset_list.currentRow()
        target_idx = self.auto_target_combo.currentIndex()
        if source_idx >= 0 and target_idx >= 0 and source_idx != target_idx:
            self.run_auto_alignment_requested.emit(
                source_idx,
                target_idx,
                self.auto_points_spin.value(),
                self.auto_tx_limit_spin.value(),
                self.auto_ty_limit_spin.value(),
                self.auto_tz_limit_spin.value(),
                self.auto_rx_limit_spin.value(),
                self.auto_ry_limit_spin.value(),
                self.auto_rz_limit_spin.value(),
            )

    def _on_calculate_error_clicked(self):
        source_idx = self.dataset_list.currentRow()
        target_idx = self.comparison_target_combo.currentIndex()
        if source_idx >= 0 and target_idx >= 0 and source_idx != target_idx:
            self.calculate_error_requested.emit(
                source_idx,
                target_idx,
                self.comparison_cutoff_spin.value(),
                self.comparison_points_spin.value(),
                self.comparison_show_map_check.isChecked(),
                self.comparison_highlight_mean_check.isChecked(),
            )

    def set_comparison_summary(self, summary: str):
        self.comparison_summary.setText(summary)
            
    def update_columns(self, columns: list):
        self.color_combo.blockSignals(True)
        self.color_combo.clear()
        self.color_combo.addItem("None")
        for col in columns:
            self.color_combo.addItem(col)
        self.color_combo.blockSignals(False)
        
    def _on_preset_changed(self, idx: int):
        if self.signalsBlocked():
            return
        preset_name = self.preset_combo.currentText()
        if preset_name in self.current_saved_transforms:
            t = self.current_saved_transforms[preset_name]
            
            self.tx_spin.blockSignals(True)
            self.ty_spin.blockSignals(True)
            self.tz_spin.blockSignals(True)
            self.scale_spin.blockSignals(True)
            self.rx_spin.blockSignals(True)
            self.ry_spin.blockSignals(True)
            self.rz_spin.blockSignals(True)
            
            self.tx_spin.setValue(t.get("tx", 0.0))
            self.ty_spin.setValue(t.get("ty", 0.0))
            self.tz_spin.setValue(t.get("tz", 0.0))
            self.scale_spin.setValue(t.get("scale", 1.0))
            self.rx_spin.setValue(t.get("rx", 0.0))
            self.ry_spin.setValue(t.get("ry", 0.0))
            self.rz_spin.setValue(t.get("rz", 0.0))
            
            self.tx_spin.blockSignals(False)
            self.ty_spin.blockSignals(False)
            self.tz_spin.blockSignals(False)
            self.scale_spin.blockSignals(False)
            self.rx_spin.blockSignals(False)
            self.ry_spin.blockSignals(False)
            self.rz_spin.blockSignals(False)
            
            self._on_settings_changed()

    def _on_preset_save_clicked(self):
        name, ok = QInputDialog.getText(self, "Save Preset As", "Enter a name for this transformation preset:")
        if ok and name:
            name = name.strip()
            if not name:
                return
            if name in self.current_saved_transforms:
                ans = QMessageBox.question(self, "Overwrite?", f"Preset '{name}' already exists. Overwrite?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if ans == QMessageBox.StandardButton.No:
                    return
                    
            self.current_saved_transforms[name] = {
                "scale": self.scale_spin.value(),
                "tx": self.tx_spin.value(),
                "ty": self.ty_spin.value(),
                "tz": self.tz_spin.value(),
                "rx": self.rx_spin.value(),
                "ry": self.ry_spin.value(),
                "rz": self.rz_spin.value()
            }
            
            self.preset_combo.blockSignals(True)
            if self.preset_combo.findText(name) == -1:
                self.preset_combo.addItem(name)
            self.preset_combo.setCurrentText(name)
            self.preset_combo.blockSignals(False)
            
            self._on_settings_changed()
            
    def _on_preset_rename_clicked(self):
        current = self.preset_combo.currentText()
        if not current:
            return
            
        name, ok = QInputDialog.getText(self, "Rename Preset", f"Rename preset '{current}' to:", text=current)
        if ok and name:
            name = name.strip()
            if not name or name == current:
                return
            if name in self.current_saved_transforms:
                QMessageBox.warning(self, "Error", "A preset with this name already exists.")
                return
                
            self.current_saved_transforms[name] = self.current_saved_transforms.pop(current)
            
            self.preset_combo.blockSignals(True)
            idx = self.preset_combo.findText(current)
            if idx >= 0:
                self.preset_combo.setItemText(idx, name)
            self.preset_combo.blockSignals(False)
            
            self._on_settings_changed()
            
    def _on_preset_delete_clicked(self):
        current = self.preset_combo.currentText()
        if not current:
            return
            
        if len(self.current_saved_transforms) <= 1:
            QMessageBox.warning(self, "Cannot Delete", "You must have at least one transformation preset.")
            return
            
        ans = QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete preset '{current}'?")
        if ans == QMessageBox.StandardButton.Yes:
            del self.current_saved_transforms[current]
            
            self.preset_combo.blockSignals(True)
            idx = self.preset_combo.findText(current)
            if idx >= 0:
                self.preset_combo.removeItem(idx)
            self.preset_combo.blockSignals(False)
            
            self._on_preset_changed(0)
        
    def apply_config(self, config: dict):
        self.blockSignals(True)
        
        # Block sub-signals
        for w in [self.base_color_combo, self.color_combo,
                  self.invert_x_check, self.invert_y_check, self.invert_z_check,
                  self.zscore_check, self.zscore_spin, self.sor_check, self.sor_k_spin, self.sor_std_spin,
                  self.bbox_check, self.bbox_zmin, self.bbox_zmax, self.voxel_check, self.voxel_spin,
                  self.scale_spin, self.tx_spin, self.ty_spin, self.tz_spin, self.rx_spin, self.ry_spin, self.rz_spin]:
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
        
        self.current_saved_transforms = config.get("saved_transforms", {"Initial": {
            "scale": config.get("scale", 1.0),
            "tx": config.get("tx", 0.0),
            "ty": config.get("ty", 0.0),
            "tz": config.get("tz", 0.0),
            "rx": config.get("rx", 0.0),
            "ry": config.get("ry", 0.0),
            "rz": config.get("rz", 0.0)
        }})
        current_preset = config.get("current_transform_name", "Initial")
        if current_preset not in self.current_saved_transforms:
            current_preset = list(self.current_saved_transforms.keys())[0]

        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        self.preset_combo.addItems(list(self.current_saved_transforms.keys()))
        self.preset_combo.setCurrentText(current_preset)
        self.preset_combo.blockSignals(False)

        active_t = self.current_saved_transforms[current_preset]
        self.scale_spin.setValue(active_t.get("scale", 1.0))
        self.tx_spin.setValue(active_t.get("tx", 0.0))
        self.ty_spin.setValue(active_t.get("ty", 0.0))
        self.tz_spin.setValue(active_t.get("tz", 0.0))
        self.rx_spin.setValue(active_t.get("rx", 0.0))
        self.ry_spin.setValue(active_t.get("ry", 0.0))
        self.rz_spin.setValue(active_t.get("rz", 0.0))
        
        # Unblock sub-signals
        for w in [self.base_color_combo, self.color_combo,
                  self.invert_x_check, self.invert_y_check, self.invert_z_check,
                  self.zscore_check, self.zscore_spin, self.sor_check, self.sor_k_spin, self.sor_std_spin,
                  self.bbox_check, self.bbox_zmin, self.bbox_zmax, self.voxel_check, self.voxel_spin,
                  self.scale_spin, self.tx_spin, self.ty_spin, self.tz_spin, self.rx_spin, self.ry_spin, self.rz_spin]:
            w.blockSignals(False)
            
        self.blockSignals(False)
        
    def get_current_settings(self) -> dict:
        current_preset = self.preset_combo.currentText()
        if current_preset:
            self.current_saved_transforms[current_preset] = {
                "scale": self.scale_spin.value(),
                "tx": self.tx_spin.value(),
                "ty": self.ty_spin.value(),
                "tz": self.tz_spin.value(),
                "rx": self.rx_spin.value(),
                "ry": self.ry_spin.value(),
                "rz": self.rz_spin.value()
            }
            
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
            "scale": self.scale_spin.value(),
            "saved_transforms": self.current_saved_transforms,
            "current_transform_name": current_preset,
            "tx": self.tx_spin.value(),
            "ty": self.ty_spin.value(),
            "tz": self.tz_spin.value(),
            "rx": self.rx_spin.value(),
            "ry": self.ry_spin.value(),
            "rz": self.rz_spin.value()
        }
