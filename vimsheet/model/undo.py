"""Command-pattern undo/redo stack for VimSheet."""

from __future__ import annotations

import copy
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from vimsheet.model.cell import Cell, CellFormat
from vimsheet.model.range import CellRange

if TYPE_CHECKING:
    from vimsheet.model.sheet import Sheet

_MAX_UNDO = 1000


@dataclass
class YankedCell:
    """Register entry that preserves both a cell's formula and its value."""

    value: Any
    formula: str | None


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------


class Command(ABC):
    description: str = ""

    @abstractmethod
    def execute(self) -> None:
        ...

    @abstractmethod
    def undo(self) -> None:
        ...


# ---------------------------------------------------------------------------
# Snapshot helpers
# ---------------------------------------------------------------------------


def _snapshot_cell(sheet: Sheet, row: int, col: int) -> Cell | None:
    """Return a deep-enough copy of the cell, or None if it doesn't exist."""
    existing = sheet.get_cell(row, col)
    if existing is None:
        return None
    return existing.copy()


def _restore_cell(sheet: Sheet, row: int, col: int, snap: Cell | None) -> None:
    """Put the cell back (or clear it) from a snapshot."""
    if snap is None:
        sheet.clear_cell(row, col)
    else:
        cell = sheet.set_cell_value(row, col, snap.value, snap.formula, record_history=False)
        cell.display = snap.display
        cell.fmt = snap.fmt.copy()
        cell.locked = snap.locked
        cell.comment = snap.comment


# ---------------------------------------------------------------------------
# Concrete commands
# ---------------------------------------------------------------------------


class SetCellCommand(Command):
    description = "set cell"

    def __init__(
        self,
        sheet: Sheet,
        row: int,
        col: int,
        new_value: Any,
        new_formula: str | None = None,
    ) -> None:
        self._sheet = sheet
        self._row = row
        self._col = col
        self._new_value = new_value
        self._new_formula = new_formula
        self._old_snap: Cell | None = None

    def execute(self) -> None:
        self._old_snap = _snapshot_cell(self._sheet, self._row, self._col)
        self._sheet.set_cell_value(self._row, self._col, self._new_value, self._new_formula)

    def undo(self) -> None:
        _restore_cell(self._sheet, self._row, self._col, self._old_snap)


class ClearCellCommand(Command):
    description = "clear cell"

    def __init__(self, sheet: Sheet, row: int, col: int) -> None:
        self._sheet = sheet
        self._row = row
        self._col = col
        self._old_snap: Cell | None = None

    def execute(self) -> None:
        self._old_snap = _snapshot_cell(self._sheet, self._row, self._col)
        self._sheet.clear_cell(self._row, self._col)

    def undo(self) -> None:
        _restore_cell(self._sheet, self._row, self._col, self._old_snap)


class DeleteRangeCommand(Command):
    description = "delete range"

    def __init__(self, sheet: Sheet, cell_range: CellRange) -> None:
        self._sheet = sheet
        self._range = cell_range
        self._snaps: dict[tuple[int, int], Cell | None] = {}

    def execute(self) -> None:
        positions = list(self._range.iter_cells())
        for r, c in positions:
            self._snaps[(r, c)] = _snapshot_cell(self._sheet, r, c)
        self._sheet.clear_cells_batch(positions)

    def undo(self) -> None:
        for (r, c), snap in self._snaps.items():
            _restore_cell(self._sheet, r, c, snap)


class FillRangeCommand(Command):
    description = "fill range"

    def __init__(self, sheet: Sheet, updates: list[tuple[int, int, Any]]) -> None:
        self._sheet = sheet
        self._updates = updates
        self._snaps: dict[tuple[int, int], Cell | None] = {}

    def execute(self) -> None:
        for r, c, _ in self._updates:
            self._snaps[(r, c)] = _snapshot_cell(self._sheet, r, c)
        self._sheet.set_cells_batch(self._updates)

    def undo(self) -> None:
        for (r, c), snap in self._snaps.items():
            _restore_cell(self._sheet, r, c, snap)


class InsertRowCommand(Command):
    description = "insert row"

    def __init__(self, sheet: Sheet, row: int) -> None:
        self._sheet = sheet
        self._row = row

    def execute(self) -> None:
        self._sheet.insert_row(self._row)

    def undo(self) -> None:
        self._sheet.delete_row(self._row)


