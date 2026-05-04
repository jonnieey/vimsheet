"""Abstract base class for all format adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from vimsheet.model.workbook import Workbook


class FormatAdapter(ABC):
    """Base class every I/O adapter must implement."""

    supported_extensions: list[str] = []
    can_read_formulas: bool = False
    can_write_formulas: bool = False
    multi_sheet: bool = False

    @abstractmethod
    def read(self, path: Path, **opts: object) -> Workbook:
        """Read *path* and return a populated Workbook."""

    @abstractmethod
    def write(self, workbook: Workbook, path: Path, **opts: object) -> None:
        """Serialise *workbook* to *path*."""
