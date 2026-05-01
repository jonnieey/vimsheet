"""Unit tests for pysheet.controller.search (Searcher and SearchState)."""

from __future__ import annotations

import pytest

from pysheet.controller.search import SearchState, Searcher
from pysheet.model.sheet import Sheet


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_sheet() -> Sheet:
    """Create a small test sheet with known content."""
    sheet = Sheet(name="TestSheet")
    # Row 0: headers
    sheet.set_cell_value(0, 0, "Name")
    sheet.set_cell_value(0, 1, "Score")
    sheet.set_cell_value(0, 2, "Grade")
    # Row 1
    sheet.set_cell_value(1, 0, "Alice")
    sheet.set_cell_value(1, 1, 95)
    sheet.set_cell_value(1, 2, "A")
    # Row 2
    sheet.set_cell_value(2, 0, "Bob")
    sheet.set_cell_value(2, 1, 72)
    sheet.set_cell_value(2, 2, "C")
    # Row 3: formula cell
    sheet.set_cell_value(3, 0, "alice")  # lowercase duplicate
    sheet.set_cell_value(3, 1, "=SUM(B2:B3)", formula="=SUM(B2:B3)")
    return sheet


# ---------------------------------------------------------------------------
# find_all tests
# ---------------------------------------------------------------------------

class TestFindAll:
    def test_simple_pattern_found(self) -> None:
        sheet = _make_sheet()
        searcher = Searcher(sheet)
        state = SearchState(pattern="Alice")
        matches = searcher.find_all(state)
        assert (1, 0) in matches

    def test_no_matches(self) -> None:
        sheet = _make_sheet()
        searcher = Searcher(sheet)
        state = SearchState(pattern="zzznomatch")
        assert searcher.find_all(state) == []

    def test_case_insensitive_by_default(self) -> None:
        sheet = _make_sheet()
        searcher = Searcher(sheet)
        # "alice" appears at (1,0) as "Alice" and (3,0) as "alice"
        state = SearchState(pattern="alice", case_sensitive=False)
        matches = searcher.find_all(state)
        assert (1, 0) in matches
        assert (3, 0) in matches

    def test_case_sensitive_no_match(self) -> None:
        sheet = _make_sheet()
        searcher = Searcher(sheet)
        state = SearchState(pattern="ALICE", case_sensitive=True)
        matches = searcher.find_all(state)
        # Neither "Alice" nor "alice" is uppercase "ALICE"
        assert (1, 0) not in matches
        assert (3, 0) not in matches

    def test_case_sensitive_exact_match(self) -> None:
        sheet = _make_sheet()
        searcher = Searcher(sheet)
        state = SearchState(pattern="Alice", case_sensitive=True)
        matches = searcher.find_all(state)
        assert (1, 0) in matches
        assert (3, 0) not in matches  # "alice" != "Alice"

    def test_regex_mode(self) -> None:
        sheet = _make_sheet()
        searcher = Searcher(sheet)
        # Match any single uppercase letter
        state = SearchState(pattern=r"^[A-Z]$", use_regex=True, case_sensitive=True)
        matches = searcher.find_all(state)
        # "A" at (1,2), "C" at (2,2) should match; "Name"/"Score"/"Grade" won't
        assert (1, 2) in matches
        assert (2, 2) in matches
        assert (0, 0) not in matches

    def test_empty_pattern_returns_all_cells(self) -> None:
        sheet = _make_sheet()
        searcher = Searcher(sheet)
        state = SearchState(pattern="")
        matches = searcher.find_all(state)
        # All non-empty cells should be returned
        assert len(matches) == len(sheet.cells)

    def test_empty_sheet_returns_empty(self) -> None:
        sheet = Sheet(name="Empty")
        searcher = Searcher(sheet)
        state = SearchState(pattern="anything")
        assert searcher.find_all(state) == []

    def test_search_in_formula_text(self) -> None:
        sheet = _make_sheet()
        searcher = Searcher(sheet)
        # The formula "=SUM(B2:B3)" at (3,1) should be found
        state = SearchState(pattern="SUM", case_sensitive=True)
        matches = searcher.find_all(state)
        assert (3, 1) in matches


# ---------------------------------------------------------------------------
# find_next / find_prev tests
# ---------------------------------------------------------------------------

