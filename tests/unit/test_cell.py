"""Unit tests for pysheet.model.cell (Cell and CellFormat)."""

from __future__ import annotations

from datetime import datetime

import pytest

from pysheet.model.cell import Cell, CellFormat


# ---------------------------------------------------------------------------
# CellFormat tests
# ---------------------------------------------------------------------------

class TestCellFormat:
    def test_defaults(self) -> None:
        fmt = CellFormat()
        assert fmt.bold is False
        assert fmt.italic is False
        assert fmt.underline is False
        assert fmt.align == "right"
        assert fmt.fg_color is None
        assert fmt.bg_color is None
        assert fmt.num_decimals is None
        assert fmt.num_format is None
        assert fmt.thousands_sep is False

    def test_copy_is_independent(self) -> None:
        fmt = CellFormat(bold=True, fg_color="#ff0000")
        copy = fmt.copy()
        copy.bold = False
        copy.fg_color = "#00ff00"
        assert fmt.bold is True
        assert fmt.fg_color == "#ff0000"

    def test_copy_values_match(self) -> None:
        fmt = CellFormat(
            bold=True, italic=True, underline=True,
            align="center", fg_color="#aabbcc", bg_color="#112233",
            num_decimals=2, num_format="%Y-%m-%d", thousands_sep=True,
        )
        copy = fmt.copy()
        assert copy.bold == fmt.bold
        assert copy.italic == fmt.italic
        assert copy.underline == fmt.underline
        assert copy.align == fmt.align
        assert copy.fg_color == fmt.fg_color
        assert copy.bg_color == fmt.bg_color
        assert copy.num_decimals == fmt.num_decimals
        assert copy.num_format == fmt.num_format
        assert copy.thousands_sep == fmt.thousands_sep


# ---------------------------------------------------------------------------
# Cell tests
# ---------------------------------------------------------------------------

class TestCell:
    def test_defaults(self) -> None:
        cell = Cell(row=0, col=0)
        assert cell.row == 0
        assert cell.col == 0
        assert cell.formula is None
        assert cell.value is None
        assert cell.display == ""
        assert isinstance(cell.fmt, CellFormat)
        assert cell.locked is False
        assert cell.comment is None
        assert cell.history == []

    def test_is_empty_when_no_content(self) -> None:
        assert Cell(row=0, col=0).is_empty()

    def test_is_not_empty_with_value(self) -> None:
        cell = Cell(row=0, col=0, value=42)
        assert not cell.is_empty()

    def test_is_not_empty_with_formula(self) -> None:
        cell = Cell(row=0, col=0, formula="=SUM(A1:A5)")
        assert not cell.is_empty()

    def test_record_history(self) -> None:
        cell = Cell(row=0, col=0, value=10)
        before = datetime.now()
        cell.record_history(10)
        after = datetime.now()
        assert len(cell.history) == 1
        ts, val = cell.history[0]
        assert val == 10
        assert before <= ts <= after

    def test_format_value_none(self) -> None:
        assert Cell(row=0, col=0).format_value() == ""

    def test_format_value_string(self) -> None:
        cell = Cell(row=0, col=0, value="hello")
        assert cell.format_value() == "hello"

    def test_format_value_bool_true(self) -> None:
        cell = Cell(row=0, col=0, value=True)
        assert cell.format_value() == "TRUE"

    def test_format_value_bool_false(self) -> None:
        cell = Cell(row=0, col=0, value=False)
        assert cell.format_value() == "FALSE"

    def test_format_value_integer(self) -> None:
        cell = Cell(row=0, col=0, value=42)
        assert cell.format_value() == "42"

    def test_format_value_float(self) -> None:
        cell = Cell(row=0, col=0, value=3.14)
        assert cell.format_value() == "3.14"

    def test_format_value_decimals(self) -> None:
        cell = Cell(row=0, col=0, value=3.14159)
        cell.fmt.num_decimals = 2
        assert cell.format_value() == "3.14"

    def test_format_value_thousands_sep(self) -> None:
        cell = Cell(row=0, col=0, value=1234567)
        cell.fmt.thousands_sep = True
        assert cell.format_value() == "1,234,567"

    def test_format_value_decimals_and_thousands(self) -> None:
        cell = Cell(row=0, col=0, value=1234567.89)
        cell.fmt.num_decimals = 2
        cell.fmt.thousands_sep = True
        result = cell.format_value()
        assert "1,234,567" in result
        assert ".89" in result

    def test_copy_is_independent(self) -> None:
        cell = Cell(row=1, col=2, value=99, formula="=A1", locked=True)
        copy = cell.copy()
        copy.value = 0
        copy.formula = None
        assert cell.value == 99
        assert cell.formula == "=A1"

    def test_copy_preserves_position(self) -> None:
        cell = Cell(row=3, col=5, value="x")
        copy = cell.copy()
        assert copy.row == 3
        assert copy.col == 5

    def test_copy_preserves_format(self) -> None:
        cell = Cell(row=0, col=0, value=1)
        cell.fmt.bold = True
        cell.fmt.fg_color = "#ff0000"
        copy = cell.copy()
        assert copy.fmt.bold is True
        assert copy.fmt.fg_color == "#ff0000"

    def test_copy_history_is_independent(self) -> None:
        cell = Cell(row=0, col=0, value=1)
        cell.record_history(0)
        copy = cell.copy()
        cell.record_history(2)
        # copy should still have only 1 history entry
        assert len(copy.history) == 1
