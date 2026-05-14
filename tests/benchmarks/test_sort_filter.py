"""Sort and filter performance benchmarks.

Measures single/multi-column sort, filter latency,
regex filtering, incremental filtering, and sort+filter combined.
"""

from __future__ import annotations

import gc
import random

import pytest

from vimsheet.model.sheet import FilterRule, Sheet

from .conftest import (
    measure,
    populate_numbers,
    result_json,
)


def _sheet_10k_varied(rows: int = 10000, cols: int = 10) -> Sheet:
    """Sheet with varied data: numeric, text, mixed columns."""
    sheet = Sheet(name="SortFilter")
    teams = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]
    regions = ["North", "South", "East", "West"]
    for r in range(rows):
        sheet.set_cell_value(r, 0, random.choice(teams))
        sheet.set_cell_value(r, 1, random.choice(regions))
        sheet.set_cell_value(r, 2, random.randint(0, 100000))
        sheet.set_cell_value(r, 3, random.gauss(50000, 15000))
        sheet.set_cell_value(r, 4, f"note_{r}_{random.randint(0, 100)}")
        sheet.set_cell_value(r, 5, random.choice(["Active", "Inactive", "Pending"]))
    return sheet


def _sheet_100k_numeric() -> Sheet:
    """100K x 5 numeric sheet for sort stress test."""
    sheet = Sheet(name="SortBig")
    populate_numbers(sheet, 100000, 5)
    return sheet


