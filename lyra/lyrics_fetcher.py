from typing import List, Optional, Tuple
from . import cache
from .sources.base import LyricsResult, LyricsSource
from .sources.lrclib import LRCLibSource
from .sources.lyricsovh import LyricsOvhSource
from .sources.netease import NeteaseSource

# Try sources in this order; first successful result wins.
_DEFAULT_SOURCES: List[LyricsSource] = [
    LRCLibSource(),   # synced LRC, covers both EN and ZH
    NeteaseSource(),  # LRC, strong for Chinese songs
    LyricsOvhSource(), # plain text fallback
]


class LyricsFetcher:
    def __init__(self, sources: Optional[List[LyricsSource]] = None) -> None:
        self.sources = sources or _DEFAULT_SOURCES

    def fetch(
        self,
        title: str,
        artist: str,
        album: str = "",
        duration: float = 0.0,
    ) -> Optional[LyricsResult]:
        """Return (format, lyrics) from cache or the first source that responds."""
        cache_key = f"{artist.lower()}::{title.lower()}"
        cached = cache.get(cache_key)
        if cached:
            return (cached["format"], cached["lyrics"])

        for source in self.sources:
            result = source.fetch(title, artist, album, duration)
            if result:
                fmt, lyrics = result
                cache.set(cache_key, {"format": fmt, "lyrics": lyrics, "source": source.name})
                return result

        return None
