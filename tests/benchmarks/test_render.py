"""Rendering performance benchmarks.

Measures frame render time, cursor movement latency, selection rendering,
and viewport redraw cost.
"""

from __future__ import annotations

import pytest
from textual.geometry import Offset, Region

from vimsheet.model.sheet import Sheet
from vimsheet.model.workbook import Workbook
from vimsheet.ui.grid import GridWidget

from .conftest import (
    measure,
    populate_numbers,
    result_json,
)

# Render benchmarks use fixed scales (skip large/sparse which are too slow)
_RENDER_SCALES = {"tiny": (100, 10), "small": (1000, 26), "medium": (10000, 26)}


def _make_grid(sheet: Sheet) -> GridWidget:
    """Create a GridWidget backed by a Workbook with *sheet*."""
    from vimsheet.model.config import Config

    wb = Workbook()
    wb.sheets.append(sheet)
    gw = GridWidget(workbook=wb, config=Config())
    # Bypass the read-only size property by setting content_region
    object.__setattr__(gw, "_content_region", Region(0, 0, 120, 50))
    object.__setattr__(gw, "_scroll_offset", Offset(0, 0))
    return gw


@pytest.mark.benchmark
class TestRenderPerformance:
    """Grid rendering micro-benchmarks."""

    @pytest.fixture
    def sheet(self) -> Sheet:
        s = Sheet(name="Render")
        populate_numbers(s, 1000, 26)
        return s

    def test_render_header_row(self, sheet: Sheet) -> None:
        """Time to render the frozen header row."""
        gw = _make_grid(sheet)

        def render_header() -> None:
            gw._render_header_row(0, 10)

        stats = measure(render_header, iterations=500, label="render_header")
        result = result_json(
            "render.header_row",
            "render",
            stats,
            dataset="numbers, 10 visible cols",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 2, f"Header render {stats['mean_ms']:.3f}ms exceeds 2ms target"

    def test_render_data_row(self, sheet: Sheet) -> None:
        """Time to render a single data row with numeric cells."""
        gw = _make_grid(sheet)

        def render_row() -> None:
            gw._render_data_row(0, 0, 10)

        stats = measure(render_row, iterations=500, label="render_data_row")
        result = result_json(
            "render.data_row",
            "render",
            stats,
            dataset="numbers, 10 visible cols",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 5, f"Data row render {stats['mean_ms']:.3f}ms exceeds 5ms target"

    def test_cell_style_lookup(self, sheet: Sheet) -> None:
        """Time _cell_style() for a single cell."""
        gw = _make_grid(sheet)

        def style_normal() -> None:
            gw._cell_style(0, 0, None)

        stats = measure(style_normal, iterations=1000, label="cell_style")
        result = result_json(
            "render.cell_style_normal",
            "render",
            stats,
            dataset="single cell, no selection",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 0.1, f"Cell style {stats['mean_ms']:.4f}ms exceeds 0.1ms target"

    def test_cell_style_visual_selection(self, sheet: Sheet) -> None:
        """Time _cell_style() with visual mode selection."""
        gw = _make_grid(sheet)
        gw.show_visual = True
        gw.visual_anchor_row = 0
        gw.visual_anchor_col = 0

        def style_selected() -> None:
            gw._cell_style(5, 5, None)

        stats = measure(style_selected, iterations=1000, label="cell_style_sel")
        result = result_json(
            "render.cell_style_selected",
            "render",
            stats,
            dataset="cell in visual selection range",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert (
            stats["mean_ms"] < 0.2
        ), f"Selected cell style {stats['mean_ms']:.4f}ms exceeds 0.2ms target"

    @pytest.mark.slow
    def test_full_viewport_repaint(self, sheet: Sheet) -> None:
        """Simulate a full viewport repaint (50 rows)."""
        gw = _make_grid(sheet)

        def repaint() -> None:
            for y in range(50):
                gw._render_data_row(y, 0, 10)

        stats = measure(repaint, iterations=50, label="viewport_repaint")
        result = result_json(
            "render.full_viewport_repaint",
            "render",
            stats,
            dataset="50 rows x 10 cols",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert (
            stats["mean_ms"] < 50
        ), f"Viewport repaint {stats['mean_ms']:.1f}ms exceeds 50ms target"
