"""E2E tests for Normal mode operations (beyond navigation)."""

from __future__ import annotations

import pytest

from tests.conftest import make_workbook
from vimsheet.app import VimSheetApp
from vimsheet.controller.mode import Mode
from vimsheet.model.register import RegisterEntry

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def app() -> VimSheetApp:
    """App backed by a blank workbook."""
    return VimSheetApp(workbook=make_workbook())


@pytest.fixture
def app_with_data() -> VimSheetApp:
    """App with a small data block."""
    wb = make_workbook(
        data=[
            ["Alpha", 10, "note"],
            ["Beta", 20, "note2"],
            ["Gamma", 30, "note3"],
        ]
    )
    return VimSheetApp(workbook=wb)


# ---------------------------------------------------------------------------
# x — clear cell
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_x_clears_cell_content(app_with_data: VimSheetApp) -> None:
    async with app_with_data.run_test() as pilot:
        sheet = app_with_data.workbook.active_sheet
        # A1 should have "Alpha"
        assert sheet.get_cell(0, 0) is not None
        assert sheet.get_cell(0, 0).value == "Alpha"

        await pilot.press("x")
        await pilot.pause()

        assert sheet.get_cell(0, 0) is None


@pytest.mark.asyncio
async def test_x_on_empty_cell_does_not_raise(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        # Empty cell — x should not crash
        await pilot.press("x")
        await pilot.pause()
        assert app.mode == Mode.NORMAL


# ---------------------------------------------------------------------------
# yy + p — yank and paste
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_yy_then_p_pastes_at_cursor(app_with_data: VimSheetApp) -> None:
    async with app_with_data.run_test() as pilot:
        sheet = app_with_data.workbook.active_sheet
        # Yank A1 ("Alpha")
        await pilot.press("y")
        await pilot.press("y")
        await pilot.pause()

        assert isinstance(app_with_data._default_register, RegisterEntry)
        assert app_with_data._default_register.value == "Alpha"
        assert app_with_data._default_register.formula is None
        assert app_with_data._default_register.src_row == 0
        assert app_with_data._default_register.src_col == 0

        # Paste at cursor (A1, row 0)
        await pilot.press("p")
        await pilot.pause()

        pasted = sheet.get_cell(0, 0)
        assert pasted is not None
        assert pasted.value == "Alpha"


# ---------------------------------------------------------------------------
# Mode entry: =, e, v
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_equals_enters_insert_mode(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("=")
        assert app.mode == Mode.INSERT


@pytest.mark.asyncio
async def test_e_enters_edit_mode(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("e")
        assert app.mode == Mode.EDIT


@pytest.mark.asyncio
async def test_v_enters_visual_mode(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("v")
        assert app.mode == Mode.VISUAL


# ---------------------------------------------------------------------------
# ir — insert row
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ir_inserts_row_and_shifts_data_down(app_with_data: VimSheetApp) -> None:
    async with app_with_data.run_test() as pilot:
        sheet = app_with_data.workbook.active_sheet
        # Original row 0 has "Alpha"
        assert sheet.get_cell(0, 0).value == "Alpha"

        # Insert row above row 0
        await pilot.press("i")
        await pilot.press("r")
        await pilot.pause()

        # "Alpha" should now be on row 1
        assert sheet.get_cell(1, 0) is not None
        assert sheet.get_cell(1, 0).value == "Alpha"
        # Row 0 should be empty
        assert sheet.get_cell(0, 0) is None


# ---------------------------------------------------------------------------
# dr — delete row
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dr_deletes_row_and_shifts_up(app_with_data: VimSheetApp) -> None:
    async with app_with_data.run_test() as pilot:
        sheet = app_with_data.workbook.active_sheet
        # Row 0 = "Alpha", row 1 = "Beta"
        assert sheet.get_cell(0, 0).value == "Alpha"
        assert sheet.get_cell(1, 0).value == "Beta"

        await pilot.press("d")
        await pilot.press("r")
        await pilot.pause()

        # "Beta" should now be at row 0
        assert sheet.get_cell(0, 0) is not None
        assert sheet.get_cell(0, 0).value == "Beta"


# ---------------------------------------------------------------------------
# fb — toggle bold
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fb_toggles_bold_on_cell(app_with_data: VimSheetApp) -> None:
    async with app_with_data.run_test() as pilot:
        sheet = app_with_data.workbook.active_sheet
        cell_before = sheet.get_cell(0, 0)
        bold_before = cell_before.fmt.bold if cell_before else False

        await pilot.press("t")
        await pilot.press("b")
        await pilot.pause()

        cell_after = sheet.get_cell(0, 0)
        assert cell_after is not None
        assert cell_after.fmt.bold != bold_before


# ---------------------------------------------------------------------------
# u — undo cell clear
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_u_undoes_x_clear(app_with_data: VimSheetApp) -> None:
    async with app_with_data.run_test() as pilot:
        sheet = app_with_data.workbook.active_sheet
        original_value = sheet.get_cell(0, 0).value  # "Alpha"

        await pilot.press("x")
        await pilot.pause()
        assert sheet.get_cell(0, 0) is None

        await pilot.press("u")
        await pilot.pause()

        restored = sheet.get_cell(0, 0)
        assert restored is not None
        assert restored.value == original_value


# ---------------------------------------------------------------------------
# ctrl+r — redo after undo
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ctrl_r_redoes_after_undo(app_with_data: VimSheetApp) -> None:
    async with app_with_data.run_test() as pilot:
        sheet = app_with_data.workbook.active_sheet

        # Clear A1
        await pilot.press("x")
        await pilot.pause()
        assert sheet.get_cell(0, 0) is None

        # Undo — cell restored
        await pilot.press("u")
        await pilot.pause()
        assert sheet.get_cell(0, 0) is not None

        # Redo — cell cleared again
        await pilot.press("ctrl+r")
        await pilot.pause()
        assert sheet.get_cell(0, 0) is None


# ---------------------------------------------------------------------------
# Marks: ma / 'a
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mark_set_and_jump(app_with_data: VimSheetApp) -> None:
    async with app_with_data.run_test() as pilot:
        # Move to row 2
        await pilot.press("j")
        await pilot.press("j")
        assert app_with_data.cursor_row == 2

        # Set mark 'a'
        await pilot.press("m")
        await pilot.press("a")
        await pilot.pause()

        # Move away
        await pilot.press("k")
        await pilot.press("k")
        assert app_with_data.cursor_row == 0

        # Jump back to mark 'a'
        await pilot.press("'")
        await pilot.press("a")
        await pilot.pause()

        assert app_with_data.cursor_row == 2


# ---------------------------------------------------------------------------
# ZQ — quit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ZQ_quits_app(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("Z")
        await pilot.press("Q")
        # After ZQ the app should have exited — the context manager returns
        # without raising, which means the app exited cleanly.
