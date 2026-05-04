"""E2E tests for undo/redo integration."""

from __future__ import annotations

import pytest

from tests.conftest import make_workbook
from vimsheet.app import VimSheetApp


@pytest.fixture
def app() -> VimSheetApp:
    return VimSheetApp(workbook=make_workbook())


@pytest.fixture
def app_with_data() -> VimSheetApp:
    wb = make_workbook(data=[["Alpha", 10], ["Beta", 20], ["Gamma", 30]])
    return VimSheetApp(workbook=wb)


@pytest.mark.asyncio
async def test_insert_value_is_undoable(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        # Type a value
        await pilot.press("=")
        for ch in "42":
            await pilot.press(ch)
        await pilot.press("enter")
        await pilot.pause()

        sheet = app.workbook.active_sheet
        assert sheet.get_cell(0, 0) is not None
        assert sheet.get_cell(0, 0).value == 42

        # Undo → cell should be gone
        await pilot.press("u")
        await pilot.pause()
        assert sheet.get_cell(0, 0) is None


@pytest.mark.asyncio
async def test_undo_stack_can_undo_flag(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        assert not app.undo_stack.can_undo

        await pilot.press("=")
        for ch in "99":
            await pilot.press(ch)
        await pilot.press("enter")
        await pilot.pause()

        assert app.undo_stack.can_undo


@pytest.mark.asyncio
async def test_redo_after_undo(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("=")
        for ch in "7":
            await pilot.press(ch)
        await pilot.press("enter")
        await pilot.pause()

        sheet = app.workbook.active_sheet
        assert sheet.get_cell(0, 0).value == 7

        await pilot.press("u")
        await pilot.pause()
        assert sheet.get_cell(0, 0) is None

        await pilot.press("ctrl+r")
        await pilot.pause()
        assert sheet.get_cell(0, 0) is not None
        assert sheet.get_cell(0, 0).value == 7


@pytest.mark.asyncio
async def test_multiple_sequential_undos(app_with_data: VimSheetApp) -> None:
    async with app_with_data.run_test() as pilot:
        sheet = app_with_data.workbook.active_sheet

        # Clear three cells
        await pilot.press("x")  # clears (0,0)
        await pilot.press("j")
        await pilot.press("x")  # clears (1,0)
        await pilot.press("j")
        await pilot.press("x")  # clears (2,0)
        await pilot.pause()

        assert sheet.get_cell(0, 0) is None
        assert sheet.get_cell(1, 0) is None
        assert sheet.get_cell(2, 0) is None

        # Undo 3 times
        await pilot.press("u")
        await pilot.pause()
        assert sheet.get_cell(2, 0) is not None  # restored

        await pilot.press("u")
        await pilot.pause()
        assert sheet.get_cell(1, 0) is not None  # restored

        await pilot.press("u")
        await pilot.pause()
        assert sheet.get_cell(0, 0) is not None  # restored


@pytest.mark.asyncio
async def test_new_action_clears_redo_stack(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("=")
        await pilot.press("1")
        await pilot.press("enter")
        await pilot.pause()

        await pilot.press("u")
        await pilot.pause()
        assert app.undo_stack.can_redo

        # New action clears redo
        await pilot.press("=")
        await pilot.press("2")
        await pilot.press("enter")
        await pilot.pause()

        assert not app.undo_stack.can_redo


@pytest.mark.asyncio
async def test_insert_row_is_undoable(app_with_data: VimSheetApp) -> None:
    async with app_with_data.run_test() as pilot:
        sheet = app_with_data.workbook.active_sheet
        assert sheet.get_cell(0, 0).value == "Alpha"

        await pilot.press("i")
        await pilot.press("r")
        await pilot.pause()

        # Row shifted down
        assert sheet.get_cell(0, 0) is None
        assert sheet.get_cell(1, 0).value == "Alpha"

        # Undo
        await pilot.press("u")
        await pilot.pause()
        assert sheet.get_cell(0, 0).value == "Alpha"


@pytest.mark.asyncio
async def test_delete_row_is_undoable(app_with_data: VimSheetApp) -> None:
    async with app_with_data.run_test() as pilot:
        sheet = app_with_data.workbook.active_sheet
        assert sheet.get_cell(0, 0).value == "Alpha"

        await pilot.press("d")
        await pilot.press("r")
        await pilot.pause()

        assert sheet.get_cell(0, 0).value == "Beta"

        await pilot.press("u")
        await pilot.pause()
        assert sheet.get_cell(0, 0).value == "Alpha"
