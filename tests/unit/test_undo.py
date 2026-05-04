"""Unit tests for vimsheet.model.undo."""

from __future__ import annotations

from vimsheet.model.range import CellRange
from vimsheet.model.sheet import Sheet
from vimsheet.model.undo import (
    ClearCellCommand,
    CompositeCommand,
    DeleteColCommand,
    DeleteRangeCommand,
    DeleteRowCommand,
    FormatCommand,
    InsertColCommand,
    InsertRowCommand,
    PasteCommand,
    SetCellCommand,
    UndoStack,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_sheet(name: str = "Sheet1") -> Sheet:
    return Sheet(name=name)


# ---------------------------------------------------------------------------
# SetCellCommand
# ---------------------------------------------------------------------------


class TestSetCellCommand:
    def test_execute_sets_value(self) -> None:
        sheet = make_sheet()
        cmd = SetCellCommand(sheet, 0, 0, 42)
        cmd.execute()
        assert sheet.get_cell(0, 0) is not None
        assert sheet.get_cell(0, 0).value == 42  # type: ignore[union-attr]

    def test_execute_sets_formula(self) -> None:
        sheet = make_sheet()
        cmd = SetCellCommand(sheet, 0, 0, 10, new_formula="=A2+1")
        cmd.execute()
        cell = sheet.get_cell(0, 0)
        assert cell is not None
        assert cell.formula == "=A2+1"

    def test_undo_restores_old_value(self) -> None:
        sheet = make_sheet()
        sheet.set_cell_value(0, 0, 100)
        cmd = SetCellCommand(sheet, 0, 0, 200)
        cmd.execute()
        assert sheet.get_cell(0, 0).value == 200  # type: ignore[union-attr]
        cmd.undo()
        assert sheet.get_cell(0, 0).value == 100  # type: ignore[union-attr]

    def test_undo_clears_cell_when_it_didnt_exist(self) -> None:
        sheet = make_sheet()
        cmd = SetCellCommand(sheet, 1, 1, "hello")
        cmd.execute()
        assert sheet.get_cell(1, 1) is not None
        cmd.undo()
        assert sheet.get_cell(1, 1) is None

    def test_undo_restores_formula(self) -> None:
        sheet = make_sheet()
        sheet.set_cell_value(1, 0, 5)  # A2 = 5
        sheet.set_cell_value(0, 0, None, formula="=A2")  # A1 = =A2 → evaluates to 5
        cmd = SetCellCommand(sheet, 0, 0, None, new_formula="=B2")
        cmd.execute()
        cmd.undo()
        cell = sheet.get_cell(0, 0)
        assert cell is not None
        assert cell.formula == "=A2"
        assert cell.value == 5  # re-evaluated from A2


# ---------------------------------------------------------------------------
# ClearCellCommand
# ---------------------------------------------------------------------------


class TestClearCellCommand:
    def test_execute_clears_cell(self) -> None:
        sheet = make_sheet()
        sheet.set_cell_value(0, 0, 99)
        cmd = ClearCellCommand(sheet, 0, 0)
        cmd.execute()
        assert sheet.get_cell(0, 0) is None

    def test_undo_restores_cell(self) -> None:
        sheet = make_sheet()
        sheet.set_cell_value(0, 0, 99)
        cmd = ClearCellCommand(sheet, 0, 0)
        cmd.execute()
        cmd.undo()
        cell = sheet.get_cell(0, 0)
        assert cell is not None
        assert cell.value == 99

    def test_clear_nonexistent_cell_is_noop(self) -> None:
        sheet = make_sheet()
        cmd = ClearCellCommand(sheet, 5, 5)
        cmd.execute()
        assert sheet.get_cell(5, 5) is None

    def test_undo_after_clearing_nonexistent_cell(self) -> None:
        sheet = make_sheet()
        cmd = ClearCellCommand(sheet, 5, 5)
        cmd.execute()
        cmd.undo()
        # Cell was absent before clear — undo should leave it absent
        assert sheet.get_cell(5, 5) is None


# ---------------------------------------------------------------------------
# DeleteRangeCommand
# ---------------------------------------------------------------------------


class TestDeleteRangeCommand:
    def test_execute_clears_range(self) -> None:
        sheet = make_sheet()
        sheet.set_cell_value(0, 0, 1)
        sheet.set_cell_value(0, 1, 2)
        sheet.set_cell_value(1, 0, 3)
        rng = CellRange(0, 0, 1, 1)
        cmd = DeleteRangeCommand(sheet, rng)
        cmd.execute()
        for r, c in rng.iter_cells():
            assert sheet.get_cell(r, c) is None

    def test_undo_restores_range(self) -> None:
        sheet = make_sheet()
        sheet.set_cell_value(0, 0, 10)
        sheet.set_cell_value(0, 1, 20)
        rng = CellRange(0, 0, 0, 1)
        cmd = DeleteRangeCommand(sheet, rng)
        cmd.execute()
        cmd.undo()
        assert sheet.get_cell(0, 0).value == 10  # type: ignore[union-attr]
        assert sheet.get_cell(0, 1).value == 20  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# InsertRowCommand
# ---------------------------------------------------------------------------


class TestInsertRowCommand:
    def test_execute_shifts_rows_down(self) -> None:
        sheet = make_sheet()
        sheet.set_cell_value(0, 0, "original")
        cmd = InsertRowCommand(sheet, 0)
        cmd.execute()
        # The original row-0 cell should now be at row 1
        assert sheet.get_cell(0, 0) is None
        assert sheet.get_cell(1, 0) is not None
        assert sheet.get_cell(1, 0).value == "original"  # type: ignore[union-attr]

    def test_undo_removes_inserted_row(self) -> None:
        sheet = make_sheet()
        sheet.set_cell_value(0, 0, "original")
        cmd = InsertRowCommand(sheet, 0)
        cmd.execute()
        cmd.undo()
        assert sheet.get_cell(0, 0) is not None
        assert sheet.get_cell(0, 0).value == "original"  # type: ignore[union-attr]
        assert sheet.get_cell(1, 0) is None


# ---------------------------------------------------------------------------
# DeleteRowCommand
# ---------------------------------------------------------------------------


class TestDeleteRowCommand:
    def test_execute_removes_row(self) -> None:
        sheet = make_sheet()
        sheet.set_cell_value(0, 0, "keep-above")
        sheet.set_cell_value(1, 0, "delete-me")
        sheet.set_cell_value(2, 0, "shift-up")
        cmd = DeleteRowCommand(sheet, 1)
        cmd.execute()
        # Row 2 should now be at row 1
        assert sheet.get_cell(1, 0) is not None
        assert sheet.get_cell(1, 0).value == "shift-up"  # type: ignore[union-attr]

    def test_undo_restores_deleted_row(self) -> None:
        sheet = make_sheet()
        sheet.set_cell_value(0, 0, "A")
        sheet.set_cell_value(1, 0, "B")
        sheet.set_cell_value(2, 0, "C")
        cmd = DeleteRowCommand(sheet, 1)
        cmd.execute()
        cmd.undo()
        assert sheet.get_cell(1, 0) is not None
        assert sheet.get_cell(1, 0).value == "B"  # type: ignore[union-attr]
        assert sheet.get_cell(2, 0) is not None
        assert sheet.get_cell(2, 0).value == "C"  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# InsertColCommand
# ---------------------------------------------------------------------------


class TestInsertColCommand:
    def test_execute_shifts_cols_right(self) -> None:
        sheet = make_sheet()
        sheet.set_cell_value(0, 0, "original")
        cmd = InsertColCommand(sheet, 0)
        cmd.execute()
        assert sheet.get_cell(0, 0) is None
        assert sheet.get_cell(0, 1) is not None
        assert sheet.get_cell(0, 1).value == "original"  # type: ignore[union-attr]

    def test_undo_removes_inserted_col(self) -> None:
        sheet = make_sheet()
        sheet.set_cell_value(0, 0, "original")
        cmd = InsertColCommand(sheet, 0)
        cmd.execute()
        cmd.undo()
        assert sheet.get_cell(0, 0) is not None
        assert sheet.get_cell(0, 0).value == "original"  # type: ignore[union-attr]
        assert sheet.get_cell(0, 1) is None


# ---------------------------------------------------------------------------
# DeleteColCommand
# ---------------------------------------------------------------------------


class TestDeleteColCommand:
    def test_execute_removes_col(self) -> None:
        sheet = make_sheet()
        sheet.set_cell_value(0, 0, "keep-left")
        sheet.set_cell_value(0, 1, "delete-me")
        sheet.set_cell_value(0, 2, "shift-left")
        cmd = DeleteColCommand(sheet, 1)
        cmd.execute()
        assert sheet.get_cell(0, 1) is not None
        assert sheet.get_cell(0, 1).value == "shift-left"  # type: ignore[union-attr]

    def test_undo_restores_deleted_col(self) -> None:
        sheet = make_sheet()
        sheet.set_cell_value(0, 0, "A")
        sheet.set_cell_value(0, 1, "B")
        sheet.set_cell_value(0, 2, "C")
        cmd = DeleteColCommand(sheet, 1)
        cmd.execute()
        cmd.undo()
        assert sheet.get_cell(0, 1) is not None
        assert sheet.get_cell(0, 1).value == "B"  # type: ignore[union-attr]
        assert sheet.get_cell(0, 2) is not None
        assert sheet.get_cell(0, 2).value == "C"  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# PasteCommand
# ---------------------------------------------------------------------------


class TestPasteCommand:
    def test_execute_pastes_data(self) -> None:
        sheet = make_sheet()
        data = [[1, 2], [3, 4]]
        cmd = PasteCommand(sheet, 0, 0, data)
        cmd.execute()
        assert sheet.get_cell(0, 0).value == 1  # type: ignore[union-attr]
        assert sheet.get_cell(0, 1).value == 2  # type: ignore[union-attr]
        assert sheet.get_cell(1, 0).value == 3  # type: ignore[union-attr]
        assert sheet.get_cell(1, 1).value == 4  # type: ignore[union-attr]

    def test_undo_restores_overwritten_cells(self) -> None:
        sheet = make_sheet()
        sheet.set_cell_value(0, 0, "old00")
        sheet.set_cell_value(0, 1, "old01")
        data = [["new00", "new01"]]
        cmd = PasteCommand(sheet, 0, 0, data)
        cmd.execute()
        cmd.undo()
        assert sheet.get_cell(0, 0).value == "old00"  # type: ignore[union-attr]
        assert sheet.get_cell(0, 1).value == "old01"  # type: ignore[union-attr]

    def test_undo_clears_cells_that_were_empty_before_paste(self) -> None:
        sheet = make_sheet()
        cmd = PasteCommand(sheet, 2, 2, [[99]])
        cmd.execute()
        cmd.undo()
        assert sheet.get_cell(2, 2) is None


# ---------------------------------------------------------------------------
# FormatCommand
# ---------------------------------------------------------------------------


class TestFormatCommand:
    def test_execute_changes_format(self) -> None:
        sheet = make_sheet()
        sheet.set_cell_value(0, 0, "x")
        cmd = FormatCommand(sheet, 0, 0, bold=True, align="center")
        cmd.execute()
        cell = sheet.get_cell(0, 0)
        assert cell is not None
        assert cell.fmt.bold is True
        assert cell.fmt.align == "center"

    def test_undo_restores_format(self) -> None:
        sheet = make_sheet()
        sheet.set_cell_value(0, 0, "x")
        cmd = FormatCommand(sheet, 0, 0, bold=True)
        cmd.execute()
        cmd.undo()
        cell = sheet.get_cell(0, 0)
        assert cell is not None
        assert cell.fmt.bold is False

    def test_format_creates_cell_if_absent(self) -> None:
        sheet = make_sheet()
        cmd = FormatCommand(sheet, 3, 3, bold=True)
        cmd.execute()
        cell = sheet.get_cell(3, 3)
        assert cell is not None
        assert cell.fmt.bold is True


# ---------------------------------------------------------------------------
# CompositeCommand
# ---------------------------------------------------------------------------


class TestCompositeCommand:
    def test_execute_runs_all_commands(self) -> None:
        sheet = make_sheet()
        cmds = [
            SetCellCommand(sheet, 0, 0, "A"),
            SetCellCommand(sheet, 1, 0, "B"),
            SetCellCommand(sheet, 2, 0, "C"),
        ]
        composite = CompositeCommand(cmds)
        composite.execute()
        assert sheet.get_cell(0, 0).value == "A"  # type: ignore[union-attr]
        assert sheet.get_cell(1, 0).value == "B"  # type: ignore[union-attr]
        assert sheet.get_cell(2, 0).value == "C"  # type: ignore[union-attr]

    def test_undo_reverses_all_commands(self) -> None:
        sheet = make_sheet()
        sheet.set_cell_value(0, 0, "before")
        cmds = [
            SetCellCommand(sheet, 0, 0, "after0"),
            SetCellCommand(sheet, 0, 0, "after1"),
        ]
        composite = CompositeCommand(cmds)
        composite.execute()
        assert sheet.get_cell(0, 0).value == "after1"  # type: ignore[union-attr]
        composite.undo()
        # After undoing in reverse: undo 'after1→after0' then undo 'before→after0'
        assert sheet.get_cell(0, 0).value == "before"  # type: ignore[union-attr]

    def test_composite_undo_is_in_reverse_order(self) -> None:
        """Verify undo runs in reverse by using InsertRow/DeleteRow pair."""
        sheet = make_sheet()
        sheet.set_cell_value(0, 0, "row0")
        sheet.set_cell_value(1, 0, "row1")
        # Insert at row 0, then delete row 2 (which was row 1 before insert)
        cmds: list = [
            InsertRowCommand(sheet, 0),
            DeleteRowCommand(sheet, 2),
        ]
        composite = CompositeCommand(cmds)
        composite.execute()
        # After insert: row0="row0" at 1, "row1" at 2. After delete row2: "row1" gone.
        assert sheet.get_cell(1, 0) is not None
        assert sheet.get_cell(2, 0) is None
        composite.undo()
        # Undo delete (restores row2), then undo insert (removes blank row0)
        assert sheet.get_cell(0, 0) is not None
        assert sheet.get_cell(1, 0) is not None


# ---------------------------------------------------------------------------
# UndoStack
# ---------------------------------------------------------------------------


class TestUndoStack:
    def test_push_executes_command(self) -> None:
        sheet = make_sheet()
        stack = UndoStack()
        stack.push(SetCellCommand(sheet, 0, 0, 42))
        assert sheet.get_cell(0, 0).value == 42  # type: ignore[union-attr]

    def test_can_undo_after_push(self) -> None:
        stack = UndoStack()
        assert not stack.can_undo
        stack.push(SetCellCommand(make_sheet(), 0, 0, 1))
        assert stack.can_undo

    def test_can_redo_after_undo(self) -> None:
        sheet = make_sheet()
        stack = UndoStack()
        stack.push(SetCellCommand(sheet, 0, 0, 1))
        assert not stack.can_redo
        stack.undo()
        assert stack.can_redo

    def test_undo_returns_true_when_stack_not_empty(self) -> None:
        sheet = make_sheet()
        stack = UndoStack()
        stack.push(SetCellCommand(sheet, 0, 0, 1))
        assert stack.undo() is True

    def test_undo_returns_false_when_stack_empty(self) -> None:
        stack = UndoStack()
        assert stack.undo() is False

    def test_redo_returns_true_when_redo_available(self) -> None:
        sheet = make_sheet()
        stack = UndoStack()
        stack.push(SetCellCommand(sheet, 0, 0, 1))
        stack.undo()
        assert stack.redo() is True

    def test_redo_returns_false_when_nothing_to_redo(self) -> None:
        stack = UndoStack()
        assert stack.redo() is False

    def test_undo_redo_cycle_restores_value(self) -> None:
        sheet = make_sheet()
        stack = UndoStack()
        stack.push(SetCellCommand(sheet, 0, 0, 99))
        stack.undo()
        assert sheet.get_cell(0, 0) is None
        stack.redo()
        assert sheet.get_cell(0, 0).value == 99  # type: ignore[union-attr]

    def test_push_clears_redo_stack(self) -> None:
        sheet = make_sheet()
        stack = UndoStack()
        stack.push(SetCellCommand(sheet, 0, 0, 1))
        stack.undo()
        assert stack.can_redo
        stack.push(SetCellCommand(sheet, 0, 0, 2))
        assert not stack.can_redo

    def test_clear_empties_both_stacks(self) -> None:
        sheet = make_sheet()
        stack = UndoStack()
        stack.push(SetCellCommand(sheet, 0, 0, 1))
        stack.undo()
        stack.clear()
        assert not stack.can_undo
        assert not stack.can_redo

    def test_max_size_is_respected(self) -> None:
        sheet = make_sheet()
        stack = UndoStack(max_size=3)
        for i in range(5):
            stack.push(SetCellCommand(sheet, 0, 0, i))
        # Only the last 3 should remain undoable
        count = 0
        while stack.undo():
            count += 1
        assert count == 3

    def test_multiple_undo_redo(self) -> None:
        sheet = make_sheet()
        stack = UndoStack()
        stack.push(SetCellCommand(sheet, 0, 0, 1))
        stack.push(SetCellCommand(sheet, 0, 0, 2))
        stack.push(SetCellCommand(sheet, 0, 0, 3))
        stack.undo()
        assert sheet.get_cell(0, 0).value == 2  # type: ignore[union-attr]
        stack.undo()
        assert sheet.get_cell(0, 0).value == 1  # type: ignore[union-attr]
        stack.redo()
        assert sheet.get_cell(0, 0).value == 2  # type: ignore[union-attr]
