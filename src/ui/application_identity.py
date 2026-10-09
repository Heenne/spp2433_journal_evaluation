"""Application icon and Windows taskbar identity."""
import sys
import warnings
from pathlib import Path

from PyQt6.QtGui import QIcon


WINDOWS_APP_ID = "SPP2433.PointCloudEvaluation"
ICON_PATH = Path(__file__).resolve().parents[1] / "assets" / "app_icon.ico"


def application_icon():
    return QIcon(str(ICON_PATH))


def set_windows_app_id():
    """Identify this viewer separately from the Python host, before any UI exists."""
    if sys.platform != "win32":
        return
    import ctypes

    setter = ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID
    setter.argtypes = [ctypes.c_wchar_p]
    setter.restype = ctypes.c_long
    result = setter(WINDOWS_APP_ID)
    if result < 0:
        warnings.warn(f"Could not set Windows taskbar identity (HRESULT {result:#x}).", RuntimeWarning)
