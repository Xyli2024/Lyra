from PyQt6.QtCore import QThread, pyqtSignal


class LyricsWorker(QThread):
    """Fetches lyrics in a background thread to keep the UI responsive."""

    lyrics_ready = pyqtSignal(str, str, str)  # (format, text, track_id)

    def __init__(self, title: str, artist: str, album: str, duration: float, track_id: str):
        super().__init__()
        self.title = title
        self.artist = artist
        self.album = album
        self.duration = duration
        self.track_id = track_id

    def run(self) -> None:
        from ..lyrics_fetcher import LyricsFetcher
        result = LyricsFetcher().fetch(self.title, self.artist, self.album, self.duration)
        if result:
            fmt, text = result
            self.lyrics_ready.emit(fmt, text, self.track_id)
