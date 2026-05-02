"""E2E tests for grid navigation in Normal mode."""

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
    """App backed by a blank workbook."""
    return PySheetApp(workbook=make_workbook())


@pytest.fixture
def app_with_data() -> PySheetApp:
    """App with a 5-row × 3-col data block."""
    wb = make_workbook(
        data=[
            ["Name", "Value", "Notes"],
            ["Alpha", 10, "a"],
            ["Beta", 20, "b"],
            ["Gamma", 30, "c"],
            ["Delta", 40, "d"],
        ]
    )
    return PySheetApp(workbook=wb)


# ---------------------------------------------------------------------------
# Basic hjkl navigation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_hjkl_right(app: PySheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("l")
        assert app.cursor == (0, 1)


@pytest.mark.asyncio
async def test_hjkl_down(app: PySheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("j")
        assert app.cursor == (1, 0)


@pytest.mark.asyncio
async def test_hjkl_up_at_top_clamps(app: PySheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("k")
        assert app.cursor_row == 0  # can't go above row 0


@pytest.mark.asyncio
async def test_hjkl_left_at_start_clamps(app: PySheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("h")
        assert app.cursor_col == 0  # can't go left of col 0


@pytest.mark.asyncio
async def test_hjkl_sequence(app: PySheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("l")  # (0,1)
        await pilot.press("j")  # (1,1)
        await pilot.press("k")  # (0,1)
        await pilot.press("h")  # (0,0)
        assert app.cursor == (0, 0)


@pytest.mark.asyncio
async def test_arrow_keys(app: PySheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("right")
        assert app.cursor_col == 1
        await pilot.press("down")
        assert app.cursor_row == 1
        await pilot.press("up")
        assert app.cursor_row == 0
        await pilot.press("left")
        assert app.cursor_col == 0


# ---------------------------------------------------------------------------
# gg / G navigation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_G_goes_to_last_row(app_with_data: PySheetApp) -> None:
    async with app_with_data.run_test() as pilot:
        await pilot.press("G")
        assert app_with_data.cursor_row == app_with_data.workbook.active_sheet.max_row


@pytest.mark.asyncio
async def test_gg_goes_to_first_row(app_with_data: PySheetApp) -> None:
    async with app_with_data.run_test() as pilot:
        await pilot.press("G")  # go to bottom
        await pilot.press("g")
        await pilot.press("g")  # gg → top
        assert app_with_data.cursor_row == 0


# ---------------------------------------------------------------------------
# 0 and $ navigation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_zero_goes_to_col_a(app: PySheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("l")
        await pilot.press("l")
        await pilot.press("0")
        assert app.cursor_col == 0


@pytest.mark.asyncio
async def test_dollar_goes_to_last_used_col(app_with_data: PySheetApp) -> None:
    async with app_with_data.run_test() as pilot:
        await pilot.press("$")
        assert app_with_data.cursor_col == app_with_data.workbook.active_sheet.max_col


# ---------------------------------------------------------------------------
# Ctrl+Home / Ctrl+End
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ctrl_home(app_with_data: PySheetApp) -> None:
    async with app_with_data.run_test() as pilot:
        await pilot.press("G")
        await pilot.press("$")
        await pilot.press("ctrl+home")
        assert app_with_data.cursor == (0, 0)


@pytest.mark.asyncio
async def test_ctrl_end(app_with_data: PySheetApp) -> None:
    async with app_with_data.run_test() as pilot:
        await pilot.press("ctrl+end")
        sheet = app_with_data.workbook.active_sheet
        assert app_with_data.cursor == (sheet.max_row, sheet.max_col)


# ---------------------------------------------------------------------------
# go{address} navigation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_goto_cell_address(app_with_data: PySheetApp) -> None:
    async with app_with_data.run_test() as pilot:
        await pilot.press("g")
        await pilot.press("o")
        for ch in "C3":
            await pilot.press(ch)
        await pilot.press("enter")
        assert app_with_data.cursor == (2, 2)


@pytest.mark.asyncio
async def test_goto_a1(app_with_data: PySheetApp) -> None:
    async with app_with_data.run_test() as pilot:
        await pilot.press("G")
        await pilot.press("g")
        await pilot.press("o")
        for ch in "A1":
            await pilot.press(ch)
        await pilot.press("enter")
        assert app_with_data.cursor == (0, 0)


# ---------------------------------------------------------------------------
# Mode verification — navigation stays in Normal mode
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_navigation_stays_in_normal_mode(app: PySheetApp) -> None:
    async with app.run_test() as pilot:
        for key in ("h", "j", "k", "l", "G", "0", "$"):
            await pilot.press(key)
        assert app.mode == Mode.NORMAL


# ---------------------------------------------------------------------------
# Sheet navigation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_gt_goes_to_next_sheet() -> None:
    wb = make_workbook(sheets={"S1": {"A1": 1}, "S2": {"A1": 2}})
    app = PySheetApp(workbook=wb)
    async with app.run_test() as pilot:
        assert app.workbook.active_sheet_idx == 0
        await pilot.press("g")
        await pilot.press("t")
        assert app.workbook.active_sheet_idx == 1


@pytest.mark.asyncio
async def test_gT_goes_to_prev_sheet() -> None:
    wb = make_workbook(sheets={"S1": {"A1": 1}, "S2": {"A1": 2}})
    wb.active_sheet_idx = 1
    app = PySheetApp(workbook=wb)
    async with app.run_test() as pilot:
        await pilot.press("g")
        await pilot.press("T")
        assert app.workbook.active_sheet_idx == 0


# ---------------------------------------------------------------------------
# Visual mode
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_visual_mode_entry_and_exit(app: PySheetApp) -> None:
    async with app.run_test() as pilot:
        assert app.mode == Mode.NORMAL
        await pilot.press("v")
        assert app.mode == Mode.VISUAL
        await pilot.press("escape")
        assert app.mode == Mode.NORMAL


@pytest.mark.asyncio
async def test_visual_mode_cursor_moves(app: PySheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("v")
        assert app.mode == Mode.VISUAL
        await pilot.press("j")
        assert app.cursor == (1, 0)
        await pilot.press("l")
        assert app.cursor == (1, 1)


@pytest.mark.asyncio
async def test_visual_selection_range(app: PySheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("v")
        await pilot.press("j")
        await pilot.press("j")
        sel = app.grid.visual_selection()
        assert sel is not None
        assert sel.start_row == 0
        assert sel.end_row == 2
        assert sel.start_col == 0
        assert sel.end_col == 0


@pytest.mark.asyncio
async def test_visual_line_mode(app: PySheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("V")
        assert app.mode == Mode.VISUAL_LINE
        await pilot.press("j")
        sel = app.grid.visual_selection()
        assert sel is not None
        assert sel.num_rows == 2
        await pilot.press("escape")
        assert app.mode == Mode.NORMAL
