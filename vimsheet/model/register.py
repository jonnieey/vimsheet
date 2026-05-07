"""Register entry for yank/paste operations with source position tracking."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RegisterEntry:
    """Holds yanked cell data along with source position for formula adjustment."""

    value: Any
    formula: str | None  # raw formula string e.g. "=IF(B2>10,...)"
    src_row: int  # 0-based source row
    src_col: int  # 0-based source col
    is_range: bool = False
    range_data: list[list[tuple[Any, str | None]]] | None = None
    range_src_top: int = 0
    range_src_left: int = 0
