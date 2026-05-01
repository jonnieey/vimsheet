"""HTML table export adapter."""

from __future__ import annotations

import html
from pathlib import Path

from pysheet.io.base import FormatAdapter
from pysheet.model.workbook import Workbook


class HTMLAdapter(FormatAdapter):
    """Export to an HTML file with a styled table. Read-only: not implemented."""

    supported_extensions = [".html", ".htm"]

    def read(self, path: Path, **opts: object) -> Workbook:
        raise NotImplementedError("HTML import is not supported")

    def write(self, workbook: Workbook, path: Path, **opts: object) -> None:
        sheet = workbook.active_sheet
        max_r = sheet.max_row
        max_c = sheet.max_col

        rows_html = []
        for r in range(max_r + 1):
            cells_html = []
            tag = "th" if r == 0 else "td"
            for c in range(max_c + 1):
                cell = sheet.get_cell(r, c)
                display = html.escape(cell.display if cell else "")
                style_parts = []
                if cell:
                    fmt = cell.fmt
                    if fmt.bold:
                        style_parts.append("font-weight:bold")
                    if fmt.italic:
                        style_parts.append("font-style:italic")
                    if fmt.underline:
                        style_parts.append("text-decoration:underline")
                    align_map = {"left": "left", "center": "center", "right": "right"}
                    style_parts.append(f"text-align:{align_map.get(fmt.align, 'right')}")
                    if fmt.fg_color:
                        style_parts.append(f"color:{fmt.fg_color}")
                    if fmt.bg_color:
                        style_parts.append(f"background-color:{fmt.bg_color}")
                style = "; ".join(style_parts)
                cells_html.append(f'<{tag} style="{style}">{display}</{tag}>')
            rows_html.append("<tr>" + "".join(cells_html) + "</tr>")

        table = (
            '<table border="1" cellspacing="0" cellpadding="4" '
            'style="border-collapse:collapse;font-family:monospace">\n'
            + "\n".join(rows_html)
            + "\n</table>"
        )
        doc = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>{html.escape(sheet.name)}</title>
</head><body>
{table}
</body></html>
"""
        path.write_text(doc, encoding="utf-8")
