"""E2E tests for Insert mode."""

from __future__ import annotations

import pytest

from pysheet.app import PySheetApp
from pysheet.controller.mode import Mode
from tests.conftest import make_workbook

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def app() -> PySheetApp:
    return PySheetApp(workbook=make_workbook())


@pytest.fixture
def app_with_data() -> PySheetApp:
    wb = make_workbook(
        data=[
            ["Hello", 42],
            ["World", 99],
        ]
    )
    return PySheetApp(workbook=wb)


# ---------------------------------------------------------------------------
# Typing builds _insert_buffer
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_typing_builds_insert_buffer(app: PySheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("=")
        assert app.mode == Mode.INSERT

        for ch in "hello":
            await pilot.press(ch)

        assert app._insert_buffer == "hello"


@pytest.mark.asyncio
async def test_backspace_removes_last_char(app: PySheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("=")
        for ch in "abc":
            await pilot.press(ch)
        assert app._insert_buffer == "abc"

        await pilot.press("backspace")
        assert app._insert_buffer == "ab"

        await pilot.press("backspace")
        assert app._insert_buffer == "a"


# ---------------------------------------------------------------------------
# Left/right arrow moves insert cursor
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_left_right_moves_insert_cursor(app: PySheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("=")
        for ch in "abc":
            await pilot.press(ch)
        # cursor at position 3
        assert app._insert_cursor == 3

        await pilot.press("left")
        assert app._insert_cursor == 2

        await pilot.press("left")
        assert app._insert_cursor == 1

        await pilot.press("right")
        assert app._insert_cursor == 2


@pytest.mark.asyncio
async def test_left_clamps_at_zero(app: PySheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("=")
        await pilot.press("left")
        await pilot.press("left")
        assert app._insert_cursor == 0


# ---------------------------------------------------------------------------
# Enter commits and moves cursor down
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_enter_commits_and_moves_down(app: PySheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("=")
        for ch in "hello":
            await pilot.press(ch)
        assert app.cursor_row == 0

        await pilot.press("enter")
        await pilot.pause()

        assert app.mode == Mode.NORMAL
        assert app._insert_buffer == ""
        # Cursor should have moved down
        assert app.cursor_row == 1

        # Value should be in the sheet at row 0
        sheet = app.workbook.active_sheet
        cell = sheet.get_cell(0, 0)
        assert cell is not None
        assert cell.value == "hello"


# ---------------------------------------------------------------------------
# Tab commits and moves cursor right
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tab_commits_and_moves_right(app: PySheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("=")
        for ch in "data":
            await pilot.press(ch)
        assert app.cursor_col == 0

        await pilot.press("tab")
        await pilot.pause()

        assert app.mode == Mode.NORMAL
        assert app.cursor_col == 1

        sheet = app.workbook.active_sheet
        cell = sheet.get_cell(0, 0)
        assert cell is not None
        assert cell.value == "data"


# ---------------------------------------------------------------------------
# Escape cancels insert
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_escape_cancels_insert(app: PySheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("=")
        for ch in "test":
            await pilot.press(ch)
        assert app._insert_buffer == "test"

        await pilot.press("escape")

        assert app.mode == Mode.NORMAL
        assert app._insert_buffer == ""

        # No value written to sheet
        sheet = app.workbook.active_sheet
        assert sheet.get_cell(0, 0) is None


# ---------------------------------------------------------------------------
# ctrl+u clears buffer
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ctrl_u_clears_buffer(app: PySheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("=")
        for ch in "clearme":
            await pilot.press(ch)
        assert app._insert_buffer == "clearme"

        await pilot.press("ctrl+u")

        assert app._insert_buffer == ""
        assert app._insert_cursor == 0
        assert app.mode == Mode.INSERT


# ---------------------------------------------------------------------------
# After commit, cell has the correct value
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_numeric_value_stored_as_int(app: PySheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("=")
        for ch in "42":
            await pilot.press(ch)
        await pilot.press("enter")
        await pilot.pause()

        sheet = app.workbook.active_sheet
        cell = sheet.get_cell(0, 0)
        assert cell is not None
        assert cell.value == 42


@pytest.mark.asyncio
async def test_string_value_stored_correctly(app: PySheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("=")
        for ch in "pysheet":
            await pilot.press(ch)
        await pilot.press("enter")
        await pilot.pause()

        sheet = app.workbook.active_sheet
        cell = sheet.get_cell(0, 0)
        assert cell is not None
        assert cell.value == "pysheet"


@pytest.mark.asyncio
async def test_insert_mode_cursor_position_after_entry(app: PySheetApp) -> None:
    """After entering insert mode via =, cursor starts at position 0."""
    async with app.run_test() as pilot:
        await pilot.press("=")
        assert app._insert_cursor == 0
        assert app._insert_buffer == ""


@pytest.mark.asyncio
async def test_typing_mid_buffer_inserts_at_cursor(app: PySheetApp) -> None:
    """Chars typed at a non-end cursor position are inserted at that position."""
    async with app.run_test() as pilot:
        await pilot.press("=")
        for ch in "ac":
            await pilot.press(ch)
        # buffer = "ac", cursor at 2
        await pilot.press("left")
        # cursor at 1
        await pilot.press("b")
        # should insert "b" between "a" and "c"
        assert app._insert_buffer == "abc"
