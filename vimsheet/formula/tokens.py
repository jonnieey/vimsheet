"""Token types and Token dataclass for the formula lexer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TT(Enum):
    """Token type enum."""

    NUMBER = auto()
    STRING = auto()
    BOOL = auto()
    CELL_REF = auto()
    RANGE_REF = auto()
    SHEET_CELL_REF = auto()  # SheetName!A1
    SHEET_RANGE_REF = auto()  # SheetName!A1:B2
    COL_RANGE_REF = auto()  # A$:B$ or A:B (whole-column range)
    NAME = auto()
    OP = auto()
    LPAREN = auto()
    RPAREN = auto()
    COMMA = auto()
    AT = auto()
    COLON = auto()
    PERCENT = auto()
    EOF = auto()


@dataclass(frozen=True)
class Token:
    type: TT
    value: str
    pos: int = 0  # character offset in the source string

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r})"
