"""File I/O performance benchmarks.

Measures CSV/XLSX/JSON import and export for various dataset sizes.
"""

from __future__ import annotations

import gc
import tempfile
from pathlib import Path

import pytest

from vimsheet.io.csv_adapter import CSVAdapter
from vimsheet.io.json_adapter import JSONAdapter
from vimsheet.model.sheet import Sheet
from vimsheet.model.workbook import Workbook

from .conftest import (
    measure,
    populate_numbers,
    result_json,
)


def _workbook_10k() -> Workbook:
    """Workbook with a 10K x 26 sheet."""
    wb = Workbook()
    s = Sheet(name="Data")
    populate_numbers(s, 10000, 26)
    wb.sheets.append(s)
    return wb


def _workbook_100k() -> Workbook:
    """Workbook with a 100K x 10 sheet."""
    wb = Workbook()
    s = Sheet(name="Data")
    populate_numbers(s, 100000, 10)
    wb.sheets.append(s)
    return wb


def _workbook_tiny() -> Workbook:
    """Workbook with a 100 x 10 sheet."""
    wb = Workbook()
    s = Sheet(name="Data")
    populate_numbers(s, 100, 10)
    wb.sheets.append(s)
    return wb


@pytest.mark.benchmark
class TestFileIOPerformance:
    """File format import/export benchmarks."""

    @pytest.fixture
    def tmp_path(self) -> Path:
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)

    # -- CSV benchmarks --

    def test_csv_export_10k(self, tmp_path: str) -> None:
        """Time CSV export of 10K x 26 (260K cells)."""
        wb = _workbook_10k()
        adapter = CSVAdapter()
        path = tmp_path / "test.csv"

        def export_csv() -> None:
            adapter.write(wb, path)

        gc.collect()
        stats = measure(export_csv, iterations=10, label="csv_export_10k")
        result = result_json(
            "io.csv_export_10k",
            "file_io",
            stats,
            dataset="10K x 26 CSV, 260K cells",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert (
            stats["mean_ms"] < 500
        ), f"CSV export 10K {stats['mean_ms']:.1f}ms exceeds 500ms target"

    def test_csv_import_10k(self, tmp_path: str) -> None:
        """Time CSV import of 10K x 26."""
        # Write the file first
        wb = _workbook_10k()
        adapter = CSVAdapter()
        path = tmp_path / "test.csv"
        adapter.write(wb, path)

        def import_csv() -> Workbook:
            return adapter.read(path)

        gc.collect()
        stats = measure(import_csv, iterations=10, label="csv_import_10k")
        result = result_json(
            "io.csv_import_10k",
            "file_io",
            stats,
            dataset="10K x 26 CSV, 260K cells",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 3000, f"CSV import 10K {stats['mean_ms']:.1f}ms exceeds 3s target"

    @pytest.mark.slow
    def test_csv_export_100k(self, tmp_path: str) -> None:
        """Time CSV export of 100K x 10 (1M cells)."""
        wb = _workbook_100k()
        adapter = CSVAdapter()
        path = tmp_path / "large.csv"

        def export_csv() -> None:
            adapter.write(wb, path)

        gc.collect()
        stats = measure(export_csv, iterations=5, label="csv_export_100k")
        result = result_json(
            "io.csv_export_100k",
            "file_io",
            stats,
            dataset="100K x 10 CSV, 1M cells",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert (
            stats["mean_ms"] < 5000
        ), f"CSV export 100K {stats['mean_ms']:.1f}ms exceeds 5s target"

    # -- JSON / .vimsheet benchmarks --

    def test_json_export_10k(self, tmp_path: str) -> None:
        """Time JSON (.vimsheet) export of 10K x 26."""
        wb = _workbook_10k()
        adapter = JSONAdapter()
        path = tmp_path / "test.vimsheet"

        def export_json() -> None:
            adapter.write(wb, path)

        gc.collect()
        stats = measure(export_json, iterations=10, label="json_export_10k")
        result = result_json(
            "io.json_export_10k",
            "file_io",
            stats,
            dataset="10K x 26 JSON, 260K cells",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert (
            stats["mean_ms"] < 1000
        ), f"JSON export 10K {stats['mean_ms']:.1f}ms exceeds 1s target"

    def test_json_import_10k(self, tmp_path: str) -> None:
        """Time JSON (.vimsheet) import of 10K x 26."""
        wb = _workbook_10k()
        adapter = JSONAdapter()
        path = tmp_path / "test.vimsheet"
        adapter.write(wb, path)

        def import_json() -> Workbook:
            return adapter.read(path)

        gc.collect()
        stats = measure(import_json, iterations=10, label="json_import_10k")
        result = result_json(
            "io.json_import_10k",
            "file_io",
            stats,
            dataset="10K x 26 JSON, 260K cells",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert (
            stats["mean_ms"] < 2000
        ), f"JSON import 10K {stats['mean_ms']:.1f}ms exceeds 2s target"

    @pytest.mark.slow
    def test_json_export_formulas(self, tmp_path: str) -> None:
        """Time JSON export of a formula-heavy workbook."""
        wb = Workbook()
        s = Sheet(name="Formulas")
        s.set_cell_value(0, 0, 1)
        for i in range(1, 10000):
            s.set_cell_value(i, 0, None, formula=f"=A{i}+1")
        wb.sheets.append(s)
        adapter = JSONAdapter()
        path = tmp_path / "formulas.vimsheet"

        def export() -> None:
            adapter.write(wb, path)

        gc.collect()
        stats = measure(export, iterations=5, label="json_export_formulas")
        result = result_json(
            "io.json_export_10k_formulas",
            "file_io",
            stats,
            dataset="10K formula cells",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert (
            stats["mean_ms"] < 2000
        ), f"JSON formula export {stats['mean_ms']:.1f}ms exceeds 2s target"

    @pytest.mark.slow
    def test_json_import_formulas(self, tmp_path: str) -> None:
        """Time JSON import of a formula-heavy workbook."""
        wb = Workbook()
        s = Sheet(name="Formulas")
        s.set_cell_value(0, 0, 1)
        for i in range(1, 10000):
            s.set_cell_value(i, 0, None, formula=f"=A{i}+1")
        wb.sheets.append(s)
        adapter = JSONAdapter()
        path = tmp_path / "formulas.vimsheet"
        adapter.write(wb, path)

        def import_json() -> Workbook:
            return adapter.read(path)

        gc.collect()
        stats = measure(import_json, iterations=5, label="json_import_formulas")
        result = result_json(
            "io.json_import_10k_formulas",
            "file_io",
            stats,
            dataset="10K formula cells",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert (
            stats["mean_ms"] < 5000
        ), f"JSON formula import {stats['mean_ms']:.1f}ms exceeds 5s target"

    def test_workbook_serialize_deserialize(self) -> None:
        """Time full serialize/deserialize round-trip for 10K cells."""
        wb = _workbook_tiny()

        def roundtrip() -> None:
            data = wb.serialize()
            Workbook.deserialize(data)

        gc.collect()
        stats = measure(roundtrip, iterations=100, label="serialize_roundtrip")
        result = result_json(
            "io.serialize_roundtrip",
            "file_io",
            stats,
            dataset="100 x 10 workbook",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert (
            stats["mean_ms"] < 10
        ), f"Serialize roundtrip {stats['mean_ms']:.3f}ms exceeds 10ms target"
