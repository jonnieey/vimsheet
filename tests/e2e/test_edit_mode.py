"""E2E tests for Edit mode."""

from __future__ import annotations

import pytest

from tests.conftest import make_workbook
from vimsheet.app import VimSheetApp
from vimsheet.controller.mode import Mode


@pytest.fixture
def app_with_data() -> VimSheetApp:
    wb = make_workbook(data=[["Hello"], ["World"]])
    return VimSheetApp(workbook=wb)


@pytest.fixture
def app() -> VimSheetApp:
    return VimSheetApp(workbook=make_workbook())


@pytest.mark.asyncio
async def test_e_loads_cell_content(app_with_data: VimSheetApp) -> None:
    async with app_with_data.run_test() as pilot:
        await pilot.press("e")
        assert app_with_data.mode == Mode.EDIT
        assert app_with_data._edit_buffer == "Hello"


@pytest.mark.asyncio
async def test_e_places_cursor_at_end(app_with_data: VimSheetApp) -> None:
    async with app_with_data.run_test() as pilot:
        await pilot.press("e")
        assert app_with_data._edit_cursor == len("Hello")


@pytest.mark.asyncio
async def test_E_places_cursor_at_start(app_with_data: VimSheetApp) -> None:
    async with app_with_data.run_test() as pilot:
        await pilot.press("E")
        assert app_with_data.mode == Mode.EDIT
        assert app_with_data._edit_cursor == 0


@pytest.mark.asyncio
async def test_enter_commits_edit(app_with_data: VimSheetApp) -> None:
    async with app_with_data.run_test() as pilot:
        await pilot.press("e")
        # In edit normal sub-mode, press Enter to commit
        await pilot.press("enter")
        await pilot.pause()
        assert app_with_data.mode == Mode.NORMAL


@pytest.mark.asyncio
async def test_escape_commits_edit(app_with_data: VimSheetApp) -> None:
    async with app_with_data.run_test() as pilot:
        await pilot.press("e")
        await pilot.press("escape")
        await pilot.pause()
        assert app_with_data.mode == Mode.NORMAL


@pytest.mark.asyncio
async def test_i_enters_insert_submode_and_typing_works(app_with_data: VimSheetApp) -> None:
    async with app_with_data.run_test() as pilot:
        await pilot.press("E")  # cursor at beginning
        await pilot.press("i")  # enter insert sub-mode
        await pilot.press("X")  # type "X"
        assert app_with_data._edit_buffer == "XHello"


@pytest.mark.asyncio
async def test_A_appends_at_end(app_with_data: VimSheetApp) -> None:
    async with app_with_data.run_test() as pilot:
        await pilot.press("e")
        await pilot.press("A")  # insert sub-mode at end
        await pilot.press("!")
        assert app_with_data._edit_buffer == "Hello!"


@pytest.mark.asyncio
async def test_x_deletes_char_under_cursor_in_edit(app_with_data: VimSheetApp) -> None:
    async with app_with_data.run_test() as pilot:
        await pilot.press("E")  # cursor at start
        await pilot.press("x")  # delete 'H'
        assert app_with_data._edit_buffer == "ello"


@pytest.mark.asyncio
async def test_u_in_edit_restores_original(app_with_data: VimSheetApp) -> None:
    async with app_with_data.run_test() as pilot:
        await pilot.press("e")
        await pilot.press("i")  # insert sub-mode
        for ch in "EXTRA":
            await pilot.press(ch)
        assert "EXTRA" in app_with_data._edit_buffer
        # Press escape to go back to edit normal sub-mode
        await pilot.press("escape")
        # Now 'u' should restore original
        await pilot.press("u")
        assert app_with_data._edit_buffer == "Hello"


@pytest.mark.asyncio
async def test_edit_empty_cell(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("e")
        assert app.mode == Mode.EDIT
        assert app._edit_buffer == ""
        await pilot.press("i")
        for ch in "new":
            await pilot.press(ch)
        await pilot.press("enter")
        await pilot.pause()
        assert app.mode == Mode.NORMAL
        cell = app.workbook.active_sheet.get_cell(0, 0)
        assert cell is not None
        assert cell.value == "new"
