"""E2E tests for colon-command editing with the unified editor."""

from __future__ import annotations

import pytest

from tests.conftest import make_workbook
from vimsheet.app import VimSheetApp
from vimsheet.controller.mode import Mode
from vimsheet.model.history import HistoryStack


@pytest.fixture
def app() -> VimSheetApp:
    a = VimSheetApp(workbook=make_workbook())
    a._cmd_history = HistoryStack()
    a._search_history = HistoryStack()
    return a


@pytest.mark.asyncio
async def test_colon_enters_command_insert_submode(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press(":")
        assert app.mode == Mode.COMMAND
        assert app.edit_handler._sub == "insert"
        assert app._edit_buffer == ""
        assert app._editor_prefix == ":"


@pytest.mark.asyncio
async def test_escape_enters_normal_without_executing(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press(":")
        await pilot.press("3")
        await pilot.press("escape")

        # Still in COMMAND, now editing the line; nothing ran yet
        assert app.mode == Mode.COMMAND
        assert app.edit_handler._sub == "normal"
        assert app._edit_buffer == "3"
        assert app.cursor_row == 0

        await pilot.press("enter")
        await pilot.pause()
        assert app.mode == Mode.NORMAL
        assert app.cursor_row == 2  # :3 jumps to row 3 (0-based 2)


@pytest.mark.asyncio
async def test_enter_executes_from_insert(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press(":")
        await pilot.press("3")
        await pilot.press("enter")
        await pilot.pause()
        assert app.mode == Mode.NORMAL
        assert app.cursor_row == 2


@pytest.mark.asyncio
async def test_escape_from_normal_cancels(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press(":")
        await pilot.press("3")
        await pilot.press("escape")  # -> normal sub-mode
        await pilot.press("escape")  # -> cancel
        assert app.mode == Mode.NORMAL
        assert app.cursor_row == 0


@pytest.mark.asyncio
async def test_edit_command_with_vim_motions_then_execute(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press(":")
        for ch in "33":
            await pilot.press(ch)
        await pilot.press("escape")  # normal sub-mode

        await pilot.press("0")  # cursor to start
        await pilot.press("x")  # delete first "3" -> "3"
        assert app._edit_buffer == "3"

        await pilot.press("enter")
        await pilot.pause()
        assert app.cursor_row == 2


@pytest.mark.asyncio
async def test_tab_completes_command(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press(":")
        for ch in "sor":
            await pilot.press(ch)
        await pilot.press("tab")
        assert app._edit_buffer == "sort"


@pytest.mark.asyncio
async def test_history_up_down_in_insert(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press(":")
        await pilot.press("3")
        await pilot.press("enter")
        await pilot.pause()

        await pilot.press(":")
        await pilot.press("up")
        assert app._edit_buffer == "3"
        await pilot.press("down")
        assert app._edit_buffer == ""

        await pilot.press("escape")
        await pilot.press("escape")
        assert app.mode == Mode.NORMAL


@pytest.mark.asyncio
async def test_history_j_k_in_normal(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press(":")
        await pilot.press("3")
        await pilot.press("enter")
        await pilot.pause()

        await pilot.press(":")
        await pilot.press("escape")  # normal sub-mode
        assert app._edit_buffer == ""

        await pilot.press("k")  # previous history
        assert app._edit_buffer == "3"
        await pilot.press("j")  # next history
        assert app._edit_buffer == ""

        await pilot.press("escape")
        assert app.mode == Mode.NORMAL


@pytest.mark.asyncio
async def test_empty_command_enter_closes(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press(":")
        await pilot.press("enter")
        await pilot.pause()
        assert app.mode == Mode.NORMAL
