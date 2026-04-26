from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QPoint, QRectF, Qt, QTimer
from PyQt6.QtGui import (
    QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPen,
)
from PyQt6.QtWidgets import QApplication, QWidget

from ..config import Config
from ..lrc_parser import LrcLines, current_index, parse_lrc, plain_to_timed
from ..monitor import MusicMonitor

_CONTEXT = 2      # lines shown above/below current line
_POLL_MS = 300    # Apple Music poll interval


# ── per-offset display style: (font_size_delta, alpha, bold) ─────────────────
_STYLE: dict[int, tuple[int, int, bool]] = {
    0: (0,   255, True),
    1: (-5,  150, False),
    2: (-9,  75,  False),
}


class LyricsWindow(QWidget):
    def __init__(self, config: Config) -> None:
        super().__init__()
        self._config = config
        self._monitor = MusicMonitor()
        self._lines: LrcLines = []
        self._current_idx: int = -1
        self._last_track_id: str = ""
        self._status: str = "Waiting for Apple Music…"
        self._drag_origin: Optional[QPoint] = None
        self._worker = None

        self._init_window()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._timer.start(_POLL_MS)

    # ── window setup ─────────────────────────────────────────────────────────

    def _init_window(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        screen = QApplication.primaryScreen().availableGeometry()
        w = self._config.window_width
        h = self._calc_height()

        if self._config.window_x >= 0:
            x, y = self._config.window_x, self._config.window_y
        else:
            x = (screen.width() - w) // 2
            y = screen.bottom() - h - 24   # 24px above Dock/taskbar

        self.setGeometry(x, y, w, h)

    def _calc_height(self) -> int:
        fs = self._config.font_size
        total = 0
        for offset in range(-_CONTEXT, _CONTEXT + 1):
            delta, _, _ = _STYLE.get(abs(offset), (-9, 60, False))
            size = max(10, fs + delta)
            total += size + 14   # line height = font size + leading
        return total + 40        # top + bottom padding

    # ── polling & lyrics loading ──────────────────────────────────────────────

    def _poll(self) -> None:
        track = self._monitor.get_current_track()

        if track is None:
            if self._status != "Music is not playing":
                self._status = "Music is not playing"
                self._lines = []
                self._current_idx = -1
                self.update()
            return

        if track.track_id != self._last_track_id:
            self._last_track_id = track.track_id
            self._lines = []
            self._current_idx = -1
            self._status = f"Loading: {track.title}…"
            self.update()
            self._start_fetch(track)

        new_idx = current_index(self._lines, track.position)
        if new_idx != self._current_idx:
            self._current_idx = new_idx
            self.update()

    def _start_fetch(self, track) -> None:
        from .worker import LyricsWorker
        if self._worker and self._worker.isRunning():
            self._worker.quit()

        self._worker = LyricsWorker(
            track.title, track.artist, track.album,
            track.duration, track.track_id,
        )
        self._worker.lyrics_ready.connect(self._on_lyrics)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

    def _on_lyrics(self, fmt: str, text: str, track_id: str) -> None:
        if track_id != self._last_track_id:
            return   # stale — track changed while fetching
        if fmt == "lrc":
            self._lines = parse_lrc(text)
        else:
            track = self._monitor.get_current_track()
            dur = track.duration if track else 240.0
            self._lines = plain_to_timed(text, dur)
        self._status = ""
        self.update()

    # ── painting ──────────────────────────────────────────────────────────────

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._draw_background(p)
        if self._status:
            self._draw_status(p, self._status)
        elif self._lines:
            self._draw_lyrics(p)
        else:
            self._draw_status(p, "No lyrics found")

    def _draw_background(self, p: QPainter) -> None:
        if self._config.theme == "dark":
            fill = QColor(16, 16, 22, int(self._config.opacity * 255))
            border = QColor(255, 255, 255, 28)
        else:
            fill = QColor(245, 245, 250, int(self._config.opacity * 255))
            border = QColor(0, 0, 0, 20)

        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, self.width(), self.height()), 18, 18)
        p.fillPath(path, fill)
        p.setPen(QPen(border, 1.0))
        p.drawPath(path)

    def _draw_status(self, p: QPainter, msg: str) -> None:
        color = QColor(180, 180, 190) if self._config.theme == "dark" else QColor(100, 100, 110)
        p.setPen(color)
        p.setFont(QFont("Helvetica Neue", 14))
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, msg)

    def _draw_lyrics(self, p: QPainter) -> None:
        if self._current_idx < 0:
            return

        fs = self._config.font_size
        is_dark = self._config.theme == "dark"

        # Build list of (offset, text, font_size, alpha, bold)
        rows = []
        for offset in range(-_CONTEXT, _CONTEXT + 1):
            idx = self._current_idx + offset
            text = self._lines[idx][1] if 0 <= idx < len(self._lines) else ""
            delta, alpha, bold = _STYLE.get(abs(offset), (-9, 60, False))
            size = max(10, fs + delta)
            rows.append((text, size, alpha, bold))

        # Measure total block height
        total_h = sum(
            QFontMetrics(self._make_font(size, bold)).height() + 10
            for _, size, _, bold in rows
        )

        y = (self.height() - total_h) // 2
        for text, size, alpha, bold in rows:
            font = self._make_font(size, bold)
            lh = QFontMetrics(font).height() + 10
            if text:
                base = 255 if is_dark else 20
                color = QColor(base, base, base, alpha)
                p.setPen(color)
                p.setFont(font)
                p.drawText(
                    0, y, self.width(), lh,
                    int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter),
                    text,
                )
            y += lh

    @staticmethod
    def _make_font(size: int, bold: bool) -> QFont:
        f = QFont()
        f.setFamilies(["SF Pro Display", "Helvetica Neue", "Arial"])
        f.setPointSize(size)
        f.setBold(bold)
        return f

    # ── interaction ───────────────────────────────────────────────────────────

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_origin = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event) -> None:
        if self._drag_origin and (event.buttons() & Qt.MouseButton.LeftButton):
            self.move(event.globalPosition().toPoint() - self._drag_origin)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_origin = None
            pos = self.pos()
            self._config.window_x = pos.x()
            self._config.window_y = pos.y()
            self._config.save()

    def wheelEvent(self, event) -> None:
        delta = 1 if event.angleDelta().y() > 0 else -1
        self._config.font_size = max(12, min(42, self._config.font_size + delta))
        self._config.save()
        new_h = self._calc_height()
        self.resize(self.width(), new_h)
        self.update()
