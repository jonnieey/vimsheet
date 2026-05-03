"""PySheet Textual application."""

from __future__ import annotations

import contextlib
import logging
from pathlib import Path
from typing import Any

from textual.app import App, ComposeResult

from pysheet.controller.edit_handler import EditHandler
from pysheet.controller.insert_handler import InsertHandler
from pysheet.controller.macro import MacroRecorder
from pysheet.controller.mode import Mode
from pysheet.controller.normal_handler import NormalHandler
from pysheet.controller.search import Searcher, SearchState
from pysheet.controller.visual_handler import VisualHandler
from pysheet.model.range import rowcol_to_a1
from pysheet.model.undo import UndoStack
from pysheet.model.workbook import Workbook
from pysheet.ui.formula_bar import FormulaBar
from pysheet.ui.grid import GridWidget
from pysheet.ui.sheet_tabs import SheetTabs
from pysheet.ui.status_bar import StatusBar

log = logging.getLogger(__name__)


def _char(event: Any) -> str:
    """Return the best key identifier for *event*.

    Uses ``event.character`` for printable keys so that shifted characters
    (``$``, ``=``, ``G``, etc.) arrive as their actual glyph rather than the
    normalised name Textual would assign (e.g. ``dollar_sign``).
    """
    if event.character and event.character.isprintable():
        return event.character
    return event.key