class DeleteRowCommand(Command):
    description = "delete row"

    def __init__(self, sheet: Sheet, row: int) -> None:
        self._sheet = sheet
        self._row = row
        self._deleted: dict[int, Cell] = {}

    def execute(self) -> None:
        self._deleted = self._sheet.delete_row(self._row)

    def undo(self) -> None:
        self._sheet.insert_row(self._row)
        for col, cell in self._deleted.items():
            restored = self._sheet.set_cell_value(
                self._row, col, cell.value, cell.formula, record_history=False
            )
            restored.display = cell.display
            restored.fmt = cell.fmt.copy()
            restored.locked = cell.locked
            restored.comment = cell.comment


class InsertColCommand(Command):
    description = "insert column"

    def __init__(self, sheet: Sheet, col: int) -> None:
        self._sheet = sheet
        self._col = col

    def execute(self) -> None:
        self._sheet.insert_col(self._col)

    def undo(self) -> None:
        self._sheet.delete_col(self._col)


class DeleteColCommand(Command):
    description = "delete column"

    def __init__(self, sheet: Sheet, col: int) -> None:
        self._sheet = sheet
        self._col = col
        self._deleted: dict[int, Cell] = {}

    def execute(self) -> None:
        self._deleted = self._sheet.delete_col(self._col)

    def undo(self) -> None:
        self._sheet.insert_col(self._col)
        for row, cell in self._deleted.items():
            restored = self._sheet.set_cell_value(
                row, self._col, cell.value, cell.formula, record_history=False
            )
            restored.display = cell.display
            restored.fmt = cell.fmt.copy()
            restored.locked = cell.locked
            restored.comment = cell.comment


class PasteCommand(Command):
    description = "paste"

    def __init__(
        self,
        sheet: Sheet,
        base_row: int,
        base_col: int,
        data: list[list[Any]],
    ) -> None:
        self._sheet = sheet
        self._base_row = base_row
        self._base_col = base_col
        self._data = data
        self._snaps: dict[tuple[int, int], Cell | None] = {}

    def execute(self) -> None:
        for dr, row_data in enumerate(self._data):
            for dc, entry in enumerate(row_data):
                r = self._base_row + dr
                c = self._base_col + dc
                self._snaps[(r, c)] = _snapshot_cell(self._sheet, r, c)
                if isinstance(entry, YankedCell):
                    self._sheet.set_cell_value(r, c, entry.value, entry.formula)
                else:
                    self._sheet.set_cell_value(r, c, entry)

    def undo(self) -> None:
        for (r, c), snap in self._snaps.items():
            _restore_cell(self._sheet, r, c, snap)


class LockCommand(Command):
    description = "lock cell"

    def __init__(self, sheet: Sheet, row: int, col: int, locked: bool) -> None:
        self._sheet = sheet
        self._row = row
        self._col = col
        self._locked = locked
        self._old_locked: bool = False

    def execute(self) -> None:
        cell = self._sheet.get_cell(self._row, self._col)
        if cell is None:
            cell = self._sheet.set_cell_value(self._row, self._col, None)
        self._old_locked = cell.locked
        cell.locked = self._locked

    def undo(self) -> None:
        cell = self._sheet.get_cell(self._row, self._col)
        if cell is not None:
            cell.locked = self._old_locked


class FormatCommand(Command):
    description = "format cell"

    def __init__(self, sheet: Sheet, row: int, col: int, **new_fmt_kwargs: Any) -> None:
        self._sheet = sheet
        self._row = row
        self._col = col
        self._new_fmt_kwargs = new_fmt_kwargs
        self._old_fmt: CellFormat | None = None

    def execute(self) -> None:
        existing = self._sheet.get_cell(self._row, self._col)
        if existing is None:
            # Create cell so it has a format to modify
            existing = self._sheet.set_cell_value(self._row, self._col, None)
        self._old_fmt = copy.deepcopy(existing.fmt)
        for key, val in self._new_fmt_kwargs.items():
            setattr(existing.fmt, key, val)

    def undo(self) -> None:
        existing = self._sheet.get_cell(self._row, self._col)
        if existing is not None and self._old_fmt is not None:
            existing.fmt = copy.deepcopy(self._old_fmt)