class TestFindNextPrev:
    def test_find_next_wraps_around(self) -> None:
        sheet = _make_sheet()
        searcher = Searcher(sheet)
        state = SearchState(pattern="alice", case_sensitive=False)
        # Start after the last known match
        nxt = searcher.find_next(state, (99, 99))
        # Should wrap to the first match
        assert nxt is not None
        matches = searcher.find_all(state)
        assert nxt == matches[0]

    def test_find_next_no_matches_returns_none(self) -> None:
        sheet = _make_sheet()
        searcher = Searcher(sheet)
        state = SearchState(pattern="zzznomatch")
        assert searcher.find_next(state, (0, 0)) is None

    def test_find_next_advances_past_from_pos(self) -> None:
        sheet = _make_sheet()
        searcher = Searcher(sheet)
        state = SearchState(pattern="alice", case_sensitive=False)
        # (1,0) = "Alice", (3,0) = "alice"
        nxt = searcher.find_next(state, (1, 0))
        assert nxt == (3, 0)

    def test_find_prev_wraps_around(self) -> None:
        sheet = _make_sheet()
        searcher = Searcher(sheet)
        state = SearchState(pattern="alice", case_sensitive=False)
        # Start before any match
        prv = searcher.find_prev(state, (0, 0))
        # Should wrap to the last match
        matches = searcher.find_all(state)
        assert prv == matches[-1]

    def test_find_prev_no_matches_returns_none(self) -> None:
        sheet = _make_sheet()
        searcher = Searcher(sheet)
        state = SearchState(pattern="zzznomatch")
        assert searcher.find_prev(state, (99, 99)) is None

    def test_find_prev_goes_backward(self) -> None:
        sheet = _make_sheet()
        searcher = Searcher(sheet)
        state = SearchState(pattern="alice", case_sensitive=False)
        # From (3,0) we should go back to (1,0)
        prv = searcher.find_prev(state, (3, 0))
        assert prv == (1, 0)


# ---------------------------------------------------------------------------
# replace_one / replace_all tests
# ---------------------------------------------------------------------------

class TestReplaceOne:
    def test_replace_one_changes_cell_value(self) -> None:
        sheet = Sheet(name="R")
        sheet.set_cell_value(0, 0, "Hello World")
        searcher = Searcher(sheet)
        state = SearchState(pattern="World", replace="PySheet")
        replaced = searcher.replace_one(state, 0, 0)
        assert replaced is True
        cell = sheet.get_cell(0, 0)
        assert cell is not None
        assert "PySheet" in (cell.display or "")

    def test_replace_one_no_match_returns_false(self) -> None:
        sheet = Sheet(name="R")
        sheet.set_cell_value(0, 0, "Hello World")
        searcher = Searcher(sheet)
        state = SearchState(pattern="zzz", replace="PySheet")
        replaced = searcher.replace_one(state, 0, 0)
        assert replaced is False

    def test_replace_one_empty_cell_returns_false(self) -> None:
        sheet = Sheet(name="R")
        searcher = Searcher(sheet)
        state = SearchState(pattern="anything", replace="something")
        assert searcher.replace_one(state, 5, 5) is False


class TestReplaceAll:
    def test_replace_all_returns_correct_count(self) -> None:
        sheet = Sheet(name="R")
        sheet.set_cell_value(0, 0, "foo bar")
        sheet.set_cell_value(0, 1, "foo baz")
        sheet.set_cell_value(0, 2, "qux")
        searcher = Searcher(sheet)
        state = SearchState(pattern="foo", replace="replaced")
        count = searcher.replace_all(state)
        assert count == 2

    def test_replace_all_no_matches_returns_zero(self) -> None:
        sheet = Sheet(name="R")
        sheet.set_cell_value(0, 0, "hello")
        searcher = Searcher(sheet)
        state = SearchState(pattern="zzz", replace="nope")
        assert searcher.replace_all(state) == 0

    def test_replace_all_modifies_cells(self) -> None:
        sheet = Sheet(name="R")
        sheet.set_cell_value(0, 0, "apple")
        sheet.set_cell_value(1, 0, "apple")
        searcher = Searcher(sheet)
        state = SearchState(pattern="apple", replace="orange")
        searcher.replace_all(state)
        for r in (0, 1):
            cell = sheet.get_cell(r, 0)
            assert cell is not None
            assert "orange" in (cell.display or "")


# ---------------------------------------------------------------------------
# Formula cell search test
# ---------------------------------------------------------------------------

class TestFormulaSearch:
    def test_search_finds_formula_text(self) -> None:
        sheet = Sheet(name="F")
        sheet.set_cell_value(0, 0, "=SUM(A1:A10)", formula="=SUM(A1:A10)")
        searcher = Searcher(sheet)
        state = SearchState(pattern="SUM", case_sensitive=True)
        matches = searcher.find_all(state)
        assert (0, 0) in matches

    def test_search_formula_case_insensitive(self) -> None:
        sheet = Sheet(name="F")
        sheet.set_cell_value(0, 0, "=SUM(A1:A10)", formula="=SUM(A1:A10)")
        searcher = Searcher(sheet)
        state = SearchState(pattern="sum", case_sensitive=False)
        matches = searcher.find_all(state)
        assert (0, 0) in matches
