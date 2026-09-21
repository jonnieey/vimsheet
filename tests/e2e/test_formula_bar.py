"""E2E tests for formula bar caret rendering."""

from __future__ import annotations

import pytest

from tests.conftest import make_workbook
from vimsheet.app import VimSheetApp
from vimsheet.ui.formula_bar import INSERT_CARET


@pytest.fixture
def app() -> VimSheetApp:
    return VimSheetApp(workbook=make_workbook())


@pytest.fixture
def app_with_data() -> VimSheetApp:
    return VimSheetApp(workbook=make_workbook(data=[["abcd"]]))


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


@pytest.mark.asyncio
async def test_insert_caret_overlays_mid_text_without_shifting(
    app_with_data: VimSheetApp,
) -> None:
    async with app_with_data.run_test() as pilot:
        await pilot.press("e")  # editor normal sub-mode, cursor at end (4)
        await pilot.press("0")  # cursor 0
        await pilot.press("l")
        await pilot.press("l")  # cursor 2
        await pilot.press("i")  # insert sub-mode at cursor 2

        assert app_with_data.formula_bar.insert_submode is True
        assert app_with_data._edit_cursor == 2
        plain = app_with_data.formula_bar._build_text().plain
        # Bar overlays the "c"; the line does not grow.
        assert f"ab{INSERT_CARET}d" in plain
        assert "abc" not in plain


@pytest.mark.asyncio
async def test_insert_caret_at_end_uses_trailing_padding(
    app_with_data: VimSheetApp,
) -> None:
    async with app_with_data.run_test() as pilot:
        await pilot.press("e")  # editor normal sub-mode, cursor at end
        await pilot.press("i")  # insert sub-mode at end

        assert app_with_data.formula_bar.insert_submode is True
        assert app_with_data._edit_cursor == 4
        plain = app_with_data.formula_bar._build_text().plain
        assert f"abcd{INSERT_CARET}" in plain
