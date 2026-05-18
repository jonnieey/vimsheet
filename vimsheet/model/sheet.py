"""Sheet model — a single tab in a workbook."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from vimsheet.formula.dependency import DependencyGraph
from vimsheet.model.cell import Cell, CellFormat
from vimsheet.model.range import CellRange, NamedRangeRegistry, a1_to_rowcol
from vimsheet.model.validation import SheetValidation


@dataclass
class CondFormatRule:
    """A conditional formatting rule applied to a range."""

    range_str: str
    operator: str  # "eq", "ne", "lt", "le", "gt", "ge", "contains", "between"
    value: Any
    value2: Any = None  # used by "between"
    fmt: CellFormat = field(default_factory=CellFormat)

    def matches(self, cell_value: Any) -> bool:
        """Return True if *cell_value* satisfies this rule's condition."""
        if cell_value is None:
            return False
        try:
            match self.operator:
                case "eq":
                    return cell_value == self.value
                case "ne":
                    return cell_value != self.value
                case "lt":
                    return float(cell_value) < float(self.value)
                case "le":
                    return float(cell_value) <= float(self.value)
                case "gt":
                    return float(cell_value) > float(self.value)
                case "ge":
                    return float(cell_value) >= float(self.value)
                case "contains":
                    return str(self.value) in str(cell_value)
                case "between":
                    v = float(cell_value)
                    return float(self.value) <= v <= float(self.value2)
                case _:
                    return False
        except (TypeError, ValueError):
            return False


@dataclass
class FilterRule:
    """A column filter rule."""

    operator: str  # "eq", "ne", "lt", "le", "gt", "ge", "contains", "regex"
    value: Any

    def matches(self, cell_value: Any) -> bool:
        """Return True if *cell_value* satisfies this filter."""
        import re as _re

        if cell_value is None:
            return self.operator == "eq" and self.value is None
        try:
            match self.operator:
                case "eq":
                    return str(cell_value) == str(self.value)
                case "ne":
                    return str(cell_value) != str(self.value)
                case "lt":
                    return float(cell_value) < float(self.value)
                case "le":
                    return float(cell_value) <= float(self.value)
                case "gt":
                    return float(cell_value) > float(self.value)
                case "ge":
                    return float(cell_value) >= float(self.value)
                case "contains":
                    return str(self.value) in str(cell_value)
                case "regex":
                    return bool(_re.search(str(self.value), str(cell_value)))
                case _:
                    return False
        except (TypeError, ValueError):
            return False


@dataclass
class SortState:
    """Remembered sort configuration for a sheet."""

    sort_keys: list[tuple[int, bool]]


