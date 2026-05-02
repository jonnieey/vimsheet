"""Unit tests for pysheet.scripting.engine.ScriptEngine."""

from __future__ import annotations

from pysheet.model.workbook import Workbook
from pysheet.scripting.engine import ScriptEngine


def make_engine(script: str = "", file: str | None = None) -> ScriptEngine:
    wb = Workbook.blank()
    engine = ScriptEngine(workbook=wb)
    if script:
        engine.run_string(script)
    return engine


# ---------------------------------------------------------------------------
# Basic set / formula
# ---------------------------------------------------------------------------


class TestSetCommand:
    def test_set_number(self):
        engine = make_engine("set A1 = 42")
        cell = engine.workbook.active_sheet.get_cell(0, 0)
        assert cell is not None
        assert cell.value == 42

    def test_set_string(self):
        engine = make_engine("set B2 = Hello World")
        cell = engine.workbook.active_sheet.get_cell(1, 1)
        assert cell.value == "Hello World"

    def test_set_without_equals_sign(self):
        engine = make_engine("set A1 99")
        cell = engine.workbook.active_sheet.get_cell(0, 0)
        assert cell.value == 99

    def test_set_float(self):
        engine = make_engine("set A1 = 3.14")
        cell = engine.workbook.active_sheet.get_cell(0, 0)
        assert abs(cell.value - 3.14) < 1e-9


class TestFormulaCommand:
    def test_formula_evaluated(self):
        script = "set A1 = 10\nset B1 = 20\nformula C1 = =A1+B1"
        engine = make_engine(script)
        c1 = engine.workbook.active_sheet.get_cell(0, 2)
        assert c1 is not None
        assert c1.formula == "=A1+B1"
        assert c1.value == 30.0

    def test_formula_without_leading_equals(self):
        script = "set A1 = 5\nformula B1 = A1*2"
        engine = make_engine(script)
        b1 = engine.workbook.active_sheet.get_cell(0, 1)
        assert b1.formula == "=A1*2"
        assert b1.value == 10.0


# ---------------------------------------------------------------------------
# Clear
# ---------------------------------------------------------------------------


class TestClearCommand:
    def test_clear_cell(self):
        script = "set A1 = 99\nclear A1"
        engine = make_engine(script)
        assert engine.workbook.active_sheet.get_cell(0, 0) is None

    def test_clear_range(self):
        script = "set A1 = 1\nset B1 = 2\nclear A1:B1"
        engine = make_engine(script)
        assert engine.workbook.active_sheet.get_cell(0, 0) is None
        assert engine.workbook.active_sheet.get_cell(0, 1) is None


# ---------------------------------------------------------------------------
# Format
# ---------------------------------------------------------------------------


class TestFormatCommand:
    def test_bold(self):
        script = "set A1 = hi\nformat A1 bold=true"
        engine = make_engine(script)
        cell = engine.workbook.active_sheet.get_cell(0, 0)
        assert cell.fmt.bold is True

    def test_align(self):
        script = "set A1 = hi\nformat A1 align=center"
        engine = make_engine(script)
        cell = engine.workbook.active_sheet.get_cell(0, 0)
        assert cell.fmt.align == "center"


# ---------------------------------------------------------------------------
# Sheet management
# ---------------------------------------------------------------------------


class TestSheetCommands:
    def test_addsheet(self):
        engine = make_engine("addsheet Sales")
        assert len(engine.workbook.sheets) == 2
        assert engine.workbook.sheets[1].name == "Sales"

    def test_renamesheet(self):
        engine = make_engine("renamesheet Sheet1 Data")
        assert engine.workbook.sheets[0].name == "Data"

    def test_sheet_switch(self):
        script = "addsheet Sheet2\nsheet Sheet2\nset A1 = hello"
        engine = make_engine(script)
        # Should have set A1 in Sheet2
        assert engine.workbook.active_sheet.name == "Sheet2"
        assert engine.workbook.sheets[1].get_cell(0, 0).value == "hello"

    def test_delsheet(self):
        script = "addsheet Sheet2\ndelsheet Sheet2"
        engine = make_engine(script)
        assert len(engine.workbook.sheets) == 1


# ---------------------------------------------------------------------------
# Column width / autofit
# ---------------------------------------------------------------------------


