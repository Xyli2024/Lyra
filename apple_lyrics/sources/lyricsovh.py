from typing import Optional
import requests
from .base import LyricsResult, LyricsSource

_BASE = "https://api.lyrics.ovh/v1"
_TIMEOUT = 6


class LyricsOvhSource(LyricsSource):
    """Plain-text lyrics fallback from lyrics.ovh."""

    @property
    def name(self) -> str:
        return "lyrics.ovh"

    def fetch(
        self,
        title: str,
        artist: str,
        album: str = "",
        duration: float = 0.0,
    ) -> Optional[LyricsResult]:
        try:
            resp = requests.get(
                f"{_BASE}/{requests.utils.quote(artist)}/{requests.utils.quote(title)}",
                timeout=_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            lyrics = data.get("lyrics", "").strip()
            if not lyrics:
                return None
            return ("plain", lyrics)
        except Exception:
            return None
