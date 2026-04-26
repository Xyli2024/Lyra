from __future__ import annotations

import random
import time
from typing import Dict, List, Optional, Tuple

from PyQt6.QtCore import QPoint, QRect, QRectF, Qt, QTimer
from PyQt6.QtGui import (
    QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPen,
)
from PyQt6.QtWidgets import QApplication, QWidget

from ..config import Config
from ..lrc_parser import LrcLines, current_index, parse_lrc, plain_to_timed
from ..monitor import MusicMonitor

_POLL_MS      = 500   # AppleScript call interval — slow, expensive
_RENDER_MS    = 16    # render + position-interpolation tick ≈ 60 fps
_LEADING      = 6
_LINE_GAP     = 8
_V_PAD        = 22
_ANIM_DURATION = 380  # ms

_CLOSE_R = 7
_CLOSE_M = 11

_PALETTE: list[Tuple[int, int, int]] = [
    (255, 251, 246),  # warm ivory
    (245, 249, 255),  # ice blue
    (244, 255, 250),  # mint
    (251, 245, 255),  # lavender
    (255, 248, 243),  # peach
    (246, 255, 246),  # sage
    (255, 253, 248),  # cream
]

_STYLE = {
    0: (+2,  255, True),
    1: (-6,  100, False),
}


def _ease(t: float) -> float:
    return t * t * (3.0 - 2.0 * t)   # smoothstep S-curve


# ── global font cache ─────────────────────────────────────────────────────────
# QFont construction is expensive; cache by (pointsize, bold).
_FONT_CACHE: Dict[Tuple[int, bool], QFont] = {}


def _font(size: int, bold: bool) -> QFont:
    key = (size, bold)
    if key not in _FONT_CACHE:
        f = QFont("Helvetica Neue")
        f.setPointSize(size)
        f.setBold(bold)
        _FONT_CACHE[key] = f
    return _FONT_CACHE[key]