class TestColWidthCommands:
    def test_colwidth(self):
        engine = make_engine("colwidth A 20")
        assert engine.workbook.active_sheet.get_col_width(0) == 20

    def test_colwidth_by_number(self):
        engine = make_engine("colwidth 2 15")
        assert engine.workbook.active_sheet.get_col_width(1) == 15

    def test_autofit(self):
        script = "set A1 = A very long value\nautofit A"
        engine = make_engine(script)
        w = engine.workbook.active_sheet.get_col_width(0)
        assert w > 10  # auto-fit should widen it


# ---------------------------------------------------------------------------
# Sort
# ---------------------------------------------------------------------------


class TestSortCommand:
    def test_sort_asc(self):
        script = "set A1 = 3\nset A2 = 1\nset A3 = 2\nsort 1 asc"
        engine = make_engine(script)
        sheet = engine.workbook.active_sheet
        vals = [sheet.get_cell(r, 0).value for r in range(3)]
        assert vals == [1, 2, 3]

    def test_sort_desc(self):
        script = "set A1 = 1\nset A2 = 3\nset A3 = 2\nsort 1 desc"
        engine = make_engine(script)
        sheet = engine.workbook.active_sheet
        vals = [sheet.get_cell(r, 0).value for r in range(3)]
        assert vals == [3, 2, 1]


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrors:
    def test_unknown_command(self):
        engine = ScriptEngine()
        result = engine.run_string("badcmd arg")
        assert not result.ok
        assert "Unknown command" in result.errors[0]

    def test_errors_collected_not_raised(self):
        script = "badcmd\nset A1 = 5"
        engine = ScriptEngine()
        result = engine.run_string(script)
        assert result.commands_run == 1  # set A1 = 5 still ran
        assert len(result.errors) == 1

    def test_comments_skipped(self):
        engine = ScriptEngine()
        result = engine.run_string("# this is a comment\n# another comment")
        assert result.commands_run == 0
        assert result.ok

    def test_empty_lines_skipped(self):
        engine = ScriptEngine()
        result = engine.run_string("\n\n\n")
        assert result.commands_run == 0
        assert result.ok


# ---------------------------------------------------------------------------
# File save / open
# ---------------------------------------------------------------------------


class TestFileCommands:
    def test_save_and_open_csv(self, tmp_path):
        path = tmp_path / "out.csv"
        script = f"set A1 = 10\nset B1 = 20\nsave {path}"
        make_engine(script)
        assert path.exists()

        engine2 = ScriptEngine()
        result = engine2.run_string(f"open {path}")
        assert result.ok
        cell = engine2.workbook.active_sheet.get_cell(0, 0)
        assert cell is not None
        assert cell.value == 10


# ---------------------------------------------------------------------------
# New sheet-level commands
# ---------------------------------------------------------------------------


class TestSheetCommands2:
    def test_hiderow_showrow(self):
        engine = make_engine("set A1 = x")
        engine.run_string("hiderow 1")
        assert 0 in engine.workbook.active_sheet.hidden_rows
        engine.run_string("showrow 1")
        assert 0 not in engine.workbook.active_sheet.hidden_rows

    def test_hidecol_showcol(self):
        engine = make_engine("set A1 = x")
        engine.run_string("hidecol A")
        assert 0 in engine.workbook.active_sheet.hidden_cols
        engine.run_string("showcol A")
        assert 0 not in engine.workbook.active_sheet.hidden_cols

    def test_freeze_unfreeze(self):
        engine = make_engine()
        engine.run_string("freeze 2 1")
        assert engine.workbook.active_sheet.freeze_rows == 2
        assert engine.workbook.active_sheet.freeze_cols == 1
        engine.run_string("unfreeze")
        assert engine.workbook.active_sheet.freeze_rows == 0
        assert engine.workbook.active_sheet.freeze_cols == 0

    def test_comment(self):
        engine = make_engine("set A1 = hello")
        engine.run_string("comment A1 This is a note")
        cell = engine.workbook.active_sheet.get_cell(0, 0)
        assert cell is not None
        assert cell.comment == "This is a note"

    def test_name_range(self):
        engine = make_engine()
        engine.run_string("name TOTAL A1:A10")
        resolved = engine.workbook.active_sheet.named_ranges.resolve("TOTAL")
        assert resolved == "A1:A10"
