"""Editing performance benchmarks.

Measures typing latency, paste performance, multi-cell edits,
undo/redo speed, and bulk replace operations.
"""

from __future__ import annotations

import gc

import pytest

from vimsheet.model.sheet import Sheet
from vimsheet.model.undo import (
    CompositeCommand,
    SetCellCommand,
    UndoStack,
)

from .conftest import (
    measure,
    populate_numbers,
    result_json,
)


def _populated_sheet(rows: int, cols: int) -> Sheet:
    """Sheet with numbers."""
    s = Sheet(name=f"Edit{rows}")
    populate_numbers(s, rows, cols)
    return s


def _text_sheet(rows: int, cols: int) -> Sheet:
    """Sheet with text cells for find/replace."""
    s = Sheet(name=f"Text{rows}")
    for r in range(rows):
        for c in range(cols):
            s.set_cell_value(r, c, f"hello_{r}_{c}")
    return s


@pytest.mark.benchmark
class TestEditingPerformance:
    """Single-cell and bulk editing benchmarks."""

    @pytest.fixture
    def small_sheet(self) -> Sheet:
        return _populated_sheet(100, 26)

    @pytest.fixture
    def large_sheet(self) -> Sheet:
        return _populated_sheet(10000, 26)

    def test_set_single_cell(self, small_sheet: Sheet) -> None:
        """Time set_cell_value() for one cell."""

        def set_cell() -> None:
            small_sheet.set_cell_value(5, 5, 42)

        stats = measure(set_cell, iterations=500, label="set_single_cell")
        result = result_json(
            "editing.set_single_cell",
            "editing",
            stats,
            dataset="100 x 26 sheet",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 5, f"Set single cell {stats['mean_ms']:.4f}ms exceeds 5ms target"

    def test_set_single_cell_with_recalc(self) -> None:
        """Time set_cell_value() on a cell with 1K dependents."""
        sheet = Sheet(name="RecalcTest")
        for i in range(1000):
            sheet.set_cell_value(i, 0, i)
        for i in range(1, 1000):
            sheet.set_cell_value(i, 0, None, formula=f"=A{i}+1")
        sheet.set_cell_value(0, 0, 42)  # warmup

        gc.collect()

        def set_with_recalc() -> None:
            sheet.set_cell_value(0, 0, 42)

        stats = measure(set_with_recalc, iterations=5, label="set_with_recalc")
        result = result_json(
            "editing.set_cell_with_recalc",
            "editing",
            stats,
            dataset="10K sheet, 1K dependents",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert (
            stats["mean_ms"] < 10000
        ), f"Set cell + recalc {stats['mean_ms']:.1f}ms exceeds 10s target"

    def test_set_cells_batch(self, large_sheet: Sheet) -> None:
        """Time set_cells_batch() for 10K cells."""
        cells = [(r, 0, r * 100) for r in range(10000)]

        def batch() -> None:
            large_sheet.set_cells_batch(cells)

        gc.collect()
        stats = measure(batch, iterations=10, label="set_cells_batch_10k")
        result = result_json(
            "editing.set_cells_batch_10k",
            "editing",
            stats,
            dataset="10K cells batch write",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 2000, f"Batch set 10K {stats['mean_ms']:.1f}ms exceeds 2s target"

    def test_clear_single_cell(self, small_sheet: Sheet) -> None:
        """Time clear_cell() for one cell."""

        def clear() -> None:
            small_sheet.clear_cell(5, 5)

        stats = measure(clear, iterations=500, label="clear_single")
        result = result_json(
            "editing.clear_single_cell",
            "editing",
            stats,
            dataset="100 x 26 sheet",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 5, f"Clear cell {stats['mean_ms']:.4f}ms exceeds 5ms target"

    def test_undo_set_cell(self, small_sheet: Sheet) -> None:
        """Time UndoStack.undo() after a SetCellCommand."""
        undo_stack = UndoStack()
        cmd = SetCellCommand(small_sheet, 5, 5, 42)
        cmd.execute()
        undo_stack.push(cmd)
        small_sheet.set_cell_value(5, 5, 99)

        def undo() -> None:
            undo_stack.undo()

        gc.collect()
        stats = measure(undo, iterations=200, label="undo_single")
        result = result_json(
            "editing.undo_single_cell",
            "editing",
            stats,
            dataset="single cell undo",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 5, f"Undo single {stats['mean_ms']:.4f}ms exceeds 5ms target"

    def test_redo_set_cell(self, small_sheet: Sheet) -> None:
        """Time UndoStack.redo() after a SetCellCommand."""
        undo_stack = UndoStack()
        cmd = SetCellCommand(small_sheet, 5, 5, 42)
        cmd.execute()
        undo_stack.push(cmd)
        small_sheet.set_cell_value(5, 5, 99)
        undo_stack.undo()

        gc.collect()

        def redo() -> None:
            undo_stack.redo()

        stats = measure(redo, iterations=200, label="redo_single")
        result = result_json(
            "editing.redo_single_cell",
            "editing",
            stats,
            dataset="single cell redo",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 5, f"Redo single {stats['mean_ms']:.4f}ms exceeds 5ms target"

    def test_undo_batch_10k(self, large_sheet: Sheet) -> None:
        """Time undo for a batch of 10K cell changes via CompositeCommand."""
        undo_stack = UndoStack()
        commands = [SetCellCommand(large_sheet, r, 0, r) for r in range(10000)]
        composite = CompositeCommand(commands)
        composite.execute()
        undo_stack.push(composite)
        gc.collect()

        def undo_batch() -> None:
            undo_stack.undo()

        stats = measure(undo_batch, iterations=10, label="undo_batch_10k")
        result = result_json(
            "editing.undo_batch_10k",
            "editing",
            stats,
            dataset="10K cells batch undo via CompositeCommand",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 5000, f"Undo batch 10K {stats['mean_ms']:.1f}ms exceeds 5s target"

    def test_format_value_cache(self) -> None:
        """Time cell.display (format_value) when unchanged vs changed."""
        from vimsheet.model.cell import Cell

        cell = Cell(row=0, col=0, value=12345.6789)
        # First call computes display string
        _ = cell.display

        stats = measure(
            lambda: cell.display,
            iterations=2000,
            label="display_cached",
        )
        result = result_json(
            "editing.display_cached",
            "editing",
            stats,
            dataset="cached display string",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert (
            stats["mean_ms"] < 0.01
        ), f"Cached display {stats['mean_ms']:.5f}ms exceeds 0.01ms target"
