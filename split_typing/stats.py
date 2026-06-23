from __future__ import annotations

import json
from pathlib import Path

DEFAULT_PATH = Path.home() / ".split-typing" / "stats.json"


class KeyStats:
    _ALPHA = 0.3
    _W_ERR = 0.6
    _W_LAT = 0.4

    def __init__(self, path: Path, data: dict[str, dict]) -> None:
        self.path = path
        self.data = data

    @classmethod
    def load(cls, path: Path | None = None) -> "KeyStats":
        path = path or DEFAULT_PATH
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}
        return cls(path, data)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def record(self, key: str, ms: float, error: bool) -> None:
        entry = self.data.setdefault(
            key, {"count": 0, "errors": 0, "total_ms": 0.0, "ema_ms": ms}
        )
        entry["count"] += 1
        entry["errors"] += 1 if error else 0
        entry["total_ms"] += ms
        entry["ema_ms"] = self._ALPHA * ms + (1 - self._ALPHA) * entry["ema_ms"]

    def weakness(self, key: str) -> float:
        entry = self.data.get(key)
        if not entry or entry["count"] == 0:
            return 0.0
        error_rate = entry["errors"] / entry["count"]
        norm_lat = min(entry["ema_ms"] / 500.0, 1.0)
        return error_rate * self._W_ERR + norm_lat * self._W_LAT

    def weakest(self, n: int) -> list[str]:
        seen = [k for k, v in self.data.items() if v["count"] > 0]
        seen.sort(key=self.weakness, reverse=True)
        return seen[:n]
