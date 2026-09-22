"""E2E tests for '.' (dot-repeat) after editor commits."""

from __future__ import annotations

import pytest

from tests.conftest import make_workbook
from vimsheet.app import VimSheetApp


@pytest.fixture
def app() -> VimSheetApp:
    return VimSheetApp(workbook=make_workbook(data=[[5, 7], [1, 2], [3, 4]]))


@pytest.mark.asyncio
async def test_dot_repeat_after_replace(app: VimSheetApp) -> None:
    """Tutorial 4 step 6/7: r + 999, Enter, then . on the cell below."""
    async with app.run_test() as pilot:
        await pilot.press("r")
        for ch in "999":
            await pilot.press(ch)
        await pilot.press("enter")
        await pilot.pause()

        sheet = app.workbook.active_sheet
        assert sheet.get_cell(0, 0).value == 999
        assert app.cursor_row == 1  # auto-move down

        await pilot.press(".")
        await pilot.pause()
        assert sheet.get_cell(1, 0).value == 999


@pytest.mark.asyncio
async def test_dot_repeat_after_formula(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("=")
        for ch in "B1":
            await pilot.press(ch)
        await pilot.press("enter")
        await pilot.pause()

        sheet = app.workbook.active_sheet
        assert sheet.get_cell(0, 0).formula == "=B1"
        assert sheet.get_cell(0, 0).value == 7
        assert app.cursor_row == 1

        await pilot.press(".")
        await pilot.pause()
        cell = sheet.get_cell(1, 0)
        assert cell is not None
        assert cell.formula == "=B1"  # verbatim, no reference adjustment
        assert cell.value == 7


@pytest.mark.asyncio
async def test_dot_repeat_after_string_insert(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("\\")
        for ch in "hi":
            await pilot.press(ch)
        await pilot.press("enter")
        await pilot.pause()

        sheet = app.workbook.active_sheet
        assert sheet.get_cell(0, 0).value == "hi"
        assert app.cursor_row == 1

        await pilot.press(".")
        await pilot.pause()
        assert sheet.get_cell(1, 0).value == "hi"


@pytest.mark.asyncio
async def test_dot_repeat_after_change_cell(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("C")
        await pilot.press("x")
        await pilot.press("enter")
        await pilot.pause()

        sheet = app.workbook.active_sheet
        assert sheet.get_cell(0, 0).value == "x"
        assert app.cursor_row == 1

        await pilot.press(".")
        await pilot.pause()
        assert sheet.get_cell(1, 0).value == "x"
