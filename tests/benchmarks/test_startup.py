"""Startup performance benchmarks.

Measures cold/warm startup time, workbook loading, and config load.
"""

from __future__ import annotations

import gc
import subprocess
import sys

import pytest

from vimsheet.app import VimSheetApp
from vimsheet.model.config import Config
from vimsheet.model.workbook import Workbook

from .conftest import measure, result_json


@pytest.mark.benchmark
class TestStartupPerformance:
    """Cold and warm startup benchmarks."""

    @pytest.mark.slow
    def test_cold_startup(self) -> None:
        """Time from ``python -c 'import vimsheet.app'`` to App instantiation."""
        code = (
            "import time; t0=time.perf_counter_ns(); "
            "from vimsheet.app import VimSheetApp; "
            "from vimsheet.model.workbook import Workbook; "
            "app=VimSheetApp(workbook=Workbook.blank()); "
            "print(f'READY:{time.perf_counter_ns()-t0}')"
        )
        times_ns: list[int] = []
        for _ in range(5):
            proc = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                timeout=30,
            )
            for line in proc.stdout.splitlines():
                if line.startswith("READY:"):
                    times_ns.append(int(line[len("READY:") :]))
                    break

        if not times_ns:
            pytest.skip("No cold-start measurements collected")
        mean_ms = sum(times_ns) / len(times_ns) / 1_000_000
        print(f"\n  Cold startup: mean={mean_ms:.0f}ms (n={len(times_ns)})")
        # target: < 1000ms
        assert mean_ms < 1000, f"Cold startup {mean_ms:.0f}ms exceeds 1s target"

    def test_warm_app_create(self) -> None:
        """Time to create an App instance (warm import)."""
        # Ensure modules are already imported
        from vimsheet.model.workbook import Workbook

        def create() -> None:
            VimSheetApp(workbook=Workbook.blank())

        stats = measure(create, iterations=30, label="warm_app_create")
        result = result_json(
            "startup.warm_app_create",
            "startup",
            stats,
            dataset="blank workbook",
            warm=True,
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 500, f"Warm create {stats['mean_ms']:.1f}ms exceeds 500ms target"

    @pytest.mark.slow
    def test_workbook_load_tiny(self) -> None:
        """Time Workbook.blank() for a tiny dataset."""

        def load() -> None:
            Workbook.blank()

        stats = measure(load, iterations=200, label="wb_load_tiny")
        result = result_json(
            "startup.workbook_load_tiny",
            "startup",
            stats,
            dataset="blank workbook",
            scale="tiny",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 10, f"Wb load {stats['mean_ms']:.3f}ms exceeds 10ms target"

    def test_config_load(self) -> None:
        """Time Config.load() with a typical config."""
        import json
        from pathlib import Path

        cfg_path = Path("test_config_bench.json")
        cfg_path.write_text(
            json.dumps(
                {
                    "theme": "dracula",
                    "autocalc": True,
                    "undo_limit": 1000,
                    "autosave_interval": 300,
                    "theme_overrides": {
                        "grid_bg": "#1e1e2e",
                        "grid_fg": "#cdd6f4",
                        "cursor_cell_bg": "#313244",
                        "header_bg": "#181825",
                    },
                }
            )
        )
        gc.collect()

        try:
            stats = measure(
                lambda: Config.load(cfg_path),
                iterations=100,
                label="config_load",
            )
        finally:
            cfg_path.unlink(missing_ok=True)

        result = result_json(
            "startup.config_load",
            "startup",
            stats,
            dataset="config.json with theme overrides",
        )
        print(f"BENCHMARK:{__import__('json').dumps(result)}")
        assert stats["mean_ms"] < 50, f"Config load {stats['mean_ms']:.3f}ms exceeds 50ms target"
