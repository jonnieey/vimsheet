"""CSV / TSV import and export adapter."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from vimsheet.io.base import FormatAdapter
from vimsheet.model.sheet import Sheet
from vimsheet.model.workbook import Workbook


class CSVAdapter(FormatAdapter):
    """Read and write CSV (or TSV) files."""

    supported_extensions = [".csv", ".tsv", ".txt"]

    def read(
        self, path: Path, delimiter: str = ",", encoding: str = "utf-8", **opts: object
    ) -> Workbook:
        """Parse *path* as CSV and return a Workbook with one sheet."""
        wb = Workbook()
        sheet = Sheet(name=path.stem or "Sheet1")

        with path.open(encoding=encoding, newline="") as fh:
            reader = csv.reader(fh, delimiter=delimiter)
            for r, row in enumerate(reader):
                for c, raw in enumerate(row):
                    val: Any = _coerce(raw)
                    sheet.set_cell_value(r, c, val)

        wb.sheets.append(sheet)
        wb.filepath = path
        return wb

    def write(
        self,
        workbook: Workbook,
        path: Path,
        delimiter: str = ",",
        encoding: str = "utf-8",
        **opts: object,
    ) -> None:
        """Write the active sheet to *path* as CSV."""
        sheet = workbook.active_sheet
        if not sheet.cells:
            path.write_text("", encoding=encoding)
            return

        max_r = sheet.max_row
        max_c = sheet.max_col

        with path.open("w", encoding=encoding, newline="") as fh:
            writer = csv.writer(fh, delimiter=delimiter)
            for r in range(max_r + 1):
                row = []
                for c in range(max_c + 1):
                    cell = sheet.get_cell(r, c)
                    row.append(cell.display if cell else "")
                writer.writerow(row)


def _coerce(raw: str) -> Any:
    """Try to parse *raw* as int, then float, else return as string."""
    raw = raw.strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    return raw
