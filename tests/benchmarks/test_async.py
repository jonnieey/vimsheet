"""Async and background processing benchmarks.

Measures UI responsiveness during background tasks, event loop blocking,
FETCH overhead, and concurrent task handling.
"""

from __future__ import annotations

import gc
import threading

import pytest

from vimsheet.model.sheet import Sheet
from vimsheet.model.workbook import Workbook

from .conftest import (
    measure,
    populate_numbers,
    result_json,
)


@pytest.mark.benchmark
class TestAsyncPerformance:
    """Background/async processing benchmarks."""

    def test_fetch_manager_init(self) -> None:
        """Time to initialize a FetchManager."""
        from vimsheet.app import VimSheetApp
        from vimsheet.fetch.fetch_manager import FetchManager

        app = VimSheetApp(workbook=Workbook.blank())

        def init_fm() -> None:
            FetchManager(app)

        gc.collect()
        stats = measure(init_fm, iterations=100, label="fetch_init")
        result = result_json(
            "async.fetch_manager_init",
            "async",
            stats,
            dataset="blank sheet",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert (
            stats["mean_ms"] < 10
        ), f"FetchManager init {stats['mean_ms']:.3f}ms exceeds 10ms target"

    def test_fetch_entry_create(self) -> None:
        """Time creating a FetchEntry."""
        from vimsheet.fetch.fetch_manager import FetchEntry

        def create_entry() -> None:
            FetchEntry(
                url="https://api.example.com/data",
                interval=60,
                json_path="$.results",
            )

        stats = measure(create_entry, iterations=2000, label="fetch_entry")
        result = result_json(
            "async.fetch_entry_create",
            "async",
            stats,
            dataset="single entry",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert (
            stats["mean_ms"] < 0.05
        ), f"FetchEntry create {stats['mean_ms']:.4f}ms exceeds 0.05ms target"

    def test_thread_spawn_overhead(self) -> None:
        """Time to spawn and join a minimal daemon thread.

        This measures the base overhead of threading for FETCH workers.
        """

        def spawn_and_join() -> None:
            done = False

            def worker() -> None:
                nonlocal done
                done = True

            t = threading.Thread(target=worker, daemon=True)
            t.start()
            t.join()

        gc.collect()
        stats = measure(spawn_and_join, iterations=100, label="thread_spawn")
        result = result_json(
            "async.thread_spawn_overhead",
            "async",
            stats,
            dataset="minimal daemon thread",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 5, f"Thread spawn {stats['mean_ms']:.3f}ms exceeds 5ms target"

    def test_set_interval_overhead(self) -> None:
        """Time set_interval() registration (used for autosave, clock)."""

        async def register() -> None:
            # Just measure the set_interval call itself
            pass

        # This is more of a Textual-level benchmark; approximate with timer
        def create_timer() -> None:
            import threading

            timer = threading.Timer(3600, lambda: None)
            timer.cancel()

        gc.collect()
        stats = measure(create_timer, iterations=1000, label="timer_create")
        result = result_json(
            "async.timer_create_overhead",
            "async",
            stats,
            dataset="threading.Timer create+cancel",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 0.5, f"Timer create {stats['mean_ms']:.4f}ms exceeds 0.5ms target"

    def test_sheet_recalc_on_batch_edit(self) -> None:
        """Time full recalc triggered by batch cell edits with 10K formulas.

        Simulates the 'event loop blocking' scenario: user pastes data
        into a formula-heavy sheet and the UI freezes while recalc runs.
        """
        sheet = Sheet(name="RecalcBatch")
        # Build a formula grid: 100 x 100 = 10K formula cells
        for r in range(1, 100):
            for c in range(100):
                if r > 0:
                    sheet.set_cell_value(
                        r,
                        c,
                        None,
                        formula=f"={chr(65 + c)}{r}+{chr(65 + c)}{r + 1}",
                    )
        # Populate first row with data
        populate_numbers(sheet, 1, 100, pct=1.0)

        # Now edit all first-row cells
        cells = [(0, c, c * 100) for c in range(100)]

        def batch_recalc() -> None:
            sheet.set_cells_batch(cells)

        gc.collect()
        stats = measure(batch_recalc, iterations=10, label="batch_recalc")
        result = result_json(
            "async.batch_recalc_10k",
            "async",
            stats,
            dataset="100x100 formula grid, edit 100 roots",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 5000, f"Batch recalc {stats['mean_ms']:.1f}ms exceeds 5s target"

    def test_worker_result_queue(self) -> None:
        """Time pushing and popping results from a worker queue.

        Simulates call_from_thread() pattern used by FETCH.
        """
        import queue

        q: queue.SimpleQueue = queue.SimpleQueue()
        results = [(r, 0, f"result_{r}") for r in range(1000)]

        def push_pop() -> None:
            for res in results:
                q.put(res)
            while not q.empty():
                q.get()

        gc.collect()
        stats = measure(push_pop, iterations=100, label="worker_queue")
        result = result_json(
            "async.worker_queue_1k",
            "async",
            stats,
            dataset="1K results pushed/popped",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 10, f"Worker queue {stats['mean_ms']:.3f}ms exceeds 10ms target"
