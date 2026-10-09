import sys
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.ui.application_identity import application_icon, set_windows_app_id

def main():
    set_windows_app_id()
    app = QApplication(sys.argv)
    app.setWindowIcon(application_icon())
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
