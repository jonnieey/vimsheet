"""Find-and-replace logic for PySheet."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pysheet.model.sheet import Sheet


@dataclass
class SearchState:
    """Holds the current search/replace state."""

    pattern: str = ""
    replace: str = ""
    case_sensitive: bool = False
    use_regex: bool = False
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
            # Prevent partial-word matches (e.g. "3" matching inside "13").
            # Word boundaries work for alphanumeric patterns; otherwise anchor
            # the whole cell value with ^ … $ so "13" is never altered by :replace 3 5.
            if re.fullmatch(r"\w+", state.pattern):
                pattern = r"\b" + pattern + r"\b"
            else:
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

    def replace_one(self, state: SearchState, row: int, col: int) -> bool:
        """Replace text in (row, col) using state.replace.

        Returns True if a replacement was made.
        """
        cell = self._sheet.get_cell(row, col)
        if cell is None:
            return False

        regex = self._compile(state)

        # Prefer replacing in the formula if present; fall back to display.
        if cell.formula:
            new_text, count = regex.subn(state.replace, cell.formula)
            if count:
                self._sheet.set_cell_value(row, col, new_text, formula=new_text)
                return True
        else:
            new_text, count = regex.subn(state.replace, cell.display)
            if count:
                self._sheet.set_cell_value(row, col, new_text)
                return True

        return False

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
