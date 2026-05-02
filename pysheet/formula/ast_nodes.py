"""AST node dataclasses for the formula parser."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class NumberNode:
    value: float


@dataclass
class StringNode:
    value: str


@dataclass
class BoolNode:
    value: bool


@dataclass
class CellRefNode:
    """A single cell reference, e.g. A1 or $B$3."""

    ref: str  # raw text like "A1", "$B$3"


@dataclass
class RangeRefNode:
    """A range reference, e.g. A1:C10."""

    ref: str  # raw text like "A1:C10"


@dataclass
class SheetCellRefNode:
    """A cross-sheet cell reference, e.g. Sheet1!A1."""

    sheet: str  # sheet name
    ref: str  # cell address like "A1"


@dataclass
class SheetRangeRefNode:
    """A cross-sheet range reference, e.g. Sheet1!A1:B2."""

    sheet: str  # sheet name
    ref: str  # range like "A1:B2"


@dataclass
class ColRangeRefNode:
    """A whole-column reference, e.g. A$:B$ or A:B or A$."""

    ref: str  # raw text like "A$:B$", "A:B", "A$"


@dataclass
class NameNode:
    """A named range or undefined identifier."""

    name: str


@dataclass
class UnaryNode:
    op: str  # "-" or "+"
    operand: Expr


@dataclass
class BinaryNode:
    op: str  # "+", "-", "*", "/", "^", "%", "&", "<", ">", "=", "<>", "<=", ">="
    left: Expr
    right: Expr


@dataclass
class PercentNode:
    """postfix % — divide by 100"""

    operand: Expr


@dataclass
class FuncCallNode:
    name: str  # upper-case function name
    args: list[Expr] = field(default_factory=list)


# Union type alias
Expr = (
    NumberNode
    | StringNode
    | BoolNode
    | CellRefNode
    | RangeRefNode
    | ColRangeRefNode
    | SheetCellRefNode
    | SheetRangeRefNode
    | NameNode
    | UnaryNode
    | BinaryNode
    | PercentNode
    | FuncCallNode
)