@dataclass
class Sheet:
    """A single sheet (tab) inside a workbook."""

    name: str
    cells: dict[tuple[int, int], Cell] = field(default_factory=dict)
    col_widths: dict[int, int] = field(default_factory=dict)  # col → chars
    row_heights: dict[int, int] = field(default_factory=dict)  # row → chars
    hidden_rows: set[int] = field(default_factory=set)
    hidden_cols: set[int] = field(default_factory=set)
    row_groups: list[tuple[int, int]] = field(default_factory=list)
    col_groups: list[tuple[int, int]] = field(default_factory=list)
    freeze_rows: int = 0
    freeze_cols: int = 0
    named_ranges: NamedRangeRegistry = field(default_factory=NamedRangeRegistry)
    cond_formats: list[CondFormatRule] = field(default_factory=list)
    filters: dict[int, FilterRule] = field(default_factory=dict)
    sort_state: SortState | None = None
    max_row: int = 0
    max_col: int = 0
    validation: SheetValidation = field(default_factory=SheetValidation)
    cursor_row: int = 0
    cursor_col: int = 0
    _filter_rows: set[int] = field(default_factory=set, init=False, repr=False, compare=False)
    _dep_graph: DependencyGraph = field(
        default_factory=DependencyGraph, init=False, repr=False, compare=False
    )
    autocalc: bool = field(default=True, init=False, repr=False, compare=False)

    # -----------------------------------------------------------------------
    # Cell access
    # -----------------------------------------------------------------------

    def get_cell(self, row: int, col: int) -> Cell | None:
        """Return the Cell at (row, col), or None if the cell is empty."""
        return self.cells.get((row, col))

    def cell(self, address: str) -> Cell | None:
        """Return the cell at an A1-notation address, or None."""
        r, c = a1_to_rowcol(address)
        return self.get_cell(r, c)

    def set_cell_value(
        self,
        row: int,
        col: int,
        value: Any,
        formula: str | None = None,
        record_history: bool = True,
    ) -> Cell:
        """Set a cell's value (and optional formula); create the cell if absent."""
        existing = self.cells.get((row, col))
        if existing is None:
            existing = Cell(row=row, col=col)
            self.cells[(row, col)] = existing
        if record_history and existing.value != value:
            existing.record_history(existing.value)
        old_formula = existing.formula
        existing.formula = formula
        if formula and formula.startswith("="):
            from vimsheet.formula.evaluator import Evaluator

            ev = Evaluator(self, getattr(self, "_workbook", None))
            existing.value = ev.eval_formula(formula, row, col)
            self._dep_graph.set_dependencies((row, col), ev.collect_deps(formula))
        else:
            existing.value = value
            if old_formula and old_formula.startswith("="):
                # Cell no longer has a formula — clear its forward dep edges.
                # Use set_dependencies(set()) rather than remove_cell() so that
                # reverse edges pointing TO this cell are preserved for other formulas.
                self._dep_graph.set_dependencies((row, col), set())
        existing.display = existing.format_value()
        self._update_extents(row, col)
        self._recalculate_dependents(row, col)
        return existing

    def clear_cell(self, row: int, col: int) -> None:
        """Remove all content from a cell."""
        direct_deps = self._dep_graph.dependents_of((row, col))
        cell = self.cells.get((row, col))
        if cell and cell.formula and cell.formula.startswith("="):
            self._dep_graph.set_dependencies((row, col), set())
        if (row, col) in self.cells:
            del self.cells[(row, col)]
        self._recalculate_extents()
        if direct_deps and self.autocalc:
            self._do_recalculate(direct_deps)

    def set_cells_batch(self, updates: list[tuple[int, int, Any]]) -> None:
        """Set plain values for many cells in one pass, recalculating only once."""
        from vimsheet.model.cell import Cell

        all_deps: set[tuple[int, int]] = set()
        for row, col, value in updates:
            existing = self.cells.get((row, col))
            if existing is None:
                existing = Cell(row=row, col=col)
                self.cells[(row, col)] = existing
            # Clear any old formula dep edges
            if existing.formula and existing.formula.startswith("="):
                self._dep_graph.set_dependencies((row, col), set())
            existing.formula = None
            existing.value = value
            existing.display = existing.format_value()
            self._update_extents(row, col)
            all_deps |= self._dep_graph.dependents_of((row, col))
        self._recalculate_extents()
        updated = {(r, c) for r, c, _ in updates}
        surviving_deps = all_deps - updated
        if surviving_deps and self.autocalc:
            self._do_recalculate(surviving_deps)

    def clear_cells_batch(self, positions: list[tuple[int, int]]) -> None:
        """Remove content from many cells in one pass, recalculating only once."""
        all_deps: set[tuple[int, int]] = set()
        for row, col in positions:
            all_deps |= self._dep_graph.dependents_of((row, col))
            cell = self.cells.get((row, col))
            if cell and cell.formula and cell.formula.startswith("="):
                self._dep_graph.set_dependencies((row, col), set())
            self.cells.pop((row, col), None)
        self._recalculate_extents()
        # Only recalculate dependents that weren't themselves cleared
        cleared = set(positions)
        surviving_deps = all_deps - cleared
        if surviving_deps and self.autocalc:
            self._do_recalculate(surviving_deps)

    # -----------------------------------------------------------------------
    # Range access
    # -----------------------------------------------------------------------

    def get_range_values(self, cell_range: CellRange) -> list[list[Any]]:
        """Return a 2-D list of values for the given range."""
        return [
            [
                self.cells[(r, c)].value if (r, c) in self.cells else None
                for c in range(cell_range.start_col, cell_range.end_col + 1)
            ]
            for r in range(cell_range.start_row, cell_range.end_row + 1)
        ]

    # -----------------------------------------------------------------------
    # Row / column operations
    # -----------------------------------------------------------------------

    def insert_row(self, before_row: int) -> None:
        """Insert a blank row before *before_row*, shifting cells down."""
        new_cells: dict[tuple[int, int], Cell] = {}
        for (r, c), cell in self.cells.items():
            if r >= before_row:
                cell.row = r + 1
                new_cells[(r + 1, c)] = cell
            else:
                new_cells[(r, c)] = cell
        self.cells = new_cells
        self.max_row += 1

    def delete_row(self, row: int) -> dict[int, Cell]:
        """Delete *row*, shift cells up. Returns snapshot of deleted cells keyed by col."""
        deleted = {c: cell for (r, c), cell in self.cells.items() if r == row}
        new_cells: dict[tuple[int, int], Cell] = {}
        for (r, c), cell in self.cells.items():
            if r == row:
                continue
            if r > row:
                cell.row = r - 1
                new_cells[(r - 1, c)] = cell
            else:
                new_cells[(r, c)] = cell
        self.cells = new_cells
        self._recalculate_extents()
        return deleted

    def insert_col(self, before_col: int) -> None:
        """Insert a blank column before *before_col*, shifting cells right."""
        new_cells: dict[tuple[int, int], Cell] = {}
        for (r, c), cell in self.cells.items():
            if c >= before_col:
                cell.col = c + 1
                new_cells[(r, c + 1)] = cell
            else:
                new_cells[(r, c)] = cell
        self.cells = new_cells
        self.max_col += 1

    def delete_col(self, col: int) -> dict[int, Cell]:
        """Delete *col*, shift cells left. Returns snapshot keyed by row."""
        deleted = {r: cell for (r, c), cell in self.cells.items() if c == col}
        new_cells: dict[tuple[int, int], Cell] = {}
        for (r, c), cell in self.cells.items():
            if c == col:
                continue
            if c > col:
                cell.col = c - 1
                new_cells[(r, c - 1)] = cell
            else:
                new_cells[(r, c)] = cell
        self.cells = new_cells
        self._recalculate_extents()
        return deleted

    # -----------------------------------------------------------------------
    # Column width helpers
    # -----------------------------------------------------------------------

    DEFAULT_COL_WIDTH = 10

    def get_col_width(self, col: int) -> int:
        """Return column width in characters."""
        return self.col_widths.get(col, self.DEFAULT_COL_WIDTH)

    def set_col_width(self, col: int, width: int) -> None:
        """Set column width, clamped to [2, 80]."""
        self.col_widths[col] = max(2, min(80, width))

    def auto_fit_col(self, col: int) -> None:
        """Set column width to the longest content in that column."""
        max_len = 1
        for (_, c), cell in self.cells.items():
            if c == col:
                max_len = max(max_len, len(cell.display or ""))
        self.col_widths[col] = max(2, min(80, max_len + 2))

    # -----------------------------------------------------------------------
    # Used-range helpers
    # -----------------------------------------------------------------------

    def used_range(self) -> CellRange | None:
        """Return the bounding CellRange of all non-empty cells, or None."""
        if not self.cells:
            return None
        rows = [r for r, _ in self.cells]
        cols = [c for _, c in self.cells]
        return CellRange(min(rows), min(cols), max(rows), max(cols))

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _recalculate_dependents(self, row: int, col: int) -> None:
        """Recalculate all formula cells that transitively depend on (row, col)."""
        if not self.autocalc:
            return
        direct = self._dep_graph.dependents_of((row, col))
        if direct:
            self._do_recalculate(direct)

    def _do_recalculate(self, start: set[tuple[int, int]]) -> None:
        """Evaluate *start* cells (and their transitive dependents) in topo order."""
        from vimsheet.formula.dependency import CycleError
        from vimsheet.formula.evaluator import Evaluator

        try:
            order = self._dep_graph.evaluation_order(start)
        except CycleError:
            for pos in start:
                if pos in self.cells:
                    self.cells[pos].value = "#CIRC"
                    self.cells[pos].display = "#CIRC"
            return
        ev = Evaluator(self, getattr(self, "_workbook", None))
        for pos in order:
            if pos not in self.cells:
                continue
            cell = self.cells[pos]
            if cell.formula:
                cell.value = ev.eval_formula(cell.formula, pos[0], pos[1])
                cell.display = cell.format_value()

    def _update_extents(self, row: int, col: int) -> None:
        if row > self.max_row:
            self.max_row = row
        if col > self.max_col:
            self.max_col = col

    def _recalculate_extents(self) -> None:
        if not self.cells:
            self.max_row = 0
            self.max_col = 0
        else:
            self.max_row = max(r for r, _ in self.cells)
            self.max_col = max(c for _, c in self.cells)

    def sort_by_col(self, col: int, ascending: bool = True) -> None:
        """Sort all rows by *col* (0-based). Single-key convenience."""
        self.sort_by_cols([(col, ascending)])

    def sort_by_cols(self, sort_keys: list[tuple[int, bool]]) -> None:
        """Sort cells in each specified column independently. Other columns unchanged."""
        if not self.cells:
            return

        def _sort_key(v: Any, asc: bool) -> tuple:
            if v is None:
                return (1, 0, ())
            try:
                num = float(v)
                return (0, num if asc else -num, ())
            except (TypeError, ValueError):
                s = str(v)
                if asc:
                    return (0, 0, tuple(ord(c) for c in s))
                else:
                    return (0, 0, tuple(-ord(c) for c in s))

        from vimsheet.model.cell import Cell as CellCls

        for col, ascending in sort_keys:
            if col < self.freeze_cols:
                continue
            gathered: list[tuple[tuple, CellCls | None]] = []
            for r in range(self.freeze_rows, self.max_row + 1):
                cell = self.get_cell(r, col)
                gathered.append((_sort_key(cell.value if cell else None, ascending), cell))
            gathered.sort(key=lambda x: x[0])
            for new_r, (_, src_cell) in enumerate(gathered):
                key = (self.freeze_rows + new_r, col)
                if src_cell is None:
                    self.cells.pop(key, None)
                else:
                    c = src_cell.copy()
                    c.row = self.freeze_rows + new_r
                    c.col = col
                    self.cells[key] = c

        self._recalculate_extents()
        self.sort_state = SortState(sort_keys=sort_keys)

    def sort_range_columns(
        self, r1: int, c1: int, r2: int, c2: int, sort_keys: list[tuple[int, bool]]
    ) -> None:
        """Sort each column within (r1,c1)-(r2,c2) independently.
        sort_keys is (col, ascending) pairs.
        """
        if not self.cells:
            return

        def _key(v: Any, asc: bool) -> tuple:
            if v is None:
                return (1, 0, ())
            try:
                num = float(v)
                return (0, num if asc else -num, ())
            except (TypeError, ValueError):
                s = str(v)
                if asc:
                    return (0, 0, tuple(ord(c) for c in s))
                return (0, 0, tuple(-ord(c) for c in s))

        for col, ascending in sort_keys:
            if col < self.freeze_cols or col < c1 or col > c2:
                continue
            actual_r1 = max(r1, self.freeze_rows)
            if actual_r1 > r2:
                continue
            gathered: list[tuple[tuple, Cell | None]] = []
            for r in range(actual_r1, r2 + 1):
                cell = self.get_cell(r, col)
                gathered.append((_key(cell.value if cell else None, ascending), cell))
            gathered.sort(key=lambda x: x[0])
            for new_idx, (_, src) in enumerate(gathered):
                dst_r = actual_r1 + new_idx
                if src is None:
                    self.cells.pop((dst_r, col), None)
                else:
                    c = src.copy()
                    c.row = dst_r
                    c.col = col
                    self.cells[(dst_r, col)] = c

    def apply_filters(self) -> None:
        """Update hidden_rows based on the current filter rules."""
        filter_hidden: set[int] = set()
        if self.filters:
            for r in range(self.max_row + 1):
                for col, rule in self.filters.items():
                    cell = self.get_cell(r, col)
                    val = cell.value if cell else None
                    if not rule.matches(val):
                        filter_hidden.add(r)
                        break
        self.hidden_rows = (self.hidden_rows - self._filter_rows) | filter_hidden
        self._filter_rows = filter_hidden
