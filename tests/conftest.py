"""Shared pytest fixtures for all test suites."""

from __future__ import annotations

from typing import Any

import pytest

from vimsheet.app import VimSheetApp
from vimsheet.model.sheet import Sheet
from vimsheet.model.workbook import Workbook

# ---------------------------------------------------------------------------
# Low-level fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def empty_sheet() -> Sheet:
    """An empty Sheet named 'Sheet1'."""
    return Sheet(name="Sheet1")


@pytest.fixture
def blank_workbook() -> Workbook:
    """A blank Workbook with one empty sheet."""
    return Workbook.blank()


# ---------------------------------------------------------------------------
# Helper functions (also usable from tests directly)
# ---------------------------------------------------------------------------


def make_sheet(data: dict[str, Any], name: str = "Sheet1") -> Sheet:
    """Create a Sheet populated with {address: value} data.

    Values that are strings starting with '=' are stored as formulas.
    """
    sheet = Sheet(name=name)
    for addr, value in data.items():
        from vimsheet.model.range import a1_to_rowcol

        r, c = a1_to_rowcol(addr)
        if isinstance(value, str) and value.startswith("="):
            sheet.set_cell_value(r, c, value, formula=value)
        else:
            sheet.set_cell_value(r, c, value)
    return sheet


def make_workbook(
    data: list[list[Any]] | None = None,
    sheets: dict[str, dict[str, Any]] | None = None,
) -> Workbook:
    """Create a Workbook from tabular *data* or a *sheets* mapping.

    Args:
        data: 2-D list; rows[0] is the first row, cols[0] is column A.
        sheets: mapping of sheet_name → {address: value} dict.
    """
    wb = Workbook()

    if data is not None:
        sheet = Sheet(name="Sheet1")
        for r, row in enumerate(data):
            for c, val in enumerate(row):
                if isinstance(val, str) and val.startswith("="):
                    sheet.set_cell_value(r, c, val, formula=val)
                else:
                    sheet.set_cell_value(r, c, val)
        wb.sheets.append(sheet)

    elif sheets is not None:
        for sheet_name, cell_data in sheets.items():
            sheet = make_sheet(cell_data, name=sheet_name)
            wb.sheets.append(sheet)

    if not wb.sheets:
        wb.sheets.append(Sheet(name="Sheet1"))

    return wb


# ---------------------------------------------------------------------------
# App fixture (for E2E tests — requires Textual)
# ---------------------------------------------------------------------------


@pytest.fixture
def app(blank_workbook: Workbook) -> VimSheetApp:
    """Return a VimSheetApp instance backed by a blank workbook."""
    return VimSheetApp(workbook=blank_workbook)


@pytest.fixture
def app_with_data() -> VimSheetApp:
    """Return a VimSheetApp pre-populated with sample data."""
    wb = make_workbook(
        data=[
            ["Name", "Q1", "Q2", "Total"],
            ["Alpha", 12400, 15200, "=@SUM(B2:C2)"],
            ["Beta", 9800, 11450, "=@SUM(B3:C3)"],
        ]
    )
    return VimSheetApp(workbook=wb)
