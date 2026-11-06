"""Application-wide light and dark visual themes."""

from pathlib import Path


LIGHT_STYLESHEET = """
QMainWindow, QWidget { background: #ffffff; color: #202938; font-family: "Segoe UI"; font-size: 10pt; }
QToolBar#projectToolbar { background: #ffffff; border: 0; border-bottom: 1px solid #e7ebf0; spacing: 4px; padding: 7px 12px; }
QToolBar#projectToolbar::separator { width: 1px; background: #e7ebf0; margin: 6px 7px; }
QToolBar#projectToolbar QToolButton { background: transparent; border: 1px solid transparent; border-radius: 7px; padding: 6px 9px; font-weight: 600; }
QToolBar#projectToolbar QToolButton:hover, QToolBar#projectToolbar QToolButton:checked { background: #f4f6f9; }
QToolBar#projectToolbar QToolButton#themeChoice, QToolBar#projectToolbar QToolButton#helpChoice, QToolBar#projectToolbar QToolButton#githubChoice { padding: 5px; }
QToolBar#projectToolbar QToolButton#themeChoice:checked { background: #eef1f5; border-color: #d8dee7; }
QToolBar#projectToolbar QToolButton#recentProjectsButton, QToolBar#projectToolbar QToolButton#exportMenuButton { min-width: 42px; padding: 4px; }
QToolBar#projectToolbar QToolButton#recentProjectsButton::menu-indicator, QToolBar#projectToolbar QToolButton#exportMenuButton::menu-indicator { image: none; width: 0; }
QToolBar#projectToolbar QToolButton#languageChoice { min-width: 38px; padding: 5px; font-weight: 700; }
QWidget#projectSidebar { background: #ffffff; border-right: 1px solid #e7ebf0; }
QWidget#datasetActions QToolButton#datasetActionButton { background: #ffffff; border: 1px solid #cbd3dd; border-radius: 6px; padding: 4px; }
QWidget#datasetActions QToolButton#datasetActionButton:hover { background: #f1f4f8; border-color: #8d99a8; }
QWidget#pointViewer { background: #ffffff; border: 0; }
QLabel#sectionHeading, QLabel#sidebarHeading { font-size: 15px; font-weight: 700; color: #17243a; }
QLabel#sectionHint, QLabel#sidebarHint { color: #64748b; font-size: 9pt; }
QLabel#sidebarSubtitle { color: #64748b; font-size: 9pt; }
QLabel#guideStepLabel { color: #0c65ae; font-size: 9pt; font-weight: 700; }
QLabel#guideHeading { color: #17243a; font-size: 18pt; font-weight: 700; }
QLabel#guideBody { color: #334155; font-size: 11pt; }
QProgressBar#guideProgress { background: #e7edf3; border: 0; border-radius: 3px; }
QProgressBar#guideProgress::chunk { background: #0c65ae; border-radius: 3px; }
QToolBar#viewerToolbar { background: transparent; border: 0; spacing: 2px; padding: 0; }
QToolBar#viewerToolbar QToolButton { background: transparent; border: 1px solid transparent; border-radius: 5px; padding: 4px; }
QToolBar#viewerToolbar QToolButton:hover, QToolBar#viewerToolbar QToolButton:checked { background: #f1f3f6; }
QStatusBar { background: #ffffff; border-top: 1px solid #e7ebf0; }
QGroupBox { background: transparent; border: 0; margin-top: 16px; padding: 8px 0 2px; font-weight: 600; }
QGroupBox::title { subcontrol-origin: margin; left: 0; padding: 0 3px 0 0; color: #334155; }
QTabWidget::pane { background: transparent; border: 0; top: -1px; }
QTabBar::tab { background: transparent; color: #64748b; border: 0; border-bottom: 2px solid transparent; padding: 9px 11px; }
QTabBar::tab:hover { color: #202938; background: #f7f8fa; }
QTabBar::tab:selected { color: #202938; background: transparent; border-bottom: 2px solid #475569; font-weight: 700; }
QPushButton, QToolButton { background: #ffffff; border: 1px solid #cbd3dd; border-radius: 6px; padding: 6px 9px; }
QPushButton:hover, QToolButton:hover { background: #f1f4f8; border-color: #8d99a8; }
QPushButton:disabled, QToolButton:disabled { color: #a1a9b5; background: #f6f7f9; border-color: #e1e5eb; }
QPushButton#primaryAction { background: #e9edf2; color: #202938; border-color: #cbd3dd; font-weight: 600; }
QPushButton#primaryAction:hover { background: #dde3ea; }
QListWidget { background: #ffffff; border: 1px solid #cbd3dd; border-radius: 5px; padding: 5px; }
QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox { background: #ffffff; border: 1px solid #cbd3dd; border-radius: 7px; padding: 2px 8px; }
QListWidget { background: #fafbfd; }
QListWidget::item { padding: 4px; }
QListWidget::item:selected { background: #e5eaf0; color: #202938; }
QMenu { background: #ffffff; border: 1px solid #e1e5eb; padding: 5px; }
QMenu::item { padding: 7px 18px; border-radius: 4px; }
QMenu::item:selected { background: #f1f3f6; color: #202938; }
QMainWindow { background: #f7f8fa; }
QToolBar#projectToolbar { background: #f7f8fa; border-bottom: 1px solid #dbe1e8; }
QWidget#toolbarSpacer, QWidget#toolbarChoices, QWidget#datasetActions, QWidget#projectSplitControl, QWidget#exportSplitControl { background: transparent; }
QWidget#themeLanguageSeparator { background: #cbd3dd; }
QToolBar#projectToolbar QToolButton#languageChoice { border: 1px solid transparent; padding: 3px; }
QToolBar#projectToolbar QToolButton#languageChoice:checked { background: #dceaf7; border: 1px solid #0c65ae; color: #0d529f; }
QToolBar#projectToolbar QToolButton#toolbarExportButton { min-width: 90px; }
QWidget#projectSidebar { background: #f7f8fa; border: 0; }
QWidget#pointViewer { background: #ffffff; }
QWidget#workspaceTools { background: #f7f8fa; border: 0; }
QSplitter#workspaceSplitter::handle:horizontal { background: #f7f8fa; border-left: 1px solid #d2d8e0; border-right: 1px solid #f7f8fa; }
QSplitter#workspaceSplitter::handle:horizontal:hover { background: #dceaf7; border-left-color: #0c65ae; }
QWidget#toolPageViewport { background: #f7f8fa; }
QWidget#toolPage { background: #f0f2f5; border: 1px solid #d6dce4; border-radius: 7px; }
QWidget#methodPage { background: transparent; }
QLabel, QCheckBox, QRadioButton { background: transparent; }
QCheckBox { min-height: 24px; spacing: 8px; }
QCheckBox::indicator { subcontrol-origin: padding; subcontrol-position: left center; width: 16px; height: 16px; margin: 0; background: #ffffff; border: 2px solid #667b91; border-radius: 3px; }
QCheckBox::indicator:hover { border-color: #0c65ae; }
QCheckBox::indicator:checked { background: #0c65ae; border-color: #0c65ae; image: url("__CHECKMARK__"); }
QCheckBox::indicator:disabled { background: #e7ebf0; border-color: #9aa8b6; }
QGroupBox#datasetGroup { background: transparent; border: 0; margin-top: 22px; padding: 2px 0 0; font-size: 14px; color: #153c68; }
QGroupBox#datasetGroup::title { color: #153c68; font-weight: 700; }
QListWidget#datasetList { background: transparent; border: 0; border-top: 1px solid #dce2e8; border-radius: 0; padding: 5px 0; }
QListWidget#datasetList::item { border-radius: 5px; padding: 8px 5px; margin: 2px 0; }
QListWidget#datasetList::item:hover { background: #e3effa; }
QListWidget#datasetList::item:selected { background: #c8e0f5; color: #103d6d; }
QListWidget#datasetList::indicator { width: 16px; height: 16px; background: #ffffff; border: 2px solid #667b91; border-radius: 3px; }
QListWidget#datasetList::indicator:hover { border-color: #0c65ae; }
QListWidget#datasetList::indicator:checked { background: #0c65ae; border-color: #0c65ae; image: url("__CHECKMARK__"); }
QListWidget#datasetList::indicator:disabled { background: #e7ebf0; border-color: #9aa8b6; }
QListWidget#datasetList::indicator:checked:disabled { background: #73879a; border-color: #687b8e; image: url("__CHECKMARK__"); }
QTabWidget#workspaceTabs { background: transparent; }
QTabWidget#workspaceTabs::pane { background: transparent; border: 0; top: 0; }
QWidget#workspaceTabNavigation, QWidget#workspaceTabStrip, QWidget#workspaceTabViewport { background: transparent; }
QScrollArea#workspaceTabScroll { background: transparent; border: 0; }
QToolButton#workspaceTabButton { background: #eef1f5; color: #26394e; border: 1px solid #c9d1da; border-bottom: 2px solid #b9c4cf; border-radius: 6px; padding: 8px 12px; font-weight: 600; }
QToolButton#workspaceTabButton:hover { background: #e3ebf3; border-color: #8ca9c3; }
QToolButton#workspaceTabButton:checked { background: #dceaf7; border-color: #7aa7cf; border-bottom: 3px solid #0c65ae; color: #0d529f; }
QToolButton#workspaceTabArrow { background: #eef1f5; border: 1px solid #b9c4cf; border-radius: 6px; padding: 0; }
QToolButton#workspaceTabArrow:hover { background: #dceaf7; border-color: #0c65ae; }
QToolButton#workspaceTabArrow:disabled { background: #f1f3f6; border-color: #d9e0e7; }
QScrollArea#toolPageScroll { background: transparent; border: 0; }
QWidget#toolSectionHeader { background: transparent; border: 0; border-radius: 0; }
QWidget#toolSectionDivider { background: #d0d8e1; margin: 0 10px; }
QLabel#toolSectionTitle { color: #253a51; font-size: 11pt; font-weight: 700; }
QGroupBox#toolSection { background: transparent; border: 0; border-radius: 0; margin-top: 0; padding: 4px 10px 12px; }
QGroupBox#filterBlock { background: transparent; border: 0; margin-top: 0; padding: 0 10px 8px; }
QCheckBox#filterHeadingCheck { color: #153c68; font-weight: 700; }
QLabel#methodLabel { color: #253a51; font-weight: 700; }
QPushButton#primaryAction { background: #d3e8fa; color: #104a81; border-color: #6da6d5; border-bottom: 2px solid #4a91ca; }
QPushButton#primaryAction:hover { background: #c1def5; }
QPushButton, QToolButton { border-bottom: 2px solid #acbfd1; }
QPushButton:hover, QToolButton:hover { border-color: #6ba4d4; background: #e5f2fd; }
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { border: 2px solid #2872b5; }
QComboBox, QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox { min-height: 24px; border-radius: 7px; padding: 2px 8px; }
QComboBox { padding: 2px 34px 2px 8px; }
QComboBox QLineEdit { background: transparent; border: 0; border-radius: 0; padding: 0; min-height: 0; }
QComboBox::drop-down { subcontrol-origin: padding; subcontrol-position: top right; width: 30px; border: 0; border-left: 1px solid #bdc9d6; border-top-right-radius: 6px; border-bottom-right-radius: 6px; background: #e7edf4; }
QComboBox::drop-down:hover { background: #d7eafa; }
QComboBox::drop-down:pressed { background: #c4def3; }
QComboBox::down-arrow { subcontrol-origin: padding; subcontrol-position: center center; image: url("__SPIN_DOWN__"); width: 12px; height: 10px; border: 0; }
QComboBox QAbstractItemView { background: #ffffff; color: #202938; border: 1px solid #cbd3dd; border-radius: 7px; padding: 4px; outline: 0; selection-background-color: #dceaf7; selection-color: #103d6d; }
QComboBox QAbstractItemView::item { min-height: 25px; padding: 5px 9px; border-radius: 4px; }
QComboBox QAbstractItemView::item:hover { background: #edf5fc; color: #103d6d; }
QSpinBox, QDoubleSpinBox { padding: 2px 34px 2px 8px; }
QSpinBox::up-button, QDoubleSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::down-button { subcontrol-origin: border; subcontrol-position: top right; width: 28px; border: 0; border-left: 1px solid #bdc9d6; background: #e7edf4; }
QSpinBox::up-button, QDoubleSpinBox::up-button { height: 14px; border-top-right-radius: 6px; border-bottom: 1px solid #cbd4de; }
QSpinBox::down-button, QDoubleSpinBox::down-button { height: 14px; subcontrol-position: bottom right; border-bottom-right-radius: 6px; }
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover, QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover { background: #d7eafa; }
QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed, QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed { background: #c4def3; }
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow { subcontrol-origin: padding; subcontrol-position: center center; image: url("__SPIN_UP__"); width: 12px; height: 10px; border: 0; }
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow { subcontrol-origin: padding; subcontrol-position: center center; image: url("__SPIN_DOWN__"); width: 12px; height: 10px; border: 0; }
QMenu { background: #ffffff; color: #202938; border: 1px solid #d4dce5; border-radius: 8px; padding: 5px; }
QMenu::item { min-height: 24px; padding: 6px 24px 6px 10px; border-radius: 5px; }
QMenu::item:selected { background: #e3effa; color: #103d6d; }
QMenu::item:disabled { color: #98a3af; }
QMenu::separator { height: 1px; background: #e1e7ee; margin: 4px 7px; }
QPushButton:disabled, QToolButton:disabled { color: #707d8c; background: #e9edf2; border: 1px solid #c3ccd6; border-bottom: 1px solid #c3ccd6; }
QPushButton#primaryAction:disabled, QToolButton#workspaceTabButton:disabled, QToolButton#workspaceTabArrow:disabled, QToolBar#projectToolbar QToolButton:disabled, QToolBar#viewerToolbar QToolButton:disabled, QWidget#datasetActions QToolButton#datasetActionButton:disabled { color: #707d8c; background: #e9edf2; border-color: #c3ccd6; border-bottom-color: #c3ccd6; }
QCheckBox:disabled, QRadioButton:disabled { color: #707d8c; }
QCheckBox::indicator:disabled, QRadioButton::indicator:disabled { background: #e4e8ed; border-color: #8997a6; }
QCheckBox::indicator:checked:disabled, QRadioButton::indicator:checked:disabled { background: #73879a; border-color: #687b8e; image: url("__CHECKMARK__"); }
QComboBox:disabled, QLineEdit:disabled, QTextEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled { color: #707d8c; background: #e9edf2; border-color: #c3ccd6; }
QComboBox QLineEdit:disabled { color: #707d8c; background: transparent; border: 0; }
QComboBox::drop-down:disabled, QSpinBox::up-button:disabled, QDoubleSpinBox::up-button:disabled, QSpinBox::down-button:disabled, QDoubleSpinBox::down-button:disabled { background: #e1e6ec; border-left-color: #c3ccd6; }
QComboBox::down-arrow:disabled { image: url("__SPIN_DOWN_DISABLED__"); }
QSpinBox::up-arrow:disabled, QDoubleSpinBox::up-arrow:disabled { image: url("__SPIN_UP_DISABLED__"); }
QSpinBox::down-arrow:disabled, QDoubleSpinBox::down-arrow:disabled { image: url("__SPIN_DOWN_DISABLED__"); }
"""

