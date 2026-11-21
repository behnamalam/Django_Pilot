import sys
from pathlib import Path
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from ui import DjangoPilotApp


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Django Pilot")
    logo = Path(__file__).resolve().parent / "assets" / "error_lover_django_pilot.png"
    if logo.is_file():
        app.setWindowIcon(QIcon(str(logo)))
    window = DjangoPilotApp()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
