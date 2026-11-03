from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QSlider, QComboBox, 
    QCheckBox, QPushButton, QGroupBox, QHBoxLayout, QFileDialog, QListWidget, QListWidgetItem,
    QDoubleSpinBox, QSpinBox, QTabWidget, QFormLayout, QInputDialog, QMessageBox, QScrollArea, QGridLayout,
    QLineEdit, QTextEdit
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
    export_full_resolution_requested = pyqtSignal(str)
    export_configured_requested = pyqtSignal(str, bool)
    export_preview_requested = pyqtSignal()
    save_data_requested = pyqtSignal()
    centre_data_requested = pyqtSignal()
    run_icp_requested = pyqtSignal(int, int, float, str) # source_idx, target_idx, max_dist, method
    run_legacy_global_alignment_requested = pyqtSignal(int, int, int) # source, reference, registration points
    run_auto_alignment_requested = pyqtSignal(int, int, int, float, float, float, float, float, float) # source, reference, points, +/- Tx/Ty/Tz, +/- Rx/Ry/Rz
    calculate_error_requested = pyqtSignal(int, int, float, int, bool, bool, str) # source_idx, reference_idx, cutoff, max_analysis_points, show_map, highlight_above_mean, colour_mode
    error_map_display_changed = pyqtSignal(bool)
    error_map_colour_mode_changed = pyqtSignal(str)
    error_map_max_changed = pyqtSignal(float)
    surface_error_settings_changed = pyqtSignal()
    comparison_report_requested = pyqtSignal()
    camera_view_requested = pyqtSignal(str)
    camera_rotate_requested = pyqtSignal(float)
    camera_angles_requested = pyqtSignal(float, float, float)
    camera_angles_read_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_saved_transforms = {"Initial": {"tx": 0.0, "ty": 0.0, "tz": 0.0, "rx": 0.0, "ry": 0.0, "rz": 0.0}}
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # --- Global Dataset List ---
        list_group = QGroupBox("Project and datasets")
        self.dataset_group = list_group
        list_layout = QVBoxLayout()
        
        self.dataset_list = QListWidget()
        self.dataset_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.dataset_list.itemChanged.connect(self._on_item_changed)
        list_layout.addWidget(self.dataset_list)
        
        btn_layout = QVBoxLayout()
        load_buttons_layout = QHBoxLayout()
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
        
        load_buttons_layout.addWidget(self.btn_add)
        load_buttons_layout.addWidget(self.btn_add_quick_ref)
        btn_layout.addLayout(load_buttons_layout)
        btn_layout.addWidget(self.btn_remove)
        order_buttons_layout = QHBoxLayout()
        order_buttons_layout.addWidget(self.btn_move_up)
        order_buttons_layout.addWidget(self.btn_move_down)
        btn_layout.addLayout(order_buttons_layout)
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
        self.error_map_colour_mode_combo.addItem("Calculated deviation", "closest_distance")
        self.error_map_colour_mode_combo.addItem("Difference from mean deviation", "difference_from_mean")
        self.error_map_colour_mode_combo.setToolTip(
            "Calculated deviation uses the latest error method. Difference from mean deviation "
            "subtracts its mean for display only; zero then means the mean, not the reference surface."
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
        camera_layout.addWidget(
            camera_button(
                "Diagonal (−X,+Y,+Z)",
                "diagonal_negative_x_positive_y_positive_z",
                "User-selected diagonal view: elevation −30°, azimuth −45°, roll 180°.",
            ),
            4,
            0,
            1,
            3,
        )

        rotate_left = QPushButton("↺ 90°")
        rotate_left.setToolTip("Rotate the camera 90 degrees counter-clockwise around Z.")
        rotate_left.clicked.connect(lambda: self.camera_rotate_requested.emit(-90.0))
        isometric = camera_button("Isometric", "isometric", "Restore a useful 3-D isometric camera angle.")
        rotate_right = QPushButton("↻ 90°")
        rotate_right.setToolTip("Rotate the camera 90 degrees clockwise around Z.")
        rotate_right.clicked.connect(lambda: self.camera_rotate_requested.emit(90.0))
        camera_layout.addWidget(rotate_left, 5, 0)
        camera_layout.addWidget(isometric, 5, 1)
        camera_layout.addWidget(rotate_right, 5, 2)
        self.camera_elevation_spin = QDoubleSpinBox()
        self.camera_azimuth_spin = QDoubleSpinBox()
        self.camera_roll_spin = QDoubleSpinBox()
        for spin, minimum, maximum in (
            (self.camera_elevation_spin, -90.0, 90.0),
            (self.camera_azimuth_spin, -360.0, 360.0),
            (self.camera_roll_spin, -180.0, 180.0),
        ):
            spin.setRange(minimum, maximum)
            spin.setDecimals(1)
            spin.setSingleStep(1.0)
            spin.setSuffix("°")
        self.camera_elevation_spin.setValue(30.0)
        self.camera_azimuth_spin.setValue(-60.0)
        self.camera_roll_spin.setValue(0.0)
        self.btn_apply_camera_angles = QPushButton("Apply Camera Angles")
        self.btn_apply_camera_angles.clicked.connect(self._on_apply_camera_angles_clicked)
        self.btn_read_camera_angles = QPushButton("Read Current View")
        self.btn_read_camera_angles.setToolTip(
            "Copies the current interactive 3-D camera orientation into the fields above."
        )
        self.btn_read_camera_angles.clicked.connect(self.camera_angles_read_requested.emit)
        camera_layout.addWidget(QLabel("Elevation:"), 6, 0)
        camera_layout.addWidget(self.camera_elevation_spin, 6, 1)
        camera_layout.addWidget(QLabel("Azimuth:"), 7, 0)
        camera_layout.addWidget(self.camera_azimuth_spin, 7, 1)
        camera_layout.addWidget(QLabel("Roll:"), 8, 0)
        camera_layout.addWidget(self.camera_roll_spin, 8, 1)
        camera_layout.addWidget(self.btn_read_camera_angles, 9, 0)
        camera_layout.addWidget(self.btn_apply_camera_angles, 9, 1, 1, 2)
        camera_group.setLayout(camera_layout)
        data_layout.addWidget(camera_group)
        
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
        self.voxel_spin.setToolTip("Size of the voxel grid cell in mm. Auto-calculated on load based on dataset bounds.")
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

        self.btn_centre_data = QPushButton("Create Centred Copy")
        self.btn_centre_data.setToolTip(
            "Copy the selected original cloud and translate every XYZ point so its centroid is at (0, 0, 0)."
        )
        self.btn_centre_data.clicked.connect(self.centre_data_requested.emit)
        filter_layout.addWidget(self.btn_centre_data)
        
        filter_layout.addStretch()
        tab_filter.setLayout(filter_layout)
        
        # --- Tabs 3-5: Manual transform, legacy alignment, and fine alignment ---
        tab_manual_transform = QWidget()
        manual_transform_layout = QVBoxLayout()
        tab_legacy_alignment = QWidget()
        legacy_alignment_layout = QVBoxLayout()
        tab_fine_alignment = QWidget()
        fine_alignment_layout = QVBoxLayout()
        tab_export = QWidget()
        export_tab_layout = QVBoxLayout()
        
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
        self.distance_unit_combo = QComboBox()
        self.distance_unit_combo.setEditable(True)
        self.distance_unit_combo.addItems(["mm", "µm", "cm", "m", "in"])
        self.distance_unit_combo.setCurrentText("mm")
        self.distance_unit_combo.currentTextChanged.connect(self._on_distance_unit_changed)
            
        self.rx_spin = QDoubleSpinBox()
        self.ry_spin = QDoubleSpinBox()
        self.rz_spin = QDoubleSpinBox()
        for spin in (self.rx_spin, self.ry_spin, self.rz_spin):
            spin.setRange(-180.0, 180.0)
            spin.setDecimals(2)
            spin.setSingleStep(1.0)
            
        manual_form.addRow("Distance unit:", self.distance_unit_combo)
        manual_form.addRow("Uniform scale:", self.scale_spin)
        self.tx_label = QLabel()
        self.ty_label = QLabel()
        self.tz_label = QLabel()
        manual_form.addRow(self.tx_label, self.tx_spin)
        manual_form.addRow(self.ty_label, self.ty_spin)
        manual_form.addRow(self.tz_label, self.tz_spin)
        manual_form.addRow("Rotate X (deg):", self.rx_spin)
        manual_form.addRow("Rotate Y (deg):", self.ry_spin)
        manual_form.addRow("Rotate Z (deg):", self.rz_spin)
        self._refresh_distance_unit_labels()
        
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
            "Independent plus/minus correction from the manual pose at the selected cloud's current centroid, in mm. "
            "Set this to 0 to lock the axis."
        )
        self.auto_tx_limit_spin = component_limit(10.0, 1_000_000.0, 6, "", translation_tooltip)
        self.auto_ty_limit_spin = component_limit(10.0, 1_000_000.0, 6, "", translation_tooltip)
        self.auto_tz_limit_spin = component_limit(10.0, 1_000_000.0, 6, "", translation_tooltip)
        rotation_tooltip = (
            "Independent plus/minus XYZ Euler-angle correction around the selected cloud's current centroid. "
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
            "frozen two-sided overlap improves measurably. For partial scans it first limits matching to the current shared X-Y footprint, "
            "so scan extensions with no counterpart do not steer the fit. Global PCA/centre-of-gravity search is intentionally not used. "
            "Both clouds must use the same units: set Uniform scale first if, for example, one file is in metres "
            "and the reference is in millimetres."
        )
        auto_info.setWordWrap(True)
        auto_info.setStyleSheet("color: #888888; font-size: 11px; font-style: italic;")
        auto_layout.addRow("", auto_info)
        auto_group.setLayout(auto_layout)
        fine_alignment_layout.addWidget(auto_group)

        comparison_group = QGroupBox("Surface Error (Source -> Reference)")
        comparison_layout = QFormLayout()
        self.comparison_source_combo = QComboBox()
        self.comparison_target_combo = QComboBox()
        self._previous_comparison_source_idx = -1
        self._previous_comparison_target_idx = -1
        self.comparison_source_combo.currentIndexChanged.connect(
            lambda _: self._sync_comparison_selectors(source_changed=True)
        )
        self.comparison_target_combo.currentIndexChanged.connect(
            lambda _: self._sync_comparison_selectors(source_changed=False)
        )
        self.comparison_cutoff_spin = QDoubleSpinBox()
        self.comparison_cutoff_spin.setRange(0.000001, 1_000_000.0)
        self.comparison_cutoff_spin.setValue(1.0)
        self.comparison_cutoff_spin.setDecimals(6)
        self.comparison_cutoff_spin.setToolTip(
            "Exclude an outer reference-edge band up to this width to avoid boundary artifacts. "
            "All remaining points inside the reference X/Y area contribute to the error statistics, "
            "including errors larger than this value."
        )
        self.comparison_points_spin = QSpinBox()
        self.comparison_points_spin.setRange(0, 5_000_000)
        self.comparison_points_spin.setValue(0)
        self.comparison_points_spin.setSingleStep(50_000)
        self.comparison_points_spin.setSpecialValueText("All source points")
        self.comparison_points_spin.setToolTip(
            "Maximum source points used for the report. A reproducible random sample is used above the limit; set to 0 for all points."
        )
        self.comparison_method_combo = QComboBox()
        self.comparison_method_combo.addItem("Unsigned nearest-reference distance (existing)", "unsigned")
        self.comparison_method_combo.addItem("Signed local normal / plane distance", "signed_normal")
        self.comparison_normal_radius_spin = QDoubleSpinBox()
        self.comparison_normal_radius_spin.setRange(0.0, 1_000_000.0)
        self.comparison_normal_radius_spin.setDecimals(6)
        self.comparison_normal_radius_spin.setSpecialValueText("Auto (3 x reference spacing)")
        self.comparison_normal_radius_spin.setToolTip("PCA neighbourhood radius in the cloud's distance unit; larger radii smooth curvature.")
        self.comparison_normal_neighbours_spin = QSpinBox()
        self.comparison_normal_neighbours_spin.setRange(3, 500)
        self.comparison_normal_neighbours_spin.setValue(30)
        self.comparison_normal_orientation_combo = QComboBox()
        self.comparison_normal_orientation_combo.addItems(["+Z", "-Z", "+X", "-X", "+Y", "-Y"])
        self.comparison_normal_orientation_combo.setToolTip(
            "Orient local normals towards this reference-coordinate direction. Positive error follows the normal. "
            "This does not automatically identify the specimen exterior; select a direction appropriate for this surface side."
        )
        self.comparison_axial_range_spin = QDoubleSpinBox()
        self.comparison_axial_range_spin.setRange(0.0, 1_000_000_000.0)
        self.comparison_axial_range_spin.setDecimals(6)
        self.comparison_axial_range_spin.setSpecialValueText("Not set")
        self.comparison_axial_range_spin.setToolTip(
            "Full axial measurement span from Table 3, in the same distance unit as the errors. "
            "Normalized SD [%] = 100 x standard deviation / axial range. "
            "For -100 to +100 mm enter 200. Zero leaves the normalized value unavailable."
        )
        self.comparison_scale_mode_combo = QComboBox()
        self.comparison_scale_mode_combo.addItem("Automatic (signed: symmetric P95 magnitude)", "auto")
        self.comparison_scale_mode_combo.addItem("Symmetric +/- maximum", "symmetric")
        self.comparison_scale_mode_combo.addItem("Custom minimum / maximum", "manual")
        self.error_map_min_spin = QDoubleSpinBox()
        self.error_map_min_spin.setRange(-1_000_000.0, 1_000_000.0)
        self.error_map_min_spin.setDecimals(6)
        self.error_map_min_spin.setValue(-1.0)
        self.comparison_colour_mode_combo = QComboBox()
        self.comparison_colour_mode_combo.addItem("Calculated deviation", "closest_distance")
        self.comparison_colour_mode_combo.addItem("Difference from mean deviation", "difference_from_mean")
        self.comparison_colour_mode_combo.setToolTip(
            "Show calculated deviations directly or subtract their mean for display only. "
            "The statistics always use the selected error method without mean subtraction."
        )
        self.error_map_max_spin = QDoubleSpinBox()
        self.error_map_max_spin.setRange(0.0, 1_000_000.0)
        self.error_map_max_spin.setDecimals(6)
        self.error_map_max_spin.setSpecialValueText("Auto (P95)")
        self.error_map_max_spin.setToolTip(
            "Upper limit for a custom range, or positive magnitude for a symmetric range. "
            "Zero means automatic only outside custom mode. Colour clipping does not alter statistics."
        )
        self.error_map_max_spin.valueChanged.connect(self.error_map_max_changed.emit)
        self.btn_calculate_error = QPushButton("Calculate Surface Error")
        self.btn_calculate_error.clicked.connect(self._on_calculate_error_clicked)
        self.comparison_show_map_check = QCheckBox("Show pointwise error colour map after calculation")
        self.comparison_show_map_check.setChecked(True)
        self.comparison_show_map_check.setToolTip(
            "Colours every analysed source-cloud point using the selected error-map colouring. "
            "Points excluded from error statistics are shown in grey."
        )
        self.comparison_highlight_mean_check = QCheckBox("Highlight errors above the mean in red")
        self.comparison_highlight_mean_check.setToolTip(
            "Keeps the continuous distance colours below the mean and overlays overlap points above the "
            "reported mean distance in red."
        )
        for signal in (
            self.comparison_target_combo.currentIndexChanged,
            self.comparison_cutoff_spin.valueChanged,
            self.comparison_points_spin.valueChanged,
            self.comparison_colour_mode_combo.currentIndexChanged,
            self.comparison_show_map_check.toggled,
            self.comparison_highlight_mean_check.toggled,
            self.comparison_method_combo.currentIndexChanged,
            self.comparison_normal_radius_spin.valueChanged,
            self.comparison_normal_neighbours_spin.valueChanged,
            self.comparison_normal_orientation_combo.currentIndexChanged,
            self.comparison_scale_mode_combo.currentIndexChanged,
            self.error_map_min_spin.valueChanged,
            self.comparison_axial_range_spin.valueChanged,
        ):
            signal.connect(lambda *_: self.surface_error_settings_changed.emit())
        self.comparison_summary = QLabel("No comparison calculated yet.")
        self.comparison_summary.setWordWrap(True)
        self.comparison_summary.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.comparison_status = QLabel("No results — calculate surface error")
        self.comparison_status.setWordWrap(True)
        self.comparison_status.setTextFormat(Qt.TextFormat.PlainText)
        self.btn_comparison_report = QPushButton("View Surface Error Results…")
        self.btn_comparison_report.setEnabled(False)
        self.btn_comparison_report.clicked.connect(self.comparison_report_requested.emit)
        comparison_layout.addRow("Source:", self.comparison_source_combo)
        comparison_layout.addRow("Reference:", self.comparison_target_combo)
        comparison_layout.addRow("Reference edge margin:", self.comparison_cutoff_spin)
        comparison_layout.addRow("Maximum source points:", self.comparison_points_spin)
        comparison_layout.addRow("Error method:", self.comparison_method_combo)
        comparison_layout.addRow("Normal radius:", self.comparison_normal_radius_spin)
        comparison_layout.addRow("Maximum normal neighbours:", self.comparison_normal_neighbours_spin)
        comparison_layout.addRow("Normal orientation:", self.comparison_normal_orientation_combo)
        comparison_layout.addRow("Axial measurement range:", self.comparison_axial_range_spin)
        comparison_layout.addRow("Error-map colouring:", self.comparison_colour_mode_combo)
        comparison_layout.addRow("Heatmap scale:", self.comparison_scale_mode_combo)
        comparison_layout.addRow("Heatmap minimum:", self.error_map_min_spin)
        comparison_layout.addRow("Heatmap maximum:", self.error_map_max_spin)
        comparison_layout.addRow("", self.btn_calculate_error)
        comparison_layout.addRow("", self.comparison_show_map_check)
        comparison_layout.addRow("", self.comparison_highlight_mean_check)
        comparison_layout.addRow("Result status:", self.comparison_status)
        comparison_layout.addRow("Last result:", self.comparison_summary)
        comparison_layout.addRow("", self.btn_comparison_report)
        comparison_group.setLayout(comparison_layout)
        fine_alignment_layout.addWidget(comparison_group)
        def update_error_controls(*_):
            signed = self.comparison_method_combo.currentData() == "signed_normal"
            for widget in (self.comparison_normal_radius_spin, self.comparison_normal_neighbours_spin,
                           self.comparison_normal_orientation_combo):
                widget.setEnabled(signed)
            manual = self.comparison_scale_mode_combo.currentData() == "manual"
            self.error_map_min_spin.setEnabled(manual)
            self.error_map_max_spin.setRange(-1_000_000.0 if manual else 0.0, 1_000_000.0)
            self.error_map_max_spin.setSpecialValueText("" if manual else "Auto (P95)")
        self.comparison_method_combo.currentIndexChanged.connect(update_error_controls)
        self.comparison_scale_mode_combo.currentIndexChanged.connect(update_error_controls)
        self._update_error_controls = update_error_controls
        update_error_controls()

        export_options_group = QGroupBox("Export Appearance")
        export_options_layout = QFormLayout()
        self.export_heatmap_check = QCheckBox("Use active error heatmap")
        self.export_heatmap_check.setChecked(True)
        self.export_heightmap_check = QCheckBox("Height map (Z coordinate)")
        self.export_heightmap_check.setToolTip(
            "Colour all exported points by their transformed Z coordinate with one shared colour scale. "
            "This takes priority over the error heatmap and reveals surface curvature and drilled holes."
        )
        self.export_heatmap_check.toggled.connect(
            lambda checked: self.export_heightmap_check.setChecked(False) if checked else None
        )
        self.export_heightmap_check.toggled.connect(
            lambda checked: self.export_heatmap_check.setChecked(False) if checked else None
        )
        self.export_heatmap_colormap_combo = QComboBox()
        self.export_heatmap_colormap_combo.addItem("Automatic (by error method)", "auto")
        self.export_heatmap_colormap_combo.addItem("Blue / white at zero / red", "blue_white_red")
        self.export_heatmap_colormap_combo.addItem("Blue / beige at zero / red", "blue_beige_red")
        for colormap in ["turbo", "viridis", "plasma", "inferno", "magma", "cividis", "coolwarm"]:
            self.export_heatmap_colormap_combo.addItem(colormap, colormap)
        self.export_heightmap_colormap_combo = QComboBox()
        self.export_heightmap_colormap_combo.addItems(
            ["viridis", "turbo", "plasma", "inferno", "magma", "cividis", "coolwarm", "height_blue_rose"]
        )
        self.export_colourbar_height_spin = QDoubleSpinBox()
        self.export_colourbar_height_spin.setRange(0.1, 1.0)
        self.export_colourbar_height_spin.setValue(1.0)
        self.export_colourbar_height_spin.setSingleStep(0.05)
        self.export_colourbar_height_spin.setDecimals(2)
        self.export_colourbar_height_spin.setToolTip("Colour-bar height as a fraction of the plot height.")
        self.export_colourbar_decimals_spin = QSpinBox()
        self.export_colourbar_decimals_spin.setRange(0, 10)
        self.export_colourbar_decimals_spin.setValue(2)
        self.export_colourbar_decimals_spin.setToolTip(
            "Number of decimal places shown on the colour-bar scale in exported images."
        )
        self.export_colourbar_label = QTextEdit()
        self.export_colourbar_label.setPlaceholderText(
            "Unsigned distance to reference\n(mm; colours capped at manual max)"
        )
        self.export_colourbar_label.setFixedHeight(72)
        self.export_colourbar_label.setToolTip(
            "Custom colour-bar label; press Enter to add a line break. "
            "Leave empty to use the automatic label with the current unit and colour limit."
        )
        for name, description in (
            ("axis_label", "X, Y and Z axis labels"),
            ("axis_tick", "Numbers on the X, Y and Z axes"),
            ("colourbar_label", "Colour-bar label"),
            ("colourbar_tick", "Numbers on the colour-bar scale"),
        ):
            font_size_spin = QDoubleSpinBox()
            font_size_spin.setRange(1.0, 72.0)
            font_size_spin.setValue(10.0)
            font_size_spin.setSingleStep(0.5)
            font_size_spin.setDecimals(1)
            font_size_spin.setSuffix(" pt")
            font_size_spin.setToolTip(f"{description} font size in points for export and preview.")
            setattr(self, f"export_{name}_font_size_spin", font_size_spin)
        self.export_z_label_spacing_spin = QDoubleSpinBox()
        self.export_z_label_spacing_spin.setRange(0.0, 200.0)
        self.export_z_label_spacing_spin.setDecimals(1)
        self.export_z_label_spacing_spin.setSuffix(" pt")
        self.export_z_label_spacing_spin.setSpecialValueText("Auto")
        self.export_z_label_spacing_spin.setToolTip("Gap between Z-axis numbers and title; Auto scales with the label font size.")
        self.export_z_tick_label_gap_spin = QDoubleSpinBox()
        self.export_z_tick_label_gap_spin.setRange(0.0, 200.0)
        self.export_z_tick_label_gap_spin.setDecimals(1)
        self.export_z_tick_label_gap_spin.setSuffix(" pt")
        self.export_z_tick_label_gap_spin.setSpecialValueText("Default")
        self.export_z_tick_label_gap_spin.setToolTip(
            "Minimum empty space between adjacent Z-axis tick numbers. "
            "Expands the displayed Z-axis height without changing coordinates or tick values. "
            "Default keeps the current axis proportions."
        )
        self.export_z_ticks_spin = QSpinBox()
        self.export_z_ticks_spin.setRange(0, 20)
        self.export_z_ticks_spin.setSpecialValueText("Auto")
        self.export_z_ticks_spin.setToolTip("Exact number of evenly spaced Z-axis ticks. Auto reduces ticks to avoid overlapping numbers.")
        self.export_z_tick_interval_spin = QDoubleSpinBox()
        self.export_z_tick_interval_spin.setRange(0.0, 1e9)
        self.export_z_tick_interval_spin.setDecimals(4)
        self.export_z_tick_interval_spin.setSingleStep(1.0)
        self.export_z_tick_interval_spin.setSpecialValueText("Auto / tick count")
        self.export_z_tick_interval_spin.setToolTip(
            "Tick spacing in axis units. For example, 10 places ticks at -20, -10, 0, 10, 20, etc. "
            "A positive interval overrides the tick count; 0 uses Auto or the selected count."
        )
        self.export_z_tick_interval_spin.valueChanged.connect(
            lambda interval: self.export_z_ticks_spin.setEnabled(interval == 0)
        )
        self.export_point_size_spin = QDoubleSpinBox()
        self.export_point_size_spin.setRange(0.1, 20.0)
        self.export_point_size_spin.setValue(2.0)
        self.export_point_size_spin.setSingleStep(0.1)
        self.export_point_size_spin.setDecimals(1)
        self.export_point_size_spin.setToolTip(
            "Scatter marker area in points². Reduce this (for example to 0.3–0.6) to reveal small holes "
            "in dense full-resolution clouds."
        )
        self.export_x_axis_name = QLineEdit("X")
        self.export_y_axis_name = QLineEdit("Y")
        self.export_z_axis_name = QLineEdit("Z")
        self.export_show_legend_check = QCheckBox("Show legend")
        self.export_show_legend_check.setChecked(True)
        self.export_legend_point_size_spin = QDoubleSpinBox()
        self.export_legend_point_size_spin.setRange(0.1, 100.0)
        self.export_legend_point_size_spin.setValue(16.0)
        self.export_legend_point_size_spin.setSingleStep(1.0)
        self.export_legend_point_size_spin.setDecimals(1)
        self.export_legend_point_size_spin.setToolTip(
            "Legend scatter-marker area in points², independent of the point size in the plot."
        )
        self.export_legend_placement_combo = QComboBox()
        self.export_legend_placement_combo.addItem("Inside plot", "inside")
        self.export_legend_placement_combo.addItem("Outside plot", "outside")
        self.export_legend_placement_combo.addItem("Best position (inside)", "best")
        self.export_legend_position_combo = QComboBox()
        self.export_legend_position_combo.addItem("Upper right", "upper right")
        self.export_legend_position_combo.addItem("Upper left", "upper left")
        self.export_legend_position_combo.addItem("Lower right", "lower right")
        self.export_legend_position_combo.addItem("Lower left", "lower left")
        self.export_legend_title = QLineEdit()
        self.export_legend_labels = QTextEdit()
        self.export_legend_labels.setPlaceholderText(
            "One label per line, in the same order as the legend.\n"
            "Line 1 renames the first legend entry; line 2 the second."
        )
        self.export_legend_labels.setFixedHeight(72)
        export_options_layout.addRow("Heatmap:", self.export_heatmap_check)
        export_options_layout.addRow("Height map:", self.export_heightmap_check)
        export_options_layout.addRow("Heatmap colours:", self.export_heatmap_colormap_combo)
        export_options_layout.addRow("Height-map colours:", self.export_heightmap_colormap_combo)
        export_options_layout.addRow("Colour-bar height:", self.export_colourbar_height_spin)
        export_options_layout.addRow("Colour-bar decimal places:", self.export_colourbar_decimals_spin)
        export_options_layout.addRow("Colour-bar label:", self.export_colourbar_label)
        export_options_layout.addRow("Colour-bar label font size:", self.export_colourbar_label_font_size_spin)
        export_options_layout.addRow("Colour-bar numbers font size:", self.export_colourbar_tick_font_size_spin)
        export_options_layout.addRow("Point size:", self.export_point_size_spin)
        export_options_layout.addRow("X-axis label:", self.export_x_axis_name)
        export_options_layout.addRow("Y-axis label:", self.export_y_axis_name)
        export_options_layout.addRow("Z-axis label:", self.export_z_axis_name)
        export_options_layout.addRow("Axis label font size:", self.export_axis_label_font_size_spin)
        export_options_layout.addRow("Axis numbers font size:", self.export_axis_tick_font_size_spin)
        export_options_layout.addRow("Z-axis title gap:", self.export_z_label_spacing_spin)
        export_options_layout.addRow("Z-axis tick label gap:", self.export_z_tick_label_gap_spin)
        export_options_layout.addRow("Z-axis tick interval:", self.export_z_tick_interval_spin)
        export_options_layout.addRow("Number of Z-axis ticks:", self.export_z_ticks_spin)
        export_options_layout.addRow("Legend:", self.export_show_legend_check)
        export_options_layout.addRow("Legend point size:", self.export_legend_point_size_spin)
        export_options_layout.addRow("Legend placement:", self.export_legend_placement_combo)
        export_options_layout.addRow("Legend corner:", self.export_legend_position_combo)
        export_options_layout.addRow("Legend title:", self.export_legend_title)
        export_options_layout.addRow("Legend labels:", self.export_legend_labels)
        export_options_group.setLayout(export_options_layout)
        export_tab_layout.addWidget(export_options_group)

        export_actions_group = QGroupBox("Export Actions")
        export_actions_layout = QVBoxLayout()
        self.btn_preview_export = QPushButton("Preview Export Settings")
        self.btn_preview_export.setToolTip("Shows a fast preview using the current display resolution.")
        self.btn_preview_export.clicked.connect(self.export_preview_requested.emit)
        self.btn_export_configured = QPushButton("Export Current Display")
        self.btn_export_configured.clicked.connect(lambda: self._on_configured_export_clicked(False))
        self.btn_export_configured_full = QPushButton("Export Full Resolution (No Voxel)")
        self.btn_export_configured_full.clicked.connect(lambda: self._on_configured_export_clicked(True))
        self.btn_save_export_settings = QPushButton("Save Export Settings…")
        self.btn_save_export_settings.clicked.connect(self._on_save_export_settings_clicked)
        self.btn_load_export_settings = QPushButton("Load Export Settings…")
        self.btn_load_export_settings.clicked.connect(self._on_load_export_settings_clicked)
        export_actions_layout.addWidget(self.btn_preview_export)
        export_actions_layout.addWidget(self.btn_export_configured)
        export_actions_layout.addWidget(self.btn_export_configured_full)
        export_actions_layout.addWidget(self.btn_save_export_settings)
        export_actions_layout.addWidget(self.btn_load_export_settings)
        export_actions_group.setLayout(export_actions_layout)
        export_tab_layout.addWidget(export_actions_group)
        export_tab_layout.addStretch()
        tab_export.setLayout(export_tab_layout)

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
        
        self.tabs.addTab(tab_data, "Data")
        self.tabs.addTab(scrollable_tab(tab_filter), "Prepare")

        align_tab = QWidget()
        align_layout = QVBoxLayout(align_tab)
        self.alignment_tabs = QTabWidget()
        self.alignment_tabs.addTab(scrollable_tab(tab_manual_transform), "Manual transform")
        self.alignment_tabs.addTab(scrollable_tab(tab_legacy_alignment), "Global alignment")
        align_layout.addWidget(self.alignment_tabs)
        self.tabs.addTab(align_tab, "Align")
        self.tabs.addTab(scrollable_tab(tab_fine_alignment), "Evaluate")
        self.tabs.addTab(scrollable_tab(tab_export), "Export")
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)
        
        # Group parts that require selection
        self.requires_selection_widgets = [
            colors_group, analysis_display_group, camera_group, voxel_group, outlier_group,
            self.btn_save_data, self.btn_centre_data, manual_group, icp_group, legacy_global_group, auto_group, comparison_group
        ]
        self._enable_selection_widgets(False)

    def take_dataset_browser(self):
        """Detach the project and dataset list so the main window can place it in its own sidebar."""
        layout = self.layout()
        if layout is not None:
            layout.removeWidget(self.dataset_group)
        self.dataset_group.setParent(None)
        return self.dataset_group
        
    def _enable_selection_widgets(self, enable: bool):
        for w in self.requires_selection_widgets:
            w.setEnabled(enable)

    def set_error_map_display_state(self, available: bool, shown: bool = False,
                                    colour_mode: str = "closest_distance", heatmap_max: float = 0.0):
        """Synchronise the runtime-only error-map display control for a dataset."""
        self.analysis_display_group.setEnabled(available)
        self.show_error_map_check.blockSignals(True)
        self.show_error_map_check.setChecked(bool(shown) if available else False)
        self.show_error_map_check.blockSignals(False)
        self.error_map_colour_mode_combo.blockSignals(True)
        mode_index = self.error_map_colour_mode_combo.findData(colour_mode)
        self.error_map_colour_mode_combo.setCurrentIndex(mode_index if mode_index >= 0 else 0)
        self.error_map_colour_mode_combo.blockSignals(False)
        self.set_comparison_heatmap_max(heatmap_max)

    def set_comparison_heatmap_max(self, maximum: float):
        self.error_map_max_spin.blockSignals(True)
        self.error_map_max_spin.setValue(float(maximum))
        self.error_map_max_spin.blockSignals(False)

    def get_surface_error_options(self) -> dict:
        return {
            "edge_margin": self.comparison_cutoff_spin.value(),
            "max_analysis_points": self.comparison_points_spin.value(),
            "colour_mode": self.comparison_colour_mode_combo.currentData(),
            "heatmap_max": self.error_map_max_spin.value(),
            "show_error_map": self.comparison_show_map_check.isChecked(),
            "highlight_above_mean": self.comparison_highlight_mean_check.isChecked(),
            "error_method": self.comparison_method_combo.currentData(),
            "normal_radius": self.comparison_normal_radius_spin.value(),
            "normal_neighbours": self.comparison_normal_neighbours_spin.value(),
            "normal_orientation": self.comparison_normal_orientation_combo.currentText(),
            "scale_mode": self.comparison_scale_mode_combo.currentData(),
            "heatmap_min": self.error_map_min_spin.value(),
            "axial_range": self.comparison_axial_range_spin.value(),
        }

    def apply_surface_error_options(self, options: dict, reference_index=None):
        """Restore a source's comparison settings without emitting edits."""
        widgets = (
            self.comparison_target_combo, self.comparison_cutoff_spin,
            self.comparison_points_spin, self.comparison_colour_mode_combo,
            self.error_map_max_spin, self.comparison_show_map_check,
            self.comparison_highlight_mean_check,
            self.comparison_method_combo, self.comparison_normal_radius_spin,
            self.comparison_normal_neighbours_spin, self.comparison_normal_orientation_combo,
            self.comparison_scale_mode_combo, self.error_map_min_spin,
            self.comparison_axial_range_spin,
        )
        previous_blocks = [widget.blockSignals(True) for widget in widgets]
        try:
            manual = options.get("scale_mode", "auto") == "manual"
            self.error_map_max_spin.setRange(-1_000_000.0 if manual else 0.0, 1_000_000.0)
            if reference_index is not None:
                self.comparison_target_combo.setCurrentIndex(reference_index)
            self.comparison_cutoff_spin.setValue(float(options.get("edge_margin", 1.0)))
            self.comparison_points_spin.setValue(int(options.get("max_analysis_points", 0)))
            mode_index = self.comparison_colour_mode_combo.findData(options.get("colour_mode", "closest_distance"))
            self.comparison_colour_mode_combo.setCurrentIndex(mode_index if mode_index >= 0 else 0)
            self.error_map_max_spin.setValue(float(options.get("heatmap_max", 0.0)))
            self.comparison_show_map_check.setChecked(bool(options.get("show_error_map", True)))
            self.comparison_highlight_mean_check.setChecked(bool(options.get("highlight_above_mean", False)))
            for combo, key, default in (
                (self.comparison_method_combo, "error_method", "unsigned"),
                (self.comparison_scale_mode_combo, "scale_mode", "auto"),
            ):
                index = combo.findData(options.get(key, default))
                combo.setCurrentIndex(index if index >= 0 else 0)
            self.comparison_normal_radius_spin.setValue(float(options.get("normal_radius", 0.0)))
            self.comparison_normal_neighbours_spin.setValue(int(options.get("normal_neighbours", 30)))
            self.comparison_normal_orientation_combo.setCurrentText(options.get("normal_orientation", "+Z"))
            self.error_map_min_spin.setValue(float(options.get("heatmap_min", -1.0)))
            self.comparison_axial_range_spin.setValue(float(options.get("axial_range") or 0.0))
        finally:
            for widget, blocked in zip(widgets, previous_blocks):
                widget.blockSignals(blocked)
        self._sync_comparison_selectors(source_changed=True)
        self._update_error_controls()
            
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
        self.comparison_source_combo.addItem(name)
        self.comparison_target_combo.addItem(name)
        self._sync_comparison_selectors(source_changed=True)
        
    def remove_dataset_from_list(self, idx: int):
        self.dataset_list.takeItem(idx)
        self.icp_target_combo.removeItem(idx)
        self.legacy_global_target_combo.removeItem(idx)
        self.auto_target_combo.removeItem(idx)
        self.comparison_source_combo.removeItem(idx)
        self.comparison_target_combo.removeItem(idx)
        self._sync_comparison_selectors(source_changed=True)

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
            self.comparison_source_combo,
            self.comparison_target_combo,
        ):
            current_text = combo.currentText()
            moved_text = combo.itemText(old_idx)
            combo.removeItem(old_idx)
            combo.insertItem(new_idx, moved_text)
            combo.setCurrentText(current_text)
        self.dataset_list.setCurrentRow(new_idx)
        self._sync_comparison_selectors(source_changed=True)

    def _sync_comparison_selectors(self, source_changed: bool):
        """Keep both clouds selectable and swap roles when selections collide."""
        source_idx = self.comparison_source_combo.currentIndex()
        target_idx = self.comparison_target_combo.currentIndex()
        count = self.comparison_source_combo.count()
        if count >= 2 and source_idx == target_idx:
            previous_idx = (
                self._previous_comparison_source_idx
                if source_changed else self._previous_comparison_target_idx
            )
            alternative = (
                previous_idx if 0 <= previous_idx < count and previous_idx != source_idx
                else next(index for index in range(count) if index != source_idx)
            )
            if source_changed:
                self.comparison_target_combo.blockSignals(True)
                self.comparison_target_combo.setCurrentIndex(alternative)
                self.comparison_target_combo.blockSignals(False)
            else:
                self.comparison_source_combo.blockSignals(True)
                self.comparison_source_combo.setCurrentIndex(alternative)
                self.comparison_source_combo.blockSignals(False)
            source_idx = self.comparison_source_combo.currentIndex()
            target_idx = self.comparison_target_combo.currentIndex()

        self._previous_comparison_source_idx = source_idx
        self._previous_comparison_target_idx = target_idx
        for combo in (self.comparison_source_combo, self.comparison_target_combo):
            model = combo.model()
            for index in range(count):
                item = model.item(index) if hasattr(model, "item") else None
                if item is not None:
                    item.setEnabled(count >= 2)
        self.btn_calculate_error.setEnabled(count >= 2)
        
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

    def _on_distance_unit_changed(self, _unit: str):
        if not hasattr(self, "tx_label"):
            return
        self._refresh_distance_unit_labels()
        self._on_settings_changed()

    def _distance_unit(self) -> str:
        return self.distance_unit_combo.currentText().strip() or "mm"

    def _refresh_distance_unit_labels(self):
        unit = self._distance_unit()
        self.tx_label.setText(f"Translate X ({unit}):")
        self.ty_label.setText(f"Translate Y ({unit}):")
        self.tz_label.setText(f"Translate Z ({unit}):")
        self.voxel_spin.setToolTip(
            f"Size of the voxel grid cell in {unit}. Auto-calculated on load based on dataset bounds."
        )
        
    def _on_export_clicked(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Export Plot", "", "PNG Image (*.png);;JPEG Image (*.jpg);;SVG Vector (*.svg)")
        if filepath:
            self.export_requested.emit(filepath)

    def _on_apply_camera_angles_clicked(self):
        self.camera_angles_requested.emit(
            self.camera_elevation_spin.value(),
            self.camera_azimuth_spin.value(),
            self.camera_roll_spin.value(),
        )

    def set_camera_angles(self, elevation: float, azimuth: float, roll: float = 0.0):
        """Show the active Matplotlib camera angles without emitting a change."""
        for spin, value in (
            (self.camera_elevation_spin, elevation),
            (self.camera_azimuth_spin, azimuth),
            (self.camera_roll_spin, roll),
        ):
            spin.blockSignals(True)
            spin.setValue(float(value))
            spin.blockSignals(False)

    def _on_export_full_resolution_clicked(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Full Resolution Plot (No Voxel)",
            "",
            "PNG Image (*.png);;JPEG Image (*.jpg);;SVG Vector (*.svg)",
        )
        if filepath:
            self.export_full_resolution_requested.emit(filepath)

    def _on_configured_export_clicked(self, full_resolution: bool):
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Plot",
            "",
            "PNG Image (*.png);;JPEG Image (*.jpg);;SVG Vector (*.svg)",
        )
        if filepath:
            self.export_configured_requested.emit(filepath, full_resolution)

    def get_export_options(self) -> dict:
        labels = {}
        sequential_labels = []
        for line in self.export_legend_labels.toPlainText().splitlines():
            line = line.strip()
            if not line:
                continue
            if "=" in line:
                source, label = (part.strip() for part in line.split("=", 1))
                if source and label:
                    labels[source] = label
            else:
                sequential_labels.append(line)
        visible_names = [
            self.dataset_list.item(index).text()
            for index in range(self.dataset_list.count())
            if self.dataset_list.item(index).checkState() == Qt.CheckState.Checked
        ]
        for name, label in zip(visible_names, sequential_labels):
            labels.setdefault(name, label)
        return {
            "use_heatmap": self.export_heatmap_check.isChecked(),
            "use_heightmap": self.export_heightmap_check.isChecked(),
            "heatmap_colormap": self.export_heatmap_colormap_combo.currentData(),
            "heightmap_colormap": self.export_heightmap_colormap_combo.currentText(),
            "colourbar_height": self.export_colourbar_height_spin.value(),
            "colourbar_decimals": self.export_colourbar_decimals_spin.value(),
            "colourbar_label": self.export_colourbar_label.toPlainText(),
            "colourbar_label_font_size": self.export_colourbar_label_font_size_spin.value(),
            "colourbar_tick_font_size": self.export_colourbar_tick_font_size_spin.value(),
            "axis_label_font_size": self.export_axis_label_font_size_spin.value(),
            "axis_tick_font_size": self.export_axis_tick_font_size_spin.value(),
            "z_axis_label_spacing": self.export_z_label_spacing_spin.value(),
            "z_axis_tick_label_gap": self.export_z_tick_label_gap_spin.value(),
            "z_axis_ticks": self.export_z_ticks_spin.value(),
            "z_axis_tick_interval": self.export_z_tick_interval_spin.value(),
            "point_size": self.export_point_size_spin.value(),
            "x_label": self.export_x_axis_name.text() or "X",
            "y_label": self.export_y_axis_name.text() or "Y",
            "z_label": self.export_z_axis_name.text() or "Z",
            "show_legend": self.export_show_legend_check.isChecked(),
            "legend_point_size": self.export_legend_point_size_spin.value(),
            "legend_placement": self.export_legend_placement_combo.currentData(),
            "legend_position": self.export_legend_position_combo.currentData(),
            "legend_title": self.export_legend_title.text(),
            "legend_labels": labels,
            "legend_labels_text": self.export_legend_labels.toPlainText(),
            # The renderer uses this ordered list, because an error-map cloud
            # can contribute more than one legend entry (for example, an
            # outside-cutoff group).  The name map above is kept so previously
            # saved settings files remain compatible.
            "legend_label_lines": sequential_labels,
        }

    def apply_export_options(self, options: dict):
        """Load a previously saved export appearance without changing data settings."""
        self.export_heatmap_check.setChecked(bool(options.get("use_heatmap", True)))
        self.export_heightmap_check.setChecked(bool(options.get("use_heightmap", False)))
        colormap_index = self.export_heatmap_colormap_combo.findData(options.get("heatmap_colormap", "auto"))
        self.export_heatmap_colormap_combo.setCurrentIndex(colormap_index if colormap_index >= 0 else 0)
        self.export_heightmap_colormap_combo.setCurrentText(options.get("heightmap_colormap", "viridis"))
        self.export_colourbar_height_spin.setValue(float(options.get("colourbar_height", 1.0)))
        self.export_colourbar_decimals_spin.setValue(int(options.get("colourbar_decimals", 2)))
        self.export_colourbar_label.setPlainText(options.get("colourbar_label", ""))
        for name in ("axis_label", "axis_tick", "colourbar_label", "colourbar_tick"):
            getattr(self, f"export_{name}_font_size_spin").setValue(
                float(options.get(f"{name}_font_size", 10.0))
            )
        self.export_point_size_spin.setValue(float(options.get("point_size", 2.0)))
        self.export_x_axis_name.setText(options.get("x_label", "X"))
        self.export_y_axis_name.setText(options.get("y_label", "Y"))
        self.export_z_axis_name.setText(options.get("z_label", "Z"))
        self.export_z_label_spacing_spin.setValue(float(options.get("z_axis_label_spacing", 0.0)))
        self.export_z_tick_label_gap_spin.setValue(float(options.get("z_axis_tick_label_gap", 0.0)))
        self.export_z_ticks_spin.setValue(int(options.get("z_axis_ticks", options.get("z_axis_max_ticks", 0))))
        self.export_z_tick_interval_spin.setValue(float(options.get("z_axis_tick_interval", 0.0)))
        self.export_show_legend_check.setChecked(bool(options.get("show_legend", True)))
        self.export_legend_point_size_spin.setValue(float(options.get("legend_point_size", 16.0)))
        position = options.get("legend_position", "upper right")
        # Version-one export settings used ``inside_best`` as the position.
        # Keep those files useful after separating placement from corner.
        placement = options.get("legend_placement", "best" if position == "inside_best" else "inside")
        if position == "inside_best":
            position = "upper right"
        placement_index = self.export_legend_placement_combo.findData(placement)
        self.export_legend_placement_combo.setCurrentIndex(placement_index if placement_index >= 0 else 0)
        index = self.export_legend_position_combo.findData(position)
        self.export_legend_position_combo.setCurrentIndex(index if index >= 0 else 0)
        self.export_legend_title.setText(options.get("legend_title", ""))
        if isinstance(options.get("legend_labels_text"), str):
            self.export_legend_labels.setPlainText(options["legend_labels_text"])
        elif isinstance(options.get("legend_label_lines"), list) and options["legend_label_lines"]:
            lines = [str(line) for line in options["legend_label_lines"]]
            labels = options.get("legend_labels", {})
            if isinstance(labels, dict):
                lines.extend(
                    f"{name} = {label}" for name, label in labels.items()
                    if str(label) not in lines
                )
            self.export_legend_labels.setPlainText("\n".join(lines))
        else:
            labels = options.get("legend_labels", {})
            if isinstance(labels, dict):
                self.export_legend_labels.setPlainText(
                    "\n".join(f"{name} = {label}" for name, label in labels.items())
                )

    def _on_save_export_settings_clicked(self):
        import json

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Export Settings", "", "Export Settings (*.json);;All Files (*)"
        )
        if not filepath:
            return
        try:
            with open(filepath, "w", encoding="utf-8") as output:
                json.dump(self.get_export_options(), output, indent=2)
        except OSError as error:
            QMessageBox.critical(self, "Save Export Settings Error", str(error))

    def _on_load_export_settings_clicked(self):
        import json

        filepath, _ = QFileDialog.getOpenFileName(
            self, "Load Export Settings", "", "Export Settings (*.json);;All Files (*)"
        )
        if not filepath:
            return
        try:
            with open(filepath, encoding="utf-8") as source:
                options = json.load(source)
            if not isinstance(options, dict):
                raise ValueError("The selected file does not contain export settings.")
            self.apply_export_options(options)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            QMessageBox.critical(self, "Load Export Settings Error", str(error))
            
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
        source_idx = self.comparison_source_combo.currentIndex()
        target_idx = self.comparison_target_combo.currentIndex()
        if source_idx >= 0 and target_idx >= 0 and source_idx != target_idx:
            self.calculate_error_requested.emit(
                source_idx,
                target_idx,
                self.comparison_cutoff_spin.value(),
                self.comparison_points_spin.value(),
                self.comparison_show_map_check.isChecked(),
                self.comparison_highlight_mean_check.isChecked(),
                self.comparison_colour_mode_combo.currentData(),
            )

    def set_comparison_summary(self, summary: str):
        self.comparison_summary.setTextFormat(Qt.TextFormat.PlainText)
        self.comparison_summary.setText(summary)

    def set_comparison_report(self, report, options=None):
        """Show availability and journal metrics separately from calculation controls."""
        from html import escape
        from src.utils.error_report import headline_rows, report_method, report_status

        status, available, state = report_status(report, options)
        self.comparison_status.setText(status)
        colour = {"ready": "#16803c", "warning": "#a06000", "empty": "#777777"}[state]
        self.comparison_status.setStyleSheet(f"color: {colour}; font-weight: bold;")
        self.btn_comparison_report.setEnabled(available)
        self.comparison_summary.setTextFormat(Qt.TextFormat.RichText)
        if not available:
            self.comparison_summary.setText("—")
            return
        method = "Signed normal deviations" if report_method(report) == "signed_normal" else "Unsigned nearest-point distances"
        rows = "".join(f"<tr><td>{escape(name)}</td><td align='right'><b>{escape(value)}</b></td></tr>"
                       for name, value in headline_rows(report))
        self.comparison_summary.setText(f"<b>{method}</b><br><table cellspacing='6'>{rows}</table>")
            
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
                  self.scale_spin, self.distance_unit_combo, self.tx_spin, self.ty_spin, self.tz_spin, self.rx_spin, self.ry_spin, self.rz_spin]:
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
        self.distance_unit_combo.setCurrentText(config.get("distance_unit", "mm"))
        
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
                  self.scale_spin, self.distance_unit_combo, self.tx_spin, self.ty_spin, self.tz_spin, self.rx_spin, self.ry_spin, self.rz_spin]:
            w.blockSignals(False)
            
        self.blockSignals(False)
        self._refresh_distance_unit_labels()
        
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
            "distance_unit": self._distance_unit(),
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
