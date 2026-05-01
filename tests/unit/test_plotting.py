"""Unit tests for pysheet.plotting.chart."""

from __future__ import annotations

import pytest

from pysheet.model.workbook import Workbook
from pysheet.plotting.chart import ChartSpec, render_chart


def make_sheet_with_data():
    wb = Workbook.blank()
    sheet = wb.active_sheet
    data = [("Month", "Sales"), ("Jan", 100), ("Feb", 150), ("Mar", 90), ("Apr", 200)]
    for r, (label, val) in enumerate(data):
        sheet.set_cell_value(r, 0, label)
        sheet.set_cell_value(r, 1, val)
    return sheet


class TestChartSpec:
    def test_defaults(self):
        spec = ChartSpec()
        assert spec.chart_type == "bar"
        assert spec.width == 60
        assert spec.height == 20
        assert spec.data_range == ""

    def test_custom_spec(self):
        spec = ChartSpec(chart_type="line", data_range="A1:B5", title="My Chart")
        assert spec.chart_type == "line"
        assert spec.title == "My Chart"


class TestRenderChart:
    def test_no_range_returns_message(self):
        sheet = make_sheet_with_data()
        spec = ChartSpec()
        result = render_chart(sheet, spec)
        assert isinstance(result, str)

    def test_renders_some_output(self):
        sheet = make_sheet_with_data()
        spec = ChartSpec(data_range="A1:B5", chart_type="bar")
        result = render_chart(sheet, spec)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_ascii_fallback(self):
        """Force ASCII fallback by using _render_ascii directly."""
        from pysheet.plotting.chart import _render_ascii
        data = [["Jan", 100], ["Feb", 150], ["Mar", 90]]
        spec = ChartSpec(chart_type="bar", width=40)
        result = _render_ascii(data, spec)
        assert "Jan" in result
        assert "█" in result

    def test_empty_range(self):
        sheet = make_sheet_with_data()
        spec = ChartSpec(data_range="Z99:Z100")  # empty range
        result = render_chart(sheet, spec)
        # Should not crash; returns some string
        assert isinstance(result, str)

    def test_single_column(self):
        sheet = make_sheet_with_data()
        spec = ChartSpec(data_range="B2:B5", chart_type="bar")
        result = render_chart(sheet, spec)
        assert isinstance(result, str)

    def test_title_included_in_ascii(self):
        from pysheet.plotting.chart import _render_ascii
        data = [["A", 1], ["B", 2]]
        spec = ChartSpec(title="My Title", width=40)
        result = _render_ascii(data, spec)
        assert "My Title" in result
