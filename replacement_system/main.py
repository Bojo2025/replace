"""
Entry point – loads the timetable and launches the Qt application.
"""

import sys
import os

# Allow imports from replacement_system/ when run directly
sys.path.insert(0, os.path.dirname(__file__))

from PyQt5.QtWidgets import QApplication, QMessageBox, QSplashScreen, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

from ui.styles import GLOBAL_STYLE
from ui.main_window import MainWindow
from data_loader import load_timetable

# ── Locate the Excel timetable ────────────────────────────────────────────────
# When running from source: look in parent of replacement_system/
# When running as PyInstaller EXE: look in same folder as the executable
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    _ROOT_DIR = os.path.dirname(sys.executable)
else:
    # Running from source
    _THIS_DIR = os.path.dirname(__file__)
    _ROOT_DIR = os.path.dirname(_THIS_DIR)

TIMETABLE = os.path.join(_ROOT_DIR, "latest 20 april.xlsx")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("BR SSS Replacement System")
    app.setStyle("Fusion")
    app.setStyleSheet(GLOBAL_STYLE)

    # ── Load timetable ────────────────────────────────────────────────────────
    if not os.path.isfile(TIMETABLE):
        QMessageBox.critical(
            None, "File Not Found",
            f"Cannot find the timetable file:\n{TIMETABLE}\n\n"
            "Please place 'latest 20 april.xlsx' in the same folder as this script "
            "and restart."
        )
        sys.exit(1)

    try:
        schedules, teacher_order = load_timetable(TIMETABLE)
    except Exception as exc:
        QMessageBox.critical(
            None, "Load Error",
            f"Failed to parse the timetable:\n{exc}"
        )
        sys.exit(1)

    if not teacher_order:
        QMessageBox.warning(
            None, "No Teachers Found",
            "The timetable was loaded but no teacher rows were detected.\n"
            "Please verify the Excel file."
        )
        sys.exit(1)

    # ── Launch ────────────────────────────────────────────────────────────────
    window = MainWindow(schedules, teacher_order)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
