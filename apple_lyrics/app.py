import sys

from PyQt6.QtWidgets import QApplication

from .config import Config
from .ui.tray import TrayIcon
from .ui.window import LyricsWindow


def run_gui() -> None:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)   # keep alive when window is hidden
    app.setApplicationName("apple-lyrics")

    config = Config.load()
    window = LyricsWindow(config)
    window.show()

    tray = TrayIcon(window)   # noqa: F841 — must stay alive

    sys.exit(app.exec())
