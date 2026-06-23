from __future__ import annotations

import json
from pathlib import Path

DEFAULT_PATH = Path.home() / ".split-typing" / "stats.json"


class KeyStats:
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
