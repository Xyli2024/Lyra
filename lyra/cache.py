import hashlib
import json
import time
from pathlib import Path
from typing import Optional

_CACHE_DIR = Path.home() / ".cache" / "lyra"
_TTL_SECONDS = 30 * 24 * 3600  # 30 days


def _cache_path(key: str) -> Path:
    digest = hashlib.md5(key.encode()).hexdigest()
    return _CACHE_DIR / f"{digest}.json"


def get(key: str) -> Optional[dict]:
    path = _cache_path(key)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if time.time() - data.get("_ts", 0) > _TTL_SECONDS:
            path.unlink(missing_ok=True)
            return None
        return data
    except Exception:
        return None


def set(key: str, data: dict) -> None:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    data["_ts"] = time.time()
    path = _cache_path(key)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
