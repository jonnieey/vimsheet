"""Find-and-replace logic for VimSheet."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from vimsheet.model.sheet import Sheet


@dataclass
class SearchState:
    """Holds the current search/replace state."""

    pattern: str = ""
    replace: str = ""
    case_sensitive: bool = False
    use_regex: bool = False
    whole_cell: bool = False  # anchor match to entire cell value (used by :replace)
    current_match: tuple[int, int] | None = None  # (row, col)
    matches: list[tuple[int, int]] = field(default_factory=list)


class Searcher:
    """Performs find/replace operations on a Sheet."""

    def __init__(self, sheet: Sheet) -> None:
        self._sheet = sheet

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _compile(self, state: SearchState) -> re.Pattern[str]:
        """Return a compiled regex for the current state."""
        pattern = state.pattern
        if not state.use_regex:
            pattern = re.escape(pattern)
            if state.whole_cell:
                pattern = "^" + pattern + "$"
        flags = 0 if state.case_sensitive else re.IGNORECASE
        return re.compile(pattern, flags)

    def _cell_texts(self, row: int, col: int) -> list[str]:
        """Return the searchable text strings for a cell."""
        cell = self._sheet.get_cell(row, col)
        if cell is None:
            return []
        texts: list[str] = []
        if cell.display:
            texts.append(cell.display)
        if cell.formula and cell.formula not in texts:
            texts.append(cell.formula)
        return texts

    def _matches_cell(self, regex: re.Pattern[str], row: int, col: int) -> bool:
        """Return True if any text in the cell matches *regex*."""
        return any(regex.search(text) for text in self._cell_texts(row, col))

    def _all_positions(self) -> list[tuple[int, int]]:
        """Return all (row, col) positions in the sheet in row-major order."""
        sheet = self._sheet
        if not sheet.cells:
            return []
        max_r = sheet.max_row
        max_c = sheet.max_col
        return [(r, c) for r in range(max_r + 1) for c in range(max_c + 1)]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def find_all(self, state: SearchState) -> list[tuple[int, int]]:
        """Return all (row, col) positions matching state.pattern.

        If the pattern is empty every non-empty cell is returned.
        """
        if not state.pattern:
            # Empty pattern — return every position that has a cell.
            return sorted(self._sheet.cells.keys())

        regex = self._compile(state)
        results: list[tuple[int, int]] = []
        for pos in self._all_positions():
            if self._matches_cell(regex, *pos):
                results.append(pos)
        return results

    def find_next(
        self,
        state: SearchState,
        from_pos: tuple[int, int],
    ) -> tuple[int, int] | None:
        """Return the next match after from_pos, wrapping around.

        Returns None when there are no matches at all.
        """
        matches = self.find_all(state)
        if not matches:
            return None

        # Find the first match that is strictly after from_pos.
        for pos in matches:
            if pos > from_pos:
                return pos

        # Wrap around: return the first match.
        return matches[0]

    def find_prev(
        self,
        state: SearchState,
        from_pos: tuple[int, int],
    ) -> tuple[int, int] | None:
        """Return the previous match before from_pos, wrapping around.

        Returns None when there are no matches at all.
        """
        matches = self.find_all(state)
        if not matches:
            return None

        # Find the last match that is strictly before from_pos.
        for pos in reversed(matches):
            if pos < from_pos:
                return pos

        # Wrap around: return the last match.
        return matches[-1]

    def replace_one(self, state: SearchState, row: int, col: int, max_subs: int = 0) -> bool:
        """Replace text in (row, col) using state.replace.

        max_subs=0 replaces all occurrences; max_subs=1 replaces only the first.
        Returns True if a replacement was made.
        """
        cell = self._sheet.get_cell(row, col)
        if cell is None:
            return False

        regex = self._compile(state)

        # Prefer replacing in the formula if present; fall back to display.
        if cell.formula:
            new_text, n = regex.subn(state.replace, cell.formula, count=max_subs)
            if n:
                self._sheet.set_cell_value(row, col, new_text, formula=new_text)
                return True
        else:
            new_text, n = regex.subn(state.replace, cell.display, count=max_subs)
            if n:
                self._sheet.set_cell_value(row, col, new_text)
                return True

        return False

    def collect_replacements(
        self, state: SearchState, rows: list[int] | None = None, cols: list[int] | None = None
    ) -> list[tuple[int, int, Any, str | None]]:
        """Return (row, col, new_value, new_formula) for matches without mutating.

        If *rows* and *cols* are both None, scans the entire sheet.
        If only *rows* given, scans those rows entirely.
        If only *cols* given, scans those columns entirely.
        If both given, scans the row×col intersection.
        """
        sheet = self._sheet
        if not sheet.cells:
            return []
        regex = self._compile(state)
        updates: list[tuple[int, int, Any, str | None]] = []

        if rows is not None and cols is not None:
            positions: list[tuple[int, int]] = [(r, c) for r in rows for c in cols]
        elif rows is not None:
            positions = [(r, c) for r in rows for c in range(sheet.max_col + 1)]
        elif cols is not None:
            positions = [(r, c) for c in cols for r in range(sheet.max_row + 1)]
        else:
            positions = self.find_all(state)

        for row, col in positions:
            cell = sheet.get_cell(row, col)
            if cell is None:
                continue
            if cell.formula:
                new_text, n = regex.subn(state.replace, cell.formula)
                if n:
                    updates.append((row, col, new_text, new_text))
            else:
                new_text, n = regex.subn(state.replace, cell.display)
                if n:
                    updates.append((row, col, new_text, None))
        return updates

    def replace_all(self, state: SearchState) -> int:
        """Replace all occurrences of state.pattern with state.replace.

        Returns the number of cells where a replacement was made.
        """
        positions = self.find_all(state)
        count = 0
        for row, col in positions:
            if self.replace_one(state, row, col):
                count += 1
        return count

    def replace_in_cols(self, state: SearchState, cols: list[int], max_subs: int = 0) -> int:
        """Replace in the given column indices only.

        max_subs=0 replaces all occurrences per cell; max_subs=1 replaces the first.
        Returns the number of cells where a replacement was made.
        """
        sheet = self._sheet
        if not sheet.cells:
            return 0
        count = 0
        for r in range(sheet.max_row + 1):
            for c in cols:
                if self.replace_one(state, r, c, max_subs=max_subs):
                    count += 1
        return count

    def replace_in_range(
        self, state: SearchState, rows: list[int], cols: list[int], max_subs: int = 0
    ) -> int:
        """Replace within a specific row+col intersection.

        Returns the number of cells where a replacement was made.
        """
        if not self._sheet.cells:
            return 0
        count = 0
        for r in rows:
            for c in cols:
                if self.replace_one(state, r, c, max_subs=max_subs):
                    count += 1
        return count

    def replace_in_rows(self, state: SearchState, rows: list[int], max_subs: int = 0) -> int:
        """Replace in the given row indices only.

        max_subs=0 replaces all occurrences per cell; max_subs=1 replaces the first.
        Returns the number of cells where a replacement was made.
        """
        sheet = self._sheet
        if not sheet.cells:
            return 0
        count = 0
        for r in rows:
            for c in range(sheet.max_col + 1):
                if self.replace_one(state, r, c, max_subs=max_subs):
                    count += 1
        return count
