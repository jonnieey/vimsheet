"""Unit tests for pysheet.formula.evaluator.Evaluator."""

import pytest

from pysheet.formula.evaluator import (
    CIRC, DIV0, ERR, NAME, REF, TYPE_ERR, Evaluator,
)
from pysheet.model.sheet import Sheet


def make_sheet(**cells) -> Sheet:
    """Helper: create a Sheet with pre-set cell values.

    Pass keyword args like A1=10, B2="hello".
    """
    sheet = Sheet(name="test")
    for addr, val in cells.items():
        from pysheet.model.range import a1_to_rowcol
        r, c = a1_to_rowcol(addr)
        if isinstance(val, str) and val.startswith("="):
            sheet.set_cell_value(r, c, val, formula=val)
        else:
            sheet.set_cell_value(r, c, val)
    return sheet


# ---------------------------------------------------------------------------
# Literal evaluation
# ---------------------------------------------------------------------------

class TestLiterals:
    def test_number(self):
        sheet = Sheet(name="t")
        ev = Evaluator(sheet)
        assert ev.eval_formula("=42") == 42

    def test_float(self):
        sheet = Sheet(name="t")
        ev = Evaluator(sheet)
        assert ev.eval_formula("=3.5") == 3.5

    def test_string(self):
        sheet = Sheet(name="t")
        ev = Evaluator(sheet)
        assert ev.eval_formula('="hello"') == "hello"

    def test_bool_true(self):
        sheet = Sheet(name="t")
        ev = Evaluator(sheet)
        assert ev.eval_formula("=TRUE") is True

    def test_bool_false(self):
        sheet = Sheet(name="t")
        ev = Evaluator(sheet)
        assert ev.eval_formula("=FALSE") is False

    def test_percent(self):
        sheet = Sheet(name="t")
        ev = Evaluator(sheet)
        assert ev.eval_formula("=50%") == 0.5

    def test_non_formula_passthrough(self):
        sheet = Sheet(name="t")
        ev = Evaluator(sheet)
        assert ev.eval_formula("hello") == "hello"


# ---------------------------------------------------------------------------
# Cell references
# ---------------------------------------------------------------------------

class TestCellRefs:
    def test_value_cell(self):
        sheet = make_sheet(A1=10)
        ev = Evaluator(sheet)
        assert ev.eval_formula("=A1") == 10

    def test_empty_cell_is_none(self):
        sheet = Sheet(name="t")
        ev = Evaluator(sheet)
        assert ev.eval_formula("=A1") is None

    def test_formula_cell_reference(self):
        sheet = make_sheet(A1=5)
        sheet.set_cell_value(0, 1, None, formula="=A1+1")
        ev = Evaluator(sheet)
        assert ev.eval_formula("=B1") == 6

    def test_absolute_ref(self):
        sheet = make_sheet(A1=99)
        ev = Evaluator(sheet)
        assert ev.eval_formula("=$A$1") == 99


# ---------------------------------------------------------------------------
# Binary operations
# ---------------------------------------------------------------------------

class TestBinaryOps:
    def test_add(self):
        sheet = Sheet(name="t")
        ev = Evaluator(sheet)
        assert ev.eval_formula("=2+3") == 5.0

    def test_sub(self):
        sheet = Sheet(name="t")
        ev = Evaluator(sheet)
        assert ev.eval_formula("=10-4") == 6.0

    def test_mul(self):
        sheet = Sheet(name="t")
        ev = Evaluator(sheet)
        assert ev.eval_formula("=3*4") == 12.0

    def test_div(self):
        sheet = Sheet(name="t")
        ev = Evaluator(sheet)
        assert ev.eval_formula("=10/4") == 2.5

    def test_div_zero(self):
        sheet = Sheet(name="t")
        ev = Evaluator(sheet)
        assert ev.eval_formula("=1/0") == DIV0

    def test_power(self):
        sheet = Sheet(name="t")
        ev = Evaluator(sheet)
        assert ev.eval_formula("=2^10") == 1024.0

    def test_string_concat(self):
        sheet = Sheet(name="t")
        ev = Evaluator(sheet)
        assert ev.eval_formula('="hello"&" world"') == "hello world"

    def test_eq_true(self):
        sheet = Sheet(name="t")
        ev = Evaluator(sheet)
        assert ev.eval_formula("=1=1") is True

    def test_eq_false(self):
        sheet = Sheet(name="t")
        ev = Evaluator(sheet)
        assert ev.eval_formula("=1=2") is False

    def test_ne(self):
        sheet = Sheet(name="t")
        ev = Evaluator(sheet)
        assert ev.eval_formula("=1<>2") is True

    def test_lt(self):
        sheet = Sheet(name="t")
        ev = Evaluator(sheet)
        assert ev.eval_formula("=1<2") is True

    def test_ge(self):
        sheet = Sheet(name="t")
        ev = Evaluator(sheet)
        assert ev.eval_formula("=2>=2") is True


