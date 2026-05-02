"""Runtime configuration for PySheet."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Config:
    """Application-level runtime configuration."""

    autosave: bool = False
    autosave_interval: int = 300  # seconds
    default_col_width: int = 10
    theme: str = "default"  # "default" | "dark" | "light"
    show_grid_lines: bool = True
    show_row_headers: bool = True
    show_col_headers: bool = True
    formula_bar_visible: bool = True
    status_bar_visible: bool = True
    max_undo: int = 1000
    scroll_speed: int = 3
    tab_size: int = 1  # how many cols tab moves
    enter_moves: str = "down"  # "down" | "right" | "none"
    decimal_separator: str = "."
    thousands_separator: str = ","

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    @classmethod
    def load(cls, path: Path) -> Config:
        """Read configuration from a JSON file, using defaults for missing keys."""
        try:
            text = path.read_text(encoding="utf-8")
            data = json.loads(text)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}

        # Only pass fields that are valid Config field names so that unknown
        # keys in the file don't cause a TypeError.
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)

    def save(self, path: Path) -> None:
        """Write current configuration to a JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def default_path(cls) -> Path:
        """Return the default config file path."""
        return Path.home() / ".config" / "pysheet" / "config.json"
