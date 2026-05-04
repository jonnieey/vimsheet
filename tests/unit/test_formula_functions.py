"""Unit tests for vimsheet built-in formula functions."""

import datetime

from vimsheet.formula.evaluator import Evaluator
from vimsheet.model.sheet import Sheet


def ev(formula: str, **cells) -> object:
    """Evaluate *formula* in a sheet pre-populated with *cells*."""
    sheet = Sheet(name="t")
    for addr, val in cells.items():
        from vimsheet.model.range import a1_to_rowcol

        r, c = a1_to_rowcol(addr)
        sheet.set_cell_value(r, c, val)
    evaluator = Evaluator(sheet)
    return evaluator.eval_formula(formula)


# ---------------------------------------------------------------------------
# Math functions
# ---------------------------------------------------------------------------


class TestMathFunctions:
    def test_sum(self):
        sheet = Sheet(name="t")
        for i, v in enumerate([1, 2, 3, 4, 5]):
            sheet.set_cell_value(i, 0, v)
        result = Evaluator(sheet).eval_formula("=SUM(A1:A5)")
        assert result == 15.0

    def test_sum_ignores_none(self):
        sheet = Sheet(name="t")
        sheet.set_cell_value(0, 0, 10)
        # A2 is empty
        sheet.set_cell_value(2, 0, 5)
        result = Evaluator(sheet).eval_formula("=SUM(A1:A3)")
        assert result == 15.0

    def test_average(self):
        sheet = Sheet(name="t")
        for i, v in enumerate([10, 20, 30]):
            sheet.set_cell_value(i, 0, v)
        result = Evaluator(sheet).eval_formula("=AVERAGE(A1:A3)")
        assert result == 20.0

    def test_count(self):
        sheet = Sheet(name="t")
        for i, v in enumerate([1, None, 3]):
            if v is not None:
                sheet.set_cell_value(i, 0, v)
        result = Evaluator(sheet).eval_formula("=COUNT(A1:A3)")
        assert result == 2

    def test_counta(self):
        sheet = Sheet(name="t")
        sheet.set_cell_value(0, 0, "a")
        sheet.set_cell_value(1, 0, "b")
        result = Evaluator(sheet).eval_formula("=COUNTA(A1:A3)")
        assert result == 2

    def test_min(self):
        assert ev("=MIN(3,1,2)") == 1.0

    def test_max(self):
        assert ev("=MAX(3,1,2)") == 3.0

    def test_abs_positive(self):
        assert ev("=ABS(5)") == 5.0

    def test_abs_negative(self):
        assert ev("=ABS(-5)") == 5.0

    def test_sqrt(self):
        assert ev("=SQRT(9)") == 3.0

    def test_round(self):
        assert ev("=ROUND(3.456,2)") == 3.46

    def test_floor(self):
        assert ev("=FLOOR(3.7)") == 3.0

    def test_ceil(self):
        assert ev("=CEILING(3.2)") == 4.0

    def test_mod(self):
        assert ev("=MOD(10,3)") == 1.0

    def test_power(self):
        assert ev("=POWER(2,8)") == 256.0

    def test_pi(self):
        import math

        result = ev("=PI()")
        assert abs(result - math.pi) < 1e-9

    def test_fact(self):
        assert ev("=FACT(5)") == 120.0

    def test_sumif(self):
        sheet = Sheet(name="t")
        vals = [1, 2, 3, 4, 5]
        for i, v in enumerate(vals):
            sheet.set_cell_value(i, 0, v)
        # Sum values > 3
        result = Evaluator(sheet).eval_formula('=SUMIF(A1:A5,">3")')
        assert result == 9.0

    def test_countif(self):
        sheet = Sheet(name="t")
        for i, v in enumerate([1, 2, 3, 4, 5]):
            sheet.set_cell_value(i, 0, v)
        result = Evaluator(sheet).eval_formula('=COUNTIF(A1:A5,">3")')
        assert result == 2


# ---------------------------------------------------------------------------
# Text functions
# ---------------------------------------------------------------------------


class TestTextFunctions:
    def test_len(self):
        assert ev('=LEN("hello")') == 5

    def test_upper(self):
        assert ev('=UPPER("hello")') == "HELLO"

    def test_lower(self):
        assert ev('=LOWER("WORLD")') == "world"

    def test_trim(self):
        assert ev('=TRIM("  hi  ")') == "hi"

    def test_left(self):
        assert ev('=LEFT("abcde",3)') == "abc"

    def test_right(self):
        assert ev('=RIGHT("abcde",2)') == "de"

    def test_mid(self):
        assert ev('=MID("abcde",2,3)') == "bcd"

    def test_concat(self):
        assert ev('=CONCAT("foo","bar")') == "foobar"

    def test_find(self):
        assert ev('=FIND("b","abc")') == 2

    def test_substitute(self):
        assert ev('=SUBSTITUTE("aaa","a","b")') == "bbb"

    def test_rept(self):
        assert ev('=REPT("ab",3)') == "ababab"

    def test_exact_true(self):
        assert ev('=EXACT("abc","abc")') is True

    def test_exact_false(self):
        assert ev('=EXACT("abc","ABC")') is False

    def test_value(self):
        assert ev('=VALUE("42")') == 42.0


# ---------------------------------------------------------------------------
# Logic functions
# ---------------------------------------------------------------------------