@pytest.mark.benchmark
class TestSortPerformance:
    """Sorting benchmarks."""

    @pytest.fixture
    def sheet_10k(self) -> Sheet:
        return _sheet_10k_varied()

    @pytest.fixture
    def sheet_100k(self) -> Sheet:
        return _sheet_100k_numeric()

    def test_sort_single_column(self, sheet_10k: Sheet) -> None:
        """Time sorting 10K x 10 by column A (text)."""

        def sort_col() -> None:
            sheet_10k.sort_by_cols([(0, True)])

        gc.collect()
        stats = measure(sort_col, iterations=20, label="sort_single_col")
        result = result_json(
            "sort.single_column_text_10k",
            "sort_filter",
            stats,
            dataset="10K x 10, text column A",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert (
            stats["mean_ms"] < 200
        ), f"Sort single col {stats['mean_ms']:.1f}ms exceeds 200ms target"

    def test_sort_numeric_column(self, sheet_10k: Sheet) -> None:
        """Time sorting 10K x 10 by column C (numeric)."""

        def sort_num() -> None:
            sheet_10k.sort_by_cols([(2, True)])

        gc.collect()
        stats = measure(sort_num, iterations=20, label="sort_numeric")
        result = result_json(
            "sort.single_column_numeric_10k",
            "sort_filter",
            stats,
            dataset="10K x 10, numeric column C",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 200, f"Sort numeric {stats['mean_ms']:.1f}ms exceeds 200ms target"

    def test_sort_multi_column(self, sheet_10k: Sheet) -> None:
        """Time sorting by 3 columns (team asc, region asc, value desc)."""

        def sort_multi() -> None:
            sheet_10k.sort_by_cols([(0, True), (1, True), (2, False)])

        gc.collect()
        stats = measure(sort_multi, iterations=20, label="sort_multi")
        result = result_json(
            "sort.multi_column_3keys_10k",
            "sort_filter",
            stats,
            dataset="10K x 10, 3-key sort",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert (
            stats["mean_ms"] < 500
        ), f"Multi-column sort {stats['mean_ms']:.1f}ms exceeds 500ms target"

    @pytest.mark.slow
    def test_sort_100k_numeric(self, sheet_100k: Sheet) -> None:
        """Time sorting 100K x 5 by column A."""

        def sort_big() -> None:
            sheet_100k.sort_by_cols([(0, True)])

        gc.collect()
        stats = measure(sort_big, iterations=5, label="sort_100k")
        result = result_json(
            "sort.single_column_100k",
            "sort_filter",
            stats,
            dataset="100K x 5, numeric",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 2000, f"Sort 100K {stats['mean_ms']:.1f}ms exceeds 2s target"


@pytest.mark.benchmark
class TestFilterPerformance:
    """Filtering benchmarks."""

    @pytest.fixture
    def sheet_10k(self) -> Sheet:
        return _sheet_10k_varied()

    def test_filter_exact_match(self, sheet_10k: Sheet) -> None:
        """Time applying an exact-match filter on column A."""

        def filter_exact() -> None:
            sheet_10k.filters = {0: FilterRule("eq", "Alpha")}
            sheet_10k.apply_filters()

        gc.collect()
        stats = measure(filter_exact, iterations=50, label="filter_exact")
        result = result_json(
            "filter.exact_match_10k",
            "sort_filter",
            stats,
            dataset="10K rows, column A eq Alpha",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 100, f"Filter exact {stats['mean_ms']:.3f}ms exceeds 100ms target"

    def test_filter_regex(self, sheet_10k: Sheet) -> None:
        """Time applying a regex filter on column E (notes)."""

        def filter_regex() -> None:
            sheet_10k.filters = {4: FilterRule("regex", r"note_\d+_5[0-9]")}
            sheet_10k.apply_filters()

        gc.collect()
        stats = measure(filter_regex, iterations=50, label="filter_regex")
        result = result_json(
            "filter.regex_10k",
            "sort_filter",
            stats,
            dataset="10K rows, regex on notes column",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 200, f"Filter regex {stats['mean_ms']:.1f}ms exceeds 200ms target"

    def test_filter_numeric_gt(self, sheet_10k: Sheet) -> None:
        """Time applying numeric > filter."""

        def filter_gt() -> None:
            sheet_10k.filters = {2: FilterRule("gt", 50000)}
            sheet_10k.apply_filters()

        gc.collect()
        stats = measure(filter_gt, iterations=50, label="filter_gt")
        result = result_json(
            "filter.numeric_gt_10k",
            "sort_filter",
            stats,
            dataset="10K rows, column C > 50000",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert (
            stats["mean_ms"] < 100
        ), f"Filter numeric > {stats['mean_ms']:.3f}ms exceeds 100ms target"

    def test_filter_multi_rule(self, sheet_10k: Sheet) -> None:
        """Time applying 2 filter rules on different columns."""

        def filter_multi() -> None:
            sheet_10k.filters = {
                0: FilterRule("eq", "Alpha"),
                5: FilterRule("eq", "Active"),
            }
            sheet_10k.apply_filters()

        gc.collect()
        stats = measure(filter_multi, iterations=50, label="filter_multi")
        result = result_json(
            "filter.multi_rule_10k",
            "sort_filter",
            stats,
            dataset="10K rows, 2 filter rules",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert (
            stats["mean_ms"] < 200
        ), f"Multi-rule filter {stats['mean_ms']:.1f}ms exceeds 200ms target"

    def test_clear_filters(self, sheet_10k: Sheet) -> None:
        """Time clearing all filters and re-showing rows."""
        sheet_10k.filters = {0: FilterRule("eq", "Alpha")}
        sheet_10k.apply_filters()

        def clear() -> None:
            sheet_10k.filters.clear()
            sheet_10k.apply_filters()

        gc.collect()
        stats = measure(clear, iterations=100, label="clear_filters")
        result = result_json(
            "filter.clear_10k",
            "sort_filter",
            stats,
            dataset="10K rows, clear all filters",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 50, f"Clear filters {stats['mean_ms']:.3f}ms exceeds 50ms target"

    def test_filter_sort_combined(self, sheet_10k: Sheet) -> None:
        """Time filter then sort — most common real-world workflow."""

        def filter_then_sort() -> None:
            sheet_10k.filters = {0: FilterRule("eq", "Alpha")}
            sheet_10k.apply_filters()
            sheet_10k.sort_by_cols([(2, False)])

        gc.collect()
        stats = measure(filter_then_sort, iterations=20, label="filter_sort")
        result = result_json(
            "sort_filter.combined_10k",
            "sort_filter",
            stats,
            dataset="10K rows, filter Alpha then sort by value desc",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 500, f"Filter+sort {stats['mean_ms']:.1f}ms exceeds 500ms target"
