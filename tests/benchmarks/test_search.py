"""Search performance benchmarks.

Measures find_all() over various dataset sizes, regex search,
highlight rendering cost, jump-to-match latency, and replace_all().
"""

from __future__ import annotations

import gc
import random

import pytest

from vimsheet.controller.search import Searcher, SearchState
from vimsheet.model.sheet import Sheet

from .conftest import (
    measure,
    result_json,
)


def _sheet_10k_text() -> Sheet:
    """10K x 26 sheet with random words."""
    sheet = Sheet(name="Search10K")
    words = [
        "apple",
        "banana",
        "cherry",
        "date",
        "elderberry",
        "fig",
        "grape",
        "honeydew",
        "kiwi",
        "lemon",
    ]
    for r in range(10000):
        for c in range(26):
            word = random.choice(words) + str(random.randint(0, 999))
            sheet.set_cell_value(r, c, word)
    return sheet


def _sheet_100k_text() -> Sheet:
    """100K x 10 sheet with random words."""
    sheet = Sheet(name="Search100K")
    words = [
        "apple",
        "banana",
        "cherry",
        "date",
        "elderberry",
        "fig",
        "grape",
        "honeydew",
        "kiwi",
        "lemon",
    ]
    for r in range(100000):
        for c in range(10):
            word = random.choice(words) + str(random.randint(0, 9999))
            sheet.set_cell_value(r, c, word)
    return sheet


@pytest.mark.benchmark
class TestSearchPerformance:
    """Full-sheet search benchmarks."""

    @pytest.fixture
    def sheet_10k(self) -> Sheet:
        return _sheet_10k_text()

    @pytest.fixture
    def sheet_100k(self) -> Sheet:
        return _sheet_100k_text()

    def test_find_all_10k_simple(self, sheet_10k: Sheet) -> None:
        """Time find_all() over 260K cells, simple substring."""
        searcher = Searcher(sheet_10k)
        state = SearchState(pattern="apple")

        gc.collect()
        stats = measure(
            lambda: searcher.find_all(state),
            iterations=10,
            label="search_10k_simple",
        )
        result = result_json(
            "search.find_all_10k_simple",
            "search",
            stats,
            dataset="260K cells, substring",
            scale="medium",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 750, f"10K search {stats['mean_ms']:.1f}ms exceeds 750ms target"

    @pytest.mark.slow
    def test_find_all_100k_simple(self, sheet_100k: Sheet) -> None:
        """Time find_all() over 1M cells, simple substring."""
        searcher = Searcher(sheet_100k)
        state = SearchState(pattern="banana")

        gc.collect()
        stats = measure(
            lambda: searcher.find_all(state),
            iterations=5,
            label="search_100k_simple",
        )
        result = result_json(
            "search.find_all_100k_simple",
            "search",
            stats,
            dataset="1M cells, substring",
            scale="large",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 2000, f"100K search {stats['mean_ms']:.1f}ms exceeds 2s target"

    def test_find_all_regex(self, sheet_10k: Sheet) -> None:
        """Time regex search over 260K cells."""
        searcher = Searcher(sheet_10k)
        state = SearchState(pattern=r"^[a-z]+_\d+$", use_regex=True)

        gc.collect()
        stats = measure(
            lambda: searcher.find_all(state),
            iterations=10,
            label="search_10k_regex",
        )
        result = result_json(
            "search.find_all_10k_regex",
            "search",
            stats,
            dataset="260K cells, regex pattern",
            scale="medium",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert (
            stats["mean_ms"] < 1500
        ), f"10K regex search {stats['mean_ms']:.1f}ms exceeds 1.5s target"

    def test_find_all_case_sensitive(self, sheet_10k: Sheet) -> None:
        """Time case-sensitive vs insensitive search."""
        searcher = Searcher(sheet_10k)

        def find_case_sensitive() -> list:
            return searcher.find_all(SearchState(pattern="Apple", case_sensitive=True))

        def find_case_insensitive() -> list:
            return searcher.find_all(SearchState(pattern="Apple", case_sensitive=False))

        gc.collect()
        stats_sens = measure(find_case_sensitive, iterations=10, label="search_case_sensitive")
        stats_insens = measure(
            find_case_insensitive, iterations=10, label="search_case_insensitive"
        )
        ratio = stats_insens["mean_ms"] / max(stats_sens["mean_ms"], 0.001)
        print(f"  Case-sensitive vs insensitive ratio: {ratio:.1f}x")
        result = result_json(
            "search.find_all_case_ratio",
            "search",
            stats_sens,
            dataset="260K cells, case comparison",
            scale="medium",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert ratio < 2.0, f"Case-insensitive is {ratio:.1f}x slower than sensitive (target <2x)"

    def test_find_next_latency(self, sheet_10k: Sheet) -> None:
        """Time find_next() — includes full find_all() per call."""
        searcher = Searcher(sheet_10k)
        state = SearchState(pattern="apple")

        gc.collect()
        stats = measure(
            lambda: searcher.find_next(state, (0, 0)),
            iterations=5,
            label="search_find_next",
        )
        result = result_json(
            "search.find_next_latency",
            "search",
            stats,
            dataset="260K cells, jump to next match",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 2000, f"Find next {stats['mean_ms']:.1f}ms exceeds 2s target"

    def test_replace_all_10k(self, sheet_10k: Sheet) -> None:
        """Time replace_all() over 260K cells with ~26K matches."""
        searcher = Searcher(sheet_10k)
        state = SearchState(pattern="apple", replace="orange")

        gc.collect()
        stats = measure(
            lambda: searcher.replace_all(state),
            iterations=5,
            label="replace_all_10k",
        )
        result = result_json(
            "search.replace_all_10k",
            "search",
            stats,
            dataset="260K cells, ~26K matches replaced",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 5000, f"Replace all {stats['mean_ms']:.1f}ms exceeds 5s target"

    def test_empty_sheet_search(self) -> None:
        """Time find_all() on an empty sheet."""
        sheet = Sheet(name="Empty")
        searcher = Searcher(sheet)
        state = SearchState(pattern="anything")

        gc.collect()
        stats = measure(
            lambda: searcher.find_all(state),
            iterations=100,
            label="search_empty",
        )
        result = result_json(
            "search.find_all_empty",
            "search",
            stats,
            dataset="empty sheet",
            scale="tiny",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert (
            stats["mean_ms"] < 5
        ), f"Empty sheet search {stats['mean_ms']:.3f}ms exceeds 5ms target"

    @pytest.mark.slow
    def test_sparse_sheet_search(self, sheet_sparse_large: Sheet) -> None:
        """Time find_all() on a sparse 100K x 100 sheet (1% density).

        Critical: find_all() iterates the full used range (100K x 100 = 10M
        positions) even though only 1% have data. This benchmark validates
        that we handle sparse sheets efficiently.
        """
        searcher = Searcher(sheet_sparse_large)
        state = SearchState(pattern="val_")

        gc.collect()
        stats = measure(
            lambda: searcher.find_all(state),
            iterations=3,
            label="search_sparse",
        )
        result = result_json(
            "search.find_all_sparse_100k",
            "search",
            stats,
            dataset="100Kx100 sparse 1%, 10M range",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        # Current implementation scans all 10M positions — may be slow
        # Target is speculative: <10s for full scan
        assert (
            stats["mean_ms"] < 10000
        ), f"Sparse search {stats['mean_ms']:.0f}ms exceeds 10s target"
