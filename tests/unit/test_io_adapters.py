"""Unit tests for I/O adapters."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from pysheet.model.sheet import Sheet
from pysheet.model.workbook import Workbook


def make_workbook() -> Workbook:  # noqa: D401
    wb = Workbook.blank()
    sheet = wb.active_sheet
    sheet.set_cell_value(0, 0, "Name")
    sheet.set_cell_value(0, 1, "Score")
    sheet.set_cell_value(1, 0, "Alice")
    sheet.set_cell_value(1, 1, 95)
    sheet.set_cell_value(2, 0, "Bob")
    sheet.set_cell_value(2, 1, 87)
    return wb


# ---------------------------------------------------------------------------
# CSV adapter
# ---------------------------------------------------------------------------

class TestCSVAdapter:
    def test_write_then_read(self, tmp_path: Path):
        from pysheet.io.csv_adapter import CSVAdapter
        wb = make_workbook()
        path = tmp_path / "test.csv"
        CSVAdapter().write(wb, path)
        wb2 = CSVAdapter().read(path)
        sheet = wb2.active_sheet
        assert sheet.get_cell(0, 0).value == "Name"
        assert sheet.get_cell(1, 1).value == 95

    def test_empty_sheet(self, tmp_path: Path):
        from pysheet.io.csv_adapter import CSVAdapter
        wb = Workbook.blank()  # one sheet, no cells
        path = tmp_path / "empty.csv"
        CSVAdapter().write(wb, path)
        assert path.read_text() == ""

    def test_tsv(self, tmp_path: Path):
        from pysheet.io.csv_adapter import CSVAdapter
        wb = make_workbook()
        path = tmp_path / "test.tsv"
        CSVAdapter().write(wb, path, delimiter="\t")
        content = path.read_text()
        assert "\t" in content


# ---------------------------------------------------------------------------
# JSON adapter
# ---------------------------------------------------------------------------

class TestJSONAdapter:
    def test_write_then_read(self, tmp_path: Path):
        from pysheet.io.json_adapter import JSONAdapter
        wb = make_workbook()
        path = tmp_path / "test.pysheet"
        JSONAdapter().write(wb, path)
        wb2 = JSONAdapter().read(path)
        sheet = wb2.active_sheet
        assert sheet.get_cell(0, 0).value == "Name"
        assert sheet.get_cell(1, 1).value == 95

    def test_formula_preserved(self, tmp_path: Path):
        from pysheet.io.json_adapter import JSONAdapter
        wb = Workbook.blank()
        sheet = wb.active_sheet
        sheet.set_cell_value(0, 0, 10)
        sheet.set_cell_value(0, 1, 20)
        sheet.set_cell_value(0, 2, None, formula="=A1+B1")
        path = tmp_path / "formulas.pysheet"
        JSONAdapter().write(wb, path)
        wb2 = JSONAdapter().read(path)
        c1 = wb2.active_sheet.get_cell(0, 2)
        assert c1 is not None
        assert c1.formula == "=A1+B1"
        assert c1.value == 30.0

    def test_multi_sheet(self, tmp_path: Path):
        from pysheet.io.json_adapter import JSONAdapter
        wb = Workbook.blank()
        wb.add_sheet("Sheet2")
        wb.sheets[1].set_cell_value(0, 0, "second")
        path = tmp_path / "multi.pysheet"
        JSONAdapter().write(wb, path)
        wb2 = JSONAdapter().read(path)
        assert len(wb2.sheets) == 2
        assert wb2.sheets[1].get_cell(0, 0).value == "second"

    def test_valid_json_structure(self, tmp_path: Path):
        from pysheet.io.json_adapter import JSONAdapter
        wb = make_workbook()
        path = tmp_path / "test.pysheet"
        JSONAdapter().write(wb, path)
        data = json.loads(path.read_text())
        assert "sheets" in data
        assert "version" in data
        assert data["version"] == 1

    def test_format_preserved(self, tmp_path: Path):
        from pysheet.io.json_adapter import JSONAdapter
        wb = Workbook.blank()
        sheet = wb.active_sheet
        sheet.set_cell_value(0, 0, "bold text")
        cell = sheet.get_cell(0, 0)
        cell.fmt.bold = True
        cell.fmt.align = "center"
        path = tmp_path / "fmt.pysheet"
        JSONAdapter().write(wb, path)
        wb2 = JSONAdapter().read(path)
        c = wb2.active_sheet.get_cell(0, 0)
        assert c.fmt.bold is True
        assert c.fmt.align == "center"


# ---------------------------------------------------------------------------
# XLSX adapter
# ---------------------------------------------------------------------------

class TestXLSXAdapter:
    def test_write_then_read(self, tmp_path: Path):
        from pysheet.io.xlsx_adapter import XLSXAdapter
        wb = make_workbook()
        path = tmp_path / "test.xlsx"
        XLSXAdapter().write(wb, path)
        wb2 = XLSXAdapter().read(path)
        sheet = wb2.active_sheet
        assert sheet.get_cell(0, 0).value == "Name"
        assert sheet.get_cell(1, 1).value == 95

    def test_multi_sheet(self, tmp_path: Path):
        from pysheet.io.xlsx_adapter import XLSXAdapter
        wb = Workbook.blank()
        wb.add_sheet("Sheet2")
        wb.sheets[1].set_cell_value(0, 0, "hello")
        path = tmp_path / "multi.xlsx"
        XLSXAdapter().write(wb, path)
        wb2 = XLSXAdapter().read(path)
        assert len(wb2.sheets) == 2


# ---------------------------------------------------------------------------
# Markdown adapter
# ---------------------------------------------------------------------------

class TestMarkdownAdapter:
    def test_write_produces_table(self, tmp_path: Path):
        from pysheet.io.markdown_adapter import MarkdownAdapter
        wb = make_workbook()
        path = tmp_path / "test.md"
        MarkdownAdapter().write(wb, path)
        content = path.read_text()
        assert "Name" in content
        assert "Score" in content
        assert "|" in content
        assert "---" in content

    def test_read_raises(self, tmp_path: Path):
        from pysheet.io.markdown_adapter import MarkdownAdapter
        path = tmp_path / "test.md"
        path.write_text("| a | b |\n|---|---|\n")
        with pytest.raises(NotImplementedError):
            MarkdownAdapter().read(path)

    def test_empty_sheet(self, tmp_path: Path):
        from pysheet.io.markdown_adapter import MarkdownAdapter
        wb = Workbook.blank()
        path = tmp_path / "empty.md"
        MarkdownAdapter().write(wb, path)
        assert path.read_text() == ""


# ---------------------------------------------------------------------------
# HTML adapter
# ---------------------------------------------------------------------------

class TestHTMLAdapter:
    def test_write_produces_html(self, tmp_path: Path):
        from pysheet.io.html_adapter import HTMLAdapter
        wb = make_workbook()
        path = tmp_path / "test.html"
        HTMLAdapter().write(wb, path)
        content = path.read_text()
        assert "<table" in content
        assert "Name" in content
        assert "Alice" in content

    def test_read_raises(self, tmp_path: Path):
        from pysheet.io.html_adapter import HTMLAdapter
        path = tmp_path / "test.html"
        path.write_text("<html></html>")
        with pytest.raises(NotImplementedError):
            HTMLAdapter().read(path)


# ---------------------------------------------------------------------------
# Adapter registry
# ---------------------------------------------------------------------------

class TestAdapterRegistry:
    def test_csv(self):
        from pysheet.io.registry import get_adapter
        a = get_adapter(Path("data.csv"))
        from pysheet.io.csv_adapter import CSVAdapter
        assert isinstance(a, CSVAdapter)

    def test_json(self):
        from pysheet.io.registry import get_adapter
        a = get_adapter(Path("data.pysheet"))
        from pysheet.io.json_adapter import JSONAdapter
        assert isinstance(a, JSONAdapter)

    def test_xlsx(self):
        from pysheet.io.registry import get_adapter
        a = get_adapter(Path("data.xlsx"))
        from pysheet.io.xlsx_adapter import XLSXAdapter
        assert isinstance(a, XLSXAdapter)

    def test_unknown_raises(self):
        from pysheet.io.registry import get_adapter
        with pytest.raises(ValueError):
            get_adapter(Path("data.xyz123"))
