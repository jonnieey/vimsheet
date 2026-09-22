"""E2E tests for the :history modal."""

from __future__ import annotations

import pytest

from tests.conftest import make_workbook
from vimsheet.app import VimSheetApp


@pytest.fixture
def app() -> VimSheetApp:
    return VimSheetApp(workbook=make_workbook(data=[["A"], ["B"]]))


@pytest.mark.asyncio
async def test_current_cell_history_opens_modal(app: VimSheetApp) -> None:
    from vimsheet.ui.history_screen import HistoryScreen

    async with app.run_test() as pilot:
        app._dispatch_command("history")
        await pilot.pause()
        assert isinstance(app.screen, HistoryScreen)


@pytest.mark.asyncio
async def test_history_with_address_opens_modal(app: VimSheetApp) -> None:
    from vimsheet.ui.history_screen import HistoryScreen

    async with app.run_test() as pilot:
        app._dispatch_command("history B2")
        await pilot.pause()
        assert isinstance(app.screen, HistoryScreen)


@pytest.mark.asyncio
async def test_range_history_opens_modal(app: VimSheetApp) -> None:
    from vimsheet.ui.history_screen import HistoryScreen

    async with app.run_test() as pilot:
        app._dispatch_command("A1:B2 history")
        await pilot.pause()
        assert isinstance(app.screen, HistoryScreen)
