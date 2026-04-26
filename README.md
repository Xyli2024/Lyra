# Apple Lyrics

Real-time lyrics overlay for Apple Music on macOS.

A lightweight menu-bar app that displays synced, line-by-line lyrics in a frosted-glass floating window at the bottom of your screen — no browser tabs, no Spotify required.

---

## Features

- **Synced lyrics** — timestamped LRC format, current line highlighted in real time
- **Multi-language** — English and Chinese both covered (lrclib.net + NetEase fallback)
- **Floating overlay** — semi-transparent rounded window, always on top, stays out of your way
- **Draggable & resizable** — drag anywhere to reposition; scroll wheel to adjust font size
- **Menu-bar icon** — toggle visibility, switch dark/light theme, quit
- **Local cache** — lyrics saved locally, no repeat network calls
- **CLI mode** — terminal fallback if you prefer the command line

---

## Requirements

- macOS 12 Monterey or later
- Apple Music (the built-in app, not the browser)
- Python 3.10+ (for running from source)

---

## Installation

### Option A — Run from source

```bash
git clone https://github.com/yourusername/apple-lyrics.git
cd apple-lyrics
pip3 install -r requirements.txt
python3 -m apple_lyrics
```

### Option B — Build a standalone .app

```bash
pip3 install -r requirements.txt pyinstaller
make app
# Then drag dist/Apple Lyrics.app to /Applications
open "dist/Apple Lyrics.app"
```

---

## Usage

| Action | Effect |
|---|---|
| Launch app | Floating lyrics window appears at screen bottom |
| Drag window | Reposition anywhere; saved automatically |
| Scroll wheel | Increase / decrease font size |
| Right-click tray icon | Toggle visibility, switch theme, quit |

### CLI mode

```bash
python3 -m apple_lyrics --cli
# or after pip install:
apple-lyrics-cli
```

---

## Configuration

Settings are stored at `~/.config/apple-lyrics/config.json` and updated automatically as you interact with the window.

| Key | Default | Description |
|---|---|---|
| `window_x` / `window_y` | auto (screen bottom center) | Window position |
| `window_width` | `520` | Window width in pixels |
| `font_size` | `22` | Base font size (pt) |
| `opacity` | `0.82` | Background opacity (0–1) |
| `theme` | `"dark"` | `"dark"` or `"light"` |

Lyrics are cached in `~/.cache/apple-lyrics/` for 30 days.

---

## Lyrics Sources

Sources are tried in order; the first successful result is used and cached.

| Priority | Source | Format | Notes |
|---|---|---|---|
| 1 | [lrclib.net](https://lrclib.net) | LRC (synced) | Free, no API key, EN + ZH |
| 2 | [NetEase Cloud Music](https://music.163.com) | LRC (synced) | Strong for Chinese songs |
| 3 | [lyrics.ovh](https://api.lyrics.ovh) | Plain text | Fallback |

---

## Adding a New Lyrics Source

1. Create `apple_lyrics/sources/mysource.py` and subclass `LyricsSource`
2. Implement `name` and `fetch(title, artist, album, duration)`
3. Add it to the list in `apple_lyrics/lyrics_fetcher.py`

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

Apple Lyrics runs entirely on your machine. No data is sent anywhere except to the lyrics APIs (track title and artist name). No telemetry, no accounts.

---

## License

MIT
