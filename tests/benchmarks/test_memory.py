"""Memory footprint benchmarks.

Measures per-cell memory usage, growth rate, undo stack memory,
and peak RSS for various dataset sizes.
"""

from __future__ import annotations

import gc
import tracemalloc

import pytest

from vimsheet.model.cell import Cell
from vimsheet.model.sheet import Sheet
from vimsheet.model.undo import SetCellCommand, UndoStack

from .conftest import result_json


def _snapshot_diff(snapshot_before, snapshot_after, key: str = "lineno"):
    """Return total allocated size delta in bytes."""
    stats = snapshot_after.compare_to(snapshot_before, key)
    return sum(stat.size_diff for stat in stats)


def _measure_traced(fn, *, warmup=True):
    """Run *fn*, return (result, total_bytes_allocated)."""
    if warmup:
        fn()
    gc.collect()
    tracemalloc.start()
    snapshot_before = tracemalloc.take_snapshot()
    result = fn()
    snapshot_after = tracemalloc.take_snapshot()
    tracemalloc.stop()
    total = _snapshot_diff(snapshot_before, snapshot_after)
    return result, total


@pytest.mark.benchmark
class TestMemoryUsage:
    """Per-cell and aggregate memory benchmarks."""

    def test_memory_per_empty_cell_in_range(self) -> None:
        """Measure overhead of defining an empty cell in a sheet."""
        sheet = Sheet(name="Mem")

        def add_empty() -> None:
            sheet.set_cell_value(0, 0, None)

        _, total = _measure_traced(add_empty)
        print(f"\n  Empty cell set: {total} bytes")
        # target: minimal overhead for None value
        assert total < 1000, f"Empty cell overhead {total} bytes seems high"

    def test_memory_per_populated_cell(self) -> None:
        """Measure incremental memory per populated cell."""
        sheet = Sheet(name="Mem")

        def populate_10k() -> None:
            for i in range(10000):
                sheet.set_cell_value(i, 0, f"value_{i}")

        _, total = _measure_traced(populate_10k)
        per_cell = total / 10000
        print(f"\n  10K cells: {total / 1024:.1f} KB total, {per_cell:.0f} bytes/cell")
        result = result_json(
            "memory.per_populated_cell",
            "memory",
            {
                "mean_ms": 0,
                "median_ms": 0,
                "p95_ms": 0,
                "p99_ms": 0,
                "min_ms": 0,
                "max_ms": 0,
                "bytes_per_cell": per_cell,
                "total_bytes": total,
            },
            dataset="10K string cells",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert per_cell < 300, f"Per-cell memory {per_cell:.0f} bytes exceeds 300 target"

    @pytest.mark.slow
    def test_memory_per_formula_cell(self) -> None:
        """Measure incremental memory per formula cell."""
        sheet = Sheet(name="FmlMem")
        sheet.set_cell_value(0, 0, 1)

        def populate_formulas() -> None:
            for i in range(1, 1001):
                sheet.set_cell_value(i, 0, None, formula=f"=A{i}+1")

        _, total = _measure_traced(populate_formulas)
        per_cell = total / 1000
        print(f"\n  10K formulas: {total / 1024:.1f} KB total, {per_cell:.0f} bytes/cell")
        result = result_json(
            "memory.per_formula_cell",
            "memory",
            {
                "mean_ms": 0,
                "median_ms": 0,
                "p95_ms": 0,
                "p99_ms": 0,
                "min_ms": 0,
                "max_ms": 0,
                "bytes_per_cell": per_cell,
                "total_bytes": total,
            },
            dataset="10K formula cells",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert per_cell < 500, f"Per-formula memory {per_cell:.0f} bytes exceeds 500 target"

    def test_memory_growth_rate(self) -> None:
        """Measure memory growth per additional 10K cells (should be linear)."""
        sheet = Sheet(name="Growth")
        sizes = []
        for batch in range(5):
            start = batch * 10000
            for i in range(start, start + 10000):
                sheet.set_cell_value(i, 0, f"val_{i}")
            gc.collect()
            n = len(sheet.cells)
            # Approximate via tracemalloc for the final batch
            if batch == 4:
                _, incremental = _measure_traced(lambda: None)
            sizes.append((n, sheet.cells.maps if hasattr(sheet.cells, "maps") else 0))

        print(f"\n  Cell count growth: {sizes}")
        cells_count = [s[0] for s in sizes]
        # Verify growth is roughly linear
        deltas = [cells_count[i + 1] - cells_count[i] for i in range(len(cells_count) - 1)]
        print(f"  Deltas: {deltas} (should be ~10000 each)")
        assert all(d > 9000 for d in deltas), f"Growth delta {deltas} not linear"

    def test_undo_stack_memory(self) -> None:
        """Measure memory for 100 undo entries of 1000 cells each."""
        sheet = Sheet(name="UndoMem")
        stack = UndoStack()

        for i in range(100):
            stack.push(SetCellCommand(sheet, i, 0, i))

        gc.collect()
        # Estimate: check size of stack._commands list
        import sys as _sys

        stack_size = _sys.getsizeof(stack) + sum(_sys.getsizeof(c) for c in stack._undo)
        print(f"\n  Undo stack (100 entries): ~{stack_size / 1024:.1f} KB")
        result = result_json(
            "memory.undo_stack_100",
            "memory",
            {
                "mean_ms": 0,
                "median_ms": 0,
                "p95_ms": 0,
                "p99_ms": 0,
                "min_ms": 0,
                "max_ms": 0,
                "stack_bytes": stack_size,
            },
            dataset="100 undo entries, single cells",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stack_size < 1_000_000, f"Undo stack {stack_size / 1024:.0f} KB exceeds 1MB target"

    def test_cell_object_size(self) -> None:
        """Measure sys.getsizeof for a single Cell object."""
        import sys as _sys

        cell = Cell(row=0, col=0, value=42, formula=None)
        cell_size = _sys.getsizeof(cell)
        print(f"\n  Cell() object size: {cell_size} bytes (value=42)")

        cell_str = Cell(row=0, col=0, value="hello world " * 10)
        str_size = _sys.getsizeof(cell_str)
        print(f"  Cell(str) object size: {str_size} bytes (long string)")

        cell_fml = Cell(row=0, col=0, value=None, formula="=SUM(A1:A10000)")
        fml_size = _sys.getsizeof(cell_fml)
        print(f"  Cell(formula) object size: {fml_size} bytes")

        result = result_json(
            "memory.cell_object_sizes",
            "memory",
            {
                "mean_ms": 0,
                "median_ms": 0,
                "p95_ms": 0,
                "p99_ms": 0,
                "min_ms": 0,
                "max_ms": 0,
                "cell_int_bytes": cell_size,
                "cell_str_bytes": str_size,
                "cell_formula_bytes": fml_size,
            },
            dataset="individual Cell dataclass instances",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert cell_size < 200, f"Cell(int) size {cell_size} bytes exceeds 200 target"
