"""Vim navigation performance benchmarks.

Measures hjkl movement, gg/G jumps, page scrolling,
visual selection, macro playback, and command mode latency.
"""

from __future__ import annotations

import pytest
from textual.geometry import Offset, Size

from vimsheet.model.sheet import Sheet
from vimsheet.model.workbook import Workbook
from vimsheet.ui.grid import GridWidget

from .conftest import (
    measure,
    populate_numbers,
    result_json,
)


@pytest.mark.benchmark
class TestNavigationPerformance:
    """Vim movement and navigation micro-benchmarks."""

    @pytest.fixture
    def grid_10k(self) -> GridWidget:
        """GridWidget backed by a 10K x 26 number sheet, with scroll disabled."""

        from textual.geometry import Region

        from vimsheet.model.config import Config

        sheet = Sheet(name="Nav10K")
        populate_numbers(sheet, 10000, 26)
        wb = Workbook()
        wb.sheets.append(sheet)
        gw = GridWidget(workbook=wb, config=Config())
        object.__setattr__(gw, "_content_region", Region(0, 0, 120, 50))
        object.__setattr__(gw, "_scroll_offset", Offset(0, 0))
        # Prevent move_cursor from calling Textual's scroll_to (needs active app)
        gw.scroll_to = lambda **kw: None
        return gw

    def test_cursor_move_down(self, grid_10k: GridWidget) -> None:
        """Time move_cursor() for 1 row down."""

        def move_j() -> None:
            grid_10k.move_cursor(5, 0)

        stats = measure(move_j, iterations=500, label="move_j")
        result = result_json(
            "nav.cursor_move_down",
            "navigation",
            stats,
            dataset="10K x 26 sheet",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 1, f"Cursor move down {stats['mean_ms']:.4f}ms exceeds 1ms target"

    def test_cursor_move_right(self, grid_10k: GridWidget) -> None:
        """Time move_cursor() for 1 col right."""

        def move_l() -> None:
            grid_10k.move_cursor(0, 5)

        stats = measure(move_l, iterations=500, label="move_l")
        result = result_json(
            "nav.cursor_move_right",
            "navigation",
            stats,
            dataset="10K x 26 sheet",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert (
            stats["mean_ms"] < 1
        ), f"Cursor move right {stats['mean_ms']:.4f}ms exceeds 1ms target"

    def test_gg_jump(self, grid_10k: GridWidget) -> None:
        """Time jump to first cell (A1)."""

        def gg() -> None:
            grid_10k.move_cursor(0, 0)

        stats = measure(gg, iterations=500, label="gg_jump")
        result = result_json(
            "nav.gg_jump",
            "navigation",
            stats,
            dataset="10K x 26 sheet",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 1, f"gg jump {stats['mean_ms']:.4f}ms exceeds 1ms target"

    def test_G_jump(self, grid_10k: GridWidget) -> None:
        """Time jump to last cell."""

        def G() -> None:
            grid_10k.move_cursor(9999, 25)

        stats = measure(G, iterations=500, label="G_jump")
        result = result_json(
            "nav.G_jump",
            "navigation",
            stats,
            dataset="10K x 26 sheet",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 1, f"G jump {stats['mean_ms']:.4f}ms exceeds 1ms target"

    def test_scroll_position_calc(self, grid_10k: GridWidget) -> None:
        """Time _scroll_cursor_into_view() — the scroll bounds check."""

        def scroll_check() -> None:
            grid_10k._scroll_cursor_into_view()

        stats = measure(scroll_check, iterations=500, label="scroll_check")
        result = result_json(
            "nav.scroll_into_view",
            "navigation",
            stats,
            dataset="10K x 26 sheet",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert (
            stats["mean_ms"] < 0.5
        ), f"Scroll into view {stats['mean_ms']:.4f}ms exceeds 0.5ms target"

    def test_visual_selection_toggle(self, grid_10k: GridWidget) -> None:
        """Time toggling visual mode and setting selection anchor."""

        def toggle_visual() -> None:
            grid_10k.show_visual = True
            grid_10k.visual_anchor_row = 0
            grid_10k.visual_anchor_col = 0
            grid_10k.move_cursor(100, 10)

        stats = measure(toggle_visual, iterations=200, label="visual_toggle")
        result = result_json(
            "nav.visual_selection_100x10",
            "navigation",
            stats,
            dataset="10K x 26 sheet, select 100x10 range",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 2, f"Visual selection {stats['mean_ms']:.4f}ms exceeds 2ms target"

    def test_get_content_size(self, grid_10k: GridWidget) -> None:
        """Time get_content_height() and get_content_width()."""

        def size() -> None:
            _ = grid_10k.get_content_height(Size(120, 50), Size(120, 50), 120)
            _ = grid_10k.get_content_width(Size(120, 50), Size(120, 50))

        stats = measure(size, iterations=500, label="content_size")
        result = result_json(
            "nav.content_size_query",
            "navigation",
            stats,
            dataset="10K x 26 sheet",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert (
            stats["mean_ms"] < 0.5
        ), f"Content size query {stats['mean_ms']:.4f}ms exceeds 0.5ms target"
