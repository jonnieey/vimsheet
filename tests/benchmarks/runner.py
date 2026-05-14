"""CI runner for the Vimsheet benchmark suite.

Usage:
    VIMSHEET_BENCHMARK=1 python tests/benchmarks/runner.py
    VIMSHEET_BENCHMARK=1 python tests/benchmarks/runner.py --compare
    VIMSHEET_BENCHMARK=1 python tests/benchmarks/runner.py --save-baseline
    VIMSHEET_BENCHMARK=1 python tests/benchmarks/runner.py --quick

The runner:
  1. Discovers and runs all benchmarks via pytest.
  2. Collects results into a structured JSON file.
  3. Optionally compares results against a stored baseline.
  4. Reports any regressions exceeding a configurable threshold.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from vimsheet import __version__

BENCHMARKS_DIR = Path(__file__).parent
PROJECT_ROOT = BENCHMARKS_DIR.parent.parent
BASELINE_FILE = BENCHMARKS_DIR / "baseline.json"
RESULTS_DIR = BENCHMARKS_DIR / "results"


def discover_benchmark_files() -> list[Path]:
    """Return all test_*.py files in the benchmarks directory."""
    return sorted(BENCHMARKS_DIR.glob("test_*.py"))


def run_pytest(quick: bool = False, verbose: bool = False) -> subprocess.CompletedProcess:
    """Run pytest on the benchmark suite."""
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(BENCHMARKS_DIR),
        "-v",
        "--tb=short",
        "--no-header",
        "-p",
        "no:cacheprovider",
    ]
    if quick:
        cmd.extend(["-k", "not slow"])
    env = os.environ.copy()
    env["VIMSHEET_BENCHMARK"] = "1"

    if verbose:
        print(f"  Running: {' '.join(cmd)}\n")
        buf = io.StringIO()
        with subprocess.Popen(
            cmd,
            env=env,
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        ) as proc:
            for line in proc.stdout or []:
                sys.stdout.write(line)
                sys.stdout.flush()
                buf.write(line)
            proc.wait()
        # Return a mock CompletedProcess with captured output for parsing
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=proc.returncode,
            stdout=buf.getvalue(),
            stderr="",
        )

    proc = subprocess.run(
        cmd,
        env=env,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    return proc

    proc = subprocess.run(
        cmd,
        env=env,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    if verbose:
        sys.stdout.write(proc.stdout or "")
        sys.stdout.flush()

    return proc


def parse_benchmark_output(output: str) -> list[dict]:
    """Parse structured JSON lines from pytest output.

    Benchmarks print JSON lines prefixed with ``BENCHMARK:``.
    """
    results: list[dict] = []
    for line in output.splitlines():
        if line.startswith("BENCHMARK:"):
            try:
                results.append(json.loads(line[len("BENCHMARK:") :]))
            except json.JSONDecodeError:
                print(f"  [warn] malformed benchmark line: {line[:80]}")
    return results


def save_results(results: list[dict], *, filename: str | None = None) -> Path:
    """Write benchmark results to a timestamped JSON file."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = RESULTS_DIR / (filename or f"benchmarks_{ts}.json")
    payload = {
        "vimsheet_version": __version__,
        "timestamp": ts,
        "results": results,
    }
    path.write_text(json.dumps(payload, indent=2))
    print(f"\n  Results written to {path}")
    return path


def load_baseline() -> dict:
    """Load stored baseline results keyed by benchmark name."""
    if not BASELINE_FILE.exists():
        return {}
    return json.loads(BASELINE_FILE.read_text())


def save_baseline(results: list[dict]) -> None:
    """Save *results* as the new baseline."""
    payload = {
        "vimsheet_version": __version__,
        "timestamp": datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"),
        "results": results,
    }
    BASELINE_FILE.write_text(json.dumps(payload, indent=2))
    print(f"\n  Baseline saved to {BASELINE_FILE}")


def compare_with_baseline(
    results: list[dict],
    baseline: dict,
    threshold_pct: float = 20.0,
) -> int:
    """Compare current results to baseline. Return exit code (0 = pass)."""
    baseline_results = {r["name"]: r for r in baseline.get("results", [])}
    failures = 0

    print("\n  === Benchmark Regression Report ===")
    print(f"  Threshold: {threshold_pct}% degradation\n")

    for result in results:
        name = result["name"]
        bl = baseline_results.get(name)
        if bl is None:
            print(f"  [new]    {name}")
            continue

        key = "mean_ms"
        current = result.get(key)
        previous = bl.get(key)
        if current is None or previous is None or previous == 0:
            continue

        change_pct = ((current - previous) / previous) * 100
        status = "PASS"
        if change_pct > threshold_pct:
            status = "FAIL"
            failures += 1
        elif change_pct < -threshold_pct:
            status = "IMPROVED"

        print(
            f"  [{status:8}] {name:50s}  {previous:.3f}ms → {current:.3f}ms  ({change_pct:+.1f}%)"
        )

    print(f"\n  Failures: {failures}")
    return 1 if failures > 0 else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Vimsheet Benchmark Runner")
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare results against stored baseline",
    )
    parser.add_argument(
        "--save-baseline",
        action="store_true",
        help="Save current results as new baseline",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run a quick subset (fewer iterations, smaller datasets)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show pytest output and per-benchmark results in real-time",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=20.0,
        help="Regression threshold percentage (default: 20)",
    )
    args = parser.parse_args()

    print(f"  Vimsheet version: {__version__}")
    print(f"  Benchmark files: {[f.name for f in discover_benchmark_files()]}")

    if args.verbose:
        print(
            f"  Flags: quick={args.quick}, compare={args.compare}, "
            f"save_baseline={args.save_baseline}, threshold={args.threshold}%\n"
        )

    proc = run_pytest(quick=args.quick, verbose=args.verbose)
    results = parse_benchmark_output(proc.stdout or "")

    if not results:
        print("  No benchmark results found. Did you set VIMSHEET_BENCHMARK=1?")
        return 1

    if args.verbose:
        print(f"\n  Parsed {len(results)} benchmark results:")
        for r in results:
            name = r.get("name", "?")
            mean = r.get("mean_ms")
            median = r.get("median_ms")
            p95 = r.get("p95_ms")
            mean_s = f"{mean:>8.3f}" if mean is not None else "     ?"
            med_s = f"{median:>8.3f}" if median is not None else "     ?"
            p95_s = f"{p95:>8.3f}" if p95 is not None else "     ?"
            print(f"    {name:50s}  μ={mean_s}ms  M={med_s}ms  p95={p95_s}ms")

    save_results(results)

    if args.save_baseline or args.compare:
        baseline = load_baseline() if args.compare else {"results": []}
        rc = compare_with_baseline(results, baseline, args.threshold)
    else:
        rc = 0

    if args.save_baseline:
        save_baseline(results)

    return rc


if __name__ == "__main__":
    sys.exit(main())
