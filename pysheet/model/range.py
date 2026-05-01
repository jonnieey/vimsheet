"""A1 notation helpers and named-range registry."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterator


# ---------------------------------------------------------------------------
# A1 ↔ (row, col) conversion  (0-based row and col)
# ---------------------------------------------------------------------------

_COL_RE = re.compile(r"^\$?([A-Za-z]{1,3})\$?(\d+)$")
_RANGE_RE = re.compile(
    r"^\$?([A-Za-z]{1,3})\$?(\d+):\$?([A-Za-z]{1,3})\$?(\d+)$"
)


def col_letters_to_index(letters: str) -> int:
    """Convert column letters (A, B, …, ZZ) to a 0-based column index.

    >>> col_letters_to_index("A")
    0
    >>> col_letters_to_index("Z")
    25
    >>> col_letters_to_index("AA")
    26
    """
    letters = letters.upper()
    result = 0
    for ch in letters:
        result = result * 26 + (ord(ch) - ord("A") + 1)
    return result - 1


def col_index_to_letters(index: int) -> str:
    """Convert a 0-based column index to column letters.

    >>> col_index_to_letters(0)
    'A'
    >>> col_index_to_letters(25)
    'Z'
    >>> col_index_to_letters(26)
    'AA'
    """
    result = ""
    n = index + 1
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = chr(ord("A") + remainder) + result
    return result


def a1_to_rowcol(address: str) -> tuple[int, int]:
    """Parse an A1-notation address to a (row, col) pair (0-based).

    Supports absolute references ($A$1).

    >>> a1_to_rowcol("A1")
    (0, 0)
    >>> a1_to_rowcol("B3")
    (2, 1)
    >>> a1_to_rowcol("$C$5")
    (4, 2)
    """
    m = _COL_RE.match(address.strip())
    if not m:
        raise ValueError(f"Invalid cell address: {address!r}")
    col_letters, row_str = m.group(1), m.group(2)
    return int(row_str) - 1, col_letters_to_index(col_letters)


def rowcol_to_a1(row: int, col: int) -> str:
    """Convert a 0-based (row, col) pair to an A1-notation address.

    >>> rowcol_to_a1(0, 0)
    'A1'
    >>> rowcol_to_a1(2, 1)
    'B3'
    """
    return f"{col_index_to_letters(col)}{row + 1}"


# ---------------------------------------------------------------------------
# Range parsing
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CellRange:
    """A rectangular range identified by its top-left and bottom-right corners (0-based)."""

    start_row: int
    start_col: int
    end_row: int
    end_col: int

    def __post_init__(self) -> None:
        if self.start_row > self.end_row or self.start_col > self.end_col:
            raise ValueError(
                f"Invalid range: start ({self.start_row},{self.start_col}) "
                f"> end ({self.end_row},{self.end_col})"
            )

    @classmethod
    def from_a1(cls, range_str: str) -> "CellRange":
        """Parse an A1:B5 range string.

        Also accepts single-cell addresses like "A1".
        """
        range_str = range_str.strip()
        if ":" in range_str:
            m = _RANGE_RE.match(range_str)
            if not m:
                raise ValueError(f"Invalid range: {range_str!r}")
            sc = col_letters_to_index(m.group(1))
            sr = int(m.group(2)) - 1
            ec = col_letters_to_index(m.group(3))
            er = int(m.group(4)) - 1
            # Normalise so start ≤ end
            return cls(min(sr, er), min(sc, ec), max(sr, er), max(sc, ec))
        else:
            r, c = a1_to_rowcol(range_str)
            return cls(r, c, r, c)

    def to_a1(self) -> str:
        """Return the canonical A1:B5 string."""
        if self.start_row == self.end_row and self.start_col == self.end_col:
            return rowcol_to_a1(self.start_row, self.start_col)
        return (
            f"{rowcol_to_a1(self.start_row, self.start_col)}"
            f":{rowcol_to_a1(self.end_row, self.end_col)}"
        )

    @property
    def num_rows(self) -> int:
        """Number of rows in the range."""
        return self.end_row - self.start_row + 1

    @property
    def num_cols(self) -> int:
        """Number of columns in the range."""
        return self.end_col - self.start_col + 1

    def iter_cells(self) -> Iterator[tuple[int, int]]:
        """Yield every (row, col) pair in the range, row-major order."""
        for r in range(self.start_row, self.end_row + 1):
            for c in range(self.start_col, self.end_col + 1):
                yield r, c

    def contains(self, row: int, col: int) -> bool:
        """Return True if (row, col) is inside this range."""
        return (
            self.start_row <= row <= self.end_row
            and self.start_col <= col <= self.end_col
        )

    def __repr__(self) -> str:
        return f"CellRange({self.to_a1()!r})"


# ---------------------------------------------------------------------------
# Named range registry
# ---------------------------------------------------------------------------

@dataclass
class NamedRangeRegistry:
    """Stores name → range-string mappings for a single sheet or workbook."""

    _names: dict[str, str] = field(default_factory=dict)

    def define(self, name: str, range_str: str) -> None:
        """Define or update a named range."""
        name = name.upper()
        # Validate the range string
        CellRange.from_a1(range_str)
        self._names[name] = range_str

    def delete(self, name: str) -> None:
        """Remove a named range. Raises KeyError if not found."""
        self._names.pop(name.upper())

    def resolve(self, name: str) -> str | None:
        """Return the range string for *name*, or None if undefined."""
        return self._names.get(name.upper())

    def all_names(self) -> list[str]:
        """Return sorted list of all defined names."""
        return sorted(self._names.keys())

    def __contains__(self, name: object) -> bool:
        if not isinstance(name, str):
            return False
        return name.upper() in self._names
