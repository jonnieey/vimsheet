"""VimSheet Textual application."""

from __future__ import annotations

import contextlib
import logging
import re
from pathlib import Path
from typing import Any

from textual.app import App, ComposeResult

from vimsheet.controller.edit_handler import EditHandler
from vimsheet.controller.insert_handler import InsertHandler
from vimsheet.controller.macro import MacroRecorder
from vimsheet.controller.mode import Mode
from vimsheet.controller.normal_handler import NormalHandler
from vimsheet.controller.search import Searcher, SearchState
from vimsheet.controller.visual_handler import VisualHandler
from vimsheet.model.config import _user_data_dir
from vimsheet.model.history import HistoryStack
from vimsheet.model.range import rowcol_to_a1
from vimsheet.model.register import RegisterEntry
from vimsheet.model.undo import UndoStack
from vimsheet.model.workbook import Workbook
from vimsheet.ui.formula_bar import FormulaBar
from vimsheet.ui.grid import GridWidget
from vimsheet.ui.grid_palette import GridPalette
from vimsheet.ui.header_bar import HeaderBar
from vimsheet.ui.sheet_tabs import SheetTabs
from vimsheet.ui.status_bar import StatusBar

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


class VimSheetApp(App[None]):
    """Main VimSheet application."""

    CSS = """
    Screen { layout: vertical; }
    """

    def __init__(
        self,
        workbook: Workbook | None = None,
        config: Any = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.workbook: Workbook = workbook or Workbook.blank()

        # ---- Config ----
        if config is None:
            from vimsheet.model.config import Config

            config = Config.load(Config.default_path())
        self.config = config

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
        self._visual_goto_buf: str | None = None  # accumulates address after "go" in visual
        self._pre_command_mode: Mode | None = None  # visual mode saved on entering command
        self._swap_buf: str | None = None
        self._swap_mode: str = ""  # "cell", "row", "col"
        self._swap_keep_cursor: bool = False
        self._yanked_formula: str | None = None  # formula string for P paste

        # ---- Registers / marks ----
        self._default_register: RegisterEntry | None = None
        self._registers: dict[str, RegisterEntry] = {}
        self._marks: dict[str, tuple[int, int, int]] = {}
        self._pending_register: str = ""  # set by "{a-z} prefix

        # ---- Repeat / last action ----
        self._last_action: tuple[Any, ...] | None = None

        # ---- Undo / macro ----
        self.undo_stack: UndoStack = UndoStack(max_size=self.config.max_undo)
        self.macro_recorder: MacroRecorder = MacroRecorder()

        # ---- Tab completion ----
        from vimsheet.command_completer import CommandCompleter

        self._cmd_completer: CommandCompleter = CommandCompleter(self)

        # ---- Command / search history ----
        self._cmd_history: HistoryStack = HistoryStack()
        self._search_history: HistoryStack = HistoryStack()
        self._load_history()

        # ---- Search state ----
        self._search_state: SearchState | None = None

        # ---- Deleted sheet undo buffer ----
        self._deleted_sheets: list[tuple[int, Any]] = []

        # ---- Buffer list (each entry is a Workbook) ----
        self._buffers: list[Workbook] = [self.workbook]
        self._active_buf_idx: int = 0

        # ---- Autosave timer handle ----
        self._autosave_handle: Any = None

        # ---- Inline yes/no confirmation (set by _ask_confirm) ----
        self._pending_confirm: tuple[str, Any] | None = None  # (prompt_text, callback)

        # ---- Macro replay guard (prevents recursive self-calling macros) ----
        self._replaying_macros: set[str] = set()

        # ---- Theme state ----
        self._current_theme_name: str = ""
        self._palette: GridPalette = GridPalette()

        # ---- Handlers (created after super().__init__ so App attrs exist) ----
        self.normal_handler = NormalHandler(self)
        self.insert_handler = InsertHandler(self)
        self.edit_handler = EditHandler(self)
        self.visual_handler = VisualHandler(self)

        # ---- HTTP fetch manager ----
        from vimsheet.fetch.fetch_manager import FetchManager, _set_global_manager

        self.fetch_manager: FetchManager = FetchManager(self)
        _set_global_manager(self.fetch_manager)

    # -----------------------------------------------------------------------
    # Layout
    # -----------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield HeaderBar(id="header-bar")
        yield FormulaBar(id="formula-bar")
        yield GridWidget(self.workbook, config=self.config, id="grid")
        yield SheetTabs(id="sheet-tabs")
        yield StatusBar(id="status-bar")

    def on_mount(self) -> None:
        # --theme CLI arg takes priority; fall back to config theme
        theme = getattr(self, "_startup_theme", None) or (
            self.config.theme if self.config.theme != "default" else None
        )
        if theme:
            self._apply_theme(theme)
        self._sync_sheet_tabs()
        # Apply config visibility settings
        if not self.config.formula_bar_visible:
            self.query_one("#formula-bar").display = False
        if not self.config.status_bar_visible:
            self.query_one("#status-bar").display = False
        # Apply autocalc to all sheets
        self.workbook.set_autocalc(self.config.autocalc)
        # Start autosave timer if enabled
        if self.config.autosave:
            self._start_autosave()
        self.status_bar.set_history_size(self.config.message_history_size)
        self._sync_formula_bar()
        self._sync_status_bar()
        self.grid.focus()
        self._trigger_fetch_cells()
        self._load_script_functions()
        # Restore saved cursor position (from .vimsheet file)
        if self.config.save_cursor:
            sheet = self.workbook.active_sheet
            self.grid.move_cursor(sheet.cursor_row, sheet.cursor_col)

    def on_unmount(self) -> None:
        self._save_history()
        self.fetch_manager.cancel_all()

    def _trigger_fetch_cells(self) -> None:
        """Re-evaluate every FETCH formula cell now that FetchManager is live.

        Formulas are evaluated during file load before the app (and FetchManager)
        exist, so FETCH cells land as #LOADING.  This pass re-runs them so the
        manager schedules background requests.
        """
        from vimsheet.formula.evaluator import Evaluator

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

        # Intercept pending y/n confirmation before all other routing
        if self._pending_confirm is not None:
            _, callback = self._pending_confirm
            if key == "y":
                self._pending_confirm = None
                self.status_bar.set_persistent_message("")
                callback()
            else:
                self._pending_confirm = None
                self.status_bar.show_message("Cancelled")
            return

        # Intercept swap address input (gx, grx, gcx)
        if self._swap_buf is not None:
            self._handle_swap_key(key)
            return

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
            case Mode.SEARCH:
                self._handle_search_key(key)

    # -----------------------------------------------------------------------
    # Command mode
    # -----------------------------------------------------------------------

    def _enter_command_mode(self, prefix: str = "") -> None:
        if self.mode.is_visual():
            self._pre_command_mode = self.mode
            self.grid.show_visual = True
        self._command_buffer = prefix
        self.mode = Mode.COMMAND
        self._show_command_prompt()

    def _show_command_prompt(self) -> None:
        """Write the current command buffer to both the formula bar and status bar."""
        prompt = f":{self._command_buffer}"
        self.status_bar.set_persistent_message(prompt)
        with contextlib.suppress(Exception):
            self.formula_bar.update_cell(
                self.formula_bar.cell_address,
                prompt,
                self.formula_bar.is_locked,
                cursor_pos=len(prompt),
            )

    def _current_history(self) -> HistoryStack:
        """Return the history stack relevant to the current command buffer."""
        if self._command_buffer.startswith("/") or self._command_buffer.startswith("?"):
            return self._search_history
        return self._cmd_history

    def _history_path(self) -> Path:
        return _user_data_dir() / "vimsheet" / "history.json"

    def _load_history(self) -> None:
        path = self._history_path()
        import json as _json

        max_size = getattr(self.config, "history_size", 50)
        try:
            data = _json.loads(path.read_text(encoding="utf-8"))
            self._cmd_history = HistoryStack(
                items=data.get("cmd", [])[-max_size:], max_size=max_size
            )
            self._search_history = HistoryStack(
                items=data.get("search", [])[-max_size:], max_size=max_size
            )
        except Exception:
            self._cmd_history = HistoryStack(max_size=max_size)
            self._search_history = HistoryStack(max_size=max_size)

    def _save_history(self) -> None:
        path = self._history_path()
        import json as _json

        path.parent.mkdir(parents=True, exist_ok=True)
        data = {"cmd": self._cmd_history.items, "search": self._search_history.items}
        path.write_text(_json.dumps(data), encoding="utf-8")

    def _handle_command_key(self, key: str) -> None:
        match key:
            case "escape":
                self._cmd_completer.reset()
                self._cmd_history.reset_browse()
                self._search_history.reset_browse()
                if self._pre_command_mode is not None:
                    self.mode = self._pre_command_mode
                    self._pre_command_mode = None
                else:
                    self.grid.show_visual = False
                    self.mode = Mode.NORMAL
                self._command_buffer = ""
                self.status_bar.set_persistent_message("")
            case "enter":
                self._cmd_completer.reset()
                self._cmd_history.reset_browse()
                self._search_history.reset_browse()
                cmd = self._command_buffer.strip()
                if cmd:
                    if cmd.startswith("/") or cmd.startswith("?"):
                        self._search_history.push(cmd[1:])
                    else:
                        self._cmd_history.push(cmd)
                    self._save_history()
                self._command_buffer = ""
                self._pre_command_mode = None
                self.grid.show_visual = False
                self.mode = Mode.NORMAL
                self._dispatch_command(cmd)
            case "up":
                hist = self._current_history()
                prev = hist.prev()
                if prev is not None:
                    prefix = ""
                    if self._command_buffer.startswith("/"):
                        prefix = "/"
                    elif self._command_buffer.startswith("?"):
                        prefix = "?"
                    self._command_buffer = prefix + prev
                    self._show_command_prompt()
            case "down":
                hist = self._current_history()
                nxt = hist.next()
                prefix = ""
                if self._command_buffer.startswith("/"):
                    prefix = "/"
                elif self._command_buffer.startswith("?"):
                    prefix = "?"
                if nxt is not None:
                    self._command_buffer = prefix + nxt
                else:
                    self._command_buffer = prefix
                self._show_command_prompt()
            case "tab":
                completed = self._cmd_completer.tab(self._command_buffer)
                self._command_buffer = completed
                self._show_command_prompt()
            case "backspace":
                self._cmd_completer.reset()
                self._command_buffer = self._command_buffer[:-1]
                self._show_command_prompt()
            case _ if len(key) == 1 and key.isprintable():
                self._cmd_completer.reset()
                self._command_buffer += key
                self._show_command_prompt()
        self._sync_formula_bar()
        self._sync_status_bar()

    # -------------------------------------------------------------------
    # Swap mode  (gx / grx / gcx address collection)
    # -------------------------------------------------------------------

    def _swap_mode_prefix(self) -> str:
        if self._swap_mode == "row":
            return "grX" if self._swap_keep_cursor else "grx"
        if self._swap_mode == "col":
            return "gcX" if self._swap_keep_cursor else "gcx"
        return "gX" if self._swap_keep_cursor else "gx"

    def _handle_swap_key(self, key: str) -> None:
        match key:
            case "escape":
                self._swap_buf = None
                self.status_bar.set_persistent_message("", priority=2)
            case "enter" | "\r" | "\n":
                self._do_swap()
            case "backspace":
                if self._swap_buf:
                    self._swap_buf = self._swap_buf[:-1]
                self.status_bar.set_persistent_message(
                    f"{self._swap_mode_prefix()}: {self._swap_buf}", priority=2
                )
            case _ if len(key) == 1 and key.isprintable():
                self._swap_buf = (self._swap_buf or "") + key
                self.status_bar.set_persistent_message(
                    f"{self._swap_mode_prefix()}: {self._swap_buf}", priority=2
                )
        self._sync_formula_bar()
        self._sync_status_bar()

    def _col_letter_to_index(self, col: str) -> int:
        """Convert column letter (A, B, ..., Z, AA, ...) to 0-indexed integer."""
        result = 0
        for ch in col.strip().upper():
            result = result * 26 + (ord(ch) - ord("A") + 1)
        return result - 1

    def _do_swap(self) -> None:
        from vimsheet.model.range import a1_to_rowcol
        from vimsheet.model.undo import CompositeCommand, SetCellCommand

        sheet = self.workbook.active_sheet
        r, c = self.cursor_row, self.cursor_col
        buf = (self._swap_buf or "").strip().upper()
        mode = self._swap_mode

        cmds: list[SetCellCommand] = []

        try:
            if mode == "cell":
                tr, tc = a1_to_rowcol(buf)
                src = sheet.get_cell(r, c)
                dst = sheet.get_cell(tr, tc)
                src_val = src.value if src else None
                src_fml = src.formula if src else None
                dst_val = dst.value if dst else None
                dst_fml = dst.formula if dst else None
                cmds.append(SetCellCommand(sheet, tr, tc, src_val, new_formula=src_fml))
                cmds.append(SetCellCommand(sheet, r, c, dst_val, new_formula=dst_fml))
                if not self._swap_keep_cursor:
                    self.grid.move_cursor(tr, tc)

            elif mode == "row":
                tr = int(buf) - 1
                max_col = sheet.max_col
                for col in range(max_col + 1):
                    src = sheet.get_cell(r, col)
                    dst = sheet.get_cell(tr, col)
                    src_val = src.value if src else None
                    src_fml = src.formula if src else None
                    dst_val = dst.value if dst else None
                    dst_fml = dst.formula if dst else None
                    cmds.append(SetCellCommand(sheet, tr, col, src_val, new_formula=src_fml))
                    cmds.append(SetCellCommand(sheet, r, col, dst_val, new_formula=dst_fml))
                if not self._swap_keep_cursor:
                    self.grid.move_cursor(tr, c)

            elif mode == "col":
                tc = self._col_letter_to_index(buf)
                max_row = sheet.max_row
                for row in range(max_row + 1):
                    src = sheet.get_cell(row, c)
                    dst = sheet.get_cell(row, tc)
                    src_val = src.value if src else None
                    src_fml = src.formula if src else None
                    dst_val = dst.value if dst else None
                    dst_fml = dst.formula if dst else None
                    cmds.append(SetCellCommand(sheet, row, tc, src_val, new_formula=src_fml))
                    cmds.append(SetCellCommand(sheet, row, c, dst_val, new_formula=dst_fml))
                if not self._swap_keep_cursor:
                    self.grid.move_cursor(r, tc)

        except Exception:
            self.status_bar.show_message(f"Invalid target: {buf}")
            self._swap_buf = None
            return

        if cmds:
            self.undo_stack.push(CompositeCommand(cmds))
            self.workbook.modified = True

        self._swap_buf = None
        self.grid.refresh_grid()
        self._sync_formula_bar()
        self._sync_status_bar()

    # -------------------------------------------------------------------
    # Search mode  (/ and ? prompts)
    # -------------------------------------------------------------------

    def _enter_search_mode(self, prefix: str = "/") -> None:
        if prefix not in ("/", "?"):
            prefix = "/"
        self._command_buffer = prefix
        self.mode = Mode.SEARCH
        self._show_search_prompt()

    def _show_search_prompt(self) -> None:
        prompt = self._command_buffer
        self.status_bar.set_persistent_message(prompt)
        with contextlib.suppress(Exception):
            self.formula_bar.update_cell(
                self.formula_bar.cell_address,
                prompt,
                self.formula_bar.is_locked,
                cursor_pos=len(prompt),
            )

    def _handle_search_key(self, key: str) -> None:
        match key:
            case "escape":
                self._command_buffer = ""
                self.mode = Mode.NORMAL
                self.status_bar.set_persistent_message("")
            case "enter":
                cmd = self._command_buffer.strip()
                if cmd:
                    self._search_history.push(cmd[1:])
                    self._save_history()
                    self._search_history.reset_browse()
                self._command_buffer = ""
                self.mode = Mode.NORMAL
                if cmd:
                    self._dispatch_command(cmd)
            case "up":
                prev = self._search_history.prev()
                if prev is not None:
                    prefix = self._command_buffer[0] if self._command_buffer else "/"
                    self._command_buffer = prefix + prev
                    self._show_search_prompt()
            case "down":
                nxt = self._search_history.next()
                prefix = self._command_buffer[0] if self._command_buffer else "/"
                if nxt is not None:
                    self._command_buffer = prefix + nxt
                else:
                    self._command_buffer = prefix
                self._show_search_prompt()
            case "backspace":
                if len(self._command_buffer) > 1:
                    self._command_buffer = self._command_buffer[:-1]
                    self._show_search_prompt()
            case _ if len(key) == 1 and key.isprintable():
                self._command_buffer += key
                self._show_search_prompt()
        self._sync_formula_bar()
        self._sync_status_bar()

    # Functions that produce a single aggregate over a range (yank, not element-wise apply)
    _AGGREGATE_FUNCS = frozenset(
        {
            "SUM",
            "AVG",
            "AVERAGE",
            "COUNT",
            "COUNTA",
            "MIN",
            "MAX",
            "PROD",
            "PRODUCT",
            "STDDEV",
            "STDEV",
            "STDEVS",
            "VAR",
            "VARS",
            "MEDIAN",
            "MODE",
            "PERCENTILE",
            "SUMIF",
            "COUNTIF",
            "AVERAGEIF",
            "SUBTOTAL",
        }
    )

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
                unsaved = [(i, wb) for i, wb in enumerate(self._buffers) if wb.modified]
                if unsaved:
                    names = ", ".join(
                        str(wb.filepath.name if wb.filepath else f"buf {i + 1}")
                        for i, wb in unsaved
                    )
                    plural = "buffers have" if len(unsaved) > 1 else "buffer has"
                    self.status_bar.show_message(
                        f"{len(unsaved)} {plural} unsaved changes: {names} — use :q! to force quit"
                    )
                else:
                    self.exit()
            case "q!":
                n_total = len(self._buffers)
                unsaved = [(i, wb) for i, wb in enumerate(self._buffers) if wb.modified]
                buf_word = "buffer" if n_total == 1 else "buffers"
                if unsaved:
                    names = ", ".join(
                        str(wb.filepath.name if wb.filepath else f"buf {i + 1}")
                        for i, wb in unsaved
                    )
                    msg = f"Close {n_total} {buf_word}? {len(unsaved)} unsaved: {names}"
                else:
                    msg = f"Close {n_total} {buf_word}?"
                self._ask_confirm(msg, self.exit)
            case "wq" | "x":
                self._save_and_quit()
            case "w" | "write":
                self._save_file(Path(parts[1]) if len(parts) > 1 else None)
            case "e" | "edit":
                if len(parts) == 2:
                    self._open_file(Path(parts[1]))
                else:
                    self.status_bar.show_message("Usage: :e <file>")
            case "sp" | "split":
                if len(parts) >= 2:
                    self._cmd_split(parts[1])
                else:
                    self.status_bar.show_message("Usage: :sp <file>")
            case "buffers" | "bufs" | "ls":
                self._cmd_buffers()
            case "buffer" | "buf":
                if len(parts) >= 2:
                    try:
                        self._switch_buffer(int(parts[1]) - 1)
                    except ValueError:
                        self.status_bar.show_message("Usage: :buf <n>")
                else:
                    name = str(self.workbook.filepath) if self.workbook.filepath else "[No Name]"
                    self.status_bar.show_message(
                        f"Buffer {self._active_buf_idx + 1}/{len(self._buffers)}: {name}"
                    )
            case "bd" | "bdel" | "bdelete":
                self._cmd_bdelete(force=False)
            case "bd!" | "bdel!" | "bdelete!":
                self._cmd_bdelete(force=True)
            case "ex" | "export":
                # :ex <file>          — export by extension
                # :ex <format> <file> — export with explicit format
                from vimsheet.io.registry import _FORMAT_NAMES

                if len(parts) == 3 and parts[1].lower() in _FORMAT_NAMES:
                    self._export_file(parts[1].lower(), Path(parts[2]))
                elif len(parts) == 2:
                    self._save_file(Path(parts[1]))
                else:
                    self.status_bar.show_message("Usage: :ex <file>  or  :ex <format> <file>")
            case "f" | "file":
                self._show_file_info()

            # ---- Sheet management ----
            case "sa" | "sheetadd":
                name = parts[1].strip("\"'") if len(parts) > 1 else None
                try:
                    self.workbook.add_sheet(name)
                except ValueError as e:
                    self.status_bar.show_message(str(e))
                    return
                self.workbook.active_sheet_idx = len(self.workbook.sheets) - 1
                self._on_sheet_changed()
                self.workbook.modified = True
                self.status_bar.show_message(f"Added sheet: {self.workbook.active_sheet.name}")
            case "sd" | "sheetdel":
                if len(self.workbook.sheets) <= 1:
                    self.status_bar.show_message("Cannot delete the only sheet")
                else:
                    target_name = parts[1].strip("\"'") if len(parts) > 1 else None
                    if target_name:
                        try:
                            self.workbook.delete_sheet(target_name)
                        except (ValueError, KeyError) as e:
                            self.status_bar.show_message(str(e))
                            return
                        self._on_sheet_changed()
                        self.status_bar.show_message(f"Deleted sheet: {target_name}")
                    else:
                        idx = self.workbook.active_sheet_idx
                        deleted_sheet = self.workbook.sheets[idx]
                        self._deleted_sheets.append((idx, deleted_sheet))
                        self.workbook.sheets.pop(idx)
                        self.workbook.active_sheet_idx = max(0, idx - 1)
                        self._on_sheet_changed()
                        self.workbook.modified = True
                        self.status_bar.show_message(
                            f"Deleted sheet: {deleted_sheet.name}  (undo with :undodelsheet)"
                        )
            case "sr" | "sheetrename":
                if len(parts) >= 3:
                    old_name = parts[1].strip("\"'")
                    new_name = parts[2].strip("\"'")
                    try:
                        self.workbook.rename_sheet(old_name, new_name)
                        self._sync_sheet_tabs()
                        self.status_bar.show_message(f"Sheet renamed: {old_name} → {new_name}")
                    except (KeyError, ValueError) as e:
                        self.status_bar.show_message(str(e))
                elif len(parts) == 2:
                    new_name = parts[1].strip("\"'")
                    old_name = self.workbook.active_sheet.name
                    try:
                        self.workbook.rename_sheet(old_name, new_name)
                        self._sync_sheet_tabs()
                        self.status_bar.show_message(f"Sheet renamed: {old_name} → {new_name}")
                    except ValueError as e:
                        self.status_bar.show_message(str(e))
                else:
                    self.status_bar.show_message(
                        "Usage: :sr <newname>   or   :sr <oldname> <newname>"
                    )
            case "sl" | "sheets" | "sheetlist":
                names = [s.name for s in self.workbook.sheets]
                active = self.workbook.active_sheet.name
                msg = "  ".join(f"[{n}]" if n == active else n for n in names)
                self.status_bar.show_message(f"Sheets ({len(names)}): {msg}")
            case "sdup" | "sc" | "sheetdupe":
                name = parts[1].strip("\"'") if len(parts) > 1 else None
                try:
                    new_sheet = self.workbook.duplicate_sheet(name)
                    self._on_sheet_changed()
                    self.status_bar.show_message(f"Duplicated sheet: {new_sheet.name}")
                except (ValueError, KeyError) as e:
                    self.status_bar.show_message(str(e))
            case "nextsheet":
                self.workbook.go_to_next_sheet()
                self._on_sheet_changed()
            case "prevsheet":
                self.workbook.go_to_prev_sheet()
                self._on_sheet_changed()
            case "sheet":
                if len(parts) > 1:
                    sub = parts[1].lower()
                    if sub == "add":
                        name = parts[2].strip("\"'") if len(parts) > 2 else None
                        try:
                            self.workbook.add_sheet(name)
                        except ValueError as e:
                            self.status_bar.show_message(str(e))
                            return
                        self.workbook.active_sheet_idx = len(self.workbook.sheets) - 1
                        self._on_sheet_changed()
                        self.workbook.modified = True
                        self.status_bar.show_message(
                            f"Added sheet: {self.workbook.active_sheet.name}"
                        )
                    elif sub in ("delete", "del"):
                        target_name = parts[2].strip("\"'") if len(parts) > 2 else None
                        self._dispatch_command(f"sd {target_name}" if target_name else "sd")
                    elif sub in ("rename", "ren"):
                        if len(parts) >= 4:
                            old_name = parts[2].strip("\"'")
                            new_name = parts[3].strip("\"'")
                            self._dispatch_command(f"sr {old_name} {new_name}")
                        elif len(parts) >= 3:
                            new_name = parts[2].strip("\"'")
                            self._dispatch_command(f"sr {new_name}")
                        else:
                            self.status_bar.show_message(
                                "Usage: :sheet rename [<oldname>] <newname>"
                            )
                    elif sub in ("dup", "duplicate", "copy"):
                        name = parts[2].strip("\"'") if len(parts) > 2 else None
                        self._dispatch_command(f"sdup {name}" if name else "sdup")
                    elif sub in ("list", "ls", "l"):
                        self._dispatch_command("sl")
                    else:
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
            case "colfit" | "colf":
                col = self.cursor_col
                self.workbook.active_sheet.auto_fit_col(col)
                self.grid.refresh_grid()
                self.status_bar.show_message(f"Column fit: col {col + 1}")
            case "rowfit" | "rowf":
                self.grid.expand_row(self.cursor_row)
                self.grid.refresh_grid()
                self.status_bar.show_message(f"Row fit: row {self.cursor_row + 1}")

            # ---- Sort ----
            case "messages" | "mess":
                from vimsheet.ui.messages_screen import MessagesScreen

                msgs = list(self.status_bar.message_history)
                if not msgs:
                    self.status_bar.show_message("No messages")
                    return
                self.push_screen(MessagesScreen(msgs))

            case "funcs" | "functions":
                from vimsheet.ui.funcs_screen import FuncsScreen

                term = parts[1] if len(parts) > 1 else ""
                self.push_screen(FuncsScreen(filter_term=term))

            case "fill":
                # :fill <value>                  — fill all cells with constant
                # :fill <start> <step>           — arithmetic sequence
                # :fill <start> <step> <func>    — sequence then apply func
                # :fill <start> <step> <range>   — inline range
                sel = self.grid.visual_selection()
                if sel is None and len(parts) > 2:
                    last = parts[-1].upper()
                    if ":" in last:
                        from vimsheet.model.range import CellRange

                        try:
                            sel = CellRange.from_a1(last)
                            parts = parts[:-1]
                        except Exception:
                            pass
                if sel is None:
                    self.status_bar.show_message("Select a range first (visual mode)")
                else:
                    self._cmd_fill(sel, parts[1:])

            case "sort":
                from vimsheet.model.undo import SortCommand

                sheet = self.workbook.active_sheet

                def _parse_col(s: str) -> int:
                    if s.isalpha():
                        return (
                            sum(
                                (ord(ch.upper()) - 64) * (26**i)
                                for i, ch in enumerate(reversed(s.upper()))
                            )
                            - 1
                        )
                    return int(s) - 1

                def _expand_col_spec(spec: str) -> list[int]:
                    cols: list[int] = []
                    for part in spec.split(","):
                        part = part.strip()
                        if not part:
                            continue
                        if ":" in part:
                            a, b = part.split(":", 1)
                            c1 = _parse_col(a.strip())
                            c2 = _parse_col(b.strip())
                            if c1 > c2:
                                c1, c2 = c2, c1
                            cols.extend(range(c1, c2 + 1))
                        else:
                            cols.append(_parse_col(part))
                    return cols

                try:
                    rest = parts[1:] if len(parts) > 1 else []
                    sort_keys: list[tuple[int, bool]] = []
                    i = 0
                    while i < len(rest):
                        token = rest[i]
                        if token.lower() in ("asc", "desc"):
                            if not sort_keys:
                                sort_keys.append((self.cursor_col, token.lower() in ("asc", "a")))
                            i += 1
                        elif ":" in token or "," in token:
                            expanded = _expand_col_spec(token)
                            asc = True
                            if i + 1 < len(rest) and rest[i + 1].lower() in ("desc", "d"):
                                asc = False
                                i += 2
                            else:
                                i += 1
                            for c in expanded:
                                sort_keys.append((c, asc))
                        elif token.isalpha() or token.isdigit():
                            col = _parse_col(token)
                            asc = True
                            if i + 1 < len(rest) and rest[i + 1].lower() in ("desc", "d"):
                                asc = False
                                i += 2
                            else:
                                i += 1
                            sort_keys.append((col, asc))
                        else:
                            i += 1
                    if not sort_keys:
                        sort_keys = [(self.cursor_col, True)]
                    # Exclude frozen columns from sort keys
                    sort_keys = [(c, asc) for c, asc in sort_keys if c >= sheet.freeze_cols]
                    if not sort_keys:
                        self.status_bar.show_message(
                            "All selected columns are frozen — nothing to sort"
                        )
                        return
                    cmd = SortCommand(sheet, sort_keys)
                    self.undo_stack.push(cmd)
                    self.grid.refresh_grid()
                    self.workbook.modified = True
                    labels = " ".join(chr(65 + c) if c < 26 else str(c + 1) for c, _ in sort_keys)
                    self.status_bar.show_message(f"Sorted by {labels}")
                except (ValueError, IndexError) as e:
                    self.status_bar.show_message(f"Sort error: {e}")

            # ---- Swap ----
            case "swap":
                if len(parts) == 2:
                    self._swap_buf = parts[1]
                    self._swap_mode = "cell"
                    self._swap_keep_cursor = False
                    self._do_swap()
                elif len(parts) == 3 and parts[1] == "row":
                    self._swap_buf = parts[2]
                    self._swap_mode = "row"
                    self._swap_keep_cursor = False
                    self._do_swap()
                elif len(parts) == 3 and parts[1] == "col":
                    self._swap_buf = parts[2]
                    self._swap_mode = "col"
                    self._swap_keep_cursor = False
                    self._do_swap()
                else:
                    self.status_bar.show_message(
                        "Usage: :swap <addr> | :swap row <n> | :swap col <c>"
                    )

            # ---- Recalculate ----
            case "recalc":
                sheet = self.workbook.active_sheet
                from vimsheet.formula.evaluator import recalculate

                recalculate(sheet, sheet._dep_graph)
                self.grid.refresh_grid()
                self.status_bar.show_message("Recalculated")

            # ---- Goto cell ----
            case "goto" | "g":
                if len(parts) > 1:
                    try:
                        from vimsheet.model.range import a1_to_rowcol

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
            case _ if re.match(r"^%s/", cmd):
                sheet = self.workbook.active_sheet
                from vimsheet.model.range import col_index_to_letters

                range_str = f"A1:{col_index_to_letters(sheet.max_col)}{sheet.max_row + 1}"
                self._cmd_substitute(range_str, cmd[1:])
            case _ if re.match(r"^\d+,\d+s/", parts[0]):
                m = re.match(r"^(\d+),(\d+)s/", parts[0])
                r1, r2 = int(m.group(1)) - 1, int(m.group(2)) - 1
                sheet = self.workbook.active_sheet
                from vimsheet.model.range import col_index_to_letters

                range_str = f"A{r1 + 1}:{col_index_to_letters(sheet.max_col)}{r2 + 1}"
                sub_cmd = "s/" + parts[0][m.end() :]
                self._cmd_substitute(range_str, sub_cmd)
            case _ if parts[0].startswith("s/") and len(parts[0]) > 2:
                r = self.cursor_row
                sheet = self.workbook.active_sheet
                from vimsheet.model.range import col_index_to_letters

                range_str = f"A{r + 1}:{col_index_to_letters(sheet.max_col)}{r + 1}"
                self._cmd_substitute(range_str, parts[0])
            case _ if re.match(r"^(?:[A-Za-z]+,[A-Za-z]+)?cs", parts[0]) and "/" in cmd:
                self._cmd_col_substitute(cmd)
            case _ if re.match(r"^(?:\d+,\d+)?rs", parts[0]) and "/" in cmd:
                self._cmd_row_substitute(cmd)
            case _ if (
                len(parts) == 2
                and ":" in parts[0]
                and re.match(r"^(?:cs|rs)", parts[1], re.IGNORECASE)
                and "/" in parts[1]
            ):
                self._cmd_range_substitute(parts[0], parts[1])

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
                from vimsheet.model.range import CellRange

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

            case _ if len(parts) >= 2 and parts[1].lower() == "sort":
                # <range> sort [col] [asc|desc] ...  — range pre-filled from visual mode
                self._cmd_range_sort(parts[0], parts[2:])

            # ---- Range format ----
            case _ if len(parts) >= 3 and parts[1].lower() in ("format", "fmt"):
                from vimsheet.model.range import CellRange
                from vimsheet.model.undo import CompositeCommand, FormatCommand

                sheet = self.workbook.active_sheet
                try:
                    cr = CellRange.from_a1(parts[0].upper())
                except Exception:
                    self.status_bar.show_message(f"Invalid range: {parts[0]!r}")
                    return
                if "=" in parts[2]:
                    kwargs = self._parse_fmt_kwargs(parts[2:])
                else:
                    prop = parts[2].lower()
                    val_str = parts[3] if len(parts) > 3 else ""
                    kwargs = self._parse_fmt_kwargs([prop, val_str])
                if kwargs is None:
                    return
                cmds: list[FormatCommand] = []
                for r in range(cr.start_row, cr.end_row + 1):
                    for c in range(cr.start_col, cr.end_col + 1):
                        cmds.append(FormatCommand(sheet, r, c, **kwargs))
                self.undo_stack.push(CompositeCommand(cmds))
                self.grid.refresh_grid()
                self.workbook.modified = True
                labels = " ".join(f"{k}={v}" for k, v in kwargs.items())
                self.status_bar.show_message(f"Formatted {cr}: {labels}")

            # ---- Range condformat ----
            case _ if len(parts) >= 4 and parts[1].lower() in ("condformat", "cond", "cf"):
                sheet = self.workbook.active_sheet
                range_str = parts[0].upper()
                args = parts[2:]
                try:
                    self._cmd_cond_format(sheet, range_str, args)
                except Exception as exc:
                    self.status_bar.show_message(f"Condformat error: {exc}")

            # ---- Range comment ----
            case _ if len(parts) >= 2 and parts[1].lower() in ("comment", "note"):
                from vimsheet.model.range import CellRange

                sheet = self.workbook.active_sheet
                try:
                    cr = CellRange.from_a1(parts[0].upper())
                except Exception:
                    self.status_bar.show_message(f"Invalid range: {parts[0]!r}")
                    return
                if len(parts) > 2:
                    text = " ".join(parts[2:])
                    for r in range(cr.start_row, cr.end_row + 1):
                        for c in range(cr.start_col, cr.end_col + 1):
                            cell = sheet.get_cell(r, c)
                            if cell is None:
                                sheet.set_cell_value(r, c, None)
                                cell = sheet.get_cell(r, c)
                            cell.comment = text  # type: ignore[union-attr]
                    self.workbook.modified = True
                    self.status_bar.show_message(f"Comment set on {cr}")
                else:
                    cell = sheet.get_cell(cr.start_row, cr.start_col)
                    msg = cell.comment if cell and cell.comment else "(no comment)"
                    self.status_bar.show_message(f"Comment: {msg}")

            # ---- Range hide/show rows ----
            case _ if len(parts) == 2 and parts[1].lower() == "hide":
                from vimsheet.model.range import CellRange

                sheet = self.workbook.active_sheet
                try:
                    cr = CellRange.from_a1(parts[0].upper())
                except Exception:
                    self.status_bar.show_message(f"Invalid range: {parts[0]!r}")
                    return
                for r in range(cr.start_row, cr.end_row + 1):
                    sheet.hidden_rows.add(r)
                self.workbook.modified = True
                self.grid.refresh_grid()
                self.status_bar.show_message(f"Hidden rows {cr.start_row + 1}–{cr.end_row + 1}")
            case _ if len(parts) == 2 and parts[1].lower() == "show":
                from vimsheet.model.range import CellRange

                sheet = self.workbook.active_sheet
                try:
                    cr = CellRange.from_a1(parts[0].upper())
                except Exception:
                    self.status_bar.show_message(f"Invalid range: {parts[0]!r}")
                    return
                for r in range(cr.start_row, cr.end_row + 1):
                    sheet.hidden_rows.discard(r)
                self.workbook.modified = True
                self.grid.refresh_grid()
                self.status_bar.show_message(f"Shown rows {cr.start_row + 1}–{cr.end_row + 1}")

            # ---- Range colwidth ----
            case _ if len(parts) >= 3 and parts[1].lower() in ("colwidth", "cw"):
                from vimsheet.model.range import CellRange

                try:
                    cr = CellRange.from_a1(parts[0].upper())
                    w = int(parts[2])
                    sheet = self.workbook.active_sheet
                    for c in range(cr.start_col, cr.end_col + 1):
                        sheet.set_col_width(c, w)
                    self.grid.refresh_grid()
                    self.status_bar.show_message(
                        f"Columns {cr.start_col + 1}–{cr.end_col + 1} width set to {w}"
                    )
                except Exception as e:
                    self.status_bar.show_message(f"Error: {e}")

            # ---- Range autofit / colfit / rowfit ----
            case _ if len(parts) >= 2 and parts[1].lower() in ("autofit", "af"):
                from vimsheet.model.range import CellRange

                try:
                    cr = CellRange.from_a1(parts[0].upper())
                    sheet = self.workbook.active_sheet
                    mode = parts[2].lower() if len(parts) > 2 else "both"
                    if mode in ("col", "cols", "both"):
                        for c in range(cr.start_col, cr.end_col + 1):
                            sheet.auto_fit_col(c)
                    if mode in ("row", "rows", "both"):
                        for r in range(cr.start_row, cr.end_row + 1):
                            self.grid.expand_row(r)
                    self.grid.refresh_grid()
                    self.status_bar.show_message(
                        f"Fitted {'columns ' if mode in ('col', 'cols') else ''}"
                        f"{'rows ' if mode in ('row', 'rows') else ''}"
                        f"{'both ' if mode == 'both' else ''}"
                        f"on {cr}"
                    )
                except Exception as e:
                    self.status_bar.show_message(f"Error: {e}")
            case _ if len(parts) >= 2 and parts[1].lower() in ("colfit", "colf"):
                from vimsheet.model.range import CellRange

                try:
                    cr = CellRange.from_a1(parts[0].upper())
                    sheet = self.workbook.active_sheet
                    for c in range(cr.start_col, cr.end_col + 1):
                        sheet.auto_fit_col(c)
                    self.grid.refresh_grid()
                    self.status_bar.show_message(f"Fitted columns on {cr}")
                except Exception as e:
                    self.status_bar.show_message(f"Error: {e}")
            case _ if len(parts) >= 2 and parts[1].lower() in ("rowfit", "rowf"):
                from vimsheet.model.range import CellRange

                try:
                    cr = CellRange.from_a1(parts[0].upper())
                    for r in range(cr.start_row, cr.end_row + 1):
                        self.grid.expand_row(r)
                    self.grid.refresh_grid()
                    self.status_bar.show_message(f"Fitted rows on {cr}")
                except Exception as e:
                    self.status_bar.show_message(f"Error: {e}")

            # ---- Range validate ----
            case _ if len(parts) >= 2 and parts[1].lower() == "validate":
                from vimsheet.model.range import CellRange
                from vimsheet.model.undo import CompositeCommand, ValidationCommand
                from vimsheet.model.validation import ValidationRule

                try:
                    cr = CellRange.from_a1(parts[0].upper())
                except Exception:
                    self.status_bar.show_message(f"Invalid range: {parts[0]!r}")
                    return
                sheet = self.workbook.active_sheet
                sub = parts[2:]
                if not sub or sub[0] == "clear":
                    cmds = []
                    for r in range(cr.start_row, cr.end_row + 1):
                        for c in range(cr.start_col, cr.end_col + 1):
                            cmds.append(ValidationCommand(sheet, r, c, None))
                    self.undo_stack.push(CompositeCommand(cmds))
                    self.status_bar.show_message(f"Validation cleared on {cr}")
                else:
                    rule_type = sub[0].lower()
                    rule: ValidationRule
                    if rule_type == "list" and len(sub) > 1:
                        choices = sub[1].split(",")
                        rule = ValidationRule(rule_type="list", choices=choices)
                    elif rule_type in ("number", "integer") and len(sub) > 2:
                        op = sub[1].lower()
                        v1 = float(sub[2])
                        v2 = float(sub[3]) if len(sub) > 3 else None
                        rule = ValidationRule(
                            rule_type=rule_type, operator=op, value1=v1, value2=v2
                        )
                    else:
                        rule = ValidationRule(rule_type=rule_type)
                    cmds = []
                    for r in range(cr.start_row, cr.end_row + 1):
                        for c in range(cr.start_col, cr.end_col + 1):
                            cmds.append(ValidationCommand(sheet, r, c, rule))
                    self.undo_stack.push(CompositeCommand(cmds))
                    self.status_bar.show_message(f"Validation set: {rule_type} on {cr}")

            # ---- Range history ----
            case _ if len(parts) >= 2 and parts[1].lower() == "history" and ":" in parts[0]:
                from vimsheet.ui.history_screen import HistoryScreen

                self.push_screen(HistoryScreen(self.workbook.active_sheet, parts[0].upper()))

            # ---- Range clearfilter ----
            case _ if len(parts) >= 2 and parts[1].lower() == "clearfilter":
                from vimsheet.model.range import CellRange

                try:
                    range_str = parts[0].upper()
                    if ":" not in range_str:
                        range_str = f"{range_str}1:{range_str}1"
                    cr = CellRange.from_a1(range_str)
                    sheet = self.workbook.active_sheet
                    for c in range(cr.start_col, cr.end_col + 1):
                        sheet.filters.pop(c, None)
                    sheet.apply_filters()
                    self.grid.refresh_grid()
                    self.status_bar.show_message(
                        f"Filter cleared on columns {cr.start_col + 1}–{cr.end_col + 1}"
                    )
                except Exception as e:
                    self.status_bar.show_message(f"Error: {e}")

            # ---- Range substitute -----
            case _ if len(parts) >= 2 and parts[1].startswith("s/"):
                self._cmd_substitute(parts[0].upper(), parts[1])

            # ---- Range element-wise function apply (non-aggregate) ----
            case _ if (
                len(parts) >= 2
                and ":" in parts[0]
                and parts[1].isalpha()
                and parts[1].upper() not in self._AGGREGATE_FUNCS
            ):
                from vimsheet.formula.functions.registry import get as _registry_get

                func_name = parts[1].upper()
                if func_name in self._get_script_func_names():
                    self._apply_script_func_to_range(parts[0].upper(), func_name)
                elif _registry_get(func_name) is None:
                    self.status_bar.show_message(
                        f"Unknown function: {func_name} — use :func to register it"
                    )
                else:
                    self._apply_func_to_range(parts[0].upper(), func_name, parts[2:])

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
                    from vimsheet.model.validation import ValidationRule

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
                        from vimsheet.model.range import a1_to_rowcol

                        r, c = a1_to_rowcol(parts[1].upper())
                    except Exception:
                        r, c = self.cursor_row, self.cursor_col
                else:
                    r, c = self.cursor_row, self.cursor_col
                from vimsheet.model.range import rowcol_to_a1 as _r2a

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
                    from vimsheet.model.sheet import FilterRule

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
                            self._set_config("autocalc", str(not self.config.autocalc))
                        case "savecursor" | "save-cursor":
                            self._set_config("save_cursor", str(not self.config.save_cursor))
                        case _ if "=" in option:
                            key, _, val = option.partition("=")
                            self._set_config(key.strip(), val.strip())
                        case _ if len(parts) == 3:
                            self._set_config(parts[1], parts[2])
                        case _:
                            cur = getattr(self.config, option, None)
                            if cur is not None:
                                self.status_bar.show_message(f"{option} = {cur!r}")
                            else:
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
                # :format <addr> bg=#rrggbb fg=white align=left bold
                from vimsheet.model.range import a1_to_rowcol
                from vimsheet.model.undo import FormatCommand

                if len(parts) >= 3:
                    try:
                        r, c = a1_to_rowcol(parts[1].upper())
                    except Exception:
                        self.status_bar.show_message(f"Invalid address: {parts[1]!r}")
                        return
                    if "=" in parts[2]:
                        kwargs = self._parse_fmt_kwargs(parts[2:])
                    else:
                        prop = parts[2].lower()
                        val_str = parts[3] if len(parts) > 3 else ""
                        kwargs = self._parse_fmt_kwargs([prop, val_str])
                    if kwargs is None:
                        return
                    cmd = FormatCommand(self.workbook.active_sheet, r, c, **kwargs)
                    self.undo_stack.push(cmd)
                    self.grid.refresh_grid()
                    self.workbook.modified = True
                    labels = " ".join(f"{k}={v}" for k, v in kwargs.items())
                    self.status_bar.show_message(f"Formatted {parts[1].upper()}: {labels}")
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
                        self._cmd_cond_format(sheet, parts[1].upper(), parts[2:])
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
                if len(parts) >= 2 and parts[1].lower() in ("open", "close", "toggle"):
                    self._fold_group(parts[1].lower())
                elif len(parts) >= 2 and parts[1].lower() == "remove":
                    self._fold_group("remove")
                elif len(parts) >= 3:
                    try:
                        r1, r2 = int(parts[1]) - 1, int(parts[2]) - 1
                        grp = (min(r1, r2), max(r1, r2))
                        self.workbook.active_sheet.row_groups.append(grp)
                        self.grid.refresh_grid()
                        self.workbook.modified = True
                        self.status_bar.show_message(f"Row group: rows {r1 + 1}–{r2 + 1}")
                    except ValueError:
                        self.status_bar.show_message(
                            "Usage: :rowgroup <open|close|toggle> | <r1> <r2>"
                        )
                else:
                    self.status_bar.show_message("Usage: :rowgroup <open|close|toggle> | <r1> <r2>")
            case "colgroup":
                if len(parts) >= 2 and parts[1].lower() in ("open", "close", "toggle"):
                    self._fold_col_group(parts[1].lower())
                elif len(parts) >= 2 and parts[1].lower() == "remove":
                    self._fold_col_group("remove")
                elif len(parts) >= 3:

                    def _col(s: str) -> int:
                        s = s.strip().upper()
                        if s.isdigit():
                            return int(s) - 1
                        from vimsheet.model.range import col_letters_to_index

                        return col_letters_to_index(s)

                    try:
                        c1, c2 = _col(parts[1]), _col(parts[2])
                        grp = (min(c1, c2), max(c1, c2))
                        self.workbook.active_sheet.col_groups.append(grp)
                        self.grid.refresh_grid()
                        self.workbook.modified = True
                        from vimsheet.model.range import col_index_to_letters

                        lab1 = col_index_to_letters(c1)
                        lab2 = col_index_to_letters(c2)
                        self.status_bar.show_message(f"Col group: cols {lab1}–{lab2}")
                    except (ValueError, IndexError):
                        self.status_bar.show_message(
                            "Usage: :colgroup <open|close|toggle> | <colA> <colB>"
                        )
                else:
                    self.status_bar.show_message(
                        "Usage: :colgroup <open|close|toggle> | <colA> <colB>"
                    )

            # ---- Theme ----
            case "theme":
                theme_name = parts[1].lower() if len(parts) > 1 else ""
                self._apply_theme(theme_name)

            # ---- Colorscheme ----
            case "colorscheme":
                self._cmd_colorscheme(parts[1:])

            # ---- External scripts ----
            case "func":
                # :func <NAME> <script_path> [description]
                if len(parts) >= 3:
                    desc = " ".join(parts[3:]) if len(parts) >= 4 else ""
                    self._register_script_func(parts[1].upper(), parts[2], desc=desc)
                else:
                    self.status_bar.show_message("Usage: :func <NAME> <script_path> [description]")

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
                self.status_bar.show_message("VimSheet 0.1.0")
            case "help":
                from vimsheet.ui.help_screen import HelpScreen

                self.push_screen(HelpScreen())
            case _ if "!" in parts[0]:
                # <range>!<script>  — no space variant
                range_part, _, script_part = parts[0].partition("!")
                self._run_external_script(range_part.upper(), script_part)
            case _ if len(parts) >= 2 and parts[1].startswith("!"):
                # <range> !<script>  — space variant
                script_part = parts[1][1:] or (" ".join(parts[2:]) if len(parts) > 2 else "")
                self._run_external_script(parts[0].upper(), script_part)
            case _ if (
                len(parts) == 2
                and ":" in parts[0]
                and parts[1].upper() in self._get_script_func_names()
            ):
                # :<range> <FUNCNAME>  — apply registered script function to range in place
                self._apply_script_func_to_range(parts[0].upper(), parts[1].upper())
            case _ if len(parts) == 2 and ":" in parts[0] and parts[1].isalpha():
                # :<range> <FUNCNAME>  — check global registry; error if unknown
                from vimsheet.formula.functions.registry import get as _registry_get

                func_name = parts[1].upper()
                if _registry_get(func_name) is None:
                    self.status_bar.show_message(
                        f"Unknown function: {func_name} — use :func to register it"
                    )
                else:
                    self._cmd_range_func(parts[0].upper(), func_name)
            # ---- Fetch range commands: <range> fetchstop / fetchnow ----
            case _ if len(parts) == 2 and parts[1].lower() == "fetchstop":
                self._cmd_fetchstop_range(parts[0].upper())
            case _ if len(parts) == 2 and parts[1].lower() == "fetchnow":
                self._cmd_fetchnow_range(parts[0].upper())
            # ---- Range-prefix name: <range> name <NAME> ----
            case _ if len(parts) == 3 and parts[1].lower() == "name":
                range_str = parts[0].upper()
                name = parts[2].upper()
                self.workbook.active_sheet.named_ranges.define(name, range_str)
                self.workbook.modified = True
                self.status_bar.show_message(f"Named range: {name} = {range_str}")
            case _:
                self.status_bar.show_message(f"Unknown command: {cmd!r}")

    def _cmd_loadtext(self, filepath: str, delimiter: str | None) -> None:
        """Load a plain-text file and fill cells from the current cursor.

        Each line becomes a row.  If *delimiter* is given (tab/comma/space/|)
        each line is split into multiple columns.  Values are coerced to
        numbers where possible.
        """
        from vimsheet.io.csv_adapter import _coerce as csv_coerce
        from vimsheet.model.undo import FillRangeCommand

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
        from vimsheet.model.range import a1_to_rowcol

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
        from vimsheet.model.range import a1_to_rowcol

        try:
            r, c = a1_to_rowcol(target.upper())
        except Exception:
            self.status_bar.show_message(f"Invalid address: {target!r}")
            return
        key = (self.workbook.active_sheet.name, r, c)
        self.fetch_manager.cancel(key)
        self.status_bar.show_message(f"Fetch stopped for {target.upper()}")

    def _cmd_fetchlist(self) -> None:
        from vimsheet.ui.fetch_list_screen import FetchListScreen

        entries = self.fetch_manager.all_entries()
        if not entries:
            self.status_bar.show_message("No active fetches")
            return
        self.push_screen(FetchListScreen(entries))

    def _cmd_fetchnow_range(self, range_str: str) -> None:
        from vimsheet.model.range import CellRange

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
        from vimsheet.model.range import CellRange

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
    # External editor
    # -----------------------------------------------------------------------

    def open_in_external_editor(self) -> None:
        """Open current cell content in $EDITOR, then write back on save."""
        import os
        import subprocess
        import tempfile

        r, c = self.cursor_row, self.cursor_col
        sheet = self.workbook.active_sheet
        cell = sheet.get_cell(r, c)
        initial = ""
        if cell:
            initial = cell.formula or cell.display or ""

        editor = os.environ.get("VISUAL") or os.environ.get("EDITOR") or "vi"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write(initial)
            tmp_path = f.name

        try:
            with self.suspend():
                subprocess.run([editor, tmp_path], check=False)  # noqa: S603
            with open(tmp_path, encoding="utf-8") as f:
                content = f.read()
            # Strip trailing newline that editors add but leave internal newlines
            if content.endswith("\n"):
                content = content[:-1]
            if content == initial:
                return  # unchanged — nothing to do
            from vimsheet.model.undo import SetCellCommand

            if content.startswith("="):
                cmd = SetCellCommand(sheet, r, c, content, new_formula=content)
            else:
                cmd = SetCellCommand(sheet, r, c, content)
            self.undo_stack.push(cmd)
            self.workbook.modified = True
            self._sync_formula_bar()
            self._sync_status_bar()
            self.grid.refresh_grid()
        finally:
            import contextlib

            with contextlib.suppress(OSError):
                os.unlink(tmp_path)

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
        self.grid.set_search_state(matches, state.current_match, pattern=state.pattern)

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
        self.grid.set_search_state(state.matches, state.current_match, pattern=state.pattern)

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
        self.grid.set_search_state(state.matches, state.current_match, pattern=state.pattern)

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
        state = SearchState(pattern=pattern, replace=replacement, whole_cell=True)
        self._search_state = state
        searcher = Searcher(self.workbook.active_sheet)
        updates = searcher.collect_replacements(state)
        self._execute_substitute(updates, "replace")

    # Matches :cs in all column-targeting forms.
    # Group 1: col range start (e.g. "A" from "A,C")
    # Group 2: col range end   (e.g. "C")
    # Group 3: optional col-spec (letter(s) or 1-based number)
    # Group 4: pattern
    # Group 5: replacement
    # Group 6: flags (g = regex global replace; absent = whole-cell literal match)
    _CS_RE = re.compile(
        r"^(?:([A-Za-z]+),([A-Za-z]+))?" r"cs" r"([A-Za-z]+|\d+)?" r"/(.+?)" r"/(.*?)" r"/([gi]*)$",
        re.IGNORECASE,
    )

    # Matches :rs in all row-targeting forms.
    # Group 1: row range start (1-based, e.g. "1" from "1,3")
    # Group 2: row range end   (1-based, e.g. "3")
    # Group 3: optional row-spec (1-based number)
    # Group 4: pattern
    # Group 5: replacement
    # Group 6: flags (g = regex global replace; absent = whole-cell literal match)
    _RS_RE = re.compile(
        r"^(?:(\d+),(\d+))?" r"rs" r"(\d+)?" r"/(.+?)" r"/(.*?)" r"/([gi]*)$",
        re.IGNORECASE,
    )

    def _cmd_substitute(self, range_str: str, sub_cmd: str) -> None:
        """Apply ``:s/pattern/replacement/flags`` within *range_str* (an A1 range)."""
        m = re.match(r"^s/(.+?)/(.*?)/([gi]*)$", sub_cmd, re.DOTALL)
        if not m:
            self.status_bar.show_message("Usage: :s/pattern/replacement/[gi]")
            return
        pattern, replacement, flags = m.groups()
        flags = flags or ""
        global_flag = "g" in flags.lower()
        case_sensitive = "i" not in flags.lower()
        state = SearchState(
            pattern=pattern,
            replace=replacement,
            use_regex=global_flag,
            whole_cell=not global_flag,
            case_sensitive=case_sensitive,
        )
        self._search_state = state
        from vimsheet.model.range import CellRange

        try:
            cr = CellRange.from_a1(range_str)
        except Exception:
            self.status_bar.show_message(f"Invalid range: {range_str!r}")
            return
        rows = list(range(cr.start_row, cr.end_row + 1))
        cols = list(range(cr.start_col, cr.end_col + 1))
        searcher = Searcher(self.workbook.active_sheet)
        updates = searcher.collect_replacements(state, rows=rows, cols=cols)
        self._execute_substitute(updates, f":{range_str}")

    def _cmd_col_substitute(self, cmd: str) -> None:
        """Handle column substitute commands.

        Without /g — whole-cell literal match (cell must equal pat exactly):
          :cs/pat/repl/         current column
          :csB/pat/repl/        column B
          :cs2/pat/repl/        column 2 (1-based)
          :A,Ccs/pat/repl/      columns A through C

        With /g — regex global replace within each cell value:
          :cs/pat/repl/g        current column
          :csB/pat/repl/g       column B
        """
        from vimsheet.model.range import col_letters_to_index

        m = self._CS_RE.match(cmd)
        if not m:
            self.status_bar.show_message("Usage: :cs/pat/repl/  :cs/pat/repl/g  :csB/…  :A,Ccs/…")
            return

        col_start_str, col_end_str, col_spec, pattern, replacement, flags = m.groups()
        flags = flags or ""
        global_flag = "g" in flags.lower()

        sheet = self.workbook.active_sheet

        if col_start_str and col_end_str:
            c1 = col_letters_to_index(col_start_str.upper())
            c2 = col_letters_to_index(col_end_str.upper())
            cols = list(range(min(c1, c2), max(c1, c2) + 1))
        elif col_spec:
            if col_spec.isdigit():
                cols = [int(col_spec) - 1]
            else:
                cols = [col_letters_to_index(col_spec.upper())]
        else:
            cols = [self.cursor_col]

        # /g → regex global replace; no /g → whole-cell literal match
        state = SearchState(
            pattern=pattern,
            replace=replacement,
            use_regex=global_flag,
            whole_cell=not global_flag,
        )
        self._search_state = state
        searcher = Searcher(sheet)
        updates = searcher.collect_replacements(state, cols=cols)
        col_labels = ", ".join(chr(ord("A") + c) if c < 26 else f"col{c + 1}" for c in cols)
        self._execute_substitute(updates, f"cs [{col_labels}]")

    def _cmd_row_substitute(self, cmd: str) -> None:
        """Handle row substitute commands.

        Without /g — whole-cell literal match (cell must equal pat exactly):
          :rs/pat/repl/         current row
          :rs3/pat/repl/        row 3 (1-based)
          :1,3rs/pat/repl/      rows 1 through 3

        With /g — regex global replace within each cell value:
          :rs/pat/repl/g        current row
        """
        m = self._RS_RE.match(cmd)
        if not m:
            self.status_bar.show_message("Usage: :rs/pat/repl/  :rs/pat/repl/g  :rs3/…  :1,3rs/…")
            return

        row_start_str, row_end_str, row_spec, pattern, replacement, flags = m.groups()
        flags = flags or ""
        global_flag = "g" in flags.lower()

        sheet = self.workbook.active_sheet

        if row_start_str and row_end_str:
            r1 = int(row_start_str) - 1
            r2 = int(row_end_str) - 1
            rows = list(range(min(r1, r2), max(r1, r2) + 1))
        elif row_spec:
            rows = [int(row_spec) - 1]
        else:
            rows = [self.cursor_row]

        state = SearchState(
            pattern=pattern,
            replace=replacement,
            use_regex=global_flag,
            whole_cell=not global_flag,
        )
        self._search_state = state
        searcher = Searcher(sheet)
        updates = searcher.collect_replacements(state, rows=rows)
        row_labels = ", ".join(str(r + 1) for r in rows)
        self._execute_substitute(updates, f"rs [row(s) {row_labels}]")

    _RANGE_SUB_RE = re.compile(r"^(cs|rs)/(.+?)/(.*?)/([gi]*)$", re.IGNORECASE)

    def _cmd_range_substitute(self, range_str: str, sub_cmd: str) -> None:
        """Handle range-prefixed substitute: :C10:D10 cs/pat/repl/[g].

        The range constrains both rows and columns.
        """
        from vimsheet.model.range import CellRange

        m = self._RANGE_SUB_RE.match(sub_cmd)
        if not m:
            self.status_bar.show_message("Usage: :A1:B5 cs/pat/repl/  or  :A1:B5 rs/pat/repl/g")
            return

        kind, pattern, replacement, flags = m.groups()
        flags = flags or ""
        global_flag = "g" in flags.lower()

        try:
            cr = CellRange.from_a1(range_str.upper())
        except Exception:
            self.status_bar.show_message(f"Invalid range: {range_str!r}")
            return

        rows = list(range(cr.start_row, cr.end_row + 1))
        cols = list(range(cr.start_col, cr.end_col + 1))

        state = SearchState(
            pattern=pattern,
            replace=replacement,
            use_regex=global_flag,
            whole_cell=not global_flag,
        )
        self._search_state = state
        searcher = Searcher(self.workbook.active_sheet)
        updates = searcher.collect_replacements(state, rows=rows, cols=cols)
        self._execute_substitute(updates, f"{kind.lower()} [{range_str.upper()}]")

    def _execute_substitute(
        self, updates: list[tuple[int, int, Any, str | None]], label: str
    ) -> None:
        """Execute a batch of cell replacements with undo support.

        *updates* is a list of (row, col, new_value, new_formula) tuples
        from ``Searcher.collect_replacements()``.
        """
        if not updates:
            self.status_bar.show_message(f"{label}: 0 substitution(s)")
            return
        from vimsheet.model.undo import CompositeCommand, SetCellCommand

        sheet = self.workbook.active_sheet
        cmds: list[SetCellCommand] = []
        for r, c, val, formula in updates:
            cmds.append(SetCellCommand(sheet, r, c, val, new_formula=formula))
        cc = CompositeCommand(cmds)
        cc.description = label
        self.undo_stack.push(cc)
        self.workbook.modified = True
        self.grid.refresh_grid()
        self.status_bar.show_message(f"{label}: {len(updates)} substitution(s)")

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
                        f"Fill: unknown function '{func_name}'. Use: {', '.join(_NUM_TRANSFORMS)}"
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

        from vimsheet.model.undo import FillRangeCommand

        cmd = FillRangeCommand(sheet, updates)
        self.undo_stack.push(cmd)
        self.workbook.modified = True
        self.grid.refresh_grid()
        self._sync_formula_bar()
        self.status_bar.show_message(f"Filled {len(updates)} cells")

    def _cmd_plot(self, data_range: str, chart_type: str = "bar", title: str = "") -> None:
        """Render a chart for *data_range* and display it in a full-screen modal."""
        from vimsheet.plotting.chart import ChartSpec, render_chart
        from vimsheet.ui.chart_screen import ChartScreen

        if not data_range:
            sheet = self.workbook.active_sheet
            from vimsheet.model.range import rowcol_to_a1

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
    # Range sort  (<range> sort [col] [asc|desc] ...)
    # -----------------------------------------------------------------------

    def _cmd_range_sort(self, range_str: str, args: list[str]) -> None:
        """Sort columns within range. Default: all columns ascending."""
        from vimsheet.model.range import CellRange

        try:
            cr = CellRange.from_a1(range_str.upper())
        except Exception:
            self.status_bar.show_message(f"Sort error: invalid range {range_str}")
            return
        r1, c1, r2, c2 = cr.start_row, cr.start_col, cr.end_row, cr.end_col

        def _parse_col(s: str) -> int:
            if s.isalpha():
                return (
                    sum(
                        (ord(ch.upper()) - 64) * (26**i) for i, ch in enumerate(reversed(s.upper()))
                    )
                    - 1
                )
            return int(s) - 1

        def _expand_col_spec(spec: str) -> list[int]:
            cols: list[int] = []
            for part in spec.split(","):
                part = part.strip()
                if not part:
                    continue
                if ":" in part:
                    a, b = part.split(":", 1)
                    c1 = _parse_col(a.strip())
                    c2 = _parse_col(b.strip())
                    if c1 > c2:
                        c1, c2 = c2, c1
                    cols.extend(range(c1, c2 + 1))
                else:
                    cols.append(_parse_col(part))
            return cols

        # Parse sort keys from args
        sort_keys: list[tuple[int, bool]] = []
        i = 0
        while i < len(args):
            token = args[i]
            if token.lower() in ("asc", "desc"):
                # Bare order keyword with no preceding col → apply to all range cols
                if not sort_keys:
                    asc = token.lower() == "asc"
                    sort_keys = [(c, asc) for c in range(c1, c2 + 1)]
                i += 1
            elif ":" in token or "," in token:
                expanded = _expand_col_spec(token)
                asc = True
                if i + 1 < len(args) and args[i + 1].lower() in ("asc", "desc"):
                    asc = args[i + 1].lower() == "asc"
                    i += 2
                else:
                    i += 1
                for c in expanded:
                    sort_keys.append((c, asc))
            elif token.isalpha() or token.isdigit():
                col = _parse_col(token)
                asc = True
                if i + 1 < len(args) and args[i + 1].lower() in ("asc", "desc"):
                    asc = args[i + 1].lower() == "asc"
                    i += 2
                else:
                    i += 1
                sort_keys.append((col, asc))
            else:
                i += 1

        if not sort_keys:
            sort_keys = [
                (c, True) for c in range(c1, c2 + 1) if c >= self.workbook.active_sheet.freeze_cols
            ]

        # Clamp sort range to exclude frozen rows/cols
        sheet = self.workbook.active_sheet
        r1 = max(r1, sheet.freeze_rows)
        if r1 > r2:
            self.status_bar.show_message("Sort range is entirely frozen")
            return
        sort_keys = [(c, asc) for c, asc in sort_keys if c >= sheet.freeze_cols]
        if not sort_keys:
            self.status_bar.show_message("All selected columns are frozen — nothing to sort")
            return

        from vimsheet.model.undo import SortCommand

        cmd = SortCommand(sheet, sort_keys, range_bounds=(r1, c1, r2, c2))
        self.undo_stack.push(cmd)
        self.grid.refresh_grid()
        self.workbook.modified = True
        labels = " ".join(chr(65 + c) if c < 26 else str(c + 1) for c, _ in sort_keys)
        self.status_bar.show_message(f"Sorted range {range_str.upper()} by {labels}")

    # -----------------------------------------------------------------------
    # Range formula yank  (<range> FUNCNAME)
    # -----------------------------------------------------------------------

    def _cmd_range_func(self, range_str: str, func_name: str) -> None:
        """Yank =FUNC(range) — p pastes computed value, P pastes the formula."""
        from vimsheet.formula.evaluator import Evaluator

        formula = f"={func_name}({range_str})"
        ev = Evaluator(self.workbook.active_sheet, self.workbook)
        value = ev.eval_formula(formula)
        self._default_register = RegisterEntry(
            value=value,
            formula=formula,
            src_row=0,
            src_col=0,
        )
        self._yanked_formula = formula
        self.status_bar.show_message(f"Yanked {func_name}={value}  (p=value  P=formula)")

    def _cmd_cond_format(self, sheet: Any, range_str: str, args: list[str]) -> None:
        """Create a conditional format rule.

        Called from both ``:cond <range> ...`` and ``:<range> cond ...``.
        *args* is everything after the range and operator, e.g.
        ``["5", "color", "#ff0000"]``.
        """
        from vimsheet.model.cell import CellFormat
        from vimsheet.model.sheet import CondFormatRule

        if len(args) < 2:
            self.status_bar.show_message(
                "Usage: :cond <range> <op> <value> [color #hex] [bg #hex] [bold]"
            )
            return
        op = args[0].lower()
        val_str = args[1]
        try:
            value: Any = float(val_str)
        except ValueError:
            value = val_str
        fmt = CellFormat()
        extras = args[2:]
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
        rule = CondFormatRule(range_str=range_str, operator=op, value=value, fmt=fmt)
        sheet.cond_formats.append(rule)
        self.grid.refresh_grid()
        self.workbook.modified = True
        self.status_bar.show_message(f"Cond format: {range_str} {op} {val_str}")

    def _apply_func_to_range(self, range_str: str, func_name: str, extra_args: list[str]) -> None:
        """Apply a scalar function element-wise to every cell in *range_str*.

        Called from ``:<range> <FUNCNAME>`` for non-aggregate functions.
        Each cell *c* is replaced with ``=FUNCNAME(c, *extra_args)``.
        Errors and unchanged values are skipped.
        """
        from vimsheet.formula.evaluator import Evaluator
        from vimsheet.model.range import CellRange
        from vimsheet.model.undo import FillRangeCommand

        try:
            cr = CellRange.from_a1(range_str)
        except Exception:
            self.status_bar.show_message(f"Invalid range: {range_str!r}")
            return
        sheet = self.workbook.active_sheet
        ev = Evaluator(sheet, self.workbook)
        updates: list[tuple[int, int, Any]] = []
        for r in range(cr.start_row, cr.end_row + 1):
            for c in range(cr.start_col, cr.end_col + 1):
                cell = sheet.get_cell(r, c)
                if cell is None:
                    continue
                val = cell.value
                if val is None or val == "":
                    continue
                args_repr = [repr(val)] + extra_args
                formula = f"={func_name}({', '.join(args_repr)})"
                try:
                    new_val = ev.eval_formula(formula)
                except Exception:
                    continue
                if isinstance(new_val, str) and new_val.startswith("#"):
                    continue
                if new_val != val:
                    updates.append((r, c, new_val))
        if updates:
            self.undo_stack.push(FillRangeCommand(sheet, updates))
            self.grid.refresh_grid()
            self.workbook.modified = True
            self.status_bar.show_message(
                f"Applied {func_name} to {len(updates)} cell{'s' if len(updates) != 1 else ''}"
            )
        else:
            self.status_bar.show_message(f"{func_name}: no cells changed")

    def _parse_fmt_kwargs(self, tokens: list[str]) -> dict | None:
        """
        Parse format property tokens (e.g. ``bg=red fg=white bold``) into
        kwargs for FormatCommand.
        """
        kwargs: dict = {}
        for token in tokens:
            key = val = ""
            if "=" in token:
                key, val = token.split("=", 1)
            else:
                key = token
                val = "true"
            key = key.lower()
            match key:
                case "color" | "fg":
                    kwargs["fg_color"] = val
                case "bg" | "background":
                    kwargs["bg_color"] = val
                case "bold":
                    kwargs["bold"] = True
                case "italic":
                    kwargs["italic"] = True
                case "underline":
                    kwargs["underline"] = True
                case "align":
                    kwargs["align"] = val
                case "num_decimals":
                    try:
                        kwargs["num_decimals"] = int(val)
                    except ValueError:
                        self.status_bar.show_message(f"Invalid num_decimals: {val!r}")
                        return None
                case "num_format":
                    kwargs["num_format"] = val
                case "thousands_sep":
                    kwargs["thousands_sep"] = val.lower() in ("true", "1", "yes")
                case _:
                    self.status_bar.show_message(f"Unknown format property: {key!r}")
                    return None
        return kwargs

    # -----------------------------------------------------------------------
    # External scripts
    # -----------------------------------------------------------------------

    def __run_external_script(self, range_str: str, script_path: str) -> None:
        """Pipe *range_str* data to *script_path* and apply JSON results back."""
        import json
        import subprocess
        import sys as _sys

        from vimsheet.model.range import CellRange, a1_to_rowcol, rowcol_to_a1

        script = self._resolve_script_path(script_path)
        if not script.exists():
            self.status_bar.show_message(f"Script not found: {script}")
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
        from vimsheet.model.undo import CompositeCommand, SetCellCommand

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
            from vimsheet.model.undo import CompositeCommand

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

    def _resolve_script_path(self, script_path: str) -> Path:
        """Resolve *script_path*, falling back to scripts_dir for relative paths."""
        from pathlib import Path as _Path

        p = _Path(script_path).expanduser()
        if not p.is_absolute():
            p = self.config.get_scripts_dir() / p
        return p

    def _register_script_func(
        self, name: str, script_path: str, *, silent: bool = False, desc: str = ""
    ) -> None:
        """Register *script_path* as formula function *name* with optional *desc*."""
        script = self._resolve_script_path(script_path)
        if not script.exists():
            msg = f"Script not found: {script}"
            if not silent:
                self.status_bar.show_message(msg)
            return
        self._script_funcs[name] = str(script)
        from vimsheet.formula.functions.registry import register_script_function

        register_script_function(name, str(script), desc=desc)
        if not silent:
            self.status_bar.show_message(f"Registered function: @{name}")

    def _load_script_functions(self) -> None:
        """Auto-register functions listed in the functions file at startup."""
        funcs_file = self.config.get_functions_file()
        if not funcs_file.exists():
            return
        loaded = 0
        for _, raw in enumerate(funcs_file.read_text(encoding="utf-8").splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(None, 2)
            if len(parts) < 2:
                continue
            name = parts[0].upper()
            path = parts[1]
            desc = parts[2] if len(parts) >= 3 else ""
            self._register_script_func(name, path, silent=True, desc=desc)
            loaded += 1
        if loaded:
            self.status_bar.show_message(f"Auto-loaded {loaded} script function(s)")

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

        from vimsheet.model.range import CellRange, a1_to_rowcol
        from vimsheet.model.undo import CompositeCommand, SetCellCommand

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
                from vimsheet.model.undo import ClearCellCommand

                r, c = self.cursor_row, self.cursor_col
                cmd = ClearCellCommand(self.workbook.active_sheet, r, c)
                self.undo_stack.push(cmd)
                self.workbook.modified = True
                self.grid.refresh_grid()
            case "paste":
                _, after, data = action
                from vimsheet.model.undo import PasteCommand

                dr = 1 if after else 0
                r, c = self.cursor_row + dr, self.cursor_col
                cmd = PasteCommand(self.workbook.active_sheet, r, c, data)
                self.undo_stack.push(cmd)
                self.workbook.modified = True
                self.grid.refresh_grid()
            case "delete_row":
                from vimsheet.model.undo import DeleteRowCommand

                r = self.cursor_row
                cmd = DeleteRowCommand(self.workbook.active_sheet, r)
                self.undo_stack.push(cmd)
                self.workbook.modified = True
                self.grid.refresh_grid()
            case "delete_col":
                from vimsheet.model.undo import DeleteColCommand

                c = self.cursor_col
                cmd = DeleteColCommand(self.workbook.active_sheet, c)
                self.undo_stack.push(cmd)
                self.workbook.modified = True
                self.grid.refresh_grid()
            case "incr":
                _, delta = action
                self.normal_handler._increment_cell(delta)
                self.status_bar.show_message("Cannot repeat this action")
        self._sync_formula_bar()
        self._sync_status_bar()

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    # -----------------------------------------------------------------------
    # Inline confirmation prompt
    # -----------------------------------------------------------------------

    def _ask_confirm(self, message: str, callback: Any) -> None:
        """Show *message* in the status bar and wait for y / n / Enter."""
        self._pending_confirm = (message, callback)
        prompt = f"{message} [y/N]: "
        self.status_bar.set_persistent_message(prompt, priority=1)
        with contextlib.suppress(Exception):
            self.formula_bar.update_cell(
                self.formula_bar.cell_address,
                prompt,
                locked=False,
                cursor_pos=len(prompt),
            )

    # -----------------------------------------------------------------------
    # Buffer management
    # -----------------------------------------------------------------------

    def _switch_buffer(self, idx: int) -> None:
        if not (0 <= idx < len(self._buffers)):
            self.status_bar.show_message(f"No buffer {idx + 1}")
            return
        self._active_buf_idx = idx
        self.workbook = self._buffers[idx]
        self.grid.workbook = self.workbook
        self.undo_stack.clear()
        self._on_sheet_changed()
        name = self.workbook.filepath.name if self.workbook.filepath else "[No Name]"
        self.status_bar.show_message(f"Buffer {idx + 1}: {name}")

    def _cmd_split(self, path_str: str) -> None:
        """Open *path_str* as a new buffer and make it active."""
        from vimsheet.io.registry import get_adapter

        path = Path(path_str)
        try:
            if path.exists():
                adapter = get_adapter(path)
                wb = adapter.read(path)
                wb._bind_sheets()
            else:
                wb = Workbook.blank()
                wb.filepath = path
            self._buffers.append(wb)
            self._active_buf_idx = len(self._buffers) - 1
            self.workbook = wb
            self.grid.workbook = self.workbook
            self.undo_stack.clear()
            self._on_sheet_changed()
            self._trigger_fetch_cells()
            label = path.name if path.exists() else f"{path.name} [new]"
            self.status_bar.show_message(f"Buffer {self._active_buf_idx + 1}: {label}")
        except Exception as exc:
            self.status_bar.show_message(f"Split error: {exc}")

    def _cmd_buffers(self) -> None:
        """Show the buffer list overlay."""
        from vimsheet.ui.buffers_screen import BuffersScreen

        self.push_screen(BuffersScreen(self._buffers, self._active_buf_idx))

    def _cmd_bdelete(self, force: bool = False) -> None:
        """Close the active buffer."""
        wb = self._buffers[self._active_buf_idx]
        if wb.modified and not force:
            self.status_bar.show_message("Unsaved changes — use :bd! to force close")
            return
        if len(self._buffers) == 1:
            self.status_bar.show_message("Last buffer — use :q to quit")
            return
        closed_name = str(wb.filepath) if wb.filepath else "[No Name]"
        self._buffers.pop(self._active_buf_idx)
        self._active_buf_idx = min(self._active_buf_idx, len(self._buffers) - 1)
        self.workbook = self._buffers[self._active_buf_idx]
        self.grid.workbook = self.workbook
        self.undo_stack.clear()
        self._on_sheet_changed()
        name = self.workbook.filepath.name if self.workbook.filepath else "[No Name]"
        self.status_bar.show_message(
            f"Closed: {closed_name}  →  Buffer {self._active_buf_idx + 1}: {name}"
        )

    def _save_and_quit(self) -> None:
        self._save_file(None)
        self.exit()

    def _save_file(self, path: Path | None) -> None:
        target = path or self.workbook.filepath
        if target is None:
            self.status_bar.show_message("No filename — use :w <file>")
            return
        from vimsheet.io.registry import get_adapter

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
        from vimsheet.io.registry import get_adapter

        try:
            adapter = get_adapter(path)
            self.workbook = adapter.read(path)
            self.workbook._bind_sheets()
            self._buffers[self._active_buf_idx] = self.workbook
            self.grid.workbook = self.workbook
            self.undo_stack.clear()
            self._on_sheet_changed()
            self._trigger_fetch_cells()
            self.status_bar.show_message(f"Opened: {path}")
        except Exception as exc:
            self.status_bar.show_message(f"Open error: {exc}")

    def _export_file(self, fmt: str, path: Path) -> None:
        from vimsheet.io.registry import get_adapter_by_name

        try:
            adapter = get_adapter_by_name(fmt)
            adapter.write(self.workbook, path)
            self.status_bar.show_message(f"Exported ({fmt}): {path}")
        except Exception as exc:
            self.status_bar.show_message(f"Export error: {exc}")

    def _set_config(self, key: str, val: str) -> None:
        """Set a config value by name, coerce type, and persist to disk."""
        from vimsheet.model.config import Config

        if not hasattr(self.config, key):
            self.status_bar.show_message(f"Unknown config key: {key!r}")
            return
        field_type = type(getattr(self.config, key))
        try:
            if field_type is bool:
                coerced: Any = val.lower() in ("true", "1", "yes", "on")
            else:
                coerced = field_type(val)
        except (ValueError, TypeError):
            self.status_bar.show_message(f"Invalid value for {key!r}: {val!r}")
            return
        setattr(self.config, key, coerced)
        self.config.save(Config.default_path())
        self.status_bar.show_message(f"{key} = {coerced!r}  (saved)")
        # Apply side effects of config changes
        match key:
            case "autocalc":
                self.workbook.set_autocalc(coerced)
            case "formula_bar_visible":
                self.query_one("#formula-bar").display = coerced
            case "status_bar_visible":
                self.query_one("#status-bar").display = coerced
            case "show_grid_lines" | "show_row_headers" | "show_col_headers" | "default_col_width":
                self.grid.update_config(self.config)
            case "autosave":
                if coerced:
                    self._start_autosave()
                else:
                    self._stop_autosave()
            case "autosave_interval":
                if self.config.autosave:
                    self._stop_autosave()
                    self._start_autosave()
            case "theme":
                self._apply_theme(coerced)

    def _start_autosave(self) -> None:
        self._stop_autosave()
        self._autosave_handle = self.set_interval(self.config.autosave_interval, self._auto_save)

    def _stop_autosave(self) -> None:
        handle = getattr(self, "_autosave_handle", None)
        if handle is not None:
            handle.stop()
            self._autosave_handle = None

    def _auto_save(self) -> None:
        if self.workbook.modified and self.workbook.filepath:
            from vimsheet.io.registry import get_adapter

            try:
                adapter = get_adapter(self.workbook.filepath)
                adapter.write(self.workbook, self.workbook.filepath)
                self.workbook.modified = False
                self.status_bar.show_message("Auto-saved")
            except Exception as exc:
                self.status_bar.show_message(f"Auto-save error: {exc}")

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

        # Show confirm prompt in formula bar when pending
        if self._pending_confirm is not None:
            msg, _ = self._pending_confirm
            content = f"{msg} [y/N]: "
            cursor_pos = len(content)
            locked = False
            self.formula_bar.update_cell(address, content, locked, cursor_pos=cursor_pos)
            self.formula_bar.is_modified = self.workbook.modified
            self.formula_bar.mode = self.mode
            return

        match self.mode:
            case Mode.INSERT:
                content = self._insert_buffer
                cursor_pos = self._insert_cursor
            case Mode.EDIT:
                content = self._edit_buffer
                cursor_pos = self._edit_cursor
            case Mode.COMMAND:
                content = f":{self._command_buffer}"
                cursor_pos = len(content)  # block cursor at end of command buffer
            case Mode.SEARCH:
                content = self._command_buffer
                cursor_pos = len(content)
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

        # Re-assert high-priority prompts — these survive any transient messages
        if self._pending_confirm is not None:
            msg, _ = self._pending_confirm
            self.status_bar.set_persistent_message(f"{msg} [y/N]: ", priority=1)
            return
        if self._swap_buf is not None:
            self.status_bar.set_persistent_message(
                f"{self._swap_mode_prefix()}: {self._swap_buf}", priority=2
            )
            return
        if self.mode == Mode.COMMAND:
            self.status_bar.set_persistent_message(f":{self._command_buffer}", priority=2)
            return
        if self.mode == Mode.SEARCH:
            self.status_bar.set_persistent_message(self._command_buffer, priority=2)
            return

        if self.mode.is_visual():
            sel = self.grid.visual_selection()
            if sel:
                self.status_bar.message = f"{sel.num_rows}r × {sel.num_cols}c selected"
        if self.macro_recorder.is_recording:
            reg = self.macro_recorder.recording_register
            self.status_bar.message = f"Recording @{reg}..."

    def _sync_grid_preview(self) -> None:
        """Update grid live preview for insert/edit mode, or clear it otherwise."""
        if self.mode == Mode.INSERT:
            self.grid.set_preview(self.cursor_row, self.cursor_col, self._insert_buffer)
            self.grid._rebuild_heights()
            self.grid.refresh()
        elif self.mode == Mode.EDIT:
            self.grid.set_preview(self.cursor_row, self.cursor_col, self._edit_buffer)
            self.grid._rebuild_heights()
            self.grid.refresh()
        else:
            if self.grid._preview_row is not None:
                self.grid.set_preview(None, None, "")
                self.grid._rebuild_heights()
                self.grid.refresh()

    def _on_sheet_changed(self) -> None:
        self._sync_sheet_tabs()
        sheet = self.workbook.active_sheet
        r = sheet.cursor_row if self.config.save_cursor else 0
        c = sheet.cursor_col if self.config.save_cursor else 0
        self.grid.move_cursor(r, c)
        self.grid.refresh_grid()
        self._sync_formula_bar()
        self._sync_status_bar()
        self._sync_grid_preview()

    def _sync_sheet_tabs(self) -> None:
        names = [s.name for s in self.workbook.sheets]
        self.sheet_tabs.set_sheets(names, self.workbook.active_sheet_idx)

    def _apply_theme(self, name: str) -> None:
        """Switch colour theme using Textual's built-in system, then push palette to widgets."""
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
            self._current_theme_name = name
            self.call_later(self._push_palette)
            self.status_bar.show_message(f"Theme: {resolved}")
        except Exception:
            available = (
                "dark light nord gruvbox dracula tokyo monokai solarized catppuccin rose-pine"
            )
            self.status_bar.show_message(f"Unknown theme {name!r}. Try: {available}")

    def _push_palette(self) -> None:
        """Compute a fresh GridPalette from the current theme and push it to all widgets."""
        self._palette = GridPalette.from_config(
            variables=self.theme_variables,
            theme_name=self._current_theme_name,
            theme_overrides=self.config.theme_overrides,
        )
        self.grid.set_palette(self._palette)
        self.sheet_tabs.set_palette(self._palette)
        self.formula_bar.set_palette(self._palette)

    def _cmd_colorscheme(self, args: list[str]) -> None:
        """Handle ``:colorscheme`` command."""
        from vimsheet.ui.grid_palette import _resolve_color_value

        def _field_names() -> list[str]:
            from dataclasses import fields as _dcf

            from vimsheet.ui.grid_palette import GridPalette

            return sorted(f.name for f in _dcf(GridPalette))

        def _show_current() -> None:
            lines = [f"{k}={v}" for k, v in self._palette.as_dict().items()]
            self.status_bar.show_message(" | ".join(lines[:6]) + " …")

        if not args:
            _show_current()
            return

        match args[0]:
            case "reset":
                if len(args) > 1:
                    field_key = args[1]
                    if field_key not in _field_names():
                        self.status_bar.show_message(f"Unknown palette field: {field_key!r}")
                        return
                    fresh = GridPalette.from_config(
                        variables=self.theme_variables,
                        theme_name=self._current_theme_name,
                        theme_overrides=self.config.theme_overrides,
                    )
                    setattr(self._palette, field_key, getattr(fresh, field_key))
                    self._push_palette()
                    self.status_bar.show_message(f"Reset {field_key} to theme default")
                else:
                    self._palette = GridPalette.from_config(
                        variables=self.theme_variables,
                        theme_name=self._current_theme_name,
                        theme_overrides=self.config.theme_overrides,
                    )
                    self._push_palette()
                    self.status_bar.show_message("Reset all palette fields to theme defaults")
            case "save":
                if not self._current_theme_name:
                    self.status_bar.show_message("No active theme — cannot save overrides")
                    return
                from vimsheet.model.config import Config

                overrides = self.config.theme_overrides or {}
                # Re-derive current overrides from theme_variables so we store
                # them as user-entered values (from current palette state).
                # We need to invert: palette has resolved hex values, config stores raw.
                # For now, store resolved hex as the simplest approach.
                theme_cfg = overrides.setdefault(self._current_theme_name, {})
                for fname in _field_names():
                    cur = getattr(self._palette, fname)
                    default_palette = GridPalette.from_theme_variables(self.theme_variables)
                    default_val = getattr(default_palette, fname)
                    if cur != default_val:
                        theme_cfg[fname] = cur
                    elif fname in theme_cfg:
                        del theme_cfg[fname]
                self.config.theme_overrides = overrides
                self.config.save(Config.default_path())
                self.status_bar.show_message(
                    f"Colorscheme saved for theme '{self._current_theme_name}'"
                )
            case _ if len(args) >= 2:
                field_key = args[0]
                raw_value = " ".join(args[1:])
                if field_key not in _field_names():
                    self.status_bar.show_message(
                        f"Unknown palette field: {field_key!r}. "
                        f"Try: {', '.join(_field_names()[:6])} …"
                    )
                    return
                resolved = _resolve_color_value(raw_value, self.theme_variables)
                if resolved is None:
                    self.status_bar.show_message(
                        f"Invalid color value: {raw_value!r}. "
                        "Use hex (#ff0000), named (red), or $variable ($primary)."
                    )
                    return
                setattr(self._palette, field_key, resolved)
                self._push_palette()
                self.status_bar.show_message(f"{field_key} = {raw_value}  ({resolved})")
            case _:
                _show_current()

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
                for r in range(r1 + 1, r2 + 1):
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
            for r in range(r1 + 1, r2 + 1):
                sheet.hidden_rows.add(r)
            self.status_bar.show_message(f"Folded rows {r1 + 1}–{r2 + 1}")
        elif action == "remove":
            sheet.row_groups.remove(grp)
            sheet.hidden_rows -= rows_in_group
            self.status_bar.show_message(f"Removed row group {r1 + 1}–{r2 + 1}")
        else:
            sheet.hidden_rows -= rows_in_group
            self.status_bar.show_message(f"Unfolded rows {r1 + 1}–{r2 + 1}")
        self.workbook.modified = True
        self.grid.refresh_grid()

    def _fold_col_group(self, action: str) -> None:
        """Fold/unfold the column group containing the cursor column.

        action: 'close' | 'open' | 'toggle' | 'open_all' | 'close_all'
        """
        sheet = self.workbook.active_sheet
        col = self.cursor_col

        if action == "open_all":
            sheet.hidden_cols.clear()
            self.grid.refresh_grid()
            self.status_bar.show_message("All column groups opened")
            return
        if action == "close_all":
            for c1, c2 in sheet.col_groups:
                for c in range(c1 + 1, c2 + 1):
                    sheet.hidden_cols.add(c)
            self.grid.refresh_grid()
            self.status_bar.show_message("All column groups closed")
            return

        grp = next(((c1, c2) for c1, c2 in sheet.col_groups if c1 <= col <= c2), None)
        if grp is None:
            self.status_bar.show_message("No column group at cursor — use :colgroup c1 c2 first")
            return
        c1, c2 = grp
        cols_in_group = set(range(c1, c2 + 1))
        currently_hidden = cols_in_group & sheet.hidden_cols

        if action == "close" or (action == "toggle" and not currently_hidden):
            for c in range(c1 + 1, c2 + 1):
                sheet.hidden_cols.add(c)
            self.status_bar.show_message(f"Folded columns {c1 + 1}–{c2 + 1}")
        elif action == "remove":
            from vimsheet.model.range import col_index_to_letters

            sheet.col_groups.remove(grp)
            sheet.hidden_cols -= cols_in_group
            self.status_bar.show_message(
                f"Removed column group {col_index_to_letters(c1)}–{col_index_to_letters(c2)}"
            )
        else:
            sheet.hidden_cols -= cols_in_group
            self.status_bar.show_message(f"Unfolded columns {c1 + 1}–{c2 + 1}")
        self.workbook.modified = True
        self.grid.refresh_grid()

    # -----------------------------------------------------------------------
    # Message handlers
    # -----------------------------------------------------------------------

    def on_grid_widget_cursor_moved(self, message: GridWidget.CursorMoved) -> None:
        self._sync_formula_bar()
        self._sync_status_bar()

    def on_sheet_tabs_sheet_selected(self, message: SheetTabs.SheetSelected) -> None:
        current = self.workbook.active_sheet
        current.cursor_row, current.cursor_col = self.grid.cursor_row, self.grid.cursor_col
        self.workbook.go_to_sheet(message.index)
        self._on_sheet_changed()

    def on_sheet_tabs_add_sheet(self, _message: SheetTabs.AddSheet) -> None:
        self.workbook.add_sheet()
        self.workbook.active_sheet_idx = len(self.workbook.sheets) - 1
        self._on_sheet_changed()
