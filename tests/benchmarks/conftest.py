"""Shared fixtures, dataset generators, and helpers for all benchmarks."""

from __future__ import annotations

import gc
import os
import random
import time
from collections.abc import Callable
from typing import Any

import pytest

from vimsheet import __version__
from vimsheet.model.sheet import Sheet
from vimsheet.model.workbook import Workbook

# ---------------------------------------------------------------------------
# Scale constants
# ---------------------------------------------------------------------------

SCALES = {
    "tiny": (100, 10),
    "small": (1_000, 26),
    "medium": (10_000, 26),
    "large": (100_000, 26),
    "wide": (1_000, 256),
    "sparse": (100_000, 100),
}


def vimsheet_version() -> str:
    """Return the current Vimsheet version string."""
    return __version__


# ---------------------------------------------------------------------------
# Benchmark helpers
# ---------------------------------------------------------------------------


def measure(
    fn: Callable[[], Any],
    *,
    iterations: int = 100,
    warmup: int = 3,
    gc_disable: bool = True,
    label: str = "",
) -> dict[str, float]:
    """Run *fn* repeatedly and return timing statistics in milliseconds.

    Parameters
    ----------
    fn:
        Zero-argument callable to benchmark.
    iterations:
        Number of timed iterations after warmup.
    warmup:
        Number of un-timed warmup runs.
    gc_disable:
        Whether to disable GC during measurement (default True).
    label:
        Optional label for debug printing.

    Returns
    -------
    dict with keys: mean, median, p95, p99, min, max (all in ms).
    """
    for _ in range(warmup):
        fn()
    if gc_disable:
        gc.disable()
    times_ns: list[int] = []
    for _ in range(iterations):
        t0 = time.perf_counter_ns()
        fn()
        elapsed = time.perf_counter_ns() - t0
        times_ns.append(elapsed)
    if gc_disable:
        gc.enable()

    times_ns.sort()
    n = len(times_ns)
    mean = sum(times_ns) / n / 1_000_000
    median = times_ns[n // 2] / 1_000_000
    p95 = times_ns[int(n * 0.95)] / 1_000_000
    p99 = times_ns[int(n * 0.99)] / 1_000_000
    lo = times_ns[0] / 1_000_000
    hi = times_ns[-1] / 1_000_000

    result = {
        "mean_ms": mean,
        "median_ms": median,
        "p95_ms": p95,
        "p99_ms": p99,
        "min_ms": lo,
        "max_ms": hi,
    }
    if label:
        print(f"\n  [{label}] mean={mean:.3f}ms  p95={p95:.3f}ms  (n={iterations})")
    return result


def result_json(
    name: str,
    category: str,
    stats: dict[str, float],
    *,
    dataset: str = "",
    scale: str = "",
    warm: bool = True,
    iterations: int = 100,
) -> dict[str, Any]:
    """Wrap measurement stats into a structured JSON-serializable dict."""
    return {
        "name": name,
        "category": category,
        "vimsheet_version": vimsheet_version(),
        "dataset": dataset,
        "scale": scale,
        "warm": warm,
        "iterations": iterations,
        **stats,
    }


# ---------------------------------------------------------------------------
# Dataset generators
# ---------------------------------------------------------------------------


def _rand_word() -> str:
    return random.choice(
        [
            "alpha",
            "beta",
            "gamma",
            "delta",
            "epsilon",
            "zeta",
            "eta",
            "theta",
            "iota",
            "kappa",
            "lambda",
            "mu",
            "nu",
            "xi",
            "omicron",
            "pi",
            "rho",
            "sigma",
            "tau",
            "upsilon",
        ]
    )


def populate_numbers(sheet: Sheet, rows: int, cols: int, pct: float = 1.0) -> Sheet:
    """Fill *sheet* with random numbers. *pct* controls density (0..1)."""
    for r in range(rows):
        for c in range(cols):
            if random.random() < pct:
                sheet.set_cell_value(r, c, random.randint(0, 10000))
    return sheet


def populate_text(sheet: Sheet, rows: int, cols: int, pct: float = 1.0) -> Sheet:
    """Fill *sheet* with random words."""
    for r in range(rows):
        for c in range(cols):
            if random.random() < pct:
                sheet.set_cell_value(r, c, f"{_rand_word()}_{r}_{c}")
    return sheet


def populate_formulas(sheet: Sheet, rows: int, cols: int, pct: float = 0.9) -> Sheet:
    """Fill with formulas referencing previous row/col."""
    sheet.set_cell_value(0, 0, 1)
    for r in range(1, rows):
        for c in range(min(cols, r + 1)):
            if random.random() < pct:
                prev = f"{chr(65 + c)}{r}"
                formula = f"={prev}+1"
                sheet.set_cell_value(r, c, None, formula=formula)
    return sheet


def populate_chain(sheet: Sheet, length: int) -> Sheet:
    """Linear dependency chain: A1=1, A2=A1+1, A3=A2+1, ..."""
    sheet.set_cell_value(0, 0, 1)
    for i in range(1, length):
        prev_ref = f"A{i}"
        sheet.set_cell_value(i, 0, None, formula=f"={prev_ref}+1")
    return sheet


def populate_mixed(sheet: Sheet, rows: int, cols: int) -> Sheet:
    """Mix of numbers, text, dates, and formulas."""
    import datetime

    for r in range(rows):
        for c in range(cols):
            kind = random.choice(["num", "text", "date", "formula"])
            if kind == "num":
                sheet.set_cell_value(r, c, random.randint(0, 100000))
            elif kind == "text":
                sheet.set_cell_value(r, c, f"{_rand_word()}_{r}_{c}")
            elif kind == "date":
                d = datetime.date(2020, 1, 1) + datetime.timedelta(days=r)
                sheet.set_cell_value(r, c, d.isoformat())
            else:
                if r > 0 and c > 0:
                    sheet.set_cell_value(
                        r,
                        c,
                        None,
                        formula=f"={chr(65 + c - 1)}{r + 1}+{chr(65 + c)}{r}",
                    )
    return sheet


def populate_sparse(sheet: Sheet, rows: int, cols: int, pct: float = 0.01) -> Sheet:
    """Sparse sheet — only *pct* of cells are populated."""
    for r in range(rows):
        for c in range(cols):
            if random.random() < pct:
                sheet.set_cell_value(r, c, f"val_{r}_{c}")
    return sheet


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(params=list(SCALES.keys()))
def scale(request: pytest.FixtureRequest) -> str:
    """Parametrize a benchmark over all scale levels."""
    return request.param


@pytest.fixture
def sheet_of_numbers(scale: str) -> Sheet:
    """Sheet populated with random numbers at the given *scale*."""
    rows, cols = SCALES[scale]
    s = Sheet(name=f"Num_{scale}")
    populate_numbers(s, rows, cols)
    return s


@pytest.fixture
def sheet_of_text(scale: str) -> Sheet:
    """Sheet populated with random text at the given *scale*."""
    rows, cols = SCALES[scale]
    s = Sheet(name=f"Text_{scale}")
    populate_text(s, rows, cols)
    return s


@pytest.fixture
def sheet_of_formulas(scale: str) -> Sheet:
    """Sheet with formula chains at the given *scale*."""
    rows, cols = SCALES[scale]
    s = Sheet(name=f"Fml_{scale}")
    populate_formulas(s, rows, cols)
    return s


@pytest.fixture
def sheet_chain_10k() -> Sheet:
    """Linear chain of 10 000 formulas."""
    return populate_chain(Sheet(name="Chain10K"), 10000)


@pytest.fixture
def sheet_chain_100k() -> Sheet:
    """Linear chain of 100 000 formulas."""
    return populate_chain(Sheet(name="Chain100K"), 100000)


@pytest.fixture
def sheet_mixed_10k() -> Sheet:
    """10K x 26 mixed-type sheet."""
    s = Sheet(name="Mixed10K")
    populate_mixed(s, 10000, 26)
    return s


@pytest.fixture
def sheet_sparse_large() -> Sheet:
    """100K x 100 sheet with 1 % density (1M cells used-range, 10K populated)."""
    s = Sheet(name="Sparse")
    populate_sparse(s, 100000, 100, pct=0.01)
    return s


@pytest.fixture
def workbook_blank() -> Workbook:
    """A blank Workbook with one empty sheet."""
    return Workbook.blank()


@pytest.fixture
def workbook_tiny() -> Workbook:
    """Workbook with a 10K x 26 sheet of numbers."""
    wb = Workbook()
    s = Sheet(name="Data")
    populate_numbers(s, 10000, 26)
    wb.sheets.append(s)
    return wb


# ---------------------------------------------------------------------------
# Environment flag: skip benchmarks unless VIMSHEET_BENCHMARK is set
# ---------------------------------------------------------------------------


def pytest_ignore_collect(collection_path: object) -> bool | None:
    """Skip benchmark collection unless VIMSHEET_BENCHMARK=1."""
    if not os.environ.get("VIMSHEET_BENCHMARK"):
        return True
    return None
