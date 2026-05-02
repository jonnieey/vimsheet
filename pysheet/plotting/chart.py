"""Spreadsheet chart rendering — ASCII fallback, plotext when available."""

from __future__ import annotations

import contextlib
from dataclasses import dataclass, field
from typing import Any

from pysheet.model.sheet import Sheet


@dataclass
class ChartSpec:
    """Specification for a chart to render."""

    chart_type: str = "bar"  # "bar" | "line" | "scatter" | "pie"
    data_range: str = ""  # A1:B10 style
    title: str = ""
    x_label: str = ""
    y_label: str = ""
    width: int = 60
    height: int = 20
    series_names: list[str] = field(default_factory=list)


def render_chart(sheet: Sheet, spec: ChartSpec) -> str:
    """Return a multi-line string containing the rendered chart.

    Backend priority: textual-plotext → plotext → gnuplot → ASCII fallback.
    """
    data = _extract_data(sheet, spec)
    if not data:
        return "(no data)"
    for renderer in (_render_textual_plotext, _render_plotext, _render_gnuplot):
        try:
            return renderer(data, spec)
        except ImportError:
            continue
        except Exception:
            continue
    return _render_ascii(data, spec)


def _extract_data(sheet: Sheet, spec: ChartSpec) -> list[list[Any]]:
    """Return 2-D list of values from spec.data_range."""
    if not spec.data_range:
        return []
    from pysheet.model.range import CellRange

    try:
        cr = CellRange.from_a1(spec.data_range.replace("$", ""))
    except Exception:
        return []
    result = []
    for r in range(cr.start_row, cr.end_row + 1):
        row_vals = []
        for c in range(cr.start_col, cr.end_col + 1):
            cell = sheet.get_cell(r, c)
            row_vals.append(cell.value if cell else None)
        result.append(row_vals)
    return result


def _render_textual_plotext(data: list[list[Any]], spec: ChartSpec) -> str:
    """Render using textual-plotext (uses plotext with color disabled for clean ASCII)."""
    from textual_plotext import PlotextPlot  # noqa: F401 — presence check

    return _render_plotext(data, spec)


