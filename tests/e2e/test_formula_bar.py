"""E2E tests for formula bar caret rendering."""

from __future__ import annotations

import pytest

from tests.conftest import make_workbook
from vimsheet.app import VimSheetApp
from vimsheet.ui.formula_bar import INSERT_CARET


@pytest.fixture
def app() -> VimSheetApp:
    return VimSheetApp(workbook=make_workbook())


@pytest.mark.asyncio
async def test_insert_submode_shows_bar_caret(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("=")
        assert app.formula_bar.insert_submode is True
        assert INSERT_CARET in app.formula_bar._build_text().plain


@pytest.mark.asyncio
async def test_normal_submode_has_no_bar_caret(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("=")
        await pilot.press("escape")
        assert app.formula_bar.insert_submode is False
        assert INSERT_CARET not in app.formula_bar._build_text().plain


@pytest.mark.asyncio
async def test_no_caret_when_not_editing(app: VimSheetApp) -> None:
    async with app.run_test():
        assert app.formula_bar.insert_submode is False
        assert INSERT_CARET not in app.formula_bar._build_text().plain
