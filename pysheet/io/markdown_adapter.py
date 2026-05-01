"""Markdown table export adapter."""

from __future__ import annotations

from pathlib import Path

from pysheet.io.base import FormatAdapter
from pysheet.model.workbook import Workbook


class MarkdownAdapter(FormatAdapter):
    """Export to GitHub-flavoured Markdown table. Read-only: not implemented."""

    supported_extensions = [".md"]

    def read(self, path: Path, **opts: object) -> Workbook:
        raise NotImplementedError("Markdown import is not supported")

    def write(self, workbook: Workbook, path: Path, **opts: object) -> None:
        sheet = workbook.active_sheet
        if not sheet.cells:
            path.write_text("", encoding="utf-8")
            return

        max_r = sheet.max_row
        max_c = sheet.max_col

        # Build 2-D display grid
        grid: list[list[str]] = []
        for r in range(max_r + 1):
            row_data = []
            for c in range(max_c + 1):
                cell = sheet.get_cell(r, c)
                row_data.append(cell.display if cell else "")
            grid.append(row_data)

        # Column widths
        col_widths = [max(len(grid[r][c]) for r in range(len(grid))) for c in range(max_c + 1)]
        col_widths = [max(w, 3) for w in col_widths]

        def fmt_row(cells: list[str]) -> str:
            parts = [f" {v.ljust(col_widths[i])} " for i, v in enumerate(cells)]
            return "|" + "|".join(parts) + "|"

        lines = []
        lines.append(fmt_row(grid[0]))
        lines.append("|" + "|".join("-" * (col_widths[c] + 2) for c in range(max_c + 1)) + "|")
        for r in range(1, len(grid)):
            lines.append(fmt_row(grid[r]))

        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