class SortCommand(Command):
    description = "sort sheet"

    def __init__(
        self,
        sheet: Sheet,
        sort_keys: list[tuple[int, bool]],
        range_bounds: tuple[int, int, int, int] | None = None,
    ) -> None:
        self._sheet = sheet
        self._sort_keys = sort_keys
        self._range_bounds = range_bounds
        self._snapshot: dict[tuple[int, int], Cell] = {}

    def execute(self) -> None:
        self._snapshot = {k: v.copy() for k, v in self._sheet.cells.items()}
        if self._range_bounds:
            r1, c1, r2, c2 = self._range_bounds
            self._sheet.sort_range_columns(r1, c1, r2, c2, self._sort_keys)
        else:
            self._sheet.sort_by_cols(self._sort_keys)

    def undo(self) -> None:
        self._sheet.cells.clear()
        for (r, c), cell_copy in self._snapshot.items():
            self._sheet.cells[(r, c)] = cell_copy
        self._sheet._recalculate_extents()
        self._sheet.sort_state = None


class ShiftCellsCommand(Command):
    """Cascade-shift a cell block one step in direction (dr, dc).

    The entire strip from the source's leading edge to the end of used data
    shifts by one, so existing content is pushed out of the way rather than
    overwritten.  The vacated leading edge is left empty.
    """

    description = "shift cells"

    def __init__(self, sheet: Sheet, src: CellRange, dr: int, dc: int) -> None:
        self._sheet = sheet
        self._src = src
        self._dr = dr
        self._dc = dc
        self._snapshot: dict[tuple[int, int], Cell | None] = {}

    def execute(self) -> None:
        sheet = self._sheet
        src = self._src
        dr, dc = self._dr, self._dc

        # Snapshot the strip that will be affected (source + everything beyond)
        if dc > 0:
            for r in range(src.start_row, src.end_row + 1):
                for c in range(src.start_col, sheet.max_col + 2):
                    self._snapshot[(r, c)] = _snapshot_cell(sheet, r, c)
        elif dc < 0:
            for r in range(src.start_row, src.end_row + 1):
                for c in range(0, src.end_col + 1):
                    self._snapshot[(r, c)] = _snapshot_cell(sheet, r, c)
        elif dr > 0:
            for c in range(src.start_col, src.end_col + 1):
                for r in range(src.start_row, sheet.max_row + 2):
                    self._snapshot[(r, c)] = _snapshot_cell(sheet, r, c)
        elif dr < 0:
            for c in range(src.start_col, src.end_col + 1):
                for r in range(0, src.end_row + 1):
                    self._snapshot[(r, c)] = _snapshot_cell(sheet, r, c)

        # Clear the snapshotted area, then shift everything by (dr, dc)
        for pos in self._snapshot:
            sheet.clear_cell(*pos)
        for (r, c), snap in self._snapshot.items():
            new_r, new_c = r + dr, c + dc
            if new_r >= 0 and new_c >= 0 and snap is not None:
                _restore_cell(sheet, new_r, new_c, snap)
        sheet._recalculate_extents()

    def undo(self) -> None:
        sheet = self._sheet
        dr, dc = self._dr, self._dc
        # Clear what was written during execute
        for r, c in self._snapshot:
            new_r, new_c = r + dr, c + dc
            if new_r >= 0 and new_c >= 0:
                sheet.clear_cell(new_r, new_c)
        # Restore original content
        for (r, c), snap in self._snapshot.items():
            _restore_cell(sheet, r, c, snap)
        sheet._recalculate_extents()


class CompositeCommand(Command):
    description = "composite"

    def __init__(self, commands: list[Command]) -> None:
        self._commands = commands

    def execute(self) -> None:
        for cmd in self._commands:
            cmd.execute()

    def undo(self) -> None:
        for cmd in reversed(self._commands):
            cmd.undo()


# ---------------------------------------------------------------------------
# Undo stack
# ---------------------------------------------------------------------------


class UndoStack:
    """Manages the undo/redo history for a sheet."""

    def __init__(self, max_size: int = _MAX_UNDO) -> None:
        self._max_size = max_size
        self._undo: list[Command] = []
        self._redo: list[Command] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    def push(self, cmd: Command) -> None:
        """Execute *cmd* and push it onto the undo stack, clearing redo history."""
        cmd.execute()
        self._redo.clear()
        self._undo.append(cmd)
        if len(self._undo) > self._max_size:
            self._undo.pop(0)

    def undo(self) -> bool:
        """Undo the most recent command. Returns True if something was undone."""
        if not self._undo:
            return False
        cmd = self._undo.pop()
        cmd.undo()
        self._redo.append(cmd)
        return True

    def redo(self) -> bool:
        """Re-apply the most recently undone command. Returns True if something was redone."""
        if not self._redo:
            return False
        cmd = self._redo.pop()
        cmd.execute()
        self._undo.append(cmd)
        return True

    def clear(self) -> None:
        """Discard all undo and redo history."""
        self._undo.clear()
        self._redo.clear()
