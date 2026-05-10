"""Unit tests for pipeline / scripting CLI mode."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from vimsheet.model.workbook import Workbook
from vimsheet.scripting.engine import ScriptEngine

# ---------------------------------------------------------------------------
# ScriptEngine.run_file
# ---------------------------------------------------------------------------


class TestRunFile:
    def test_run_script_file(self, tmp_path: Path):
        script = tmp_path / "test.vsheet"
        script.write_text("set A1 = 10\nset B1 = 20\n")
        engine = ScriptEngine()
        result = engine.run_file(script)
        assert result.ok
        assert result.commands_run == 2
        assert engine.workbook.active_sheet.get_cell(0, 0).value == 10

    def test_script_file_with_comments(self, tmp_path: Path):
        script = tmp_path / "test.vsheet"
        script.write_text("# header\nset A1 = 5\n# done\n")
        engine = ScriptEngine()
        result = engine.run_file(script)
        assert result.ok
        assert result.commands_run == 1

    def test_script_saves_output(self, tmp_path: Path):
        out = tmp_path / "result.csv"
        script = tmp_path / "test.vsheet"
        script.write_text(f"set A1 = hello\nsave {out}\n")
        engine = ScriptEngine()
        result = engine.run_file(script)
        assert result.ok
        assert out.exists()
        assert "hello" in out.read_text()


# ---------------------------------------------------------------------------
# Pipeline round-trip: script → save → load → verify
# ---------------------------------------------------------------------------


class TestRoundTrip:
    def test_csv_round_trip(self, tmp_path: Path):
        engine = ScriptEngine()
        engine.run_string("set A1 = 100\nset B1 = 200")
        out = tmp_path / "data.csv"
        engine.run_string(f"save {out}")
        engine2 = ScriptEngine()
        engine2.run_string(f"open {out}")
        assert engine2.workbook.active_sheet.get_cell(0, 0).value == 100

    def test_json_round_trip(self, tmp_path: Path):
        engine = ScriptEngine()
        engine.run_string("set A1 = 42\nset B1 = hello")
        out = tmp_path / "data.vimsheet"
        engine.run_string(f"save {out}")
        engine2 = ScriptEngine()
        engine2.run_string(f"open {out}")
        assert engine2.workbook.active_sheet.get_cell(0, 0).value == 42
        assert engine2.workbook.active_sheet.get_cell(0, 1).value == "hello"

    def test_formula_preserved_in_json(self, tmp_path: Path):
        engine = ScriptEngine()
        engine.run_string("set A1 = 5\nset B1 = 10\nformula C1 =A1+B1")
        out = tmp_path / "formulas.vimsheet"
        engine.run_string(f"save {out}")
        engine2 = ScriptEngine()
        engine2.run_string(f"open {out}")
        c1 = engine2.workbook.active_sheet.get_cell(0, 2)
        assert c1 is not None
        assert c1.formula == "=A1+B1"
        assert c1.value == 15.0


# ---------------------------------------------------------------------------
# Diff helper (imported from __main__)
# ---------------------------------------------------------------------------


class TestDiff:
    def test_identical_files_no_diff(self, tmp_path: Path, capsys):
        from vimsheet.io.csv_adapter import CSVAdapter

        wb = Workbook.blank()
        wb.active_sheet.set_cell_value(0, 0, "hello")
        path = tmp_path / "a.csv"
        CSVAdapter().write(wb, path)

        # Diff identical files
        sys.argv = ["vimsheet", "--diff", str(path), str(path)]
        from vimsheet.__main__ import _run_diff

        _run_diff(str(path), str(path))
        out = capsys.readouterr().out
        assert "0 difference(s)" in out

    def test_different_files_finds_changes(self, tmp_path: Path, capsys):
        from vimsheet.io.csv_adapter import CSVAdapter

        wb_a = Workbook.blank()
        wb_a.active_sheet.set_cell_value(0, 0, "hello")
        path_a = tmp_path / "a.csv"
        CSVAdapter().write(wb_a, path_a)

        wb_b = Workbook.blank()
        wb_b.active_sheet.set_cell_value(0, 0, "world")
        path_b = tmp_path / "b.csv"
        CSVAdapter().write(wb_b, path_b)

        from vimsheet.__main__ import _run_diff

        with pytest.raises(SystemExit) as exc_info:
            _run_diff(str(path_a), str(path_b))
        assert exc_info.value.code == 1
        out = capsys.readouterr().out
        assert "1 difference(s)" in out
        assert "CHANGED" in out


# ---------------------------------------------------------------------------
# Print command
# ---------------------------------------------------------------------------


class TestPrintCommand:
    def test_print_cell(self, capsys):
        engine = ScriptEngine()
        engine.run_string("set A1 = hello\nprint A1")
        captured = capsys.readouterr()
        assert "hello" in captured.out

    def test_print_range(self, capsys):
        engine = ScriptEngine()
        engine.run_string("set A1 = 1\nset B1 = 2\nprint A1:B1")
        captured = capsys.readouterr()
        assert "1" in captured.out
        assert "2" in captured.out

    def test_print_all(self, capsys):
        engine = ScriptEngine()
        engine.run_string("set A1 = row1\nset A2 = row2")
        engine.run_string("print")
        captured = capsys.readouterr()
        assert "row1" in captured.out
        assert "row2" in captured.out
