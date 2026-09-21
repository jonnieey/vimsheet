"""E2E tests for formula bar caret rendering."""

from __future__ import annotations

import pytest
from rich.console import Console

from tests.conftest import make_workbook
from vimsheet.app import VimSheetApp


@pytest.fixture
def app() -> VimSheetApp:
    return VimSheetApp(workbook=make_workbook())


@pytest.fixture
def app_with_data() -> VimSheetApp:
    return VimSheetApp(workbook=make_workbook(data=[["abcd"]]))


def _content_segment(text) -> str:
    """Return the cell-content part of the formula bar line."""
    parts = text.plain.split("│")
    return parts[1].strip() if len(parts) > 1 else ""


def _has_underline(text) -> bool:
    console = Console()
    return any(text.get_style_at_offset(console, i).underline for i in range(len(text.plain)))


@pytest.mark.asyncio
async def test_insert_submode_underlines_caret(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("=")
        assert app.formula_bar.insert_submode is True
        assert _has_underline(app.formula_bar._build_text())


@pytest.mark.asyncio
async def test_no_caret_when_not_editing(app: VimSheetApp) -> None:
    async with app.run_test():
        assert app.formula_bar.insert_submode is False
        assert not _has_underline(app.formula_bar._build_text())


@pytest.mark.asyncio
async def test_insert_caret_keeps_characters_and_does_not_shift(
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
        text = app_with_data.formula_bar._build_text()
        # All characters remain, unchanged length, and the caret is an underline
        assert _content_segment(text) == "abcd"
        assert _has_underline(text)


@pytest.mark.asyncio
async def test_normal_submode_uses_block_not_underline(
    app_with_data: VimSheetApp,
) -> None:
    async with app_with_data.run_test() as pilot:
        await pilot.press("e")  # normal sub-mode at end
        assert app_with_data.formula_bar.insert_submode is False
        text = app_with_data.formula_bar._build_text()
        assert _content_segment(text) == "abcd"
        assert not _has_underline(text)


@pytest.mark.asyncio
async def test_insert_caret_at_end_keeps_characters(
    app_with_data: VimSheetApp,
) -> None:
    async with app_with_data.run_test() as pilot:
        await pilot.press("e")  # normal sub-mode, cursor at end
        await pilot.press("i")  # insert sub-mode at end

        assert app_with_data.formula_bar.insert_submode is True
        assert app_with_data._edit_cursor == 4
        text = app_with_data.formula_bar._build_text()
        assert _content_segment(text) == "abcd"
        assert _has_underline(text)
