"""Cell and CellFormat dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal


@dataclass
class CellFormat:
    """Visual formatting applied to a single cell."""

    bold: bool = False
    italic: bool = False
    underline: bool = False
    align: Literal["left", "right", "center"] = "right"
    fg_color: str | None = None  # hex RGB e.g. "#ff0000"
    bg_color: str | None = None
    num_decimals: int | None = None
    num_format: str | None = None  # strftime or number pattern
    thousands_sep: bool = False

    def copy(self) -> CellFormat:
        """Return a shallow copy of this format."""
        return CellFormat(
            bold=self.bold,
            italic=self.italic,
            underline=self.underline,
            align=self.align,
            fg_color=self.fg_color,
            bg_color=self.bg_color,
            num_decimals=self.num_decimals,
            num_format=self.num_format,
            thousands_sep=self.thousands_sep,
        )


@dataclass
class Cell:
    """A single spreadsheet cell with content, formatting, and metadata."""

    row: int
    col: int
    # Content
    formula: str | None = None  # raw formula string e.g. "=SUM(A1:A5)"
    value: Any = None  # computed/stored value
    display: str = ""  # formatted string for display
    # Metadata
    fmt: CellFormat = field(default_factory=CellFormat)
    locked: bool = False
    comment: str | None = None
    history: list[tuple[datetime, Any]] = field(default_factory=list)

    def is_empty(self) -> bool:
        """Return True if the cell has no content."""
        return self.formula is None and self.value is None

    def record_history(self, value: Any) -> None:
        """Record a value change in the cell's history."""
        self.history.append((datetime.now(), value))

    def format_value(self) -> str:
        """Return a display string for the cell's value, applying format rules."""
        if self.value is None:
            return ""

        fmt = self.fmt

        if isinstance(self.value, str):
            return self.value

        if isinstance(self.value, bool):
            return "TRUE" if self.value else "FALSE"

        if isinstance(self.value, int | float):
            num = float(self.value)

            decimals = fmt.num_decimals
            if decimals is not None:
                formatted = f"{num:.{decimals}f}"
            else:
                # Remove trailing zeros for clean display
                if num == int(num) and abs(num) < 1e15:
                    formatted = str(int(num))
                else:
                    formatted = str(num)

            if fmt.thousands_sep:
                # Insert thousands separator
                parts = formatted.split(".")
                parts[0] = f"{int(parts[0]):,}"
                formatted = ".".join(parts)

            return formatted

        return str(self.value)

    def copy(self) -> Cell:
        """Return a copy of this cell (same position, same content)."""
        return Cell(
            row=self.row,
            col=self.col,
            formula=self.formula,
            value=self.value,
            display=self.display,
            fmt=self.fmt.copy(),
            locked=self.locked,
            comment=self.comment,
            history=list(self.history),
        )
