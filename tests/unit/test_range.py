"""Unit tests for vimsheet.model.range."""

from __future__ import annotations

import pytest

from vimsheet.model.range import (
    CellRange,
    NamedRangeRegistry,
    a1_to_rowcol,
    col_index_to_letters,
    col_letters_to_index,
    rowcol_to_a1,
)

# ---------------------------------------------------------------------------
# col_letters_to_index
# ---------------------------------------------------------------------------


class TestColLettersToIndex:
    def test_a(self) -> None:
        assert col_letters_to_index("A") == 0

    def test_z(self) -> None:
        assert col_letters_to_index("Z") == 25

    def test_aa(self) -> None:
        assert col_letters_to_index("AA") == 26

    def test_ab(self) -> None:
        assert col_letters_to_index("AB") == 27

    def test_az(self) -> None:
        assert col_letters_to_index("AZ") == 51

    def test_ba(self) -> None:
        assert col_letters_to_index("BA") == 52

    def test_zz(self) -> None:
        assert col_letters_to_index("ZZ") == 701

    def test_lowercase(self) -> None:
        assert col_letters_to_index("a") == 0
        assert col_letters_to_index("aa") == 26


# ---------------------------------------------------------------------------
# col_index_to_letters
# ---------------------------------------------------------------------------


class TestColIndexToLetters:
    def test_zero(self) -> None:
        assert col_index_to_letters(0) == "A"

    def test_25(self) -> None:
        assert col_index_to_letters(25) == "Z"

    def test_26(self) -> None:
        assert col_index_to_letters(26) == "AA"

    def test_27(self) -> None:
        assert col_index_to_letters(27) == "AB"

    def test_701(self) -> None:
        assert col_index_to_letters(701) == "ZZ"

    def test_roundtrip(self) -> None:
        for i in [0, 1, 25, 26, 27, 51, 52, 100, 701]:
            assert col_letters_to_index(col_index_to_letters(i)) == i


# ---------------------------------------------------------------------------
# a1_to_rowcol
# ---------------------------------------------------------------------------


class TestA1ToRowcol:
    def test_a1(self) -> None:
        assert a1_to_rowcol("A1") == (0, 0)

    def test_b3(self) -> None:
        assert a1_to_rowcol("B3") == (2, 1)

    def test_z26(self) -> None:
        assert a1_to_rowcol("Z26") == (25, 25)

    def test_absolute_refs(self) -> None:
        assert a1_to_rowcol("$A$1") == (0, 0)
        assert a1_to_rowcol("$C$5") == (4, 2)

    def test_mixed_refs(self) -> None:
        assert a1_to_rowcol("$B3") == (2, 1)
        assert a1_to_rowcol("B$3") == (2, 1)

    def test_large_column(self) -> None:
        r, c = a1_to_rowcol("AA1")
        assert r == 0
        assert c == 26

    def test_invalid_raises(self) -> None:
        with pytest.raises(ValueError):
            a1_to_rowcol("1A")
        with pytest.raises(ValueError):
            a1_to_rowcol("")
        with pytest.raises(ValueError):
            a1_to_rowcol("A")


# ---------------------------------------------------------------------------
# rowcol_to_a1
# ---------------------------------------------------------------------------


class TestRowcolToA1:
    def test_origin(self) -> None:
        assert rowcol_to_a1(0, 0) == "A1"

    def test_b3(self) -> None:
        assert rowcol_to_a1(2, 1) == "B3"

    def test_roundtrip(self) -> None:
        for r, c in [(0, 0), (5, 3), (99, 25), (0, 26)]:
            assert a1_to_rowcol(rowcol_to_a1(r, c)) == (r, c)


# ---------------------------------------------------------------------------
# CellRange
# ---------------------------------------------------------------------------


