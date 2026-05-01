"""Native JSON format — lossless round-trip for all PySheet features."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pysheet.io.base import FormatAdapter
from pysheet.model.cell import Cell, CellFormat
from pysheet.model.sheet import Sheet
from pysheet.model.workbook import Workbook


class JSONAdapter(FormatAdapter):
    """Read and write PySheet's native JSON format."""

    supported_extensions = [".pysheet", ".json"]
    can_read_formulas = True
    can_write_formulas = True
    multi_sheet = True

    def read(self, path: Path, **opts: object) -> Workbook:
        data = json.loads(path.read_text(encoding="utf-8"))
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

    def write(self, workbook: Workbook, path: Path, **opts: object) -> None:
        sheets_data = []
        for sheet in workbook.sheets:
            cells_data = []
            for (r, c), cell in sorted(sheet.cells.items()):
                cd: dict[str, Any] = {"row": r, "col": c}
                if cell.formula:
                    cd["formula"] = cell.formula
                val = cell.value
                if val is not None:
                    import datetime
                    if isinstance(val, (datetime.date, datetime.datetime, datetime.time)):
                        cd["value"] = str(val)
                    else:
                        cd["value"] = val
                fmt = cell.fmt
                if any([fmt.bold, fmt.italic, fmt.underline, fmt.align != "right",
                        fmt.fg_color, fmt.bg_color, fmt.num_decimals is not None,
                        fmt.num_format, fmt.thousands_sep]):
                    cd["fmt"] = {
                        "bold": fmt.bold, "italic": fmt.italic, "underline": fmt.underline,
                        "align": fmt.align, "fg_color": fmt.fg_color, "bg_color": fmt.bg_color,
                        "num_decimals": fmt.num_decimals, "num_format": fmt.num_format,
                        "thousands_sep": fmt.thousands_sep,
                    }
                if cell.locked:
                    cd["locked"] = True
                if cell.comment:
                    cd["comment"] = cell.comment
                cells_data.append(cd)
            sheets_data.append({
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
            })
        doc = {"version": 1, "active_sheet": workbook.active_sheet_idx, "sheets": sheets_data}
        path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
