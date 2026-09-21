"""E2E tests for insert-style cell entry through the unified editor."""

from __future__ import annotations

import pytest

from tests.conftest import make_workbook
from vimsheet.app import VimSheetApp
from vimsheet.controller.mode import Mode

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def app() -> VimSheetApp:
    return VimSheetApp(workbook=make_workbook())


@pytest.fixture
def app_with_data() -> VimSheetApp:
    wb = make_workbook(
        data=[
            ["Hello", 42],
            ["World", 99],
        ]
    )
    return VimSheetApp(workbook=wb)


# ---------------------------------------------------------------------------
# Entry keys open the unified editor in insert sub-mode
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_backslash_enters_insert_submode(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("\\")
        assert app.mode == Mode.EDIT
        assert app.edit_handler._sub == "insert"
        assert app._edit_buffer == ""
        assert app._edit_cursor == 0


@pytest.mark.asyncio
async def test_equals_enters_insert_submode_with_prefix(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("=")
        assert app.mode == Mode.EDIT
        assert app.edit_handler._sub == "insert"
        assert app._edit_buffer == "="
        assert app._edit_cursor == 1


# ---------------------------------------------------------------------------
# Typing builds _edit_buffer
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_typing_builds_buffer(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("\\")
        for ch in "hello":
            await pilot.press(ch)
        assert app._edit_buffer == "hello"


@pytest.mark.asyncio
async def test_backspace_removes_last_char(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("\\")
        for ch in "abc":
            await pilot.press(ch)
        assert app._edit_buffer == "abc"

        await pilot.press("backspace")
        assert app._edit_buffer == "ab"

        await pilot.press("backspace")
        assert app._edit_buffer == "a"


# ---------------------------------------------------------------------------
# Left/right arrow moves cursor
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_left_right_moves_cursor(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("\\")
        for ch in "abc":
            await pilot.press(ch)
        assert app._edit_cursor == 3

        await pilot.press("left")
        assert app._edit_cursor == 2

        await pilot.press("left")
        assert app._edit_cursor == 1

        await pilot.press("right")
        assert app._edit_cursor == 2


@pytest.mark.asyncio
async def test_left_clamps_at_zero(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("\\")
        await pilot.press("left")
        await pilot.press("left")
        assert app._edit_cursor == 0


# ---------------------------------------------------------------------------
# Enter commits and moves cursor down
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_enter_commits_and_moves_down(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("\\")
        for ch in "hello":
            await pilot.press(ch)
        assert app.cursor_row == 0

        await pilot.press("enter")
        await pilot.pause()

        assert app.mode == Mode.NORMAL
        assert app._edit_buffer == ""
        assert app.cursor_row == 1

        sheet = app.workbook.active_sheet
        cell = sheet.get_cell(0, 0)
        assert cell is not None
        assert cell.value == "hello"


# ---------------------------------------------------------------------------
# Tab commits and moves cursor right
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tab_commits_and_moves_right(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("\\")
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
# Escape leaves insert sub-mode for normal sub-mode; commit with Enter / Esc
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_escape_enters_normal_submode_without_committing(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("\\")
        for ch in "test":
            await pilot.press(ch)
        await pilot.press("escape")

        # Still in the editor, now in normal sub-mode, buffer preserved
        assert app.mode == Mode.EDIT
        assert app.edit_handler._sub == "normal"
        assert app._edit_buffer == "test"

        # Nothing written yet
        assert app.workbook.active_sheet.get_cell(0, 0) is None


@pytest.mark.asyncio
async def test_enter_after_escape_commits(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("\\")
        for ch in "test":
            await pilot.press(ch)
        await pilot.press("escape")
        await pilot.press("enter")
        await pilot.pause()

        assert app.mode == Mode.NORMAL
        cell = app.workbook.active_sheet.get_cell(0, 0)
        assert cell is not None
        assert cell.value == "test"


@pytest.mark.asyncio
async def test_double_escape_commits(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("\\")
        for ch in "test":
            await pilot.press(ch)
        await pilot.press("escape")
        await pilot.press("escape")
        await pilot.pause()

        assert app.mode == Mode.NORMAL
        cell = app.workbook.active_sheet.get_cell(0, 0)
        assert cell is not None
        assert cell.value == "test"


# ---------------------------------------------------------------------------
# ctrl+u clears buffer
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ctrl_u_clears_buffer(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("\\")
        for ch in "clearme":
            await pilot.press(ch)
        assert app._edit_buffer == "clearme"

        await pilot.press("ctrl+u")

        assert app._edit_buffer == ""
        assert app._edit_cursor == 0
        assert app.mode == Mode.EDIT


# ---------------------------------------------------------------------------
# Commit value semantics
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_numeric_formula_valueized_to_int(app: VimSheetApp) -> None:
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
        assert cell.formula is None  # =42 → value-ized to plain number


@pytest.mark.asyncio
async def test_string_value_stored_correctly(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("\\")
        for ch in "vimsheet":
            await pilot.press(ch)
        await pilot.press("enter")
        await pilot.pause()

        sheet = app.workbook.active_sheet
        cell = sheet.get_cell(0, 0)
        assert cell is not None
        assert cell.value == "vimsheet"


@pytest.mark.asyncio
async def test_backslash_keeps_numeric_text_as_string(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("\\")
        for ch in "42":
            await pilot.press(ch)
        await pilot.press("enter")
        await pilot.pause()

        cell = app.workbook.active_sheet.get_cell(0, 0)
        assert cell is not None
        assert cell.value == "42"  # string, not int


@pytest.mark.asyncio
async def test_backslash_uses_left_alignment(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("\\")
        for ch in "hi":
            await pilot.press(ch)
        await pilot.press("enter")
        await pilot.pause()

        cell = app.workbook.active_sheet.get_cell(0, 0)
        assert cell is not None
        assert cell.fmt.align == "left"


# ---------------------------------------------------------------------------
# Editing a formula with vim motions, then committing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fix_formula_with_vim_motions(app_with_data: VimSheetApp) -> None:
    """Also covers the Esc → normal sub-mode → fix → Enter flow."""
    async with app_with_data.run_test() as pilot:
        # (0,0) A1 == "Hello"; write a wrong formula "=B1" then fix it to "=B2"
        await pilot.press("=")
        for ch in "B1":
            await pilot.press(ch)
        assert app_with_data._edit_buffer == "=B1"

        await pilot.press("escape")  # normal sub-mode
        assert app_with_data.edit_handler._sub == "normal"

        await pilot.press("x")  # delete the "1" under the cursor
        await pilot.press("a")  # back to insert after cursor
        await pilot.press("2")  # -> "=B2"
        assert app_with_data._edit_buffer == "=B2"

        await pilot.press("enter")
        await pilot.pause()

        cell = app_with_data.workbook.active_sheet.get_cell(0, 0)
        assert cell is not None
        assert cell.formula == "=B2"
        assert cell.value == 99  # B2 holds 99


# ---------------------------------------------------------------------------
# Validation applies to insert-style entry too
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_validation_blocks_insert_commit(app: VimSheetApp) -> None:
    from vimsheet.model.validation import ValidationRule

    async with app.run_test() as pilot:
        sheet = app.workbook.active_sheet
        sheet.validation.add(0, 0, ValidationRule(rule_type="number", operator="gt", value1=0))

        await pilot.press("=")
        for ch in "-5":
            await pilot.press(ch)
        await pilot.press("enter")
        await pilot.pause()

        assert app.mode == Mode.NORMAL
        assert sheet.get_cell(0, 0) is None


# ---------------------------------------------------------------------------
# Cursor position details
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_insert_cursor_position_after_entry(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("\\")
        assert app._edit_cursor == 0
        assert app._edit_buffer == ""


@pytest.mark.asyncio
async def test_typing_mid_buffer_inserts_at_cursor(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("\\")
        for ch in "ac":
            await pilot.press(ch)
        await pilot.press("left")
        await pilot.press("b")
        assert app._edit_buffer == "abc"


# ---------------------------------------------------------------------------
# Sub-mode is reflected in the bars
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_submode_indicator_follows_editor(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        await pilot.press("=")
        assert app.formula_bar.insert_submode is True
        assert app.status_bar.insert_submode is True

        await pilot.press("escape")
        assert app.edit_handler._sub == "normal"
        assert app.formula_bar.insert_submode is False
        assert app.status_bar.insert_submode is False
