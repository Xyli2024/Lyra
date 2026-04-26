# Lyra 天琴座

Real-time lyrics overlay for Apple Music on macOS.

A lightweight menu-bar app that displays synced, line-by-line lyrics in a frosted-glass floating window — KTV-style, always on top, always out of your way.

![macOS](https://img.shields.io/badge/macOS-12%2B-blue) ![Python](https://img.shields.io/badge/Python-3.10%2B-blue) ![License](https://img.shields.io/badge/License-MIT-green)

---

## Features

- **KTV-style display** — current line large and bright, next line small and dim, smooth scroll animation between them
- **Synced lyrics** — LRC format with millisecond precision; 60 fps position interpolation between AppleScript polls
- **Multi-language** — English and Chinese both covered (lrclib.net + NetEase fallback)
- **Frosted-glass overlay** — semi-transparent rounded window, always on top across all Spaces and full-screen apps
- **Draggable & resizable** — drag to reposition, scroll wheel to adjust font size; position is saved
- **Menu-bar icon** — toggle visibility, switch dark/light theme, quit
- **Local cache** — lyrics saved locally for 30 days, no repeat network calls
- **CLI mode** — terminal fallback with a rich progress bar

---

## Requirements

- macOS 12 Monterey or later
- Apple Music (the built-in app, not the browser)
- Python 3.10+

---

## Installation

### Run from source

```bash
git clone https://github.com/Xyli2024/lyra.git
cd lyra
pip3 install -r requirements.txt
python3 -m lyra
```

### Global `lyra` command (optional)

```bash
# Creates /opt/homebrew/bin/lyra pointing to your clone
make install
```

Or manually:

```bash
cat > /opt/homebrew/bin/lyra << 'EOF'
#!/bin/zsh
PYTHONPATH=/path/to/lyra \
exec /opt/homebrew/opt/python@3.12/bin/python3.12 -m lyra "$@"
EOF
chmod +x /opt/homebrew/bin/lyra
```

---

## Usage

| Action | Effect |
|---|---|
| Launch (`lyra`) | Floating lyrics window at screen bottom |
| Drag window | Reposition anywhere; saved automatically |
| Scroll wheel | Increase / decrease font size |
| Right-click tray icon | Toggle visibility, switch theme, quit |

### CLI mode

```bash
lyra --cli
```

---

## Configuration

Settings are auto-saved to `~/.config/lyra/config.json`.

| Key | Default | Description |
|---|---|---|
| `window_x` / `window_y` | screen bottom center | Window position |
| `window_width` | `680` | Window width in pixels |
| `font_size` | `26` | Base font size (pt) |
| `opacity` | `0.52` | Background opacity (0–1) |
| `theme` | `"light"` | `"dark"` or `"light"` |

Lyrics cache: `~/.cache/lyra/` (30-day TTL).

---

## Lyrics Sources

Tried in order; first successful result is cached.

| Priority | Source | Format | Notes |
|---|---|---|---|
| 1 | [lrclib.net](https://lrclib.net) | LRC (synced) | Free, no API key, EN + ZH |
| 2 | [NetEase Cloud Music](https://music.163.com) | LRC (synced) | Best for Chinese songs |
| 3 | [lyrics.ovh](https://api.lyrics.ovh) | Plain text | Fallback |

---

## Adding a Lyrics Source

1. Create `lyra/sources/mysource.py`, subclass `LyricsSource`
2. Implement `name` and `fetch(title, artist, album, duration)`
3. Add it to `lyra/lyrics_fetcher.py`

```python
from .sources.base import LyricsSource, LyricsResult

class MySource(LyricsSource):
    @property
    def name(self) -> str:
        return "mysource"

    def fetch(self, title, artist, album="", duration=0.0):
        # return ("lrc", lrc_text) or ("plain", plain_text) or None
        ...
```

---

## Privacy

Lyra runs entirely on your machine. The only data sent externally is track title and artist name to the lyrics APIs. No telemetry, no accounts.

---

## License

MIT
