from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon


def _make_icon() -> QIcon:
    """Generate a simple music-note tray icon programmatically."""
    px = QPixmap(22, 22)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    # Circle background
    p.setBrush(QColor(60, 200, 130))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(1, 1, 20, 20)
    # Simple "♪" note shape: stem + filled head
    p.setBrush(QColor(255, 255, 255))
    p.drawEllipse(5, 13, 6, 5)   # note head
    p.fillRect(11, 6, 2, 10, QColor(255, 255, 255))   # stem
    p.fillRect(11, 6, 5, 2, QColor(255, 255, 255))    # flag
    p.end()
    return QIcon(px)


class TrayIcon(QSystemTrayIcon):
    def __init__(self, window, parent=None) -> None:
        super().__init__(_make_icon(), parent)
        self._window = window
        self.setToolTip("lyra")

        menu = QMenu()
        self._vis_action = menu.addAction("Hide Lyrics")
        self._vis_action.triggered.connect(self._toggle_visibility)
        menu.addSeparator()

        theme_menu = menu.addMenu("Theme")
        theme_menu.addAction("Dark").triggered.connect(lambda: self._set_theme("dark"))
        theme_menu.addAction("Light").triggered.connect(lambda: self._set_theme("light"))
        menu.addSeparator()

        menu.addAction("Stats").triggered.connect(self._show_stats)
        menu.addSeparator()

        menu.addAction("Quit").triggered.connect(QApplication.quit)
        self.setContextMenu(menu)
        self.show()

    def _toggle_visibility(self) -> None:
        if self._window.isVisible():
            self._window.hide()
            self._vis_action.setText("Show Lyrics")
        else:
            self._window.show()
            self._window.raise_()
            # Re-apply native on-top level after re-show
            self._window._apply_native_ontop()
            self._vis_action.setText("Hide Lyrics")

    def _set_theme(self, theme: str) -> None:
        self._window._config.theme = theme
        self._window._config.save()
        self._window.update()

    def _show_stats(self) -> None:
        from .stats_dialog import StatsDialog
        dlg = StatsDialog()
        dlg.exec()
