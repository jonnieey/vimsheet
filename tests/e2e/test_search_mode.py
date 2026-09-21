"""E2E tests for search-prompt editing with the unified editor."""

from __future__ import annotations

import pytest

from tests.conftest import make_workbook
from vimsheet.app import VimSheetApp
from vimsheet.controller.mode import Mode
from vimsheet.model.history import HistoryStack


@pytest.fixture
def app() -> VimSheetApp:
    a = VimSheetApp(workbook=make_workbook(data=[["Alice"], ["Bob"], ["Carol"]]))
    a._cmd_history = HistoryStack()
    a._search_history = HistoryStack()
    return a


@pytest.mark.asyncio
async def test_slash_enters_search_insert_submode(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("/")
        assert app.mode == Mode.SEARCH
        assert app.edit_handler._sub == "insert"
        assert app._edit_buffer == ""
        assert app._editor_prefix == "/"


@pytest.mark.asyncio
async def test_question_uses_question_prefix(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("?")
        assert app.mode == Mode.SEARCH
        assert app._editor_prefix == "?"


@pytest.mark.asyncio
async def test_enter_dispatches_search(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("/")
        for ch in "Bob":
            await pilot.press(ch)
        await pilot.press("enter")
        await pilot.pause()
        assert app.mode == Mode.NORMAL
        assert (app.cursor_row, app.cursor_col) == (1, 0)


@pytest.mark.asyncio
async def test_escape_enters_normal_then_cancels(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("/")
        for ch in "Bob":
            await pilot.press(ch)
        await pilot.press("escape")
        assert app.mode == Mode.SEARCH
        assert app.edit_handler._sub == "normal"
        assert app.cursor_row == 0

        await pilot.press("escape")
        assert app.mode == Mode.NORMAL
        assert app.cursor_row == 0  # never searched


@pytest.mark.asyncio
async def test_edit_search_with_r_then_execute(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("/")
        for ch in "Boc":  # typo: c instead of b
            await pilot.press(ch)
        await pilot.press("escape")  # normal sub-mode, cursor on "c"

        await pilot.press("r")
        await pilot.press("b")  # replace c -> b
        assert app._edit_buffer == "Bob"

        await pilot.press("enter")
        await pilot.pause()
        assert (app.cursor_row, app.cursor_col) == (1, 0)


@pytest.mark.asyncio
async def test_history_up_in_insert(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("/")
        for ch in "Bob":
            await pilot.press(ch)
        await pilot.press("enter")
        await pilot.pause()

        await pilot.press("/")
        await pilot.press("up")
        assert app._edit_buffer == "Bob"

        await pilot.press("escape")
        await pilot.press("escape")
        assert app.mode == Mode.NORMAL
