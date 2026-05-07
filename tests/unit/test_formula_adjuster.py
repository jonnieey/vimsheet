"""Tests for vimsheet.formula.adjuster.adjust_formula."""

from __future__ import annotations

from vimsheet.formula.adjuster import adjust_formula


# Row references are SET to destination row number (dst_row + 1 in 1-based)
# When dst_row == src_row (same row), original reference row is preserved.
def test_no_offset_returns_unchanged():
    assert adjust_formula("=IF(B2>10,1,0)", 0, 0, 0, 0) == "=IF(B2>10,1,0)"


def test_row_down_one_stays_same_ref():
    """Paste one row down: ref row set to dst+1 = 2, same as original B2."""
    assert adjust_formula("=B2", 1, 0, 0, 0) == "=B2"


def test_row_down_two():
    assert adjust_formula("=B2", 2, 0, 0, 0) == "=B3"


def test_col_right_one():
    assert adjust_formula("=B2", 0, 1, 0, 0) == "=C2"


def test_col_left_one():
    assert adjust_formula("=C2", 0, -1, 0, 0) == "=B2"


def test_both_axes():
    assert adjust_formula("=B2", 2, 3, 0, 0) == "=E3"


def test_range_both_ends_adjusted():
    assert adjust_formula("=@SUM(A1:C3)", 1, 1, 0, 0) == "=@SUM(B2:D2)"


def test_absolute_row_not_adjusted():
    assert adjust_formula("=B$2", 5, 0, 0, 0) == "=B$2"


def test_absolute_col_not_adjusted():
    assert adjust_formula("=$B2", 0, 5, 0, 0) == "=$B2"


def test_fully_absolute_never_adjusted():
    assert adjust_formula("=$B$2", 10, 10, 0, 0) == "=$B$2"


def test_mixed_in_range():
    assert adjust_formula("=@SUM($A1:A$5)", 2, 2, 0, 0) == "=@SUM($A3:C$5)"


def test_string_literal_not_adjusted():
    assert adjust_formula('=IF(A1="B2","yes","no")', 1, 0, 0, 0) == '=IF(A2="B2","yes","no")'


def test_xlsx_style_d1_to_d3():
    """D1 formula pasted to D3: reference row becomes 3."""
    result = adjust_formula('=IF(B2>10,"true","false")', 2, 3, 0, 3)
    assert result == '=IF(B3>10,"true","false")'


def test_xlsx_style_d1_to_d5():
    """D1 formula pasted to D5: reference row becomes 5."""
    result = adjust_formula('=IF(B2>10,"true","false")', 4, 3, 0, 3)
    assert result == '=IF(B5>10,"true","false")'


def test_non_formula_unchanged():
    assert adjust_formula("hello", 5, 5, 0, 0) == "hello"


def test_none_unchanged():
    assert adjust_formula(None, 1, 1, 0, 0) is None


def test_cross_sheet_ref_cell_adjusted():
    result = adjust_formula("=Sheet2!B2", 1, 0, 0, 0)
    assert result == "=Sheet2!B2"


def test_cross_sheet_ref_range_adjusted():
    result = adjust_formula("=Sheet2!A1:C3", 2, 1, 0, 0)
    assert result == "=Sheet2!B3:D3"


def test_multiple_refs_in_formula():
    result = adjust_formula("=A1+B2-C3", 1, 1, 0, 0)
    assert result == "=B2+C2-D2"


def test_nested_function():
    result = adjust_formula("=@IF(@SUM(A1:A3)>B1,C1,D1)", 1, 0, 0, 0)
    assert result == "=@IF(@SUM(A2:A2)>B2,C2,D2)"
