from __future__ import annotations

import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any


class JsonStateStore:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self, default: Any) -> Any:
        if not self.path.exists():
            return default
        with self.path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def save(self, payload: Any) -> None:
        serialized = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=self.path.parent) as handle:
            handle.write(serialized)
            temp_path = Path(handle.name)
        temp_path.replace(self.path)
