import json
import os
from PyQt6.QtCore import QStandardPaths

SETTINGS_FILE = "app_settings.json"
_DEFAULT_SETTINGS_FILE = SETTINGS_FILE


def _settings_path():
    """Use the platform's per-user config directory, while reading legacy local settings."""
    if SETTINGS_FILE != _DEFAULT_SETTINGS_FILE:
        return SETTINGS_FILE
    config_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
    if not config_dir:
        return SETTINGS_FILE
    return os.path.join(config_dir, SETTINGS_FILE)

def load_app_settings():
    settings_path = _settings_path()
    legacy_path = SETTINGS_FILE if SETTINGS_FILE == _DEFAULT_SETTINGS_FILE else None
    if not os.path.exists(settings_path) and legacy_path and os.path.exists(legacy_path):
        settings_path = legacy_path
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_app_settings(settings):
    settings_path = _settings_path()
    try:
        os.makedirs(os.path.dirname(os.path.abspath(settings_path)), exist_ok=True)
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"Failed to save app settings: {e}")
