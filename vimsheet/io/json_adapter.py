"""JSON I/O for VimSheet.

.vimsheet  — lossless native format (formulas, formatting, multi-sheet)
.json     — plain JSON array of objects, first row used as column headers
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any

from vimsheet.io.base import FormatAdapter
from vimsheet.model.cell import Cell, CellFormat
from vimsheet.model.sheet import Sheet
from vimsheet.model.workbook import Workbook


def _col_letter(c: int) -> str:
    """0-based column index → spreadsheet letter (A, B, … Z, AA, …)."""
    name = ""
    n = c + 1
    while n:
        n, rem = divmod(n - 1, 26)
        name = chr(65 + rem) + name
    return name


def _serialize_value(val: object) -> object:
    if isinstance(val, datetime.date | datetime.datetime | datetime.time):
        return str(val)
    return val


class JSONAdapter(FormatAdapter):
    """Read and write JSON.

    .vimsheet  →  lossless native (formulas, formatting, multi-sheet)
    .json     →  plain array-of-objects using row 0 as header row
    """

    supported_extensions = [".vimsheet", ".json"]
    can_read_formulas = True
    can_write_formulas = True
    multi_sheet = True

    # ------------------------------------------------------------------ #
    # Public interface                                                      #
    # ------------------------------------------------------------------ #

    def read(self, path: Path, **opts: object) -> Workbook:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        if path.suffix.lower() == ".json" and isinstance(data, list):
            return self._read_plain(data, path)
        return self._read_native(data, path)

    def write(self, workbook: Workbook, path: Path, **opts: object) -> None:
        if path.suffix.lower() == ".json":
            self._write_plain(workbook.active_sheet, path)
        else:
            self._write_native(workbook, path)

    # ------------------------------------------------------------------ #
    # Plain JSON  (.json)                                                   #
    # ------------------------------------------------------------------ #

    def _write_plain(self, sheet: Sheet, path: Path) -> None:
        """Export active sheet as [{header: value, ...}, ...] array.

        Row 0 is used as the header row if it contains non-numeric string values
        that look like intentional column names; otherwise column letters (A, B, …)
        are used as headers and all rows become data rows.
        """
        if not sheet.cells:
            path.write_text("[]", encoding="utf-8")
            return

        max_row = max(r for r, _ in sheet.cells)
        max_col = max(c for _, c in sheet.cells)

        # Decide whether row 0 is a header row: it must have at least one cell
        # whose value is a non-empty string that isn't purely numeric.
        def _looks_like_header(val: object) -> bool:
            if not isinstance(val, str):
                return False
            s = val.strip()
            if not s:
                return False
            try:
                float(s)
                return False
            except ValueError:
                return True

        row0_cells = [sheet.cells.get((0, c)) for c in range(max_col + 1)]
        row0_values = [c.value if c else None for c in row0_cells]
        has_header_row = any(_looks_like_header(v) for v in row0_values)

        if has_header_row:
            # Build headers from row 0, deduplicating identical names
            raw: list[str] = [
                str(v) if v is not None else _col_letter(c) for c, v in enumerate(row0_values)
            ]
            data_start = 1
        else:
            # No header row — use column letters, export all rows as data
            raw = [_col_letter(c) for c in range(max_col + 1)]
            data_start = 0

        # Deduplicate: "Name", "Name" → "Name", "Name_2"
        seen: dict[str, int] = {}
        headers: list[str] = []
        for h in raw:
            if h not in seen:
                seen[h] = 1
                headers.append(h)
            else:
                seen[h] += 1
                headers.append(f"{h}_{seen[h]}")

        rows: list[dict[str, Any]] = []
        for r in range(data_start, max_row + 1):
            row_has_data = any((r, c) in sheet.cells for c in range(max_col + 1))
            if not row_has_data:
                continue
            obj: dict[str, Any] = {}
            for c, header in enumerate(headers):
                cell = sheet.cells.get((r, c))
                val = cell.value if cell else None
                if val is not None:
                    obj[header] = _serialize_value(val)
            if obj:
                rows.append(obj)

        path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

    def _read_plain(self, records: list[dict[str, Any]], path: Path) -> Workbook:
        """Import [{header: value, ...}, ...] into a single sheet."""
        wb = Workbook()
        wb.sheets.clear()
        sheet = Sheet(name="Sheet1")

        if not records:
            wb.sheets.append(sheet)
            wb.filepath = path
            return wb

        # Collect all keys in order of first appearance (union across all records)
        seen_keys: dict[str, int] = {}
        for record in records:
            for k in record:
                if k not in seen_keys:
                    seen_keys[k] = len(seen_keys)
        headers = list(seen_keys.keys())

        # If every header is exactly the auto-generated column letter for its
        # position (A, B, C, …), they were artificial — skip writing them and
        # put data starting at row 0.
        auto_headers = all(h == _col_letter(c) for c, h in enumerate(headers))

        if auto_headers:
            data_start = 0
        else:
            # Write header row (row 0)
            for c, h in enumerate(headers):
                sheet.set_cell_value(0, c, h, record_history=False)
            data_start = 1

        # Write data rows
        for r, record in enumerate(records, start=data_start):
            for h, c in seen_keys.items():
                val = record.get(h)
                if val is not None:
                    sheet.set_cell_value(r, c, val, record_history=False)

        wb.sheets.append(sheet)
        wb.filepath = path
        return wb

    # ------------------------------------------------------------------ #
    # Native format  (.vimsheet / .json with "sheets" key)                  #
    # ------------------------------------------------------------------ #

    def _read_native(self, data: dict[str, Any], path: Path) -> Workbook:
        wb = Workbook()
        wb.sheets.clear()
        for sd in data.get("sheets", []):
            sheet = Sheet(name=sd.get("name", "Sheet1"))
            sheet.col_widths = {int(k): v for k, v in sd.get("col_widths", {}).items()}
            sheet.row_heights = {int(k): v for k, v in sd.get("row_heights", {}).items()}
            sheet.hidden_rows = set(sd.get("hidden_rows", []))
            sheet.hidden_cols = set(sd.get("hidden_cols", []))
            sheet.row_groups = [tuple(g) for g in sd.get("row_groups", [])]  # type: ignore[assignment]
            sheet.col_groups = [tuple(g) for g in sd.get("col_groups", [])]  # type: ignore[assignment]
            sheet.freeze_rows = sd.get("freeze_rows", 0)
            sheet.freeze_cols = sd.get("freeze_cols", 0)
            for cd in sd.get("cells", []):
                r, c = cd["row"], cd["col"]
                formula = cd.get("formula")
                value = cd.get("value")
                cell: Cell
                if formula:
                    sheet.set_cell_value(r, c, value, formula=formula, record_history=False)
                else:
                    sheet.set_cell_value(r, c, value, record_history=False)
                cell = sheet.cells[(r, c)]
                if "fmt" in cd:
                    f = cd["fmt"]
                    cell.fmt = CellFormat(
                        bold=f.get("bold", False),
                        italic=f.get("italic", False),
                        underline=f.get("underline", False),
                        align=f.get("align", "right"),
                        fg_color=f.get("fg_color"),
                        bg_color=f.get("bg_color"),
                        num_decimals=f.get("num_decimals"),
                        num_format=f.get("num_format"),
                        thousands_sep=f.get("thousands_sep", False),
                    )
                cell.locked = cd.get("locked", False)
                cell.comment = cd.get("comment")
            wb.sheets.append(sheet)
        wb.active_sheet_idx = data.get("active_sheet", 0)
        wb.filepath = path
        return wb

    def _write_native(self, workbook: Workbook, path: Path) -> None:
        sheets_data = []
        for sheet in workbook.sheets:
            cells_data = []
            for (r, c), cell in sorted(sheet.cells.items()):
                cd: dict[str, Any] = {"row": r, "col": c}
                if cell.formula:
                    cd["formula"] = cell.formula
                val = cell.value
                if val is not None:
                    cd["value"] = _serialize_value(val)
                fmt = cell.fmt
                if any(
                    [
                        fmt.bold,
                        fmt.italic,
                        fmt.underline,
                        fmt.align != "right",
                        fmt.fg_color,
                        fmt.bg_color,
                        fmt.num_decimals is not None,
                        fmt.num_format,
                        fmt.thousands_sep,
                    ]
                ):
                    cd["fmt"] = {
                        "bold": fmt.bold,
                        "italic": fmt.italic,
                        "underline": fmt.underline,
                        "align": fmt.align,
                        "fg_color": fmt.fg_color,
                        "bg_color": fmt.bg_color,
                        "num_decimals": fmt.num_decimals,
                        "num_format": fmt.num_format,
                        "thousands_sep": fmt.thousands_sep,
                    }
                if cell.locked:
                    cd["locked"] = True
                if cell.comment:
                    cd["comment"] = cell.comment
                cells_data.append(cd)
            sheets_data.append(
                {
                    "name": sheet.name,
                    "cells": cells_data,
                    "col_widths": {str(k): v for k, v in sheet.col_widths.items()},
                    "row_heights": {str(k): v for k, v in sheet.row_heights.items()},
                    "hidden_rows": sorted(sheet.hidden_rows),
                    "hidden_cols": sorted(sheet.hidden_cols),
                    "row_groups": [list(g) for g in sheet.row_groups],
                    "col_groups": [list(g) for g in sheet.col_groups],
                    "freeze_rows": sheet.freeze_rows,
                    "freeze_cols": sheet.freeze_cols,
                }
            )
        doc = {"version": 1, "active_sheet": workbook.active_sheet_idx, "sheets": sheets_data}
        path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
