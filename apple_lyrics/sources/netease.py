"""
NetEase Cloud Music lyrics source.
Uses the public (undocumented) search API — best for Chinese songs.
"""
from typing import Optional
import requests
from .base import LyricsResult, LyricsSource

_SEARCH_URL = "https://music.163.com/api/search/get/web"
_LYRIC_URL = "https://music.163.com/api/song/lyric"
_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://music.163.com",
}
_TIMEOUT = 6


class NeteaseSource(LyricsSource):
    """Fetches LRC lyrics from NetEase Cloud Music (best for Chinese songs)."""

    @property
    def name(self) -> str:
        return "netease"

    def fetch(
        self,
        title: str,
        artist: str,
        album: str = "",
        duration: float = 0.0,
    ) -> Optional[LyricsResult]:
        song_id = self._search_id(title, artist)
        if not song_id:
            return None
        return self._get_lyric(song_id)

    def _search_id(self, title: str, artist: str) -> Optional[int]:
        query = f"{artist} {title}"
        try:
            resp = requests.get(
                _SEARCH_URL,
                params={"s": query, "type": 1, "offset": 0, "total": "true", "limit": 5},
                headers=_HEADERS,
                timeout=_TIMEOUT,
            )
            resp.raise_for_status()
            songs = resp.json().get("result", {}).get("songs", [])
            if not songs:
                return None
            # Pick the closest match by name
            title_lower = title.lower()
            for song in songs:
                if song.get("name", "").lower() == title_lower:
                    return song["id"]
            return songs[0]["id"]
        except Exception:
            return None

    def _get_lyric(self, song_id: int) -> Optional[LyricsResult]:
        try:
            resp = requests.get(
                _LYRIC_URL,
                params={"id": song_id, "lv": 1, "kv": 1, "tv": -1},
                headers=_HEADERS,
                timeout=_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            lrc = data.get("lrc", {}).get("lyric", "").strip()
            if not lrc:
                return None
            return ("lrc", lrc)
        except Exception:
            return None
