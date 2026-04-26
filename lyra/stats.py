"""Query play history and compute listening statistics."""
import sqlite3
from typing import Dict, List, Optional, Tuple

from .history import _DB_PATH


def _conn() -> Optional[sqlite3.Connection]:
    if not _DB_PATH.exists():
        return None
    return sqlite3.connect(str(_DB_PATH))


def total_stats() -> Dict:
    conn = _conn()
    if not conn:
        return {}
    try:
        row = conn.execute(
            "SELECT COUNT(*), SUM(played_s)/3600.0, "
            "COUNT(DISTINCT artist), COUNT(DISTINCT NULLIF(genre,'')) "
            "FROM plays"
        ).fetchone()
        return {
            "total_plays":    row[0] or 0,
            "total_hours":    round(row[1] or 0.0, 1),
            "unique_artists": row[2] or 0,
            "unique_genres":  row[3] or 0,
        }
    finally:
        conn.close()


def top_artists(n: int = 10) -> List[Tuple[str, int, float]]:
    """[(artist, plays, hours)] sorted by plays desc."""
    conn = _conn()
    if not conn:
        return []
    try:
        return conn.execute(
            "SELECT artist, COUNT(*) AS cnt, SUM(played_s)/3600.0 AS hrs "
            "FROM plays GROUP BY artist COLLATE NOCASE "
            "ORDER BY cnt DESC LIMIT ?",
            (n,),
        ).fetchall()
    finally:
        conn.close()


def genre_distribution() -> List[Tuple[str, int]]:
    """[(genre, count)] sorted by count desc, empty genre excluded."""
    conn = _conn()
    if not conn:
        return []
    try:
        return conn.execute(
            "SELECT genre, COUNT(*) AS cnt FROM plays "
            "WHERE genre != '' GROUP BY genre COLLATE NOCASE "
            "ORDER BY cnt DESC"
        ).fetchall()
    finally:
        conn.close()


def recent_plays(n: int = 20) -> List[Tuple[str, str, str, float]]:
    """[(title, artist, genre, played_s)] most recent first."""
    conn = _conn()
    if not conn:
        return []
    try:
        return conn.execute(
            "SELECT title, artist, genre, played_s FROM plays "
            "ORDER BY ts DESC LIMIT ?",
            (n,),
        ).fetchall()
    finally:
        conn.close()
