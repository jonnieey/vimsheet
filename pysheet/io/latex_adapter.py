"""LaTeX tabular export adapter."""

from __future__ import annotations

from pathlib import Path

from pysheet.io.base import FormatAdapter
from pysheet.model.workbook import Workbook


class LaTeXAdapter(FormatAdapter):
    """Export to LaTeX tabular environment. Import not supported."""

    supported_extensions = [".tex"]

    def read(self, path: Path, **opts: object) -> Workbook:
        raise NotImplementedError("LaTeX import is not supported")

    def write(self, workbook: Workbook, path: Path, **opts: object) -> None:
        sheet = workbook.active_sheet
        if not sheet.cells:
            path.write_text("", encoding="utf-8")
            return

        max_r = sheet.max_row
        max_c = sheet.max_col

        grid: list[list[str]] = []
        for r in range(max_r + 1):
            row_data = []
            for c in range(max_c + 1):
                cell = sheet.get_cell(r, c)
                val = cell.display if cell else ""
                # Escape LaTeX special characters
                for ch, repl in [("&", r"\&"), ("%", r"\%"), ("$", r"\$"),
                                  ("#", r"\#"), ("_", r"\_"), ("{", r"\{"),
                                  ("}", r"\}"), ("~", r"\textasciitilde{}"),
                                  ("^", r"\textasciicircum{}"), ("\\", r"\textbackslash{}")]:
                    val = val.replace(ch, repl)
                row_data.append(val)
            grid.append(row_data)

        col_spec = "l" * (max_c + 1)
        lines = [
            r"\begin{tabular}{" + col_spec + "}",
            r"\hline",
        ]
        for i, row_data in enumerate(grid):
            lines.append(" & ".join(row_data) + r" \\")
            if i == 0:
                lines.append(r"\hline")
        lines.append(r"\hline")
        lines.append(r"\end{tabular}")

        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