class PySheetApp(App[None]):
    """Main PySheet application."""

    CSS = """
    Screen { layout: vertical; }
    """

    def __init__(self, workbook: Workbook | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.workbook: Workbook = workbook or Workbook.blank()

        # ---- Mode controller state ----
        self._key_buffer: str = ""
        self._command_buffer: str = ""
        self._insert_buffer: str = ""
        self._insert_cursor: int = 0
        self._insert_align: str = "right"
        self._edit_buffer: str = ""
        self._edit_cursor: int = 0
        self._edit_chord: str = ""  # pending chord in Edit normal sub-mode
        self._visual_chord: str = ""  # pending chord in Visual mode

        # ---- Registers / marks ----
        self._default_register: list[list[Any]] = []
        self._registers: dict[str, list[list[Any]]] = {}
        self._marks: dict[str, tuple[int, int, int]] = {}
        self._pending_register: str = ""  # set by "{a-z} prefix

        # ---- Repeat / last action ----
        self._last_action: tuple[Any, ...] | None = None

        # ---- Undo / macro ----
        self.undo_stack: UndoStack = UndoStack()
        self.macro_recorder: MacroRecorder = MacroRecorder()

        # ---- Search state ----
        self._search_state: SearchState | None = None

        # ---- Deleted sheet undo buffer ----
        self._deleted_sheets: list[tuple[int, Any]] = []

        # ---- Autocalc flag ----
        self._autocalc: bool = True

        # ---- Macro replay guard (prevents recursive self-calling macros) ----
        self._replaying_macros: set[str] = set()

        # ---- Handlers (created after super().__init__ so App attrs exist) ----
        self.normal_handler = NormalHandler(self)
        self.insert_handler = InsertHandler(self)
        self.edit_handler = EditHandler(self)
        self.visual_handler = VisualHandler(self)

        # ---- HTTP fetch manager ----
        from pysheet.fetch.fetch_manager import FetchManager, _set_global_manager

        self.fetch_manager: FetchManager = FetchManager(self)
        _set_global_manager(self.fetch_manager)

    # -----------------------------------------------------------------------
    # Layout
    # -----------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield FormulaBar(id="formula-bar")
        yield GridWidget(self.workbook, id="grid")
        yield SheetTabs(id="sheet-tabs")
        yield StatusBar(id="status-bar")

    def on_mount(self) -> None:
        if startup_theme := getattr(self, "_startup_theme", None):
            self._apply_theme(startup_theme)
        self._sync_sheet_tabs()
        self._sync_formula_bar()
        self._sync_status_bar()
        self.grid.focus()
        self._trigger_fetch_cells()

    def on_unmount(self) -> None:
        self.fetch_manager.cancel_all()

    def _trigger_fetch_cells(self) -> None:
        """Re-evaluate every FETCH formula cell now that FetchManager is live.

        Formulas are evaluated during file load before the app (and FetchManager)
        exist, so FETCH cells land as #LOADING.  This pass re-runs them so the
        manager schedules background requests.
        """
        from pysheet.formula.evaluator import Evaluator

        for sheet in self.workbook.sheets:
            fetch_cells = [
                (r, c, cell)
                for (r, c), cell in sheet.cells.items()
                if cell.formula and "FETCH" in cell.formula.upper()
            ]
            if not fetch_cells:
                continue
            ev = Evaluator(sheet, self.workbook)
            for r, c, cell in fetch_cells:
                cell.value = ev.eval_formula(cell.formula, r, c)
                cell.display = cell.format_value()
        self.grid.refresh_grid()

    # -----------------------------------------------------------------------
    # Widget shortcuts
    # -----------------------------------------------------------------------

    @property
    def grid(self) -> GridWidget:
        return self.query_one("#grid", GridWidget)

    @property
    def formula_bar(self) -> FormulaBar:
        return self.query_one("#formula-bar", FormulaBar)

    @property
    def status_bar(self) -> StatusBar:
        return self.query_one("#status-bar", StatusBar)

    @property
    def sheet_tabs(self) -> SheetTabs:
        return self.query_one("#sheet-tabs", SheetTabs)

    @property
    def mode(self) -> Mode:
        return self.grid.mode

    @mode.setter
    def mode(self, value: Mode) -> None:
        self.grid.mode = value
        self.formula_bar.mode = value
        self.status_bar.mode = value

    @property
    def cursor_row(self) -> int:
        return self.grid.cursor_row

    @property
    def cursor_col(self) -> int:
        return self.grid.cursor_col

    @property
    def cursor(self) -> tuple[int, int]:
        return self.grid.cursor_row, self.grid.cursor_col

    # -----------------------------------------------------------------------
    # Key routing
    # -----------------------------------------------------------------------

    def on_key(self, event: Any) -> None:
        """Route all key events through the active mode handler."""
        # Let modal screens handle their own keys
        if len(self.screen_stack) > 1:
            return

        event.prevent_default()
        event.stop()

        key = _char(event)

        match self.mode:
            case Mode.NORMAL:
                self.normal_handler.handle(key)
            case Mode.INSERT:
                self.insert_handler.handle(key)
            case Mode.EDIT:
                self.edit_handler.handle(key)
            case Mode.VISUAL | Mode.VISUAL_LINE | Mode.VISUAL_BLOCK:
                self.visual_handler.handle(key)
            case Mode.COMMAND:
                self._handle_command_key(key)

    # -----------------------------------------------------------------------
    # Command mode
    # -----------------------------------------------------------------------

    def _enter_command_mode(self, prefix: str = "") -> None:
        self._command_buffer = prefix
        self.mode = Mode.COMMAND
        self._show_command_prompt()

    def _show_command_prompt(self) -> None:
        """Write the current command buffer to both the formula bar and status bar."""
        prompt = f":{self._command_buffer}"
        self.status_bar.set_persistent_message(prompt)
        # Also show in formula bar content area (reliable fallback)
        with contextlib.suppress(Exception):
            self.formula_bar.formula_text = prompt

    def _handle_command_key(self, key: str) -> None:
        match key:
            case "escape":
                self.mode = Mode.NORMAL
                self._command_buffer = ""
                self.status_bar.set_persistent_message("")
            case "enter":
                cmd = self._command_buffer.strip()
                self._command_buffer = ""
                self.mode = Mode.NORMAL
                self._dispatch_command(cmd)
            case "backspace":
                self._command_buffer = self._command_buffer[:-1]
                self._show_command_prompt()
            case _ if len(key) == 1 and key.isprintable():
                self._command_buffer += key
                self._show_command_prompt()
        self._sync_formula_bar()
        self._sync_status_bar()

    def _dispatch_command(self, cmd: str) -> None:
        """Dispatch a colon command string (without the leading colon)."""
        parts = cmd.split()
        if not parts:
            return

        # ---- Line/row-number jump: :42 ----
        if cmd.isdigit():
            row = int(cmd) - 1
            self.grid.move_cursor(max(0, row), self.cursor_col)
            return

        match parts[0]:
            # ---- File operations ----
            case "q" | "quit":
                if self.workbook.modified:
                    self.status_bar.show_message("Unsaved changes — use :q! to force quit")
                else:
                    self.exit()
            case "q!":
                self.exit()
            case "wq" | "x":
                self._save_and_quit()
            case "w" | "write":
                self._save_file(Path(parts[1]) if len(parts) > 1 else None)
            case "e" | "edit":
                if len(parts) == 2:
                    self._open_file(Path(parts[1]))
                else:
                    self.status_bar.show_message("Usage: :e <file>")
            case "ex" | "export":
                # :ex <file>          — export by extension
                # :ex <format> <file> — export with explicit format
                from pysheet.io.registry import _FORMAT_NAMES

                if len(parts) == 3 and parts[1].lower() in _FORMAT_NAMES:
                    self._export_file(parts[1].lower(), Path(parts[2]))
                elif len(parts) == 2:
                    self._save_file(Path(parts[1]))
                else:
                    self.status_bar.show_message("Usage: :ex <file>  or  :ex <format> <file>")
            case "f" | "file":
                self._show_file_info()

            # ---- Sheet management ----
            case "addsheet" | "newsheet" | "sheet+":
                name = parts[1].strip("\"'") if len(parts) > 1 else None
                self.workbook.add_sheet(name)
                self.workbook.active_sheet_idx = len(self.workbook.sheets) - 1
                self._on_sheet_changed()
                self.workbook.modified = True
                self.status_bar.show_message(f"Added sheet: {self.workbook.active_sheet.name}")
            case "nextsheet":
                self.workbook.go_to_next_sheet()
                self._on_sheet_changed()
            case "prevsheet":
                self.workbook.go_to_prev_sheet()
                self._on_sheet_changed()
            case "delsheet" | "sheet-":
                if len(self.workbook.sheets) <= 1:
                    self.status_bar.show_message("Cannot delete the only sheet")
                else:
                    target_name = parts[1].strip("\"'") if len(parts) > 1 else None
                    if target_name:
                        idx = next(
                            (
                                i
                                for i, s in enumerate(self.workbook.sheets)
                                if s.name == target_name
                            ),
                            None,
                        )
                        if idx is None:
                            self.status_bar.show_message(f"Sheet not found: {target_name!r}")
                            return
                    else:
                        idx = self.workbook.active_sheet_idx
                    deleted_sheet = self.workbook.sheets[idx]
                    # Push to a simple undo list so the sheet can be restored
                    self._deleted_sheets.append((idx, deleted_sheet))
                    self.workbook.sheets.pop(idx)
                    self.workbook.active_sheet_idx = max(0, idx - 1)
                    self._on_sheet_changed()
                    self.workbook.modified = True
                    self.status_bar.show_message(
                        f"Deleted sheet: {deleted_sheet.name}  (undo with :undodelsheet)"
                    )
            case "renamesheet" | "renames":
                if len(parts) > 1:
                    new_name = parts[1].strip("\"'")
                    self.workbook.active_sheet.name = new_name
                    self._sync_sheet_tabs()
                    self.workbook.modified = True
                    self.status_bar.show_message(f"Sheet renamed to: {new_name}")
                else:
                    self.status_bar.show_message("Usage: :renamesheet <name>")
            case "sheet":
                if len(parts) > 1:
                    for i, s in enumerate(self.workbook.sheets):
                        if s.name == parts[1]:
                            self.workbook.go_to_sheet(i)
                            self._on_sheet_changed()
                            return
                    self.status_bar.show_message(f"Sheet not found: {parts[1]!r}")
                else:
                    self.status_bar.show_message(
                        f"Current sheet: {self.workbook.active_sheet.name}"
                    )

            # ---- Column width ----
            case "colwidth" | "cw":
                if len(parts) >= 2:
                    try:
                        w = int(parts[1])
                        self.workbook.active_sheet.set_col_width(self.cursor_col, w)
                        self.grid.refresh_grid()
                        self.status_bar.show_message(f"Column width set to {w}")
                    except ValueError:
                        self.status_bar.show_message("Usage: :colwidth <n>")
                else:
                    self.status_bar.show_message("Usage: :colwidth <n>")
            case "autofit" | "af":
                col = self.cursor_col
                self.workbook.active_sheet.auto_fit_col(col)
                self.grid.refresh_grid()
                self.status_bar.show_message(f"Auto-fit column {col + 1}")

            # ---- Sort ----
            case "funcs" | "functions":
                from pysheet.ui.funcs_screen import FuncsScreen

                term = parts[1] if len(parts) > 1 else ""
                self.push_screen(FuncsScreen(filter_term=term))

            case "fill":
                # :fill <value>                  — fill all cells with constant
                # :fill <start> <step>           — arithmetic sequence
                # :fill <start> <step> <func>    — sequence then apply func
                sel = self.grid.visual_selection()
                cr = sel if sel else None
                if cr is None:
                    self.status_bar.show_message("Select a range first (visual mode)")
                else:
                    self._cmd_fill(cr, parts[1:])

            case "sort":
                from pysheet.model.undo import SortCommand

                sheet = self.workbook.active_sheet
                col_arg = parts[1] if len(parts) > 1 else None
                asc = True
                if (
                    len(parts) > 2
                    and parts[2].lower() in ("desc", "d")
                    or len(parts) > 1
                    and parts[-1].lower() in ("desc", "d")
                ):
                    asc = False
                try:
                    if col_arg is None or col_arg.lower() in ("asc", "desc"):
                        sort_col = self.cursor_col
                    elif col_arg.isalpha():
                        sort_col = (
                            sum(
                                (ord(ch.upper()) - 64) * (26**i)
                                for i, ch in enumerate(reversed(col_arg.upper()))
                            )
                            - 1
                        )
                    else:
                        sort_col = int(col_arg) - 1
                    cmd = SortCommand(sheet, sort_col, asc)
                    self.undo_stack.push(cmd)
                    self.grid.refresh_grid()
                    self.workbook.modified = True
                    label = chr(65 + sort_col) if sort_col < 26 else str(sort_col + 1)
                    self.status_bar.show_message(
                        f"Sorted by col {label} ({'asc' if asc else 'desc'})"
                    )
                except (ValueError, IndexError) as e:
                    self.status_bar.show_message(f"Sort error: {e}")

            # ---- Recalculate ----
            case "recalc":
                sheet = self.workbook.active_sheet
                from pysheet.formula.evaluator import recalculate

                recalculate(sheet, sheet._dep_graph)
                self.grid.refresh_grid()
                self.status_bar.show_message("Recalculated")

            # ---- Goto cell ----
            case "goto" | "g":
                if len(parts) > 1:
                    try:
                        from pysheet.model.range import a1_to_rowcol

                        r, c = a1_to_rowcol(parts[1].upper())
                        self.grid.move_cursor(r, c)
                    except Exception:
                        self.status_bar.show_message(f"Invalid address: {parts[1]!r}")
                else:
                    self.status_bar.show_message("Usage: :goto <A1>")

            # ---- Freeze ----
            case "freeze":
                sheet = self.workbook.active_sheet
                try:
                    rows = int(parts[1]) if len(parts) > 1 else self.cursor_row
                    cols = int(parts[2]) if len(parts) > 2 else 0
                    sheet.freeze_rows = rows
                    sheet.freeze_cols = cols
                    self.grid.refresh_grid()
                    self.status_bar.show_message(f"Frozen: {rows} rows, {cols} cols")
                except (ValueError, IndexError):
                    self.status_bar.show_message("Usage: :freeze [rows] [cols]")
            case "unfreeze":
                sheet = self.workbook.active_sheet
                sheet.freeze_rows = 0
                sheet.freeze_cols = 0
                self.grid.refresh_grid()
                self.status_bar.show_message("Unfrozen")

            # ---- Search (also handles /pattern and ?pattern prefixes) ----
            case _ if parts[0].startswith("/") or parts[0] == "find":
                pattern = cmd[1:].strip() if parts[0].startswith("/") else " ".join(parts[1:])
                self._cmd_find(pattern)
            case _ if parts[0].startswith("?"):
                # ?pattern — reverse search (find then jump to last match)
                pattern = cmd[1:].strip()
                self._cmd_find(pattern)
                if self._search_state and self._search_state.matches:
                    self._cmd_find_prev()
            case "findnext":
                self._cmd_find_next()
            case "findprev":
                self._cmd_find_prev()
            case "replace":
                if len(parts) >= 3:
                    self._cmd_replace_all(parts[1], parts[2])
                else:
                    self.status_bar.show_message("Usage: :replace <pattern> <replacement>")
            case "replaceall":
                if len(parts) >= 3:
                    self._cmd_replace_all(parts[1], parts[2])
                else:
                    self.status_bar.show_message("Usage: :replaceall <pattern> <replacement>")

            # ---- Plot ----
            case "plot":
                # :plot [range] <type> [title]
                # :plot line  /  :plot A1:B5 bar  /  :A1:B5 plot line
                _chart_types = {"line", "bar", "scatter", "pie", "histogram", "hist"}
                if (
                    len(parts) > 1
                    and parts[1].upper() not in {t.upper() for t in _chart_types}
                    and ":" in parts[1]
                ):
                    # :plot <range> <type>
                    data_range = parts[1]
                    chart_type = parts[2] if len(parts) > 2 else "bar"
                    title = " ".join(parts[3:]) if len(parts) > 3 else ""
                else:
                    data_range = ""
                    chart_type = parts[1] if len(parts) > 1 else "bar"
                    title = " ".join(parts[2:]) if len(parts) > 2 else ""
                self._cmd_plot(data_range, chart_type, title)
            case _ if len(parts) >= 2 and parts[1] == "fill":
                # <range> fill [start] [step] [func]
                from pysheet.model.range import CellRange

                try:
                    cr = CellRange.from_a1(parts[0].upper())
                    self._cmd_fill(cr, parts[2:])
                except Exception as e:
                    self.status_bar.show_message(f"Fill error: {e}")

            case _ if len(parts) >= 2 and parts[1] == "plot":
                # <range> plot <type> [title]  — range pre-filled from visual mode
                data_range = parts[0]
                chart_type = parts[2] if len(parts) > 2 else "bar"
                title = " ".join(parts[3:]) if len(parts) > 3 else ""
                self._cmd_plot(data_range, chart_type, title)

            # ---- Cell comment ----
            case "comment" | "note":
                r, c = self.cursor_row, self.cursor_col
                if len(parts) > 1:
                    comment_text = " ".join(parts[1:])
                    sheet = self.workbook.active_sheet
                    cell = sheet.get_cell(r, c)
                    if cell is None:
                        sheet.set_cell_value(r, c, None)
                        cell = sheet.get_cell(r, c)
                    cell.comment = comment_text  # type: ignore[union-attr]
                    self.workbook.modified = True
                    self.status_bar.show_message(f"Comment set on {self.cursor}")
                else:
                    cell = self.workbook.active_sheet.get_cell(r, c)
                    msg = cell.comment if cell and cell.comment else "(no comment)"
                    self.status_bar.show_message(f"Comment: {msg}")

            # ---- Named ranges ----
            case "name":
                if len(parts) >= 3:
                    name, range_str = parts[1], parts[2].upper()
                    self.workbook.active_sheet.named_ranges.define(name.upper(), range_str)
                    self.workbook.modified = True
                    self.status_bar.show_message(f"Named range: {name.upper()} = {range_str}")
                elif len(parts) == 2:
                    name = parts[1].upper()
                    val = self.workbook.active_sheet.named_ranges.resolve(name)
                    self.status_bar.show_message(
                        f"{name} = {val}" if val else f"{name}: not defined"
                    )
                else:
                    self.status_bar.show_message("Usage: :name <NAME> <A1:B5>  or  :name <NAME>")

            # ---- Data validation ----
            case "validate":
                # :validate list val1,val2,val3
                # :validate number gt 0
                # :validate integer between 1 100
                # :validate clear
                r, c = self.cursor_row, self.cursor_col
                sheet = self.workbook.active_sheet
                if not parts[1:] or parts[1] == "clear":
                    sheet.validation.remove(r, c)
                    self.status_bar.show_message("Validation cleared")
                else:
                    rule_type = parts[1].lower()
                    from pysheet.model.validation import ValidationRule

                    rule: ValidationRule
                    if rule_type == "list" and len(parts) > 2:
                        choices = parts[2].split(",")
                        rule = ValidationRule(rule_type="list", choices=choices)
                    elif rule_type in ("number", "integer") and len(parts) > 3:
                        op = parts[2].lower()
                        v1 = float(parts[3])
                        v2 = float(parts[4]) if len(parts) > 4 else None
                        rule = ValidationRule(
                            rule_type=rule_type, operator=op, value1=v1, value2=v2
                        )
                    else:
                        rule = ValidationRule(rule_type=rule_type)
                    sheet.validation.add(r, c, rule)
                    self.status_bar.show_message(f"Validation set: {rule_type}")

            # ---- Cell history ----
            case "history":
                if len(parts) > 1:
                    try:
                        from pysheet.model.range import a1_to_rowcol

                        r, c = a1_to_rowcol(parts[1].upper())
                    except Exception:
                        r, c = self.cursor_row, self.cursor_col
                else:
                    r, c = self.cursor_row, self.cursor_col
                from pysheet.model.range import rowcol_to_a1 as _r2a

                addr = _r2a(r, c)
                cell = self.workbook.active_sheet.get_cell(r, c)
                if cell:
                    entries = [f"{t.strftime('%H:%M:%S')}={v}" for t, v in cell.history[-5:]]
                    entries.append(f"current={cell.value}")
                    self.status_bar.show_message(f"{addr} history: {'; '.join(entries)}")
                else:
                    self.status_bar.show_message(f"No history for {addr}")

            # ---- Filter ----
            case "filter":
                # :filter <col_letter> <op> <value>   e.g. :filter A gt 10
                if len(parts) >= 4:
                    from pysheet.model.sheet import FilterRule

                    col_letter = parts[1].upper()
                    try:
                        filter_col = (
                            sum(
                                (ord(ch) - 64) * (26**i)
                                for i, ch in enumerate(reversed(col_letter))
                            )
                            - 1
                        )
                    except Exception:
                        self.status_bar.show_message("Usage: :filter <col> <op> <value>")
                        return
                    op = parts[2].lower()
                    val_str = parts[3]
                    try:
                        val: Any = float(val_str)
                    except ValueError:
                        val = val_str
                    self.workbook.active_sheet.filters[filter_col] = FilterRule(
                        operator=op, value=val
                    )
                    self.workbook.active_sheet.apply_filters()
                    self.grid.refresh_grid()
                    self.status_bar.show_message(f"Filter: col {col_letter} {op} {val_str}")
                else:
                    self.status_bar.show_message("Usage: :filter <col> <op> <value>")
            case "clearfilter":
                sheet = self.workbook.active_sheet
                sheet.filters.clear()
                sheet.hidden_rows -= sheet._filter_rows
                sheet._filter_rows = set()
                self.grid.refresh_grid()
                self.status_bar.show_message("Filter cleared")

            # ---- Set options ----
            case "set":
                if len(parts) >= 2:
                    option = parts[1].lower()
                    match option:
                        case "autocalc":
                            self._autocalc = not getattr(self, "_autocalc", True)
                            self.status_bar.show_message(
                                f"autocalc {'on' if self._autocalc else 'off'}"
                            )
                        case _:
                            self.status_bar.show_message(f"Unknown option: {option!r}")
                else:
                    self.status_bar.show_message("Usage: :set <option>")

            # ---- Undo delete sheet ----
            case "undodelsheet":
                if hasattr(self, "_deleted_sheets") and self._deleted_sheets:
                    idx, sheet = self._deleted_sheets.pop()
                    self.workbook.sheets.insert(idx, sheet)
                    self.workbook.active_sheet_idx = idx
                    self._on_sheet_changed()
                    self.status_bar.show_message(f"Restored sheet: {sheet.name}")
                else:
                    self.status_bar.show_message("Nothing to restore")

            # ---- Cell formatting ----
            case "format" | "fmt":
                # :format <addr> color <#rrggbb>
                # :format <addr> bg <#rrggbb>
                # :format <addr> bold | italic | underline
                from pysheet.model.range import a1_to_rowcol
                from pysheet.model.undo import FormatCommand

                if len(parts) >= 3:
                    try:
                        r, c = a1_to_rowcol(parts[1].upper())
                    except Exception:
                        self.status_bar.show_message(f"Invalid address: {parts[1]!r}")
                        return
                    prop = parts[2].lower()
                    val_str = parts[3] if len(parts) > 3 else ""
                    match prop:
                        case "color" | "fg":
                            cmd = FormatCommand(self.workbook.active_sheet, r, c, fg_color=val_str)
                        case "bg" | "background":
                            cmd = FormatCommand(self.workbook.active_sheet, r, c, bg_color=val_str)
                        case "bold":
                            cmd = FormatCommand(self.workbook.active_sheet, r, c, bold=True)
                        case "italic":
                            cmd = FormatCommand(self.workbook.active_sheet, r, c, italic=True)
                        case "underline":
                            cmd = FormatCommand(self.workbook.active_sheet, r, c, underline=True)
                        case _:
                            self.status_bar.show_message(f"Unknown format property: {prop!r}")
                            return
                    self.undo_stack.push(cmd)
                    self.grid.refresh_grid()
                    self.workbook.modified = True
                    self.status_bar.show_message(f"Formatted {parts[1].upper()}: {prop} {val_str}")
                else:
                    self.status_bar.show_message(
                        "Usage: :format <addr> color|bg|bold|italic|underline [value]"
                    )

            # ---- Conditional formatting ----
            case "condformat" | "cond" | "cf":
                # :cond <range> <op> <value> [color <#hex>] [bg <#hex>] [bold] [italic]
                # :cond A1:A10 gt 50 color #ff0000
                # :cond clear
                sheet = self.workbook.active_sheet
                try:
                    if len(parts) > 1 and parts[1] == "clear":
                        sheet.cond_formats.clear()
                        self.grid.refresh_grid()
                        self.status_bar.show_message("All conditional formatting cleared")
                    elif len(parts) >= 4:
                        from pysheet.model.cell import CellFormat
                        from pysheet.model.sheet import CondFormatRule

                        range_str = parts[1].upper()
                        op = parts[2].lower()
                        val_str = parts[3]
                        try:
                            value: Any = float(val_str)
                        except ValueError:
                            value = val_str
                        fmt = CellFormat()
                        extras = parts[4:]
                        i = 0
                        while i < len(extras):
                            tok = extras[i].lower()
                            if tok in ("color", "fg") and i + 1 < len(extras):
                                fmt.fg_color = extras[i + 1]
                                i += 2
                            elif tok in ("bg", "background") and i + 1 < len(extras):
                                fmt.bg_color = extras[i + 1]
                                i += 2
                            elif tok.startswith("fg="):
                                fmt.fg_color = extras[i][3:]
                                i += 1
                            elif tok.startswith("bg="):
                                fmt.bg_color = extras[i][3:]
                                i += 1
                            elif tok == "bold":
                                fmt.bold = True
                                i += 1
                            elif tok == "italic":
                                fmt.italic = True
                                i += 1
                            else:
                                i += 1
                        rule = CondFormatRule(
                            range_str=range_str, operator=op, value=value, fmt=fmt
                        )
                        sheet.cond_formats.append(rule)
                        self.grid.refresh_grid()
                        self.workbook.modified = True
                        self.status_bar.show_message(f"Cond format: {range_str} {op} {val_str}")
                    else:
                        self.status_bar.show_message(
                            "Usage: :cond <range> <op> <value> [color #hex] [bg #hex] [bold]"
                        )
                except Exception as exc:
                    self.status_bar.show_message(f"Condformat error: {exc}")

            # ---- Hide / show rows and cols ----
            case "hiderow":
                r = int(parts[1]) - 1 if len(parts) > 1 else self.cursor_row
                self.workbook.active_sheet.hidden_rows.add(r)
                self.workbook.modified = True
                self.grid.refresh_grid()
                self.status_bar.show_message(f"Hidden row {r + 1}")
            case "showrow":
                r = int(parts[1]) - 1 if len(parts) > 1 else self.cursor_row
                self.workbook.active_sheet.hidden_rows.discard(r)
                self.workbook.modified = True
                self.grid.refresh_grid()
                self.status_bar.show_message(f"Shown row {r + 1}")
            case "hidecol":
                c = int(parts[1]) - 1 if len(parts) > 1 else self.cursor_col
                self.workbook.active_sheet.hidden_cols.add(c)
                self.workbook.modified = True
                self.grid.refresh_grid()
                self.status_bar.show_message(f"Hidden col {c + 1}")
            case "showcol":
                c = int(parts[1]) - 1 if len(parts) > 1 else self.cursor_col
                self.workbook.active_sheet.hidden_cols.discard(c)
                self.workbook.modified = True
                self.grid.refresh_grid()
                self.status_bar.show_message(f"Shown col {c + 1}")

            # ---- Row / col grouping ----
            case "rowgroup":
                if len(parts) >= 3:
                    try:
                        r1, r2 = int(parts[1]) - 1, int(parts[2]) - 1
                        grp = (min(r1, r2), max(r1, r2))
                        self.workbook.active_sheet.row_groups.append(grp)
                        self.workbook.modified = True
                        self.status_bar.show_message(f"Row group: rows {r1+1}–{r2+1}")
                    except ValueError:
                        self.status_bar.show_message("Usage: :rowgroup <r1> <r2>")
                else:
                    self.status_bar.show_message("Usage: :rowgroup <r1> <r2>")
            case "colgroup":
                if len(parts) >= 3:
                    try:
                        c1, c2 = int(parts[1]) - 1, int(parts[2]) - 1
                        grp = (min(c1, c2), max(c1, c2))
                        self.workbook.active_sheet.col_groups.append(grp)
                        self.workbook.modified = True
                        self.status_bar.show_message(f"Col group: cols {c1+1}–{c2+1}")
                    except ValueError:
                        self.status_bar.show_message("Usage: :colgroup <c1> <c2>")
                else:
                    self.status_bar.show_message("Usage: :colgroup <c1> <c2>")

            # ---- Theme ----
            case "theme":
                theme_name = parts[1].lower() if len(parts) > 1 else ""
                self._apply_theme(theme_name)

            # ---- External scripts ----
            case "func":
                # :func <NAME> <script_path>
                if len(parts) >= 3:
                    self._register_script_func(parts[1].upper(), parts[2])
                else:
                    self.status_bar.show_message("Usage: :func <NAME> <script_path>")

            # ---- Load plain-text file into cells ----
            case "loadtext" | "lt":
                if len(parts) >= 2:
                    delim = parts[2] if len(parts) >= 3 else None
                    self._cmd_loadtext(parts[1], delim)
                else:
                    self.status_bar.show_message("Usage: :loadtext <file> [delimiter]")

            # ---- Fetch commands ----
            case "fetchnow":
                addr = parts[1].upper() if len(parts) > 1 else ""
                if addr:
                    self._cmd_fetchnow(addr)
                else:
                    self.status_bar.show_message("Usage: :fetchnow <A1>")
            case "fetchstop":
                target = parts[1] if len(parts) > 1 else "all"
                self._cmd_fetchstop(target)
            case "fetchlist":
                self._cmd_fetchlist()

            # ---- Misc ----
            case "version":
                self.status_bar.show_message("PySheet 0.1.0")
            case "help":
                from pysheet.ui.help_screen import HelpScreen

                self.push_screen(HelpScreen())
            case _ if "!" in parts[0]:
                # <range>!<script>  — no space variant
                range_part, _, script_part = parts[0].partition("!")
                self._run_external_script(range_part.upper(), script_part)
            case _ if len(parts) >= 2 and parts[1].startswith("!"):
                # <range> !<script>  — space variant
                script_part = parts[1][1:] or (" ".join(parts[2:]) if len(parts) > 2 else "")
                self._run_external_script(parts[0].upper(), script_part)
            case _ if len(parts) == 2 and ":" in parts[0] and parts[
                1
            ].upper() in self._get_script_func_names():
                # :<range> <FUNCNAME>  — apply registered script function to range in place
                self._apply_script_func_to_range(parts[0].upper(), parts[1].upper())
            # ---- Fetch range commands: <range> fetchstop / fetchnow ----
            case _ if len(parts) == 2 and parts[1].lower() == "fetchstop":
                self._cmd_fetchstop_range(parts[0].upper())
            case _ if len(parts) == 2 and parts[1].lower() == "fetchnow":
                self._cmd_fetchnow_range(parts[0].upper())
            case _:
                self.status_bar.show_message(f"Unknown command: {cmd!r}")

    def _cmd_loadtext(self, filepath: str, delimiter: str | None) -> None:
        """Load a plain-text file and fill cells from the current cursor.

        Each line becomes a row.  If *delimiter* is given (tab/comma/space/|)
        each line is split into multiple columns.  Values are coerced to
        numbers where possible.
        """
        from pysheet.io.csv_adapter import _coerce as csv_coerce
        from pysheet.model.undo import FillRangeCommand

        path = Path(filepath).expanduser()
        if not path.exists():
            self.status_bar.show_message(f"File not found: {filepath}")
            return

        _DELIM_MAP = {
            "tab": "\t",
            "comma": ",",
            "space": " ",
            "pipe": "|",
            "|": "|",
            ",": ",",
            ";": ";",
        }
        sep: str | None = _DELIM_MAP.get(delimiter.lower(), delimiter) if delimiter else None

        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        base_row, base_col = self.cursor_row, self.cursor_col

        updates: list[tuple[int, int, Any]] = []
        for dr, line in enumerate(lines):
            if not line.strip():
                continue
            cells = [csv_coerce(c) for c in line.split(sep)] if sep else [csv_coerce(line.strip())]
            for dc, val in enumerate(cells):
                if val is not None:
                    updates.append((base_row + dr, base_col + dc, val))

        if not updates:
            self.status_bar.show_message("No data loaded")
            return

        sheet = self.workbook.active_sheet
        cmd = FillRangeCommand(sheet, updates)
        self.undo_stack.push(cmd)
        self.workbook.modified = True
        self.grid.refresh_grid()
        self._sync_formula_bar()
        self.status_bar.show_message(f"Loaded {len(updates)} cells from {path.name}")

    # -----------------------------------------------------------------------
    # Fetch helpers
    # -----------------------------------------------------------------------

    def _cmd_fetchnow(self, addr: str) -> None:
        from pysheet.model.range import a1_to_rowcol

        try:
            r, c = a1_to_rowcol(addr)
        except Exception:
            self.status_bar.show_message(f"Invalid address: {addr!r}")
            return
        key = (self.workbook.active_sheet.name, r, c)
        self.fetch_manager.fetch_now(key)
        self.status_bar.show_message(f"Fetching {addr}…")

    def _cmd_fetchstop(self, target: str) -> None:
        if target.lower() == "all":
            self.fetch_manager.cancel_all()
            self.status_bar.show_message("All fetches stopped")
            return
        from pysheet.model.range import a1_to_rowcol

        try:
            r, c = a1_to_rowcol(target.upper())
        except Exception:
            self.status_bar.show_message(f"Invalid address: {target!r}")
            return
        key = (self.workbook.active_sheet.name, r, c)
        self.fetch_manager.cancel(key)
        self.status_bar.show_message(f"Fetch stopped for {target.upper()}")

    def _cmd_fetchlist(self) -> None:
        from pysheet.ui.fetch_list_screen import FetchListScreen

        entries = self.fetch_manager.all_entries()
        if not entries:
            self.status_bar.show_message("No active fetches")
            return
        self.push_screen(FetchListScreen(entries))

    def _cmd_fetchnow_range(self, range_str: str) -> None:
        from pysheet.model.range import CellRange

        try:
            cr = CellRange.from_a1(range_str)
        except Exception:
            self.status_bar.show_message(f"Invalid range: {range_str!r}")
            return
        sheet_name = self.workbook.active_sheet.name
        count = 0
        for r in range(cr.start_row, cr.end_row + 1):
            for c in range(cr.start_col, cr.end_col + 1):
                key = (sheet_name, r, c)
                if key in {k for k, _ in self.fetch_manager.all_entries()}:
                    self.fetch_manager.fetch_now(key)
                    count += 1
        self.status_bar.show_message(f"Re-fetching {count} cell{'s' if count != 1 else ''}")

    def _cmd_fetchstop_range(self, range_str: str) -> None:
        from pysheet.model.range import CellRange

        try:
            cr = CellRange.from_a1(range_str)
        except Exception:
            self.status_bar.show_message(f"Invalid range: {range_str!r}")
            return
        sheet_name = self.workbook.active_sheet.name
        count = 0
        for r in range(cr.start_row, cr.end_row + 1):
            for c in range(cr.start_col, cr.end_col + 1):
                key = (sheet_name, r, c)
                self.fetch_manager.cancel(key)
                count += 1
        self.status_bar.show_message(f"Stopped fetches for {count} cell{'s' if count != 1 else ''}")

    # -----------------------------------------------------------------------
    # Search helpers
    # -----------------------------------------------------------------------

    def _cmd_find(self, pattern: str) -> None:
        """Find all matches for *pattern* and jump to the first one."""
        state = SearchState(pattern=pattern)
        searcher = Searcher(self.workbook.active_sheet)
        matches = searcher.find_all(state)
        state.matches = matches
        self._search_state = state
        if matches:
            state.current_match = matches[0]
            self.grid.move_cursor(*matches[0])
            self.status_bar.show_message(f"/{pattern}  [{1}/{len(matches)}]")
        else:
            self.status_bar.show_message(f"Pattern not found: {pattern!r}")

    def _cmd_find_next(self) -> None:
        """Jump to the next search match."""
        if self._search_state is None or not self._search_state.pattern:
            self.status_bar.show_message("No search pattern — use :find <pattern>")
            return
        state = self._search_state
        searcher = Searcher(self.workbook.active_sheet)
        nxt = searcher.find_next(state, self.cursor)
        if nxt:
            state.current_match = nxt
            self.grid.move_cursor(*nxt)
            self.status_bar.show_message(f"/{state.pattern}  [next]")
        else:
            self.status_bar.show_message("No matches")

    def _cmd_find_prev(self) -> None:
        """Jump to the previous search match."""
        if self._search_state is None or not self._search_state.pattern:
            self.status_bar.show_message("No search pattern — use :find <pattern>")
            return
        state = self._search_state
        searcher = Searcher(self.workbook.active_sheet)
        prv = searcher.find_prev(state, self.cursor)
        if prv:
            state.current_match = prv
            self.grid.move_cursor(*prv)
            self.status_bar.show_message(f"/{state.pattern}  [prev]")
        else:
            self.status_bar.show_message("No matches")

    def _cmd_replace(self, pattern: str, replacement: str) -> None:
        """Replace the first occurrence at the cursor."""
        state = SearchState(pattern=pattern, replace=replacement)
        self._search_state = state
        searcher = Searcher(self.workbook.active_sheet)
        replaced = searcher.replace_one(state, self.cursor_row, self.cursor_col)
        if replaced:
            self.workbook.modified = True
            self.grid.refresh_grid()
            self.status_bar.show_message(f"Replaced at {self.cursor}")
        else:
            self.status_bar.show_message("No match at cursor")

    def _cmd_replace_all(self, pattern: str, replacement: str) -> None:
        """Replace all occurrences and show the count."""
        state = SearchState(pattern=pattern, replace=replacement)
        self._search_state = state
        searcher = Searcher(self.workbook.active_sheet)
        count = searcher.replace_all(state)
        if count:
            self.workbook.modified = True
            self.grid.refresh_grid()
        self.status_bar.show_message(f"Replaced {count} occurrence(s)")

    def _cmd_fill(self, cr: Any, args: list[str]) -> None:
        """Fill a CellRange with a constant, sequence, or string with optional transform.

        Numeric:  fill <start> [step] [func]   — arithmetic sequence + numeric transform
        String:   fill <text> [str_func]        — constant string + optional string transform
        """
        _NUM_TRANSFORMS: dict[str, Any] = {
            "double": lambda v: v * 2,
            "triple": lambda v: v * 3,
            "square": lambda v: v**2,
            "sqrt": lambda v: v**0.5,
            "half": lambda v: v / 2,
            "neg": lambda v: -v,
        }
        _STR_TRANSFORMS: dict[str, Any] = {
            "upper": str.upper,
            "lower": str.lower,
            "title": str.title,
            "capitalize": str.capitalize,
            "strip": str.strip,
            "reverse": lambda s: s[::-1],
        }

        sheet = self.workbook.active_sheet
        updates: list[tuple[int, int, Any]] = []

        if not args:
            # default: fill with 0, 1, 2 …
            for i, (r, c) in enumerate(
                (r, c)
                for r in range(cr.start_row, cr.end_row + 1)
                for c in range(cr.start_col, cr.end_col + 1)
            ):
                updates.append((r, c, i))
        else:
            first = args[0]
            # Detect string vs numeric by attempting float conversion
            try:
                start = float(first)
            except ValueError:
                # ── String fill ──────────────────────────────────────────
                str_func_name = args[1].lower() if len(args) >= 2 else None
                str_transform = _STR_TRANSFORMS.get(str_func_name) if str_func_name else None
                if str_func_name and str_transform is None:
                    self.status_bar.show_message(
                        f"Fill: unknown string function '{str_func_name}'. "
                        f"Use: {', '.join(_STR_TRANSFORMS)}"
                    )
                    return
                value: str = str_transform(first) if str_transform else first
                for r in range(cr.start_row, cr.end_row + 1):
                    for c in range(cr.start_col, cr.end_col + 1):
                        updates.append((r, c, value))
            else:
                # ── Numeric fill ─────────────────────────────────────────
                step: float | None
                func_name: str | None
                if len(args) == 1:
                    step, func_name = None, None
                elif len(args) == 2:
                    try:
                        step, func_name = float(args[1]), None
                    except ValueError:
                        step, func_name = None, args[1].lower()
                else:
                    try:
                        step, func_name = float(args[1]), args[2].lower()
                    except ValueError:
                        self.status_bar.show_message("Fill: invalid numeric args")
                        return

                transform = _NUM_TRANSFORMS.get(func_name) if func_name else None
                if func_name and transform is None:
                    self.status_bar.show_message(
                        f"Fill: unknown function '{func_name}'. "
                        f"Use: {', '.join(_NUM_TRANSFORMS)}"
                    )
                    return

                i = 0
                for r in range(cr.start_row, cr.end_row + 1):
                    for c in range(cr.start_col, cr.end_col + 1):
                        val: float = start if step is None else start + i * step
                        if transform:
                            val = transform(val)
                        stored: Any = (
                            int(val) if isinstance(val, float) and val.is_integer() else val
                        )
                        updates.append((r, c, stored))
                        i += 1

        from pysheet.model.undo import FillRangeCommand

        cmd = FillRangeCommand(sheet, updates)
        self.undo_stack.push(cmd)
        self.workbook.modified = True
        self.grid.refresh_grid()
        self._sync_formula_bar()
        self.status_bar.show_message(f"Filled {len(updates)} cells")

    def _cmd_plot(self, data_range: str, chart_type: str = "bar", title: str = "") -> None:
        """Render a chart for *data_range* and display it in a full-screen modal."""
        from pysheet.plotting.chart import ChartSpec, render_chart
        from pysheet.ui.chart_screen import ChartScreen

        if not data_range:
            sheet = self.workbook.active_sheet
            from pysheet.model.range import rowcol_to_a1

            top = rowcol_to_a1(0, self.cursor_col)
            bot = rowcol_to_a1(sheet.max_row, self.cursor_col)
            data_range = f"{top}:{bot}"
        spec = ChartSpec(
            chart_type=chart_type,
            data_range=data_range,
            title=title or f"{chart_type.title()} — {data_range}",
            width=80,
            height=22,
        )
        chart = render_chart(self.workbook.active_sheet, spec)
        self.push_screen(ChartScreen(chart_text=chart, title=spec.title))

    # -----------------------------------------------------------------------
    # Insert mode entry
    # -----------------------------------------------------------------------

    def _enter_insert(self, align: str = "right") -> None:
        cell = self.workbook.active_sheet.get_cell(self.cursor_row, self.cursor_col)
        if cell is not None and cell.locked:
            self.status_bar.show_message("Cell is locked — use 'ru' to unlock")
            return
        self._insert_buffer = ""
        self._insert_cursor = 0
        self._insert_align = align
        self.mode = Mode.INSERT
        self._sync_formula_bar()

    # -----------------------------------------------------------------------
    # External scripts
    # -----------------------------------------------------------------------

    def __run_external_script(self, range_str: str, script_path: str) -> None:
        """Pipe *range_str* data to *script_path* and apply JSON results back."""
        import json
        import subprocess
        import sys as _sys
        from pathlib import Path as _Path

        from pysheet.model.range import CellRange, a1_to_rowcol, rowcol_to_a1

        script = _Path(script_path)
        if not script.exists():
            self.status_bar.show_message(f"Script not found: {script_path}")
            return

        sheet = self.workbook.active_sheet
        try:
            cr = CellRange.from_a1(range_str)
        except Exception as e:
            self.status_bar.show_message(f"Invalid range {range_str!r}: {e}")
            return

        # Build payload: {"rows": [{"_row": 1, "A": 10, ...}, ...]}
        rows_data = []
        for r in range(cr.start_row, cr.end_row + 1):
            row: dict[str, Any] = {"_row": r + 1}
            for c in range(cr.start_col, cr.end_col + 1):
                col_letter = chr(65 + c) if c < 26 else rowcol_to_a1(0, c)[:-1]
                cell = sheet.get_cell(r, c)
                val = cell.value if cell else None
                # coerce string-numbers so scripts receive proper numeric types
                if isinstance(val, str):
                    try:
                        val = int(val)
                    except ValueError:
                        with contextlib.suppress(ValueError):
                            val = float(val)
                row[col_letter] = val
            rows_data.append(row)
        payload = json.dumps({"rows": rows_data})

        try:
            proc = subprocess.run(
                [_sys.executable, str(script)],
                input=payload + "\n",
                capture_output=True,
                text=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            self.status_bar.show_message("Script timed out")
            return
        except Exception as exc:
            self.status_bar.show_message(f"Script error: {exc}")
            return

        if proc.returncode != 0:
            err = (proc.stderr or "unknown error").strip()[:100]
            self.status_bar.show_message(f"Script stderr: {err}")
            return

        # Process output lines
        from pysheet.model.undo import CompositeCommand, SetCellCommand

        cmds = []
        messages = []
        for line in proc.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            match obj.get("type"):
                case "cell":
                    addr = obj.get("address", "").upper()
                    value = obj.get("value")
                    try:
                        r2, c2 = a1_to_rowcol(addr)
                        cmds.append(SetCellCommand(sheet, r2, c2, value))
                    except Exception:
                        pass
                case "message":
                    messages.append(str(obj.get("text", "")))
                case "done":
                    break

        if cmds:
            from pysheet.model.undo import CompositeCommand

            self.undo_stack.push(CompositeCommand(cmds))
            self.workbook.modified = True
            self.grid.refresh_grid()

        msg = f"Script done: {len(cmds)} cell(s) updated"
        if messages:
            msg = messages[-1]
        self.status_bar.show_message(msg)
        return

    def _run_external_script(self, range_str: str, script_path: str) -> None:
        try:
            self.__run_external_script(range_str, script_path)
        except Exception as exc:
            self.status_bar.show_message(f"Script fatal: {exc}")

    _script_funcs: dict[str, str] = {}

    def _register_script_func(self, name: str, script_path: str) -> None:
        """Register *script_path* as formula function *name*."""
        from pathlib import Path as _Path

        script = _Path(script_path)
        if not script.exists():
            self.status_bar.show_message(f"Script not found: {script_path}")
            return
        self._script_funcs[name] = str(script)
        from pysheet.formula.functions.registry import register_script_function

        register_script_function(name, str(script))
        self.status_bar.show_message(f"Registered function: @{name}")

    def _get_script_func_names(self) -> set[str]:
        return set(self._script_funcs.keys())

    def _apply_script_func_to_range(self, range_str: str, func_name: str) -> None:
        """Apply a registered script function to *range_str* in place."""
        script_path = self._script_funcs.get(func_name)
        if not script_path:
            self.status_bar.show_message(
                f"Unknown function: {func_name} — use :func to register it"
            )
            return
        import json
        import subprocess
        import sys as _sys

        from pysheet.model.range import CellRange, a1_to_rowcol
        from pysheet.model.undo import CompositeCommand, SetCellCommand

        sheet = self.workbook.active_sheet
        try:
            cr = CellRange.from_a1(range_str)
        except Exception as e:
            self.status_bar.show_message(f"Invalid range: {e}")
            return

        rows_data = []
        for r in range(cr.start_row, cr.end_row + 1):
            for c in range(cr.start_col, cr.end_col + 1):
                col_letter = chr(65 + c) if c < 26 else f"C{c}"
                cell = sheet.get_cell(r, c)
                val = cell.value if cell else None
                if isinstance(val, str):
                    try:
                        val = int(val)
                    except ValueError:
                        with contextlib.suppress(ValueError):
                            val = float(val)
                rows_data.append({"_row": r + 1, col_letter: val})

        payload = json.dumps({"rows": rows_data})
        try:
            proc = subprocess.run(
                [_sys.executable, script_path],
                input=payload + "\n",
                capture_output=True,
                text=True,
                timeout=30,
            )
        except Exception as exc:
            self.status_bar.show_message(f"Script error: {exc}")
            return

        if proc.returncode != 0:
            self.status_bar.show_message(f"Script stderr: {proc.stderr.strip()[:80]}")
            return

        cmds = []
        for line in proc.stdout.splitlines():
            try:
                obj = json.loads(line)
                if obj.get("type") == "cell":
                    addr = obj.get("address", "").upper()
                    val = obj.get("value")
                    r2, c2 = a1_to_rowcol(addr)
                    cmds.append(SetCellCommand(sheet, r2, c2, val))
                elif obj.get("type") == "done":
                    break
            except Exception:
                pass

        if cmds:
            self.undo_stack.push(CompositeCommand(cmds))
            self.workbook.modified = True
            self.grid.refresh_grid()
        self.status_bar.show_message(f"{func_name}: {len(cmds)} cell(s) updated")

    # -----------------------------------------------------------------------
    # Macro replay
    # -----------------------------------------------------------------------

    def _replay_keys(self, keys: list[str]) -> None:
        """Inject a list of pre-recorded keys back into the key handler."""
        for key in keys:
            match self.mode:
                case Mode.NORMAL:
                    self.normal_handler.handle(key)
                case Mode.INSERT:
                    self.insert_handler.handle(key)
                case Mode.EDIT:
                    self.edit_handler.handle(key)
                case Mode.VISUAL | Mode.VISUAL_LINE | Mode.VISUAL_BLOCK:
                    self.visual_handler.handle(key)
        # Force visual update after replay completes
        self.grid.refresh_grid()
        self._sync_formula_bar()
        self._sync_status_bar()

    # -----------------------------------------------------------------------
    # Dot repeat
    # -----------------------------------------------------------------------

    def _repeat_last_action(self) -> None:
        if self._last_action is None:
            self.status_bar.show_message("Nothing to repeat")
            return
        action = self._last_action
        match action[0]:
            case "clear_cell":
                from pysheet.model.undo import ClearCellCommand

                r, c = self.cursor_row, self.cursor_col
                cmd = ClearCellCommand(self.workbook.active_sheet, r, c)
                self.undo_stack.push(cmd)
                self.workbook.modified = True
                self.grid.refresh_grid()
            case "paste":
                _, after, data = action
                from pysheet.model.undo import PasteCommand

                dr = 1 if after else 0
                r, c = self.cursor_row + dr, self.cursor_col
                cmd = PasteCommand(self.workbook.active_sheet, r, c, data)
                self.undo_stack.push(cmd)
                self.workbook.modified = True
                self.grid.refresh_grid()
            case _:
                self.status_bar.show_message("Cannot repeat this action")
        self._sync_formula_bar()
        self._sync_status_bar()

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _save_and_quit(self) -> None:
        self._save_file(None)
        self.exit()

    def _save_file(self, path: Path | None) -> None:
        target = path or self.workbook.filepath
        if target is None:
            self.status_bar.show_message("No filename — use :w <file>")
            return
        from pysheet.io.registry import get_adapter

        try:
            adapter = get_adapter(target)
            adapter.write(self.workbook, target)
            self.workbook.filepath = target
            self.workbook.modified = False
            self.status_bar.show_message(f"Written: {target}")
            self._sync_formula_bar()
            self._sync_status_bar()
        except Exception as exc:
            self.status_bar.show_message(f"Save error: {exc}")

    def _open_file(self, path: Path) -> None:
        from pysheet.io.registry import get_adapter

        try:
            adapter = get_adapter(path)
            self.workbook = adapter.read(path)
            self.workbook._bind_sheets()
            self.grid.workbook = self.workbook
            self.undo_stack.clear()
            self._on_sheet_changed()
            self._trigger_fetch_cells()
            self.status_bar.show_message(f"Opened: {path}")
        except Exception as exc:
            self.status_bar.show_message(f"Open error: {exc}")

    def _export_file(self, fmt: str, path: Path) -> None:
        from pysheet.io.registry import get_adapter_by_name

        try:
            adapter = get_adapter_by_name(fmt)
            adapter.write(self.workbook, path)
            self.status_bar.show_message(f"Exported ({fmt}): {path}")
        except Exception as exc:
            self.status_bar.show_message(f"Export error: {exc}")

    def _show_file_info(self) -> None:
        path = str(self.workbook.filepath) if self.workbook.filepath else "[no file]"
        sheet = self.workbook.active_sheet
        self.status_bar.show_message(
            f"{path}  —  {sheet.max_row + 1} rows × {sheet.max_col + 1} cols"
        )

    def _sync_formula_bar(self) -> None:
        r, c = self.cursor_row, self.cursor_col
        address = rowcol_to_a1(r, c)
        cell = self.workbook.active_sheet.get_cell(r, c)
        cursor_pos = -1
        match self.mode:
            case Mode.INSERT:
                content = self._insert_buffer
                cursor_pos = self._insert_cursor
            case Mode.EDIT:
                content = self._edit_buffer
                cursor_pos = self._edit_cursor
            case Mode.COMMAND:
                content = f":{self._command_buffer}"
            case _:
                content = (cell.formula or cell.display or "") if cell else ""
        locked = cell.locked if cell else False
        self.formula_bar.update_cell(address, content, locked, cursor_pos=cursor_pos)
        self.formula_bar.is_modified = self.workbook.modified
        self.formula_bar.mode = self.mode

    def _sync_status_bar(self) -> None:
        r, c = self.cursor_row, self.cursor_col
        self.status_bar.update_cursor(r, c, rowcol_to_a1(r, c))
        self.status_bar.mode = self.mode
        self.status_bar.sheet_name = self.workbook.active_sheet.name
        self.status_bar.used_rows = self.workbook.active_sheet.max_row + 1
        self.status_bar.filename = self.workbook.filepath.name if self.workbook.filepath else ""
        self.status_bar.file_modified = self.workbook.modified
        # Preserve the command prompt — don't overwrite with positional info
        if self.mode == Mode.COMMAND:
            self.status_bar.set_persistent_message(f":{self._command_buffer}")
            return
        if self.mode.is_visual():
            sel = self.grid.visual_selection()
            if sel:
                self.status_bar.message = f"{sel.num_rows}r × {sel.num_cols}c selected"
        if self.macro_recorder.is_recording:
            reg = self.macro_recorder.recording_register
            self.status_bar.message = f"Recording @{reg}..."

    def _on_sheet_changed(self) -> None:
        self._sync_sheet_tabs()
        self.grid.move_cursor(0, 0)
        self.grid.refresh_grid()
        self._sync_formula_bar()
        self._sync_status_bar()

    def _sync_sheet_tabs(self) -> None:
        names = [s.name for s in self.workbook.sheets]
        self.sheet_tabs.set_sheets(names, self.workbook.active_sheet_idx)

    def _apply_theme(self, name: str) -> None:
        """Switch colour theme using Textual's built-in theme system."""
        _ALIASES = {
            "dark": "textual-dark",
            "light": "textual-light",
            "nord": "nord",
            "gruvbox": "gruvbox",
            "dracula": "dracula",
            "tokyo": "tokyo-night",
            "monokai": "monokai",
            "solarized": "solarized-dark",
            "solarized-light": "solarized-light",
            "catppuccin": "catppuccin-mocha",
            "rose-pine": "rose-pine",
        }
        resolved = _ALIASES.get(name, name)
        try:
            self.theme = resolved
            self.status_bar.show_message(f"Theme: {resolved}")
        except Exception:
            available = (
                "dark light nord gruvbox dracula tokyo monokai solarized catppuccin rose-pine"
            )
            self.status_bar.show_message(f"Unknown theme {name!r}. Try: {available}")

    def _fold_group(self, action: str) -> None:
        """Fold/unfold the row group containing the cursor row.

        action: 'close' | 'open' | 'toggle' | 'open_all' | 'close_all'
        """
        sheet = self.workbook.active_sheet
        row = self.cursor_row

        if action == "open_all":
            sheet.hidden_rows.clear()
            self.grid.refresh_grid()
            self.status_bar.show_message("All row groups opened")
            return
        if action == "close_all":
            for r1, r2 in sheet.row_groups:
                for r in range(r1, r2 + 1):
                    sheet.hidden_rows.add(r)
            self.grid.refresh_grid()
            self.status_bar.show_message("All row groups closed")
            return

        grp = next(((r1, r2) for r1, r2 in sheet.row_groups if r1 <= row <= r2), None)
        if grp is None:
            self.status_bar.show_message("No row group at cursor — use :rowgroup r1 r2 first")
            return
        r1, r2 = grp
        rows_in_group = set(range(r1, r2 + 1))
        currently_hidden = rows_in_group & sheet.hidden_rows

        if action == "close" or (action == "toggle" and not currently_hidden):
            sheet.hidden_rows |= rows_in_group
            self.status_bar.show_message(f"Folded rows {r1+1}–{r2+1}")
        else:
            sheet.hidden_rows -= rows_in_group
            self.status_bar.show_message(f"Unfolded rows {r1+1}–{r2+1}")
        self.workbook.modified = True
        self.grid.refresh_grid()

    # -----------------------------------------------------------------------
    # Message handlers
    # -----------------------------------------------------------------------

    def on_grid_widget_cursor_moved(self, message: GridWidget.CursorMoved) -> None:
        self._sync_formula_bar()
        self._sync_status_bar()

    def on_sheet_tabs_sheet_selected(self, message: SheetTabs.SheetSelected) -> None:
        self.workbook.go_to_sheet(message.index)
        self._on_sheet_changed()

    def on_sheet_tabs_add_sheet(self, _message: SheetTabs.AddSheet) -> None:
        self.workbook.add_sheet()
        self.workbook.active_sheet_idx = len(self.workbook.sheets) - 1
        self._on_sheet_changed()