def _render_gnuplot(data: list[list[Any]], spec: ChartSpec) -> str:
    """Render using gnuplot via subprocess (dumb terminal → ASCII art)."""
    import os
    import shutil
    import subprocess
    import tempfile

    if not shutil.which("gnuplot"):
        raise ImportError("gnuplot not found")

    if not data or not data[0]:
        return "(empty range)"

    # Write data to a temp file
    num_cols = len(data[0])
    with tempfile.NamedTemporaryFile(mode="w", suffix=".dat", delete=False) as f:
        dat_path = f.name
        for i, row in enumerate(data):
            val = row[0] if num_cols == 1 else (row[1] if len(row) > 1 else None)
            label = str(row[0]) if row[0] is not None else str(i)
            with contextlib.suppress(TypeError, ValueError):
                f.write(f"{i + 1}\t{float(val)}\t{label}\n")  # type: ignore[arg-type]

    ct = spec.chart_type
    if ct == "bar":
        plot_cmd = f"set style data histogram; plot '{dat_path}' using 2:xtic(3) notitle"
    elif ct == "line":
        plot_cmd = f"plot '{dat_path}' using 1:2 with linespoints notitle"
    elif ct == "scatter":
        plot_cmd = f"plot '{dat_path}' using 1:2 with points notitle"
    else:
        plot_cmd = f"plot '{dat_path}' using 1:2 with linespoints notitle"

    title_cmd = f"set title '{spec.title}'" if spec.title else ""
    script = f"set terminal dumb {spec.width} {spec.height}\n" f"{title_cmd}\n" f"{plot_cmd}\n"
    try:
        proc = subprocess.run(
            ["gnuplot"],
            input=script,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return proc.stdout if proc.stdout else "(gnuplot produced no output)"
    finally:
        os.unlink(dat_path)


def _strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from a string."""
    import re

    return re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text)


def _render_plotext(data: list[list[Any]], spec: ChartSpec) -> str:
    """Render using plotext to a plain-text string."""
    import io
    import sys

    import plotext as plt

    plt.clf()
    with contextlib.suppress(AttributeError):
        plt.colorless()  # disable ANSI color codes
    plt.plotsize(spec.width, spec.height)
    if spec.title:
        plt.title(spec.title)
    if spec.x_label:
        plt.xlabel(spec.x_label)
    if spec.y_label:
        plt.ylabel(spec.y_label)

    # Transpose: rows = observations, first col = x or labels, rest = series
    if not data or not data[0]:
        return "(empty range)"

    num_cols = len(data[0])
    chart_type = spec.chart_type.lower()

    # Build xs (labels) and ys (values) — first col = labels, second = values
    if num_cols == 1:
        xs = list(range(1, len(data) + 1))
        ys_raw = [row[0] for row in data]
    else:
        xs = [row[0] for row in data]
        ys_raw = [row[1] if len(row) > 1 else None for row in data]

    labels = [str(x) if x is not None else "" for x in xs]
    y_nums = [float(v) for v in ys_raw if isinstance(v, int | float)]
    labels_clean = labels[: len(y_nums)]

    if chart_type == "pie":
        # plotext has no pie; render as ASCII percentage table instead
        total = sum(y_nums) or 1
        title_line = (spec.title + "\n\n") if spec.title else ""
        bar_w = 30
        rows = []
        for lbl, v in zip(labels_clean, y_nums, strict=False):
            pct = v / total * 100
            filled = int(pct / 100 * bar_w)
            bar = "█" * filled + "░" * (bar_w - filled)
            rows.append(f"  {lbl:>10}  {bar}  {pct:5.1f}%  ({v})")
        return title_line + "\n".join(rows)
    elif chart_type in ("histogram", "hist"):
        plt.hist(y_nums, bins=min(10, len(y_nums)))
    elif chart_type == "bar":
        plt.bar(labels_clean, y_nums)
    else:
        x_nums = list(range(1, len(y_nums) + 1))
        _plot_series(plt, chart_type, x_nums, y_nums, "Series 1")

    buf = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buf
    try:
        plt.show()
    finally:
        sys.stdout = old_stdout
    return _strip_ansi(buf.getvalue())


def _plot_series(plt: Any, chart_type: str, xs: list, ys: list, name: str) -> None:
    clean_ys = [float(v) for v in ys if isinstance(v, int | float)]
    clean_xs = xs[: len(clean_ys)]
    match chart_type:
        case "line":
            plt.plot(clean_xs, clean_ys, label=name)
        case "scatter":
            plt.scatter(clean_xs, clean_ys, label=name)
        case _:
            plt.bar(clean_xs, clean_ys, label=name)


def _render_ascii(data: list[list[Any]], spec: ChartSpec) -> str:
    """Minimal ASCII bar chart — used when plotext is unavailable."""
    if not data:
        return "(no data)"
    # Collect numeric values from the last column
    nums: list[float] = []
    labels: list[str] = []
    for row in data:
        if not row:
            continue
        label = str(row[0]) if row[0] is not None else ""
        val = row[-1] if len(row) > 1 else row[0]
        try:
            nums.append(float(val))  # type: ignore[arg-type]
            labels.append(label)
        except (TypeError, ValueError):
            pass
    if not nums:
        return "(no numeric data)"

    max_val = max(nums)
    bar_width = max(1, spec.width - 20)
    lines = []
    if spec.title:
        lines.append(spec.title.center(spec.width))
        lines.append("")
    for label, val in zip(labels, nums, strict=False):
        bar_len = int(val / max_val * bar_width) if max_val else 0
        bar = "█" * bar_len
        lines.append(f"{label:>10} │{bar:<{bar_width}} {val}")
    return "\n".join(lines)
