"""Adapter registry — maps file extensions and format names to FormatAdapter instances."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pysheet.io.base import FormatAdapter

_adapters: list["FormatAdapter"] = []

# Map short format names (used in :e <fmt> <file>) to adapter index
_FORMAT_NAMES: dict[str, str] = {
    "csv":  ".csv",
    "tsv":  ".tsv",
    "json": ".json",
    "xlsx": ".xlsx",
    "xls":  ".xls",
    "mkd":  ".md",
    "md":   ".md",
    "tex":  ".tex",
    "html": ".html",
    "htm":  ".htm",
}


def _init() -> None:
    from pysheet.io.csv_adapter import CSVAdapter
    from pysheet.io.html_adapter import HTMLAdapter
    from pysheet.io.json_adapter import JSONAdapter
    from pysheet.io.latex_adapter import LaTeXAdapter
    from pysheet.io.markdown_adapter import MarkdownAdapter
    from pysheet.io.xls_adapter import XLSAdapter
    from pysheet.io.xlsx_adapter import XLSXAdapter

    _adapters.extend([
        JSONAdapter(),
        XLSXAdapter(),
        XLSAdapter(),
        CSVAdapter(),
        MarkdownAdapter(),
        LaTeXAdapter(),
        HTMLAdapter(),
    ])


def get_adapter(path: Path) -> "FormatAdapter":
    """Return the adapter for *path*'s extension. Raises ValueError if none match."""
    if not _adapters:
        _init()
    ext = path.suffix.lower()
    for adapter in _adapters:
        if ext in adapter.supported_extensions:
            return adapter
    raise ValueError(f"Unsupported file format: {ext!r}")


def get_adapter_by_name(fmt: str) -> "FormatAdapter":
    """Return the adapter for a short format name like 'csv', 'mkd', 'tex'."""
    if not _adapters:
        _init()
    ext = _FORMAT_NAMES.get(fmt.lower())
    if ext is None:
        raise ValueError(f"Unknown format name: {fmt!r}")
    for adapter in _adapters:
        if ext in adapter.supported_extensions:
            return adapter
    raise ValueError(f"No adapter for format: {fmt!r}")