class LyricsWindow(QWidget):
    def __init__(self, config: Config) -> None:
        super().__init__()
        self._config   = config
        self._monitor  = MusicMonitor()
        self._lines: LrcLines = []
        self._current_idx: int   = -1
        self._last_track_id: str = ""
        self._status: str        = "Waiting for Apple Music…"
        self._drag_origin: Optional[QPoint] = None
        self._close_hovered: bool = False
        self._workers: List = []
        self._bg_tint = random.choice(_PALETTE)
        self._last_track_info = None   # TrackInfo of the currently-playing track

        # ── position interpolation state ──────────────────────────────────────
        # The poll timer updates these every 500ms; the render timer uses them
        # to estimate the *current* playback position at 60fps precision.
        self._play_pos: float  = 0.0   # confirmed position from AppleScript
        self._play_ts:  float  = 0.0   # monotonic time when _play_pos was set
        self._is_playing: bool = False
        self._track_dur: float = 0.0

        # ── animation state ───────────────────────────────────────────────────
        self._anim_progress: float = 1.0
        self._anim_from_idx: int   = -1
        # pre-cached objects filled in _start_anim
        self._af0: Optional[QFont] = None   # settled current-line font
        self._af1: Optional[QFont] = None   # settled next-line font
        self._alh0: int = 0                 # pre-measured line heights
        self._alh1: int = 0
        self._as0: int  = 0                 # point sizes (for interpolation)
        self._as1: int  = 0

        # ── cached geometry ───────────────────────────────────────────────────
        self._clip: QPainterPath = QPainterPath()

        self._init_window()

        # Slow: AppleScript (expensive)
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll)
        self._poll_timer.start(_POLL_MS)

        # Fast: render + position interpolation (cheap)
        self._render_timer = QTimer(self)
        self._render_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._render_timer.timeout.connect(self._render_tick)
        self._render_timer.start(_RENDER_MS)

    # ── window setup ─────────────────────────────────────────────────────────

    def _init_window(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)

        screen = QApplication.primaryScreen().availableGeometry()
        w = self._config.window_width
        h = self._calc_height()

        if self._config.window_x >= 0:
            x, y = self._config.window_x, self._config.window_y
        else:
            x = (screen.width() - w) // 2
            y = screen.bottom() - h - 28

        self.setGeometry(x, y, w, h)
        self._rebuild_clip()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._rebuild_clip()

    def _rebuild_clip(self) -> None:
        self._clip = QPainterPath()
        self._clip.addRoundedRect(QRectF(0, 0, self.width(), self.height()), 16, 16)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        QTimer.singleShot(0, self._apply_native_ontop)

    def _apply_native_ontop(self) -> None:
        try:
            import ctypes, ctypes.util
            lib = ctypes.CDLL(ctypes.util.find_library("objc"))
            lib.sel_registerName.restype  = ctypes.c_void_p
            lib.sel_registerName.argtypes = [ctypes.c_char_p]

            fn = ctypes.cast(lib.objc_msgSend, ctypes.c_void_p).value
            MsgPtr  = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)
            MsgLong = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long)
            get_win   = MsgPtr(fn)
            set_level = MsgLong(fn)
            set_beh   = MsgLong(fn)

            ns_view   = ctypes.c_void_p(int(self.winId()))
            ns_window = ctypes.c_void_p(get_win(ns_view, lib.sel_registerName(b"window")))
            if ns_window:
                set_level(ns_window, lib.sel_registerName(b"setLevel:"), 3)
                set_beh(ns_window, lib.sel_registerName(b"setCollectionBehavior:"), 1 | 64)
        except Exception:
            pass

    def _calc_height(self) -> int:
        fs = self._config.font_size
        total = 0
        for offset in (0, 1):
            delta, _, _ = _STYLE[offset]
            total += QFontMetrics(_font(max(10, fs + delta), False)).height() + _LEADING
        return total + _LINE_GAP + _V_PAD * 2

    def _close_btn_rect(self) -> QRect:
        d = _CLOSE_R * 2
        return QRect(self.width() - _CLOSE_M - d, _CLOSE_M, d, d)

    # ── slow poll (AppleScript) ───────────────────────────────────────────────

    def _poll(self) -> None:
        try:
            self._do_poll()
        except Exception:
            pass

    def _log_current_play(self) -> None:
        info = self._last_track_info
        if info is None:
            return
        self._last_track_info = None
        try:
            from ..history import log_play
            log_play(info.title, info.artist, info.album, info.genre,
                     info.duration, self._play_pos)
        except Exception:
            pass

    def _do_poll(self) -> None:
        track = self._monitor.get_current_track()

        if track is None:
            if self._is_playing or self._lines:
                self._log_current_play()
                self._is_playing = False
                self._lines      = []
                self._current_idx = -1
                self._anim_progress = 1.0
                self._status = "Music is not playing"
                self.update()
            return

        # Refresh position anchor — the render tick interpolates between polls
        self._play_pos   = track.position
        self._play_ts    = time.monotonic()
        self._is_playing = track.is_playing
        self._track_dur  = track.duration

        if track.track_id == self._last_track_id:
            return   # nothing structural changed

        # ── new track ─────────────────────────────────────────────────────
        self._log_current_play()
        self._last_track_id   = track.track_id
        self._last_track_info = track
        self._lines           = []
        self._current_idx     = -1
        self._anim_progress   = 1.0
        self._status          = f"Loading: {track.title}…"
        self.update()
        self._start_fetch(track)

    # ── fast render tick (60 fps) ─────────────────────────────────────────────

    def _render_tick(self) -> None:
        needs_repaint = False

        # Advance animation
        if self._anim_progress < 1.0:
            self._anim_progress = min(
                1.0, self._anim_progress + _RENDER_MS / _ANIM_DURATION
            )
            needs_repaint = True

        # Interpolate playback position and detect line changes
        if self._is_playing and self._lines and not self._status:
            elapsed  = time.monotonic() - self._play_ts
            pos      = min(self._track_dur, self._play_pos + elapsed)
            new_idx  = current_index(self._lines, pos)

            if new_idx != self._current_idx:
                if new_idx == self._current_idx + 1 and self._anim_progress >= 0.85:
                    self._start_anim(self._current_idx)
                self._current_idx = new_idx
                needs_repaint = True

        if needs_repaint:
            self.update()

    # ── lyrics fetching ───────────────────────────────────────────────────────

    def _start_fetch(self, track) -> None:
        from .worker import LyricsWorker
        for w in self._workers:
            try:
                w.lyrics_ready.disconnect(self._on_lyrics)
            except RuntimeError:
                pass
        self._workers = [w for w in self._workers if w.isRunning()]

        worker = LyricsWorker(
            track.title, track.artist, track.album,
            track.duration, track.track_id,
        )
        worker.lyrics_ready.connect(self._on_lyrics)
        worker.finished.connect(lambda: self._prune_workers())
        worker.start()
        self._workers.append(worker)

    def _prune_workers(self) -> None:
        self._workers = [w for w in self._workers if w.isRunning()]

    def _on_lyrics(self, fmt: str, text: str, track_id: str) -> None:
        if track_id != self._last_track_id:
            return
        try:
            if fmt == "lrc":
                self._lines = parse_lrc(text)
            else:
                track = self._monitor.get_current_track()
                self._lines = plain_to_timed(text, track.duration if track else 240.0)
            self._status = ""
            # Pre-warm font cache now (idle time) so _start_anim has zero overhead later
            QTimer.singleShot(0, self._prewarm_fonts)
            self.update()
        except Exception:
            pass

    def _prewarm_fonts(self) -> None:
        """Create all QFont objects the animation will need. Called once per track."""
        fs = self._config.font_size
        for sz in range(max(10, fs + _STYLE[1][0]), max(10, fs + _STYLE[0][0]) + 1):
            _font(sz, False)
            _font(sz, True)

    # ── animation ─────────────────────────────────────────────────────────────

    def _start_anim(self, from_idx: int) -> None:
        # All QFont objects are pre-warmed by the time this runs,
        # so every _font() call here is a pure dict lookup — no allocation.
        fs = self._config.font_size
        self._as0  = max(10, fs + _STYLE[0][0])
        self._as1  = max(10, fs + _STYLE[1][0])
        self._af0  = _font(self._as0, True)
        self._af1  = _font(self._as1, False)
        self._alh0 = QFontMetrics(self._af0).height() + _LEADING
        self._alh1 = QFontMetrics(self._af1).height() + _LEADING

        self._anim_from_idx = from_idx
        self._anim_progress = 0.0

    # ── painting ──────────────────────────────────────────────────────────────

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._draw_bg(p)
        if self._status:
            self._draw_status(p, self._status)
        elif self._lines:
            if self._anim_progress < 1.0 and self._anim_from_idx >= 0 and self._af0:
                self._draw_anim(p)
            else:
                self._draw_static(p)
        else:
            self._draw_status(p, "No lyrics found")
        self._draw_close(p)

    def _draw_bg(self, p: QPainter) -> None:
        if self._config.theme == "light":
            r, g, b = self._bg_tint
            fill = QColor(r, g, b, int(self._config.opacity * 255))
        else:
            fill = QColor(16, 16, 22, int(self._config.opacity * 255))
        p.fillPath(self._clip, fill)
        p.setPen(Qt.PenStyle.NoPen)

    def _draw_status(self, p: QPainter, msg: str) -> None:
        color = QColor(100, 100, 110) if self._config.theme == "light" else QColor(180, 180, 190)
        p.setPen(color)
        p.setFont(_font(13, False))
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, msg)

    def _draw_close(self, p: QPainter) -> None:
        rect = self._close_btn_rect()
        p.save()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(220, 60, 50, 210) if self._close_hovered else QColor(120, 120, 130, 80))
        p.drawEllipse(rect)
        cx, cy = rect.center().x(), rect.center().y()
        pen = QPen(QColor(255, 255, 255, 200), 1.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        o = 3.5
        p.drawLine(int(cx - o), int(cy - o), int(cx + o), int(cy + o))
        p.drawLine(int(cx + o), int(cy - o), int(cx - o), int(cy + o))
        p.restore()

    def _layout(self) -> Tuple[int, int, int, int, int]:
        """Return (y0, y1, lh0, lh1, shift) for the settled two-line layout."""
        lh0   = self._alh0 if self._af0 else (QFontMetrics(_font(max(10, self._config.font_size + _STYLE[0][0]), True)).height() + _LEADING)
        lh1   = self._alh1 if self._af1 else (QFontMetrics(_font(max(10, self._config.font_size + _STYLE[1][0]), False)).height() + _LEADING)
        total = lh0 + _LINE_GAP + lh1
        y0    = (self.height() - total) // 2
        y1    = y0 + lh0 + _LINE_GAP
        return y0, y1, lh0, lh1, lh0 + _LINE_GAP

    def _draw_static(self, p: QPainter) -> None:
        fs   = self._config.font_size
        base = 20 if self._config.theme == "light" else 255

        lh0 = QFontMetrics(_font(max(10, fs + _STYLE[0][0]), True)).height()  + _LEADING
        lh1 = QFontMetrics(_font(max(10, fs + _STYLE[1][0]), False)).height() + _LEADING
        total = lh0 + _LINE_GAP + lh1
        y     = (self.height() - total) // 2

        for i, offset in enumerate((0, 1)):
            idx  = self._current_idx + offset
            text = self._lines[idx][1] if 0 <= idx < len(self._lines) else ""
            delta, alpha, bold = _STYLE[offset]
            lh = lh0 if offset == 0 else lh1
            if text:
                p.setPen(QColor(base, base, base, alpha))
                p.setFont(_font(max(10, fs + delta), bold))
                p.drawText(0, y, self.width(), lh,
                           int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter),
                           text)
            y += lh
            if i == 0:
                y += _LINE_GAP

    def _draw_anim(self, p: QPainter) -> None:
        t    = _ease(self._anim_progress)
        base = 20 if self._config.theme == "light" else 255

        lh0   = self._alh0
        lh1   = self._alh1
        total = lh0 + _LINE_GAP + lh1
        y0    = (self.height() - total) // 2
        y1    = y0 + lh0 + _LINE_GAP
        shift = lh0 + _LINE_GAP

        fi   = self._anim_from_idx
        ci   = self._current_idx

        p.save()
        p.setClipPath(self._clip)   # use cached clip path — no allocation

        # ① old current: slides up, fades out
        if 0 <= fi < len(self._lines) and self._lines[fi][1]:
            p.setPen(QColor(base, base, base, max(0, int(255 * (1.0 - t)))))
            p.setFont(self._af0)
            p.drawText(0, int(y0 - t * shift), self.width(), lh0,
                       int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter),
                       self._lines[fi][1])

        # ② new current (was next): slides up, grows, brightens
        if 0 <= ci < len(self._lines) and self._lines[ci][1]:
            sz   = self._as1 + int(t * (self._as0 - self._as1))
            alp  = int(_STYLE[1][1] + t * (255 - _STYLE[1][1]))
            # Height interpolation — no QFontMetrics call per frame
            lh_i = int(lh1 + t * (lh0 - lh1))
            p.setPen(QColor(base, base, base, alp))
            p.setFont(_font(sz, True))          # always bold — no abrupt switch at t=0.5
            p.drawText(0, int(y1 - t * shift), self.width(), lh_i,
                       int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter),
                       self._lines[ci][1])

        # ③ incoming next: slides in from below, fades in
        ni = ci + 1
        if 0 <= ni < len(self._lines) and self._lines[ni][1]:
            p.setPen(QColor(base, base, base, max(0, int(_STYLE[1][1] * t))))
            p.setFont(self._af1)
            p.drawText(0, int(y1 + shift * (1.0 - t)), self.width(), lh1,
                       int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter),
                       self._lines[ni][1])

        p.restore()

    # ── helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _make_font(size: int, bold: bool) -> QFont:
        return _font(size, bold)

    # ── interaction ───────────────────────────────────────────────────────────

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if self._close_btn_rect().contains(event.position().toPoint()):
                self.hide()
                return
            self._drag_origin = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event) -> None:
        pos     = event.position().toPoint()
        hovered = self._close_btn_rect().contains(pos)
        if hovered != self._close_hovered:
            self._close_hovered = hovered
            self.update()
        if self._drag_origin and (event.buttons() & Qt.MouseButton.LeftButton):
            self.move(event.globalPosition().toPoint() - self._drag_origin)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_origin = None
            pos = self.pos()
            self._config.window_x = pos.x()
            self._config.window_y = pos.y()
            self._config.save()

    def leaveEvent(self, event) -> None:
        if self._close_hovered:
            self._close_hovered = False
            self.update()

    def wheelEvent(self, event) -> None:
        delta = 1 if event.angleDelta().y() > 0 else -1
        self._config.font_size = max(12, min(42, self._config.font_size + delta))
        self._config.save()
        self.resize(self.width(), self._calc_height())
        self.update()
