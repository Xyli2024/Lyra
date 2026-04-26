"""SQLite-backed play history. All writes are fire-and-forget."""
import sqlite3
import time
from pathlib import Path

_DB_PATH = Path.home() / ".local" / "share" / "lyra" / "history.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS plays (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ts        REAL    NOT NULL,
    title     TEXT    NOT NULL,
    artist    TEXT    NOT NULL,
    album     TEXT    NOT NULL DEFAULT '',
    genre     TEXT    NOT NULL DEFAULT '',
    duration  REAL    NOT NULL DEFAULT 0,
    played_s  REAL    NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS plays_ts     ON plays(ts);
CREATE INDEX IF NOT EXISTS plays_artist ON plays(artist COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS plays_genre  ON plays(genre  COLLATE NOCASE);
"""

_MIN_PLAYED_S = 10.0   # ignore accidental skips shorter than this


def _open() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    conn.executescript(_SCHEMA)
    return conn


def log_play(title: str, artist: str, album: str, genre: str,
             duration: float, played_s: float) -> None:
    if played_s < _MIN_PLAYED_S:
        return
    try:
        with _open() as conn:
            conn.execute(
                "INSERT INTO plays (ts, title, artist, album, genre, duration, played_s) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (time.time(), title, artist, album, genre,
                 round(duration, 1), round(played_s, 1)),
            )
    except Exception:
        pass
