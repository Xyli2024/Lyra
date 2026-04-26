from typing import Optional
import requests
from .base import LyricsResult, LyricsSource

_BASE = "https://lrclib.net/api"
_HEADERS = {"User-Agent": "apple-lyrics/0.1 (https://github.com/yourusername/apple-lyrics)"}
_TIMEOUT = 6


class LRCLibSource(LyricsSource):
    """Fetches synced (LRC) lyrics from lrclib.net — free, no auth required."""

    @property
    def name(self) -> str:
        return "lrclib"

    def fetch(
        self,
        title: str,
        artist: str,
        album: str = "",
        duration: float = 0.0,
    ) -> Optional[LyricsResult]:
        params: dict = {"track_name": title, "artist_name": artist}
        if album:
            params["album_name"] = album
        if duration:
            params["duration"] = int(duration)

        try:
            resp = requests.get(
                f"{_BASE}/get", params=params, headers=_HEADERS, timeout=_TIMEOUT
            )
            if resp.status_code == 404:
                # Fall back to fuzzy search
                return self._search(title, artist)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return None

        return self._extract(data)

    def _search(self, title: str, artist: str) -> Optional[LyricsResult]:
        try:
            resp = requests.get(
                f"{_BASE}/search",
                params={"track_name": title, "artist_name": artist},
                headers=_HEADERS,
                timeout=_TIMEOUT,
            )
            resp.raise_for_status()
            results = resp.json()
            if not results:
                return None
            return self._extract(results[0])
        except Exception:
            return None

    @staticmethod
    def _extract(data: dict) -> Optional[LyricsResult]:
        if data.get("instrumental"):
            return ("plain", "[Instrumental]")
        synced = data.get("syncedLyrics", "").strip()
        if synced:
            return ("lrc", synced)
        plain = data.get("plainLyrics", "").strip()
        if plain:
            return ("plain", plain)
        return None
