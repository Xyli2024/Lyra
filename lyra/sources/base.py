from abc import ABC, abstractmethod
from typing import Optional, Tuple

LyricsResult = Tuple[str, str]  # (format: "lrc" | "plain", content)


class LyricsSource(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def fetch(
        self,
        title: str,
        artist: str,
        album: str = "",
        duration: float = 0.0,
    ) -> Optional[LyricsResult]:
        """Return (format, lyrics_text) or None if not found."""
        ...
