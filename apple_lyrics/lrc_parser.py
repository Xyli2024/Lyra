import re
from typing import List, Tuple

# Matches [mm:ss.xx], [mm:ss:xx], or [mm:ss]
_TIME_RE = re.compile(r"\[(\d{1,3}):(\d{2})(?:[.:](\d+))?\]")
# Matches metadata tags like [ti:...], [ar:...] — skip these
_META_RE = re.compile(r"\[[a-z]+:.+\]", re.IGNORECASE)

LrcLines = List[Tuple[float, str]]  # (timestamp_seconds, text)


def parse_lrc(text: str) -> LrcLines:
    """Parse LRC-format lyrics into sorted (timestamp, text) pairs."""
    result: LrcLines = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or _META_RE.fullmatch(line):
            continue

        timestamps: List[Tuple[float, int]] = []
        for m in _TIME_RE.finditer(line):
            minutes = int(m.group(1))
            seconds = int(m.group(2))
            sub = m.group(3) or "0"
            # sub can be centiseconds (2 digits) or milliseconds (3 digits)
            sub_sec = int(sub) / (1000 if len(sub) == 3 else 100)
            ts = minutes * 60 + seconds + sub_sec
            timestamps.append((ts, m.end()))

        if not timestamps:
            continue

        # Lyric text follows the last timestamp tag
        last_end = max(end for _, end in timestamps)
        lyric_text = line[last_end:].strip()

        for ts, _ in timestamps:
            result.append((ts, lyric_text))

    result.sort(key=lambda x: x[0])
    return result


def plain_to_timed(text: str, duration: float) -> LrcLines:
    """Convert plain lyrics to evenly-spaced timed lines (rough estimation)."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        return []
    interval = duration / len(lines)
    return [(i * interval, line) for i, line in enumerate(lines)]


def current_index(lines: LrcLines, position: float) -> int:
    """Return the index of the active lyric line at the given playback position."""
    if not lines:
        return -1
    idx = 0
    for i, (ts, _) in enumerate(lines):
        if ts <= position:
            idx = i
        else:
            break
    return idx
