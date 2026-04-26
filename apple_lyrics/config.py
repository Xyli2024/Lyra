import json
from dataclasses import asdict, dataclass
from pathlib import Path

_CONFIG_PATH = Path.home() / ".config" / "apple-lyrics" / "config.json"


@dataclass
class Config:
    window_x: int = -1          # -1 = auto-center
    window_y: int = -1
    window_width: int = 520
    font_size: int = 22
    opacity: float = 0.82
    theme: str = "dark"         # "dark" | "light"

    def save(self) -> None:
        _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        _CONFIG_PATH.write_text(
            json.dumps(asdict(self), indent=2), encoding="utf-8"
        )

    @classmethod
    def load(cls) -> "Config":
        if not _CONFIG_PATH.exists():
            return cls()
        try:
            data = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
            valid = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
            return cls(**valid)
        except Exception:
            return cls()
