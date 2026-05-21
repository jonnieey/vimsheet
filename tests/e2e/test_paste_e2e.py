"""E2E tests for relative vs absolute formula paste."""

from __future__ import annotations

import pytest

from tests.conftest import make_workbook
from vimsheet.app import VimSheetApp
from vimsheet.controller.mode import Mode


@pytest.fixture
def app() -> VimSheetApp:
    """App backed by a blank workbook."""
    return VimSheetApp(workbook=make_workbook())


@pytest.mark.asyncio
async def test_p_adjusts_row(app: VimSheetApp) -> None:
    """Enter =IF(B2>10,\"t\",\"f\") at B2, yy, move to B3, p → B3 has row adjusted."""
    sheet = app.workbook.active_sheet
    sheet.set_cell_value(1, 1, "t", formula='=IF(B2>10,"t","f")')
    async with app.run_test() as pilot:
        await pilot.press("g")
        await pilot.press("o")
        await pilot.press("b")
        await pilot.press("2")
        await pilot.press("enter")
        await pilot.pause()

        await pilot.press("y")
        await pilot.press("y")
        await pilot.pause()

        await pilot.press("j")
        await pilot.pause()

        await pilot.press("p")
        await pilot.pause()

        cell = sheet.get_cell(2, 1)
        assert cell is not None
        assert cell.formula == '=IF(B3>10,"t","f")'


@pytest.mark.asyncio
async def test_p_adjusts_column(app: VimSheetApp) -> None:
    """Enter =IF(B2>10,\"t\",\"f\") at B2, yy, move to C2, p → C2 has column adjusted."""
    sheet = app.workbook.active_sheet
    sheet.set_cell_value(1, 1, "t", formula='=IF(B2>10,"t","f")')
    async with app.run_test() as pilot:
        await pilot.press("g")
        await pilot.press("o")
        await pilot.press("b")
        await pilot.press("2")
        await pilot.press("enter")
        await pilot.pause()

        await pilot.press("y")
        await pilot.press("y")
        await pilot.pause()

        await pilot.press("l")
        await pilot.pause()

        await pilot.press("p")
        await pilot.pause()

        cell = sheet.get_cell(1, 2)
        assert cell is not None
        assert cell.formula == '=IF(C2>10,"t","f")'


@pytest.mark.asyncio
async def test_P_pastes_value_only(app: VimSheetApp) -> None:
    """yy yanks a formula cell, P pastes value-only (no formula)."""
    sheet = app.workbook.active_sheet
    sheet.set_cell_value(0, 1, 10)  # B1 = 10
    sheet.set_cell_value(1, 1, 20, formula="=B1*2")  # B2 = 20
    async with app.run_test() as pilot:
        await pilot.press("g")
        await pilot.press("o")
        await pilot.press("b")
        await pilot.press("2")
        await pilot.press("enter")
        await pilot.pause()

        await pilot.press("y")
        await pilot.press("y")
        await pilot.pause()

        await pilot.press("l")
        await pilot.pause()

        await pilot.press("P")
        await pilot.pause()

        cell = sheet.get_cell(1, 2)  # C2
        assert cell is not None
        assert cell.value == 20
        assert cell.formula is None


@pytest.mark.asyncio
async def test_range_yank_paste_adjusts_column(app: VimSheetApp) -> None:
    """Fill B2:B4 with =A2,=A3,=A4 → visual yank → paste at C2 → column adjusted."""
    sheet = app.workbook.active_sheet
    sheet.set_cell_value(1, 1, 2, formula="=A2")
    sheet.set_cell_value(2, 1, 3, formula="=A3")
    sheet.set_cell_value(3, 1, 4, formula="=A4")
    async with app.run_test() as pilot:
        await pilot.press("g")
        await pilot.press("o")
        await pilot.press("b")
        await pilot.press("2")
        await pilot.press("enter")
        await pilot.pause()

        await pilot.press("v")
        await pilot.press("j")
        await pilot.press("j")
        await pilot.pause()

        await pilot.press("y")
        await pilot.pause()
        assert app.mode == Mode.NORMAL

        await pilot.press("g")
        await pilot.press("o")
        await pilot.press("c")
        await pilot.press("2")
        await pilot.press("enter")
        await pilot.pause()

        await pilot.press("p")
        await pilot.pause()

        cell_c2 = sheet.get_cell(1, 2)
        assert cell_c2 is not None
        assert cell_c2.formula == "=B2"

        cell_c3 = sheet.get_cell(2, 2)
        assert cell_c3 is not None
        assert cell_c3.formula == "=B3"

        cell_c4 = sheet.get_cell(3, 2)
        assert cell_c4 is not None
        assert cell_c4.formula == "=B4"


@pytest.mark.asyncio
async def test_absolute_ref_survives_paste(app: VimSheetApp) -> None:
    """Enter =$A$1 at B2, yy, move to D10, p → D10 has =$A$1 unchanged."""
    sheet = app.workbook.active_sheet
    sheet.set_cell_value(1, 1, 42, formula="=$A$1")
    async with app.run_test() as pilot:
        await pilot.press("g")
        await pilot.press("o")
        await pilot.press("b")
        await pilot.press("2")
        await pilot.press("enter")
        await pilot.pause()

        await pilot.press("y")
        await pilot.press("y")
        await pilot.pause()

        await pilot.press("g")
        await pilot.press("o")
        await pilot.press("d")
        await pilot.press("1")
        await pilot.press("0")
        await pilot.press("enter")
        await pilot.pause()

        await pilot.press("p")
        await pilot.pause()

        cell = sheet.get_cell(9, 3)
        assert cell is not None
        assert cell.formula == "=$A$1"