# ---------------------------------------------------------------------------
# Error propagation
# ---------------------------------------------------------------------------

class TestErrors:
    def test_div0_propagates(self):
        sheet = make_sheet(A1=0)
        ev = Evaluator(sheet)
        result = ev.eval_formula("=1/A1+5")
        assert result == DIV0

    def test_type_error(self):
        sheet = Sheet(name="t")
        ev = Evaluator(sheet)
        result = ev.eval_formula('="x"+1')
        assert result == TYPE_ERR

    def test_name_error_for_unknown_func(self):
        sheet = Sheet(name="t")
        ev = Evaluator(sheet)
        assert ev.eval_formula("=NOTAFUNC(1)") == NAME


# ---------------------------------------------------------------------------
# Circular reference detection
# ---------------------------------------------------------------------------

class TestCircular:
    def test_self_reference(self):
        sheet = Sheet(name="t")
        from pysheet.model.range import a1_to_rowcol
        r, c = a1_to_rowcol("A1")
        sheet.cells[(r, c)] = __import__(
            "pysheet.model.cell", fromlist=["Cell"]
        ).Cell(row=r, col=c, formula="=A1")
        ev = Evaluator(sheet)
        result = ev.eval_formula("=A1")
        assert result == CIRC


# ---------------------------------------------------------------------------
# Dependency collection
# ---------------------------------------------------------------------------

class TestCollectDeps:
    def test_single_ref(self):
        sheet = Sheet(name="t")
        ev = Evaluator(sheet)
        deps = ev.collect_deps("=A1")
        from pysheet.model.range import a1_to_rowcol
        assert a1_to_rowcol("A1") in deps

    def test_range_ref(self):
        sheet = Sheet(name="t")
        ev = Evaluator(sheet)
        deps = ev.collect_deps("=SUM(A1:A3)")
        from pysheet.model.range import a1_to_rowcol
        assert a1_to_rowcol("A1") in deps
        assert a1_to_rowcol("A2") in deps
        assert a1_to_rowcol("A3") in deps

    def test_no_deps_for_literal(self):
        sheet = Sheet(name="t")
        ev = Evaluator(sheet)
        assert ev.collect_deps("=42") == set()

    def test_non_formula_returns_empty(self):
        sheet = Sheet(name="t")
        ev = Evaluator(sheet)
        assert ev.collect_deps("hello") == set()


# ---------------------------------------------------------------------------
# Sheet-level auto-recalculation
# ---------------------------------------------------------------------------

class TestSheetRecalc:
    def test_formula_evaluates_on_set(self):
        sheet = Sheet(name="t")
        sheet.set_cell_value(0, 0, 10)           # A1 = 10
        sheet.set_cell_value(0, 1, None, formula="=A1*2")  # B1 = =A1*2
        b1 = sheet.get_cell(0, 1)
        assert b1.value == 20.0

    def test_dependent_recalculates_on_change(self):
        sheet = Sheet(name="t")
        sheet.set_cell_value(0, 0, 5)
        sheet.set_cell_value(0, 1, None, formula="=A1+1")
        sheet.set_cell_value(0, 0, 10)  # change A1
        b1 = sheet.get_cell(0, 1)
        assert b1.value == 11.0

    def test_chain_recalculates(self):
        sheet = Sheet(name="t")
        sheet.set_cell_value(0, 0, 1)            # A1=1
        sheet.set_cell_value(0, 1, None, formula="=A1+1")   # B1=A1+1
        sheet.set_cell_value(0, 2, None, formula="=B1+1")   # C1=B1+1
        sheet.set_cell_value(0, 0, 10)           # change A1
        assert sheet.get_cell(0, 1).value == 11.0
        assert sheet.get_cell(0, 2).value == 12.0

    def test_clear_cell_triggers_recalc(self):
        sheet = Sheet(name="t")
        sheet.set_cell_value(0, 0, 5)
        sheet.set_cell_value(0, 1, None, formula="=A1+1")
        sheet.clear_cell(0, 0)
        b1 = sheet.get_cell(0, 1)
        # A1 is now None, so =A1+1 should be TYPE_ERR or similar
        assert b1 is not None
        assert b1.value != 6.0
