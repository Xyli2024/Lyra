"""Headless background recorder — no Qt, no GUI.

Polls Apple Music every 5 seconds and writes plays to the history DB.
Designed to run as a macOS LaunchAgent so stats accumulate even when
the Lyra window is not open.

Usage:  lyra --daemon
"""
import signal
import time

from .history import log_play
from .monitor import MusicMonitor, TrackInfo

_POLL_S = 5.0


def run() -> None:
    monitor  = MusicMonitor()
    last_id  = ""
    last_info: TrackInfo | None = None
    last_pos  = 0.0

    def _flush() -> None:
        if last_info is not None:
            log_play(last_info.title, last_info.artist, last_info.album,
                     last_info.genre, last_info.duration, last_pos)

    signal.signal(signal.SIGTERM, lambda *_: (_flush(), exit(0)))
    signal.signal(signal.SIGINT,  lambda *_: (_flush(), exit(0)))

    while True:
        try:
            track = monitor.get_current_track()
        except Exception:
            track = None

        if track is None:
            if last_info is not None:
                _flush()
                last_info = None
                last_id   = ""
        else:
            last_pos = track.position
            if track.track_id != last_id:
                _flush()
                last_id   = track.track_id
                last_info = track

        time.sleep(_POLL_S)
