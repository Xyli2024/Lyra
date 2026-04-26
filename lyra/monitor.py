import subprocess
from dataclasses import dataclass
from typing import Optional

_APPLESCRIPT = """\
tell application "Music"
    if player state is playing or player state is paused then
        set nl to (ASCII character 10)
        set t to name of current track
        set ar to artist of current track
        set al to album of current track
        set pos to player position
        set dur to duration of current track
        try
            set gen to genre of current track
        on error
            set gen to ""
        end try
        if player state is playing then
            set stateStr to "playing"
        else
            set stateStr to "paused"
        end if
        return t & nl & ar & nl & al & nl & (pos as string) & nl & (dur as string) & nl & stateStr & nl & gen
    else
        return "stopped"
    end if
end tell
"""


@dataclass
class TrackInfo:
    title: str
    artist: str
    album: str
    position: float   # seconds
    duration: float   # seconds
    is_playing: bool
    genre: str = ""

    @property
    def track_id(self) -> str:
        """Unique key for this track (used for cache lookup)."""
        return f"{self.artist.lower()}::{self.title.lower()}"


class MusicMonitor:
    def get_current_track(self) -> Optional[TrackInfo]:
        try:
            result = subprocess.run(
                ["osascript"],
                input=_APPLESCRIPT,
                capture_output=True, text=True, timeout=3,
            )
            output = result.stdout.strip()
            if not output or output == "stopped":
                return None
            parts = output.split("\n")
            if len(parts) < 6:
                return None
            return TrackInfo(
                title=parts[0],
                artist=parts[1],
                album=parts[2],
                position=max(0.0, float(parts[3])),
                duration=max(1.0, float(parts[4])),
                is_playing=(parts[5].strip() == "playing"),
                genre=parts[6].strip() if len(parts) > 6 else "",
            )
        except Exception:
            return None