class TestCellRange:
    def test_single_cell(self) -> None:
        cr = CellRange.from_a1("A1")
        assert cr.start_row == 0
        assert cr.start_col == 0
        assert cr.end_row == 0
        assert cr.end_col == 0

    def test_range_a1_b5(self) -> None:
        cr = CellRange.from_a1("A1:B5")
        assert cr.start_row == 0
        assert cr.start_col == 0
        assert cr.end_row == 4
        assert cr.end_col == 1

    def test_range_normalises_reversed(self) -> None:
        cr = CellRange.from_a1("B5:A1")
        assert cr.start_row == 0
        assert cr.start_col == 0
        assert cr.end_row == 4
        assert cr.end_col == 1

    def test_num_rows(self) -> None:
        assert CellRange.from_a1("A1:A5").num_rows == 5

    def test_num_cols(self) -> None:
        assert CellRange.from_a1("A1:E1").num_cols == 5

    def test_single_cell_num_rows_cols(self) -> None:
        cr = CellRange.from_a1("C3")
        assert cr.num_rows == 1
        assert cr.num_cols == 1

    def test_iter_cells_single(self) -> None:
        cells = list(CellRange.from_a1("B2").iter_cells())
        assert cells == [(1, 1)]

    def test_iter_cells_range(self) -> None:
        cells = list(CellRange.from_a1("A1:B2").iter_cells())
        assert cells == [(0, 0), (0, 1), (1, 0), (1, 1)]

    def test_contains_inside(self) -> None:
        cr = CellRange.from_a1("A1:C3")
        assert cr.contains(1, 1)
        assert cr.contains(0, 0)
        assert cr.contains(2, 2)

    def test_contains_outside(self) -> None:
        cr = CellRange.from_a1("A1:C3")
        assert not cr.contains(3, 0)
        assert not cr.contains(0, 3)

    def test_to_a1_single(self) -> None:
        assert CellRange.from_a1("A1").to_a1() == "A1"

    def test_to_a1_range(self) -> None:
        assert CellRange.from_a1("A1:B5").to_a1() == "A1:B5"

    def test_invalid_range_raises(self) -> None:
        with pytest.raises(ValueError):
            CellRange.from_a1("notarange")

    def test_direct_construction_invalid_raises(self) -> None:
        with pytest.raises(ValueError):
            CellRange(start_row=5, start_col=0, end_row=2, end_col=0)

    def test_absolute_refs_in_range(self) -> None:
        cr = CellRange.from_a1("$A$1:$C$3")
        assert cr.start_row == 0
        assert cr.end_row == 2
        assert cr.start_col == 0
        assert cr.end_col == 2


# ---------------------------------------------------------------------------
# NamedRangeRegistry
# ---------------------------------------------------------------------------


class TestNamedRangeRegistry:
    def test_define_and_resolve(self) -> None:
        reg = NamedRangeRegistry()
        reg.define("profit", "B2:B50")
        assert reg.resolve("PROFIT") == "B2:B50"

    def test_resolve_case_insensitive(self) -> None:
        reg = NamedRangeRegistry()
        reg.define("Total", "D1")
        assert reg.resolve("total") == "D1"
        assert reg.resolve("TOTAL") == "D1"

    def test_resolve_unknown_returns_none(self) -> None:
        reg = NamedRangeRegistry()
        assert reg.resolve("NOPE") is None

    def test_define_updates_existing(self) -> None:
        reg = NamedRangeRegistry()
        reg.define("x", "A1")
        reg.define("x", "A2")
        assert reg.resolve("X") == "A2"

    def test_delete(self) -> None:
        reg = NamedRangeRegistry()
        reg.define("x", "A1")
        reg.delete("x")
        assert reg.resolve("X") is None

    def test_delete_missing_raises(self) -> None:
        reg = NamedRangeRegistry()
        with pytest.raises(KeyError):
            reg.delete("missing")

    def test_all_names_sorted(self) -> None:
        reg = NamedRangeRegistry()
        reg.define("b", "B1")
        reg.define("a", "A1")
        reg.define("c", "C1")
        assert reg.all_names() == ["A", "B", "C"]

    def test_contains(self) -> None:
        reg = NamedRangeRegistry()
        reg.define("total", "A1:A10")
        assert "TOTAL" in reg
        assert "total" in reg
        assert "other" not in reg

    def test_define_invalid_range_raises(self) -> None:
        reg = NamedRangeRegistry()
        with pytest.raises(ValueError):
            reg.define("bad", "notarange")
