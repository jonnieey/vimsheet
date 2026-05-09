"""Command and search history stacks."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class HistoryStack:
    """A bounded circular history buffer with prev/next browsing."""

    items: list[str] = field(default_factory=list)
    max_size: int = 50
    _index: int = -1  # -1 = not browsing

    def push(self, item: str) -> None:
        if not item:
            return
        if self.items and self.items[-1] == item:
            return
        self.items.append(item)
        if len(self.items) > self.max_size:
            self.items.pop(0)

    def prev(self) -> str | None:
        if not self.items:
            return None
        if self._index == -1:
            self._index = len(self.items) - 1
        else:
            self._index = max(0, self._index - 1)
        return self.items[self._index]

    def next(self) -> str | None:
        if not self.items or self._index == -1:
            return None
        self._index += 1
        if self._index >= len(self.items):
            self._index = -1
            return None
        return self.items[self._index]

    def reset_browse(self) -> None:
        self._index = -1

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.items), encoding="utf-8")

    @classmethod
    def load(cls, path: Path, max_size: int = 50) -> HistoryStack:
        try:
            items = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(items, list):
                return cls(items=items[-max_size:], max_size=max_size)
        except Exception:
            pass
        return cls(max_size=max_size)
