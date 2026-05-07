"""Integration tests for relative vs absolute formula paste via workbook API."""

from __future__ import annotations

from typing import Any

from vimsheet.formula.adjuster import adjust_formula
from vimsheet.model.register import RegisterEntry
from vimsheet.model.sheet import Sheet
from vimsheet.model.undo import PasteCommand, UndoStack, YankedCell


def _setup_sheet_with_formula() -> Sheet:
    """Return a sheet with =IF(B2>10,"true","false") at B2."""
    sheet = Sheet(name="Sheet1")
    sheet.set_cell_value(1, 1, "true", formula='=IF(B2>10,"true","false")')
    return sheet


def test_p_adjusts_formula():
    """p adjusts cell references relative to offset."""
    sheet = _setup_sheet_with_formula()
    entry = RegisterEntry(
        value="true",
        formula='=IF(B2>10,"true","false")',
        src_row=1,
        src_col=1,
    )
    dst_row, dst_col = 2, 1  # B3
    adjusted = adjust_formula(entry.formula, dst_row, dst_col, entry.src_row, entry.src_col)
    assert adjusted == '=IF(B3>10,"true","false")'

    paste_entry = YankedCell(value=entry.value, formula=adjusted)
    cmd = PasteCommand(sheet, dst_row, dst_col, [[paste_entry]])
    cmd.execute()

    cell = sheet.get_cell(2, 1)
    assert cell is not None
    assert cell.formula == '=IF(B3>10,"true","false")'


def test_P_keeps_formula_exact():
    """P pastes formula exactly as copied."""
    sheet = _setup_sheet_with_formula()
    entry = RegisterEntry(
        value="true",
        formula='=IF(B2>10,"true","false")',
        src_row=1,
        src_col=1,
    )
    dst_row, dst_col = 2, 1  # B3
    # No adjustment — exact formula
    paste_entry = YankedCell(value=entry.value, formula=entry.formula)
    cmd = PasteCommand(sheet, dst_row, dst_col, [[paste_entry]])
    cmd.execute()

    cell = sheet.get_cell(2, 1)
    assert cell is not None
    assert cell.value == "true"
    assert cell.formula == '=IF(B2>10,"true","false")'


def test_range_paste_adjusts_each_cell():
    """Visual yank range paste adjusts each formula by row offset only."""
    sheet = Sheet(name="Sheet1")
    # A1:A3 with formulas referencing same column, different rows
    sheet.set_cell_value(0, 0, 10, formula="=A1")
    sheet.set_cell_value(1, 0, 20, formula="=A2")
    sheet.set_cell_value(2, 0, 30, formula="=A3")

    range_data: list[list[tuple[Any, str | None]]] = [
        [(10, "=A1")],
        [(20, "=A2")],
        [(30, "=A3")],
    ]
    entry = RegisterEntry(
        value=None,
        formula=None,
        src_row=0,
        src_col=0,
        is_range=True,
        range_data=range_data,
        range_src_top=0,
        range_src_left=0,
    )
    dst_row, dst_col = 3, 0  # paste at A4 (row offset +3, same column)

    data: list[list[Any]] = []
    for _, row_data in enumerate(entry.range_data):
        row: list[Any] = []
        for _, (value, formula) in enumerate(row_data):
            adjusted = adjust_formula(
                formula, dst_row, dst_col, entry.range_src_top, entry.range_src_left
            )
            if formula is not None and adjusted is not None:
                row.append(YankedCell(value=value, formula=adjusted))
            else:
                row.append(value)
        data.append(row)

    cmd = PasteCommand(sheet, dst_row, dst_col, data)
    cmd.execute()

    # All references get row set to destination row (4 in 1-based)
    cell_a4 = sheet.get_cell(3, 0)
    assert cell_a4 is not None
    assert cell_a4.formula == "=A4"  # =A1 → =A4 (dst row = 4)

    cell_a5 = sheet.get_cell(4, 0)
    assert cell_a5 is not None
    assert cell_a5.formula == "=A4"  # =A2 → =A4 (dst row = 4)

    cell_a6 = sheet.get_cell(5, 0)
    assert cell_a6 is not None
    assert cell_a6.formula == "=A4"  # =A3 → =A4 (dst row = 4)


def test_undo_paste_restores_original():
    """Undo after paste restores previous cell state."""
    sheet = _setup_sheet_with_formula()
    undo_stack = UndoStack()

    entry = RegisterEntry(
        value="true",
        formula='=IF(B2>10,"true","false")',
        src_row=1,
        src_col=1,
    )
    dst_row, dst_col = 2, 1  # B3

    # Snapshot the destination before paste
    from vimsheet.model.undo import _snapshot_cell

    snap_before = _snapshot_cell(sheet, dst_row, dst_col)

    adjusted = adjust_formula(entry.formula, dst_row, dst_col, entry.src_row, entry.src_col)
    paste_entry = YankedCell(value=entry.value, formula=adjusted)
    cmd = PasteCommand(sheet, dst_row, dst_col, [[paste_entry]])

    # Execute (push also calls execute in UndoStack)
    assert sheet.get_cell(dst_row, dst_col) is None  # B3 was empty
    undo_stack.push(cmd)

    cell = sheet.get_cell(dst_row, dst_col)
    assert cell is not None
    assert cell.formula == '=IF(B3>10,"true","false")'

    # Undo
    undo_stack.undo()
    if snap_before is None:
        assert sheet.get_cell(dst_row, dst_col) is None
    else:
        restored = sheet.get_cell(dst_row, dst_col)
        assert restored is not None
        assert restored.value == snap_before.value