DARK_STYLESHEET = """
QMainWindow, QWidget { background: #17191d; color: #e6e8eb; font-family: "Segoe UI"; font-size: 10pt; }
QToolBar#projectToolbar { background: #17191d; border: 0; border-bottom: 1px solid #30343a; spacing: 4px; padding: 7px 12px; }
QToolBar#projectToolbar::separator { width: 1px; background: #30343a; margin: 6px 7px; }
QToolBar#projectToolbar QToolButton { background: transparent; border: 1px solid transparent; border-radius: 7px; padding: 6px 9px; font-weight: 600; }
QToolBar#projectToolbar QToolButton:hover, QToolBar#projectToolbar QToolButton:checked { background: #24272c; }
QToolBar#projectToolbar QToolButton#themeChoice, QToolBar#projectToolbar QToolButton#helpChoice, QToolBar#projectToolbar QToolButton#githubChoice { padding: 5px; }
QToolBar#projectToolbar QToolButton#themeChoice:checked { background: #292d33; border-color: #3b4048; }
QToolBar#projectToolbar QToolButton#recentProjectsButton, QToolBar#projectToolbar QToolButton#exportMenuButton { min-width: 42px; padding: 4px; }
QToolBar#projectToolbar QToolButton#recentProjectsButton::menu-indicator, QToolBar#projectToolbar QToolButton#exportMenuButton::menu-indicator { image: none; width: 0; }
QToolBar#projectToolbar QToolButton#languageChoice { min-width: 38px; padding: 5px; font-weight: 700; }
QWidget#projectSidebar { background: #17191d; border-right: 1px solid #30343a; }
QWidget#datasetActions QToolButton#datasetActionButton { background: #20242a; border: 1px solid #424953; border-radius: 6px; padding: 4px; }
QWidget#datasetActions QToolButton#datasetActionButton:hover { background: #2b3037; border-color: #747d89; }
QWidget#pointViewer { background: #17191d; border: 0; }
QLabel#sectionHeading, QLabel#sidebarHeading { font-size: 15px; font-weight: 700; color: #f0f1f2; }
QLabel#sectionHint, QLabel#sidebarHint, QLabel#sidebarSubtitle { color: #a3a8b0; font-size: 9pt; }
QLabel#guideStepLabel { color: #7db9e9; font-size: 9pt; font-weight: 700; }
QLabel#guideHeading { color: #f0f1f2; font-size: 18pt; font-weight: 700; }
QLabel#guideBody { color: #d0d6dd; font-size: 11pt; }
QProgressBar#guideProgress { background: #343b44; border: 0; border-radius: 3px; }
QProgressBar#guideProgress::chunk { background: #5ba2dc; border-radius: 3px; }
QToolBar#viewerToolbar { background: transparent; border: 0; spacing: 2px; padding: 0; }
QToolBar#viewerToolbar QToolButton { background: transparent; border: 1px solid transparent; border-radius: 5px; padding: 4px; }
QToolBar#viewerToolbar QToolButton:hover, QToolBar#viewerToolbar QToolButton:checked { background: #24272c; }
QStatusBar { background: #17191d; border-top: 1px solid #30343a; }
QGroupBox { background: transparent; border: 0; margin-top: 16px; padding: 8px 0 2px; font-weight: 600; }
QGroupBox::title { subcontrol-origin: margin; left: 0; padding: 0 3px 0 0; color: #d0d3d8; }
QTabWidget::pane { background: transparent; border: 0; top: -1px; }
QTabBar::tab { background: transparent; color: #a3a8b0; border: 0; border-bottom: 2px solid transparent; padding: 9px 11px; }
QTabBar::tab:hover { color: #f0f1f2; background: #202328; }
QTabBar::tab:selected { color: #f0f1f2; background: transparent; border-bottom: 2px solid #a3a8b0; font-weight: 700; }
QPushButton, QToolButton { background: #20242a; border: 1px solid #424953; border-radius: 6px; padding: 6px 9px; }
QPushButton:hover, QToolButton:hover { background: #2b3037; border-color: #747d89; }
QPushButton:disabled, QToolButton:disabled { color: #686e77; background: #1c1f24; border-color: #30343a; }
QPushButton#primaryAction { background: #30363e; color: #f0f1f2; border-color: #545d69; font-weight: 600; }
QPushButton#primaryAction:hover { background: #3a424c; }
QListWidget { background: #1c1f24; color: #e6e8eb; border: 1px solid #424953; border-radius: 5px; padding: 5px; }
QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox { background: #1c1f24; color: #e6e8eb; border: 1px solid #424953; border-radius: 7px; padding: 2px 8px; }
QListWidget { background: #1b1e23; }
QListWidget::item { padding: 4px; }
QListWidget::item:selected { background: #353b43; color: #ffffff; }
QMenu { background: #1c1f24; border: 1px solid #343941; padding: 5px; }
QMenu::item { padding: 7px 18px; border-radius: 4px; }
QMenu::item:selected { background: #30343a; color: #f0f1f2; }
QMainWindow { background: #20252d; }
QToolBar#projectToolbar { background: #20252d; border-bottom: 1px solid #353d47; }
QWidget#toolbarSpacer, QWidget#toolbarChoices, QWidget#datasetActions, QWidget#projectSplitControl, QWidget#exportSplitControl { background: transparent; }
QWidget#themeLanguageSeparator { background: #4a515b; }
QToolBar#projectToolbar QToolButton#languageChoice { border: 1px solid transparent; padding: 3px; }
QToolBar#projectToolbar QToolButton#languageChoice:checked { background: #294f70; border: 1px solid #7db9e9; color: #ffffff; }
QToolBar#projectToolbar QToolButton#toolbarExportButton { min-width: 90px; }
QWidget#projectSidebar { background: #20252d; border: 0; }
QWidget#pointViewer { background: #1b2027; }
QWidget#workspaceTools { background: #20252d; border: 0; }
QSplitter#workspaceSplitter::handle:horizontal { background: #20252d; border-left: 1px solid #434c57; border-right: 1px solid #20252d; }
QSplitter#workspaceSplitter::handle:horizontal:hover { background: #2d445c; border-left-color: #6db3e8; }
QWidget#toolPageViewport { background: #20252d; }
QWidget#toolPage { background: #2a3039; border: 1px solid #424b57; border-radius: 7px; }
QWidget#methodPage { background: transparent; }
QLabel, QCheckBox, QRadioButton { background: transparent; }
QCheckBox { min-height: 24px; spacing: 8px; }
QCheckBox::indicator { subcontrol-origin: padding; subcontrol-position: left center; width: 16px; height: 16px; margin: 0; background: #20252d; border: 2px solid #a3b0be; border-radius: 3px; }
QCheckBox::indicator:hover { border-color: #7db9e9; }
QCheckBox::indicator:checked { background: #0c65ae; border-color: #7db9e9; image: url("__CHECKMARK__"); }
QCheckBox::indicator:disabled { background: #2b323b; border-color: #738190; }
QGroupBox#datasetGroup { background: transparent; border: 0; margin-top: 22px; padding: 2px 0 0; font-size: 14px; color: #c4e4ff; }
QGroupBox#datasetGroup::title { color: #c4e4ff; font-weight: 700; }
QListWidget#datasetList { background: transparent; border: 0; border-top: 1px solid #3d4652; border-radius: 0; padding: 5px 0; }
QListWidget#datasetList::item { border-radius: 5px; padding: 8px 5px; margin: 2px 0; }
QListWidget#datasetList::item:hover { background: #254564; }
QListWidget#datasetList::item:selected { background: #245e91; color: #ffffff; }
QListWidget#datasetList::indicator { width: 16px; height: 16px; background: #20252d; border: 2px solid #a3b0be; border-radius: 3px; }
QListWidget#datasetList::indicator:hover { border-color: #7db9e9; }
QListWidget#datasetList::indicator:checked { background: #0c65ae; border-color: #7db9e9; image: url("__CHECKMARK__"); }
QListWidget#datasetList::indicator:disabled { background: #2b323b; border-color: #738190; }
QListWidget#datasetList::indicator:checked:disabled { background: #526b82; border-color: #748ba0; image: url("__CHECKMARK__"); }
QTabWidget#workspaceTabs { background: transparent; }
QTabWidget#workspaceTabs::pane { background: transparent; border: 0; top: 0; }
QWidget#workspaceTabNavigation, QWidget#workspaceTabStrip, QWidget#workspaceTabViewport { background: transparent; }
QScrollArea#workspaceTabScroll { background: transparent; border: 0; }
QToolButton#workspaceTabButton { background: #2b323b; color: #e4e9ee; border: 1px solid #4a5460; border-bottom: 2px solid #596574; border-radius: 6px; padding: 8px 12px; font-weight: 600; }
QToolButton#workspaceTabButton:hover { background: #364351; border-color: #6f8ca7; }
QToolButton#workspaceTabButton:checked { background: #294f70; border-color: #5789b2; border-bottom: 3px solid #7db9e9; color: #ffffff; }
QToolButton#workspaceTabArrow { background: #2b323b; border: 1px solid #596574; border-radius: 6px; padding: 0; }
QToolButton#workspaceTabArrow:hover { background: #294f70; border-color: #7db9e9; }
QToolButton#workspaceTabArrow:disabled { background: #252b33; border-color: #424c58; }
QScrollArea#toolPageScroll { background: transparent; border: 0; }
QWidget#toolSectionHeader { background: transparent; border: 0; border-radius: 0; }
QWidget#toolSectionDivider { background: #495462; margin: 0 10px; }
QLabel#toolSectionTitle { color: #e5ebf2; font-size: 11pt; font-weight: 700; }
QGroupBox#toolSection { background: transparent; border: 0; border-radius: 0; margin-top: 0; padding: 4px 10px 12px; }
QGroupBox#filterBlock { background: transparent; border: 0; margin-top: 0; padding: 0 10px 8px; }
QCheckBox#filterHeadingCheck { color: #c4e4ff; font-weight: 700; }
QLabel#methodLabel { color: #e5ebf2; font-weight: 700; }
QPushButton#primaryAction { background: #245d8b; color: #ffffff; border-color: #5598cb; border-bottom: 2px solid #70b6e9; }
QPushButton#primaryAction:hover { background: #3175ab; }
QPushButton, QToolButton { border-bottom: 2px solid #47617a; }
QPushButton:hover, QToolButton:hover { border-color: #6ba9dc; background: #294764; }
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { border: 2px solid #5ca8e8; }
QComboBox, QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox { min-height: 24px; border-radius: 7px; padding: 2px 8px; }
QComboBox { padding: 2px 34px 2px 8px; }
QComboBox QLineEdit { background: transparent; border: 0; border-radius: 0; padding: 0; min-height: 0; }
QComboBox::drop-down { subcontrol-origin: padding; subcontrol-position: top right; width: 30px; border: 0; border-left: 1px solid #4a5968; border-top-right-radius: 6px; border-bottom-right-radius: 6px; background: #323b47; }
QComboBox::drop-down:hover { background: #3e5e7b; }
QComboBox::drop-down:pressed { background: #294f70; }
QComboBox::down-arrow { subcontrol-origin: padding; subcontrol-position: center center; image: url("__SPIN_DOWN__"); width: 12px; height: 10px; border: 0; }
QComboBox QAbstractItemView { background: #20252d; color: #e6e8eb; border: 1px solid #46515e; border-radius: 7px; padding: 4px; outline: 0; selection-background-color: #294f70; selection-color: #ffffff; }
QComboBox QAbstractItemView::item { min-height: 25px; padding: 5px 9px; border-radius: 4px; }
QComboBox QAbstractItemView::item:hover { background: #2c4258; color: #ffffff; }
QSpinBox, QDoubleSpinBox { padding: 2px 34px 2px 8px; }
QSpinBox::up-button, QDoubleSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::down-button { subcontrol-origin: border; subcontrol-position: top right; width: 28px; border: 0; border-left: 1px solid #4a5968; background: #323b47; }
QSpinBox::up-button, QDoubleSpinBox::up-button { height: 14px; border-top-right-radius: 6px; border-bottom: 1px solid #414b57; }
QSpinBox::down-button, QDoubleSpinBox::down-button { height: 14px; subcontrol-position: bottom right; border-bottom-right-radius: 6px; }
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover, QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover { background: #3e5e7b; }
QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed, QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed { background: #294f70; }
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow { subcontrol-origin: padding; subcontrol-position: center center; image: url("__SPIN_UP__"); width: 12px; height: 10px; border: 0; }
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow { subcontrol-origin: padding; subcontrol-position: center center; image: url("__SPIN_DOWN__"); width: 12px; height: 10px; border: 0; }
QMenu { background: #20252d; color: #e6e8eb; border: 1px solid #46515e; border-radius: 8px; padding: 5px; }
QMenu::item { min-height: 24px; padding: 6px 24px 6px 10px; border-radius: 5px; }
QMenu::item:selected { background: #294f70; color: #ffffff; }
QMenu::item:disabled { color: #788391; }
QMenu::separator { height: 1px; background: #3b4652; margin: 4px 7px; }
QPushButton:disabled, QToolButton:disabled { color: #a1aab5; background: #292e35; border: 1px solid #4a545f; border-bottom: 1px solid #4a545f; }
QPushButton#primaryAction:disabled, QToolButton#workspaceTabButton:disabled, QToolButton#workspaceTabArrow:disabled, QToolBar#projectToolbar QToolButton:disabled, QToolBar#viewerToolbar QToolButton:disabled, QWidget#datasetActions QToolButton#datasetActionButton:disabled { color: #a1aab5; background: #292e35; border-color: #4a545f; border-bottom-color: #4a545f; }
QCheckBox:disabled, QRadioButton:disabled { color: #a1aab5; }
QCheckBox::indicator:disabled, QRadioButton::indicator:disabled { background: #292e35; border-color: #7b8794; }
QCheckBox::indicator:checked:disabled, QRadioButton::indicator:checked:disabled { background: #526b82; border-color: #748ba0; image: url("__CHECKMARK__"); }
QComboBox:disabled, QLineEdit:disabled, QTextEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled { color: #a1aab5; background: #292e35; border-color: #4a545f; }
QComboBox QLineEdit:disabled { color: #a1aab5; background: transparent; border: 0; }
QComboBox::drop-down:disabled, QSpinBox::up-button:disabled, QDoubleSpinBox::up-button:disabled, QSpinBox::down-button:disabled, QDoubleSpinBox::down-button:disabled { background: #252a31; border-left-color: #4a545f; }
QComboBox::down-arrow:disabled { image: url("__SPIN_DOWN_DISABLED__"); }
QSpinBox::up-arrow:disabled, QDoubleSpinBox::up-arrow:disabled { image: url("__SPIN_UP_DISABLED__"); }
QSpinBox::down-arrow:disabled, QDoubleSpinBox::down-arrow:disabled { image: url("__SPIN_DOWN_DISABLED__"); }
"""


def apply_theme(application, theme: str) -> None:
    """Apply a named theme to a QApplication instance."""
    stylesheet = DARK_STYLESHEET if theme == "dark" else LIGHT_STYLESHEET
    assets = Path(__file__).resolve().parent.parent / "assets"
    dark = theme == "dark"
    replacements = {
        "__CHECKMARK__": (assets / "checkmark.svg").as_posix(),
        "__SPIN_UP__": (assets / f"spin_up_{'dark' if dark else 'light'}.svg").as_posix(),
        "__SPIN_DOWN__": (assets / f"spin_down_{'dark' if dark else 'light'}.svg").as_posix(),
        "__SPIN_UP_DISABLED__": (assets / f"spin_up_{'dark' if dark else 'light'}_disabled.svg").as_posix(),
        "__SPIN_DOWN_DISABLED__": (assets / f"spin_down_{'dark' if dark else 'light'}_disabled.svg").as_posix(),
    }
    for token, path in replacements.items():
        stylesheet = stylesheet.replace(token, path)
    application.setStyleSheet(stylesheet)
