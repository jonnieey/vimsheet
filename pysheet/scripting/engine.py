"""PySheet scripting engine — executes a mini-DSL of spreadsheet commands."""

from __future__ import annotations

import contextlib
import shlex
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pysheet.model.workbook import Workbook


@dataclass
class ScriptResult:
    """Outcome of running a script."""

    commands_run: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


class ScriptError(Exception):
    """Raised when a script command cannot be executed."""


class ScriptEngine:
    """Execute PySheet script commands against a Workbook.

    Script syntax — one command per line; lines starting with ``#`` are comments::

        # Set values
        set A1 = Hello
        set B1 = 42
        formula C1 = =SUM(A1:B1)

        # Formatting
        format A1 bold=true align=left

        # Sheet ops
        addsheet Sales
        sheet Sheet1

        # File ops
        open data.csv
        save output.xlsx

        # Column width
        colwidth A 15
        autofit B

        # Sort
        sort 1 asc
    """

    def __init__(self, workbook: Workbook | None = None) -> None:
        self.workbook: Workbook = workbook or Workbook.blank()

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def run_file(self, path: Path) -> ScriptResult:
        """Execute all commands in *path*."""
        lines = path.read_text(encoding="utf-8").splitlines()
        return self.run_lines(lines)

    def run_string(self, script: str) -> ScriptResult:
        """Execute all commands in *script* string."""
        return self.run_lines(script.splitlines())

    def run_lines(self, lines: list[str]) -> ScriptResult:
        """Execute a sequence of command lines."""
        result = ScriptResult()
        for lineno, raw in enumerate(lines, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            try:
                self._exec_line(line)
                result.commands_run += 1
            except ScriptError as e:
                result.errors.append(f"Line {lineno}: {e}")
            except Exception as e:
                result.errors.append(f"Line {lineno}: unexpected error — {e}")
        return result

    # -----------------------------------------------------------------------
    # Command dispatcher
    # -----------------------------------------------------------------------

    def _exec_line(self, line: str) -> None:
        # Strip leading colon and translate TUI command aliases
        if line.startswith(":"):
            line = line[1:].strip()
        try:
            parts = shlex.split(line)
        except ValueError as e:
            raise ScriptError(f"Parse error: {e}") from e
        if not parts:
            return
        cmd = parts[0].lower()
        args = parts[1:]

        # TUI command aliases → ScriptEngine commands
        _ALIASES: dict[str, str] = {
            "w": "save",
            "write": "save",
            "e": "open",
            "edit": "open",
            "r": "open",
            "read": "open",
            "q": "quit",
            "q!": "quit",
            "wq": "wquit",
            "x": "wquit",
            "newsheet": "addsheet",
            "sheet+": "addsheet",
            "nextsheet": "sheet_next",
            "prevsheet": "sheet_prev",
            "renamesheet": "renamesheet",
            "delsheet": "delsheet",
            "find": "print",
            "set": "config",
        }
        cmd = _ALIASES.get(cmd, cmd)

        # No-op commands in pipeline mode
        if cmd in ("quit", "sheet_next", "sheet_prev", "config"):
            return

        # :wq — save then quit
        if cmd == "wquit":
            if args:
                self._cmd_save(args)
            elif self.workbook.filepath:
                self._cmd_save([str(self.workbook.filepath)])
            return

        match cmd:
            case "set":
                self._cmd_set(args)
            case "formula":
                self._cmd_formula(args)
            case "clear":
                self._cmd_clear(args)
            case "format":
                self._cmd_format(args)
            case "colwidth":
                self._cmd_colwidth(args)
            case "autofit":
                self._cmd_autofit(args)
            case "sort":
                self._cmd_sort(args)
            case "addsheet":
                self._cmd_addsheet(args)
            case "delsheet":
                self._cmd_delsheet(args)
            case "renamesheet":
                self._cmd_renamesheet(args)
            case "sheet":
                self._cmd_sheet(args)
            case "open" | "load":
                self._cmd_open(args)
            case "save":
                self._cmd_save(args)
            case "print":
                self._cmd_print(args)
            case "hiderow":
                self._cmd_hiderow(args)
            case "showrow":
                self._cmd_showrow(args)
            case "hidecol":
                self._cmd_hidecol(args)
            case "showcol":
                self._cmd_showcol(args)
            case "freeze":
                self._cmd_freeze(args)
            case "unfreeze":
                self.workbook.active_sheet.freeze_rows = 0
                self.workbook.active_sheet.freeze_cols = 0
            case "comment":
                self._cmd_comment(args)
            case "name":
                self._cmd_name(args)
            case _:
                raise ScriptError(f"Unknown command: {cmd!r}")

    # -----------------------------------------------------------------------
    # Command implementations
    # -----------------------------------------------------------------------

    def _cmd_set(self, args: list[str]) -> None:
        # set A1 = value   OR   set A1 value
        if len(args) < 2:
            raise ScriptError("Usage: set <cell> = <value>")
        addr = args[0].upper()
        # strip optional '='
        vals = args[1:] if args[1] != "=" else args[2:]
        raw = " ".join(vals)
        r, c = self._parse_addr(addr)
        val = _coerce(raw)
        self.workbook.active_sheet.set_cell_value(r, c, val)

    def _cmd_formula(self, args: list[str]) -> None:
        # formula A1 = =SUM(B1:B5)   OR   formula A1 =SUM(B1:B5)
        if len(args) < 2:
            raise ScriptError("Usage: formula <cell> = <formula>")
        addr = args[0].upper()
        vals = args[1:] if args[1] != "=" else args[2:]
        raw = " ".join(vals)
        if not raw.startswith("="):
            raw = "=" + raw
        r, c = self._parse_addr(addr)
        self.workbook.active_sheet.set_cell_value(r, c, raw, formula=raw)

    def _cmd_clear(self, args: list[str]) -> None:
        if not args:
            raise ScriptError("Usage: clear <cell_or_range>")
        from pysheet.model.range import CellRange

        addr = args[0].upper()
        if ":" in addr:
            cr = CellRange.from_a1(addr)
            for r in range(cr.start_row, cr.end_row + 1):
                for c in range(cr.start_col, cr.end_col + 1):
                    self.workbook.active_sheet.clear_cell(r, c)
        else:
            r, c = self._parse_addr(addr)
            self.workbook.active_sheet.clear_cell(r, c)

    def _cmd_format(self, args: list[str]) -> None:
        # format A1 bold=true italic=false align=left
        if not args:
            raise ScriptError("Usage: format <cell> [fmt_key=value ...]")
        addr = args[0].upper()
        r, c = self._parse_addr(addr)
        sheet = self.workbook.active_sheet
        cell = sheet.get_cell(r, c)
        if cell is None:
            sheet.set_cell_value(r, c, None)
            cell = sheet.get_cell(r, c)
        for kv in args[1:]:
            if "=" not in kv:
                continue
            key, _, val_str = kv.partition("=")
            self._apply_fmt(cell, key.lower(), val_str)  # type: ignore[arg-type]

    def _apply_fmt(self, cell: Any, key: str, val_str: str) -> None:
        fmt = cell.fmt
        val_str = val_str.lower()
        match key:
            case "bold":
                fmt.bold = val_str in ("true", "1", "yes")
            case "italic":
                fmt.italic = val_str in ("true", "1", "yes")
            case "underline":
                fmt.underline = val_str in ("true", "1", "yes")
            case "align":
                if val_str in ("left", "right", "center"):
                    fmt.align = val_str  # type: ignore[assignment]
            case "fg" | "fg_color":
                fmt.fg_color = val_str or None
            case "bg" | "bg_color":
                fmt.bg_color = val_str or None
            case "decimals" | "num_decimals":
                with contextlib.suppress(ValueError):
                    fmt.num_decimals = int(val_str)
            case "thousands":
                fmt.thousands_sep = val_str in ("true", "1", "yes")

    def _cmd_colwidth(self, args: list[str]) -> None:
        # colwidth A 15  OR  colwidth 1 15  (1-based col number)
        if len(args) < 2:
            raise ScriptError("Usage: colwidth <col> <width>")
        col_str, width_str = args[0], args[1]
        c = self._parse_col(col_str)
        try:
            w = int(width_str)
        except ValueError as err:
            raise ScriptError(f"Invalid width: {width_str!r}") from err
        self.workbook.active_sheet.set_col_width(c, w)

    def _cmd_autofit(self, args: list[str]) -> None:
        if not args:
            raise ScriptError("Usage: autofit <col>")
        c = self._parse_col(args[0])
        self.workbook.active_sheet.auto_fit_col(c)

    def _cmd_sort(self, args: list[str]) -> None:
        # sort 1 asc  (1-based col)
        if not args:
            raise ScriptError("Usage: sort <col> [asc|desc]")
        c = self._parse_col(args[0])
        asc = bool(len(args) < 2 or args[1].lower() in ("asc", "a"))
        _sort_sheet(self.workbook.active_sheet, c, asc)

    def _cmd_addsheet(self, args: list[str]) -> None:
        name = args[0] if args else None
        self.workbook.add_sheet(name)

    def _cmd_delsheet(self, args: list[str]) -> None:
        if not args:
            raise ScriptError("Usage: delsheet <name>")
        self.workbook.delete_sheet(args[0])

    def _cmd_renamesheet(self, args: list[str]) -> None:
        if len(args) < 2:
            raise ScriptError("Usage: renamesheet <old> <new>")
        self.workbook.rename_sheet(args[0], args[1])

    def _cmd_sheet(self, args: list[str]) -> None:
        if not args:
            raise ScriptError("Usage: sheet <name>")
        for i, s in enumerate(self.workbook.sheets):
            if s.name == args[0]:
                self.workbook.go_to_sheet(i)
                return
        raise ScriptError(f"Sheet not found: {args[0]!r}")

    def _cmd_open(self, args: list[str]) -> None:
        if not args:
            raise ScriptError("Usage: open <file>")
        path = Path(args[0])
        from pysheet.io.registry import get_adapter

        try:
            adapter = get_adapter(path)
            self.workbook = adapter.read(path)
        except Exception as e:
            raise ScriptError(f"Cannot open {path}: {e}") from e

    def _cmd_save(self, args: list[str]) -> None:
        if not args and self.workbook.filepath is None:
            raise ScriptError("Usage: save <file>")
        path = Path(args[0]) if args else self.workbook.filepath
        from pysheet.io.registry import get_adapter

        try:
            adapter = get_adapter(path)  # type: ignore[arg-type]
            adapter.write(self.workbook, path)  # type: ignore[arg-type]
            self.workbook.filepath = path  # type: ignore[assignment]
            self.workbook.modified = False
        except Exception as e:
            raise ScriptError(f"Cannot save {path}: {e}") from e

    def _cmd_print(self, args: list[str]) -> None:
        # print A1  OR  print A1:B3
        if not args:
            # Print whole sheet
            sheet = self.workbook.active_sheet
            for r in range(sheet.max_row + 1):
                row_vals = []
                for c in range(sheet.max_col + 1):
                    cell = sheet.get_cell(r, c)
                    row_vals.append(cell.display if cell else "")
                print("\t".join(row_vals))
            return
        addr = args[0].upper()
        from pysheet.model.range import CellRange

        if ":" in addr:
            cr = CellRange.from_a1(addr)
            sheet = self.workbook.active_sheet
            for r in range(cr.start_row, cr.end_row + 1):
                row_vals = []
                for c in range(cr.start_col, cr.end_col + 1):
                    cell = sheet.get_cell(r, c)
                    row_vals.append(cell.display if cell else "")
                print("\t".join(row_vals))
        else:
            r, c = self._parse_addr(addr)
            cell = self.workbook.active_sheet.get_cell(r, c)
            print(cell.display if cell else "")

    def _cmd_hiderow(self, args: list[str]) -> None:
        if not args:
            raise ScriptError("Usage: hiderow <row>")
        try:
            r = int(args[0]) - 1
        except ValueError as err:
            raise ScriptError(f"Invalid row: {args[0]!r}") from err
        self.workbook.active_sheet.hidden_rows.add(r)

    def _cmd_showrow(self, args: list[str]) -> None:
        if not args:
            raise ScriptError("Usage: showrow <row>")
        try:
            r = int(args[0]) - 1
        except ValueError as err:
            raise ScriptError(f"Invalid row: {args[0]!r}") from err
        self.workbook.active_sheet.hidden_rows.discard(r)

    def _cmd_hidecol(self, args: list[str]) -> None:
        if not args:
            raise ScriptError("Usage: hidecol <col>")
        c = self._parse_col(args[0])
        self.workbook.active_sheet.hidden_cols.add(c)

    def _cmd_showcol(self, args: list[str]) -> None:
        if not args:
            raise ScriptError("Usage: showcol <col>")
        c = self._parse_col(args[0])
        self.workbook.active_sheet.hidden_cols.discard(c)

    def _cmd_freeze(self, args: list[str]) -> None:
        # freeze <rows> [cols]
        if not args:
            raise ScriptError("Usage: freeze <rows> [cols]")
        try:
            rows = int(args[0])
            cols = int(args[1]) if len(args) > 1 else 0
        except ValueError as err:
            raise ScriptError("freeze rows and cols must be integers") from err
        self.workbook.active_sheet.freeze_rows = rows
        self.workbook.active_sheet.freeze_cols = cols

    def _cmd_comment(self, args: list[str]) -> None:
        # comment A1 Some comment text here
        if len(args) < 2:
            raise ScriptError("Usage: comment <cell> <text>")
        r, c = self._parse_addr(args[0].upper())
        text = " ".join(args[1:])
        sheet = self.workbook.active_sheet
        cell = sheet.get_cell(r, c)
        if cell is None:
            sheet.set_cell_value(r, c, None)
            cell = sheet.get_cell(r, c)
        cell.comment = text  # type: ignore[union-attr]

    def _cmd_name(self, args: list[str]) -> None:
        # name TOTAL A1:A10
        if len(args) < 2:
            raise ScriptError("Usage: name <NAME> <range>")
        name = args[0].upper()
        range_str = args[1].upper()
        self.workbook.active_sheet.named_ranges.define(name, range_str)

    # -----------------------------------------------------------------------
    # Address helpers
    # -----------------------------------------------------------------------

    def _parse_addr(self, addr: str) -> tuple[int, int]:
        from pysheet.model.range import a1_to_rowcol

        try:
            return a1_to_rowcol(addr.replace("$", ""))
        except Exception as err:
            raise ScriptError(f"Invalid cell address: {addr!r}") from err

    def _parse_col(self, col_str: str) -> int:
        """Parse 'A' or '1' (1-based) into 0-based column index."""
        col_str = col_str.upper()
        if col_str.isdigit():
            c = int(col_str) - 1
        else:
            from pysheet.model.range import a1_to_rowcol

            try:
                _, c = a1_to_rowcol(col_str + "1")
            except Exception as err:
                raise ScriptError(f"Invalid column: {col_str!r}") from err
        return c


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _coerce(raw: str) -> Any:
    """Try int → float → str."""
    s = raw.strip()
    if not s:
        return None
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def _sort_sheet(sheet: Any, col: int, ascending: bool) -> None:
    """Sort sheet rows by 0-based column."""
    from pysheet.model.sheet import SortState

    if not sheet.cells:
        return
    max_r = sheet.max_row
    max_c = sheet.max_col
    rows: list[tuple[Any, dict]] = []
    for r in range(max_r + 1):
        row_cells: dict[int, tuple] = {}
        for c in range(max_c + 1):
            cell = sheet.get_cell(r, c)
            if cell:
                row_cells[c] = (
                    cell.value,
                    cell.formula,
                    cell.fmt.copy(),
                    cell.locked,
                    cell.comment,
                )
        key = None
        if col in row_cells:
            v = row_cells[col][0]
            try:
                key = float(v) if v is not None else ""
            except (TypeError, ValueError):
                key = str(v) if v is not None else ""
        rows.append((key, row_cells))
    rows.sort(key=lambda x: (x[0] is None, x[0]), reverse=not ascending)
    sheet.cells.clear()
    for new_r, (_, row_cells) in enumerate(rows):
        for c, (val, formula, fmt, locked, comment) in row_cells.items():
            sheet.set_cell_value(new_r, c, val, formula=formula, record_history=False)
            cell = sheet.get_cell(new_r, c)
            if cell:
                cell.fmt = fmt
                cell.locked = locked
                cell.comment = comment
    sheet._recalculate_extents()
    sheet.sort_state = SortState(col=col, ascending=ascending)
