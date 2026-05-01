"""Legacy Excel .xls import via xlrd."""

from __future__ import annotations

from pathlib import Path

from pysheet.io.base import FormatAdapter
from pysheet.model.sheet import Sheet
from pysheet.model.workbook import Workbook


class XLSAdapter(FormatAdapter):
    """Read legacy Excel .xls files (write not supported)."""

    supported_extensions = [".xls"]
    multi_sheet = True

    def read(self, path: Path, **opts: object) -> Workbook:
        try:
            import xlrd
        except ImportError:
            raise RuntimeError("xlrd is required for .xls support: pip install xlrd")

        wb_xls = xlrd.open_workbook(str(path))
        wb = Workbook()
        wb.sheets.clear()
        for ws in wb_xls.sheets():
            sheet = Sheet(name=ws.name)
            for r in range(ws.nrows):
                for c in range(ws.ncols):
                    cell = ws.cell(r, c)
                    val = cell.value
                    if val == "":
                        continue
                    # xlrd type constants: 0=empty,1=text,2=number,3=date,4=bool,5=error
                    if cell.ctype == xlrd.XL_CELL_BOOLEAN:
                        val = bool(val)
                    elif cell.ctype == xlrd.XL_CELL_DATE:
                        import datetime
                        try:
                            tup = xlrd.xldate_as_tuple(val, wb_xls.datemode)
                            val = datetime.datetime(*tup) if tup[3:] != (0, 0, 0) else datetime.date(*tup[:3])
                        except Exception:
                            pass
                    sheet.set_cell_value(r, c, val, record_history=False)
            wb.sheets.append(sheet)
        wb.filepath = path
        return wb

    def write(self, workbook: Workbook, path: Path, **opts: object) -> None:
        raise NotImplementedError(".xls write is not supported; use .xlsx instead")