class TestLogicFunctions:
    def test_if_true(self):
        assert ev("=IF(1=1,10,20)") == 10

    def test_if_false(self):
        assert ev("=IF(1=2,10,20)") == 20

    def test_and_true(self):
        assert ev("=AND(TRUE,TRUE)") is True

    def test_and_false(self):
        assert ev("=AND(TRUE,FALSE)") is False

    def test_or_true(self):
        assert ev("=OR(FALSE,TRUE)") is True

    def test_or_false(self):
        assert ev("=OR(FALSE,FALSE)") is False

    def test_not(self):
        assert ev("=NOT(TRUE)") is False

    def test_iferror_no_error(self):
        assert ev("=IFERROR(5,99)") == 5

    def test_iferror_with_error(self):
        assert ev("=IFERROR(1/0,99)") == 99

    def test_isblank_blank(self):
        sheet = Sheet(name="t")
        assert Evaluator(sheet).eval_formula("=ISBLANK(A1)") is True

    def test_isblank_not_blank(self):
        assert ev("=ISBLANK(1)") is False

    def test_isnumber(self):
        assert ev("=ISNUMBER(42)") is True
        assert ev('=ISNUMBER("x")') is False

    def test_istext(self):
        assert ev('=ISTEXT("hi")') is True
        assert ev("=ISTEXT(1)") is False

    def test_iserror(self):
        assert ev('=ISERROR("#ERR")') is True
        assert ev("=ISERROR(1)") is False

    def test_ifs(self):
        assert ev("=IFS(FALSE,1,TRUE,2)") == 2

    def test_switch(self):
        assert ev('=SWITCH("b","a",1,"b",2,"c",3)') == 2


# ---------------------------------------------------------------------------
# Lookup functions
# ---------------------------------------------------------------------------


class TestLookupFunctions:
    def _make_table(self) -> Sheet:
        sheet = Sheet(name="t")
        data = [(1, "one"), (2, "two"), (3, "three")]
        for r, (num, word) in enumerate(data):
            sheet.set_cell_value(r, 0, num)
            sheet.set_cell_value(r, 1, word)
        return sheet

    def test_vlookup_exact(self):
        sheet = self._make_table()
        result = Evaluator(sheet).eval_formula("=VLOOKUP(2,A1:B3,2,FALSE)")
        assert result == "two"

    def test_vlookup_miss(self):
        sheet = self._make_table()
        result = Evaluator(sheet).eval_formula("=VLOOKUP(99,A1:B3,2,FALSE)")
        assert result == "#N/A"

    def test_index(self):
        sheet = self._make_table()
        result = Evaluator(sheet).eval_formula("=INDEX(A1:B3,2,1)")
        assert result == 2

    def test_match_exact(self):
        sheet = self._make_table()
        result = Evaluator(sheet).eval_formula("=MATCH(2,A1:A3,0)")
        assert result == 2

    def test_match_miss(self):
        sheet = self._make_table()
        result = Evaluator(sheet).eval_formula("=MATCH(99,A1:A3,0)")
        assert result == "#N/A"

    def test_choose(self):
        assert ev("=CHOOSE(2,10,20,30)") == 20

    def test_rows(self):
        sheet = self._make_table()
        result = Evaluator(sheet).eval_formula("=ROWS(A1:B3)")
        assert result == 3

    def test_cols(self):
        sheet = self._make_table()
        result = Evaluator(sheet).eval_formula("=COLS(A1:B3)")
        assert result == 2

    def test_xlookup(self):
        sheet = self._make_table()
        result = Evaluator(sheet).eval_formula("=XLOOKUP(3,A1:A3,B1:B3)")
        assert result == "three"


# ---------------------------------------------------------------------------
# Date functions
# ---------------------------------------------------------------------------


class TestDateFunctions:
    def test_today_is_date(self):
        sheet = Sheet(name="t")
        result = Evaluator(sheet).eval_formula("=TODAY()")
        assert isinstance(result, datetime.date)

    def test_date(self):
        sheet = Sheet(name="t")
        result = Evaluator(sheet).eval_formula("=DATE(2024,1,15)")
        assert result == datetime.date(2024, 1, 15)

    def test_year(self):
        sheet = Sheet(name="t")
        sheet.set_cell_value(0, 0, datetime.date(2024, 6, 1))
        result = Evaluator(sheet).eval_formula("=YEAR(A1)")
        assert result == 2024

    def test_month(self):
        sheet = Sheet(name="t")
        sheet.set_cell_value(0, 0, datetime.date(2024, 6, 1))
        result = Evaluator(sheet).eval_formula("=MONTH(A1)")
        assert result == 6

    def test_day(self):
        sheet = Sheet(name="t")
        sheet.set_cell_value(0, 0, datetime.date(2024, 6, 15))
        result = Evaluator(sheet).eval_formula("=DAY(A1)")
        assert result == 15

    def test_datedif_days(self):
        sheet = Sheet(name="t")
        sheet.set_cell_value(0, 0, "2024-01-01")
        sheet.set_cell_value(0, 1, "2024-01-10")
        result = Evaluator(sheet).eval_formula('=DATEDIF(A1,B1,"D")')
        assert result == 9

    def test_edate(self):
        sheet = Sheet(name="t")
        sheet.set_cell_value(0, 0, datetime.date(2024, 1, 31))
        result = Evaluator(sheet).eval_formula("=EDATE(A1,1)")
        assert result == datetime.date(2024, 2, 29)  # leap year

    def test_networkdays(self):
        sheet = Sheet(name="t")
        # Mon 2024-01-01 to Fri 2024-01-05 = 5 workdays
        sheet.set_cell_value(0, 0, "2024-01-01")
        sheet.set_cell_value(0, 1, "2024-01-05")
        result = Evaluator(sheet).eval_formula("=NETWORKDAYS(A1,B1)")
        assert result == 5
