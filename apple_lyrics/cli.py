"""
CLI lyrics display for Apple Music.
Usage: python -m apple_lyrics
"""
import time
from typing import List, Optional, Tuple

from rich.align import Align
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn
from rich.text import Text

from .lrc_parser import LrcLines, current_index, parse_lrc, plain_to_timed
from .lyrics_fetcher import LyricsFetcher
from .monitor import MusicMonitor, TrackInfo

POLL_INTERVAL = 0.3   # seconds between UI refreshes
CONTEXT_LINES = 2     # lines to show above/below current line

_console = Console()
_monitor = MusicMonitor()
_fetcher = LyricsFetcher()


def _format_time(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def _build_display(
    track: TrackInfo,
    lines: LrcLines,
    idx: int,
) -> Panel:
    # ── track header ──────────────────────────────────────────
    header = Text()
    header.append(track.title, style="bold white")
    header.append("  —  ", style="dim")
    header.append(track.artist, style="cyan")
    if not track.is_playing:
        header.append("  ⏸", style="yellow")

    # ── progress bar ──────────────────────────────────────────
    pct = track.position / track.duration if track.duration else 0
    bar_width = 36
    filled = int(bar_width * pct)
    bar = (
        Text("─" * filled, style="cyan")
        + Text("●", style="bold cyan")
        + Text("─" * (bar_width - filled), style="dim")
    )
    time_str = Text(
        f" {_format_time(track.position)} / {_format_time(track.duration)} ",
        style="dim",
    )

    # ── lyrics block ──────────────────────────────────────────
    lyric_block = Text(justify="center")

    if not lines:
        lyric_block.append("\n[lyrics not found]\n", style="dim italic")
    else:
        start = max(0, idx - CONTEXT_LINES)
        end = min(len(lines), idx + CONTEXT_LINES + 1)

        lyric_block.append("\n")
        for i in range(start, end):
            _, text = lines[i]
            if not text:          # blank separator line — keep as spacer
                lyric_block.append("\n")
                continue
            if i == idx:
                lyric_block.append(f"  {text}  ", style="bold bright_white")
            elif abs(i - idx) == 1:
                lyric_block.append(text, style="white")
            else:
                lyric_block.append(text, style="dim")
            lyric_block.append("\n")

    # ── assemble panel ────────────────────────────────────────
    content = Text(justify="center")
    content.append_text(header)
    content.append("\n")
    content.append_text(bar)
    content.append_text(time_str)
    content.append("\n")
    content.append_text(lyric_block)

    return Panel(
        Align.center(content, vertical="middle"),
        border_style="bright_black",
        padding=(0, 2),
    )


def run() -> None:
    last_track_id: Optional[str] = None
    lines: LrcLines = []
    fetching_msg: Optional[str] = None

    _console.print(
        "\n[bold cyan]apple-lyrics[/] — [dim]Ctrl+C to quit[/]\n"
    )

    with Live(console=_console, refresh_per_second=int(1 / POLL_INTERVAL)) as live:
        while True:
            track = _monitor.get_current_track()

            if track is None:
                live.update(
                    Panel(
                        Align.center(
                            Text("Music is not playing", style="dim italic"),
                            vertical="middle",
                        ),
                        border_style="bright_black",
                        padding=(1, 4),
                    )
                )
                time.sleep(POLL_INTERVAL)
                continue

            # ── new track detected ────────────────────────────
            if track.track_id != last_track_id:
                last_track_id = track.track_id
                lines = []
                fetching_msg = f"Fetching lyrics for "{track.title}"…"
                live.update(
                    Panel(
                        Align.center(
                            Text(fetching_msg, style="dim italic"),
                            vertical="middle",
                        ),
                        border_style="bright_black",
                        padding=(1, 4),
                    )
                )
                result = _fetcher.fetch(
                    track.title, track.artist, track.album, track.duration
                )
                if result:
                    fmt, text = result
                    if fmt == "lrc":
                        lines = parse_lrc(text)
                    else:
                        lines = plain_to_timed(text, track.duration)
                fetching_msg = None

            # ── render current frame ──────────────────────────
            idx = current_index(lines, track.position)
            live.update(_build_display(track, lines, idx))
            time.sleep(POLL_INTERVAL)
