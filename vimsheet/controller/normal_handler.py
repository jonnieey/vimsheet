"""Normal mode key handler — all vim-like Normal mode bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from vimsheet.controller.mode import Mode
from vimsheet.controller.search import Searcher, SearchState
from vimsheet.model.range import CellRange
from vimsheet.model.register import RegisterEntry

if TYPE_CHECKING:
    from vimsheet.app import VimSheetApp


class NormalHandler:
    """Handles all key events while in Normal mode."""

    def __init__(self, app: VimSheetApp) -> None:
        self._app = app

    def handle(self, key: str) -> None:  # noqa: C901
        app = self._app

        buf = app._key_buffer + key

        # Stop macro recording on bare q — do this before recording the key
        if key == "q" and buf == "q" and app.macro_recorder.is_recording:
            app.macro_recorder.stop_recording()
            app._key_buffer = ""
            app.status_bar.show_message("Macro recorded")
            self._end_key()
            return

        # Record key into macro if recording (after stop-check so stop-q isn't stored)
        app.macro_recorder.record_key(key)

        # ---- Multi-character chords ------------------------------------------
        match buf:
            # Numeric prefix: 1-9 starts a count, 0-9 continues it
            # (bare "0" is not buffered — it falls through to move_to_row_start)
            case s if s.isdigit() and (s[0] != "0" or len(s) > 1):
                app._key_buffer = s
                app.status_bar.set_persistent_message(s)
                return

            # <n>ctrl+a / <n>ctrl+x — add/subtract n from current cell
            case s if s.endswith("ctrl+a") and s[: -len("ctrl+a")].isdigit():
                self._increment_cell(int(s[: -len("ctrl+a")]))
                app._key_buffer = ""
                app._last_action = ("incr", int(s[: -len("ctrl+a")]))
                app.status_bar.set_persistent_message("")
                return
            case s if s.endswith("ctrl+x") and s[: -len("ctrl+x")].isdigit():
                self._increment_cell(-int(s[: -len("ctrl+x")]))
                app._key_buffer = ""
                app._last_action = ("incr", -int(s[: -len("ctrl+x")]))
                app.status_bar.set_persistent_message("")
                return

            # nG — jump to row n
            case s if len(s) >= 2 and s[:-1].isdigit() and s[-1] == "G":
                app.grid.move_cursor(max(0, int(s[:-1]) - 1), app.cursor_col)
                app._key_buffer = ""
                app.status_bar.set_persistent_message("")
                return

            # Navigation chords
            case "gg":
                app.grid.move_to_first_row()
                app._key_buffer = ""
                return

            # go{address}<Enter> — navigate to cell address
            case "go":
                app._key_buffer = "go"
                app.status_bar.set_persistent_message("go: ", priority=2)
                return
            case s if s.startswith("go") and len(s) > 2:
                if key == "escape":
                    app._key_buffer = ""
                    app.status_bar.set_persistent_message("", priority=2)
                elif key in ("enter", "\r", "\n"):
                    addr = app._key_buffer[2:]
                    self._goto_address(addr)
                    app._key_buffer = ""
                elif key == "backspace":
                    current = app._key_buffer
                    app._key_buffer = current[:-1] if len(current) > 2 else "go"
                    app.status_bar.set_persistent_message(f"go: {app._key_buffer[2:]}", priority=2)
                else:
                    app._key_buffer = s
                    app.status_bar.set_persistent_message(f"go: {app._key_buffer[2:]}", priority=2)
                return

            # Sheet navigation
            case "gt":
                app.workbook.go_to_next_sheet()
                app._on_sheet_changed()
                app._key_buffer = ""
                return
            case "gT":
                app.workbook.go_to_prev_sheet()
                app._on_sheet_changed()
                app._key_buffer = ""
                return
            case s if len(s) == 2 and s[0] == "g" and s[1].isdigit():
                app.workbook.go_to_sheet(int(s[1]) - 1)
                app._on_sheet_changed()
                app._key_buffer = ""
                return

            # gw — open cell in $EDITOR / $VISUAL
            case "gw":
                app._key_buffer = ""
                app.open_in_external_editor()
                return

            # gv — valueize: replace formula with current computed value
            case "gv":
                self._valueize_cell()
                app._key_buffer = ""
                return

            # gx prefix — swap cell with address
            case "gx":
                app._key_buffer = ""
                app._swap_buf = ""
                app._swap_mode = "cell"
                app._swap_keep_cursor = False
                app.status_bar.set_persistent_message("gx: ", priority=2)
                return
            case "gX":
                app._key_buffer = ""
                app._swap_buf = ""
                app._swap_mode = "cell"
                app._swap_keep_cursor = True
                app.status_bar.set_persistent_message("gX: ", priority=2)
                return

            # grx prefix — swap row with target row
            case "grx":
                app._key_buffer = ""
                app._swap_buf = ""
                app._swap_mode = "row"
                app._swap_keep_cursor = False
                app.status_bar.set_persistent_message("grx: ", priority=2)
                return
            case "grX":
                app._key_buffer = ""
                app._swap_buf = ""
                app._swap_mode = "row"
                app._swap_keep_cursor = True
                app.status_bar.set_persistent_message("grX: ", priority=2)
                return

            # gcx prefix — swap column with target column
            case "gcx":
                app._key_buffer = ""
                app._swap_buf = ""
                app._swap_mode = "col"
                app._swap_keep_cursor = False
                app.status_bar.set_persistent_message("gcx: ", priority=2)
                return
            case "gcX":
                app._key_buffer = ""
                app._swap_buf = ""
                app._swap_mode = "col"
                app._swap_keep_cursor = True
                app.status_bar.set_persistent_message("gcX: ", priority=2)
                return

            # c prefix — change (clear + enter insert)
            case "cw" | "cc":
                self._clear_cell()
                app._enter_insert("right")
                app._key_buffer = ""
                return

            # d prefix — delete (clear, stay in normal)
            case "dw":
                self._clear_cell()
                app._key_buffer = ""
                return
            case "d$":
                self._delete_to_row_end()
                app._key_buffer = ""
                return

            # gs prefix — shift cell
            case "gsj":
                self._shift_cell(1, 0)
                app._key_buffer = ""
                return
            case "gsk":
                self._shift_cell(-1, 0)
                app._key_buffer = ""
                return
            case "gsl":
                self._shift_cell(0, 1)
                app._key_buffer = ""
                return
            case "gsh":
                self._shift_cell(0, -1)
                app._key_buffer = ""
                return

            # Marks: m{a-zA-Z} set, '{a-z} jump
            case s if len(s) == 2 and s[0] == "m" and s[1].isalpha():
                reg = s[1]
                sheet_idx = app.workbook.active_sheet_idx
                app._marks[reg] = (sheet_idx, app.cursor_row, app.cursor_col)
                app.status_bar.show_message(f"Mark '{reg}' set")
                app._key_buffer = ""
                return
            case s if len(s) == 2 and s[0] == "'" and s[1].isalpha():
                reg = s[1]
                if reg in app._marks:
                    sheet_idx, r, c = app._marks[reg]
                    if sheet_idx != app.workbook.active_sheet_idx:
                        app.workbook.go_to_sheet(sheet_idx)
                        app._on_sheet_changed()
                    app.grid.move_cursor(r, c)
                else:
                    app.status_bar.show_message(f"Mark '{reg}' not set")
                app._key_buffer = ""
                return

            # Macro: q{a-z} start recording, q stop
            case s if len(s) == 2 and s[0] == "q" and s[1].islower():
                reg = s[1]
                app.macro_recorder.start_recording(reg)
                app.status_bar.show_message(f"Recording macro '{reg}'...")
                app._key_buffer = ""
                return

            # @{a-z} run macro, @@ run last
            case s if len(s) == 2 and s[0] == "@":
                reg = s[1]
                if app.macro_recorder.is_recording:
                    app.status_bar.show_message("Cannot replay macro while recording")
                    app._key_buffer = ""
                    return
                if reg == "@":
                    actual_reg = app.macro_recorder.recording_register or reg
                    keys = app.macro_recorder.replay_last()
                else:
                    actual_reg = reg
                    keys = app.macro_recorder.get_macro(reg)
                if keys:
                    if actual_reg in app._replaying_macros:
                        app.status_bar.show_message(f"Recursive macro '@{actual_reg}' skipped")
                        app._key_buffer = ""
                        return
                    app._replaying_macros.add(actual_reg)
                    app._key_buffer = ""
                    try:
                        app._replay_keys(keys)
                    finally:
                        app._replaying_macros.discard(actual_reg)
                else:
                    app.status_bar.show_message(f"No macro in register '{reg}'")
                app._key_buffer = ""
                return

            # Named register: "{a-z/+} prefix for yank/paste
            case s if (
                len(s) == 2 and s[0] == '"' and (s[1].isalpha() or s[1].isdigit() or s[1] == "+")
            ):
                app._pending_register = s[1]
                app._key_buffer = ""
                # Next key is the operation — let it fall through
                return

            # System clipboard prefix "+
            case '"+':
                app._pending_register = "+"
                app._key_buffer = ""
                return

            # Format chords (t prefix — toggle)
            case "tb":
                self._toggle_fmt("bold")
                app._key_buffer = ""
                return
            case "ti":
                self._toggle_fmt("italic")
                app._key_buffer = ""
                return
            case "tu":
                self._toggle_fmt("underline")
                app._key_buffer = ""
                return
            case "tl":
                self._set_align("left")
                app._key_buffer = ""
                return
            case "tr":
                self._set_align("right")
                app._key_buffer = ""
                return
            case "tc":
                self._set_align("center")
                app._key_buffer = ""
                return

            # Row / col operations
            case "ir":
                self._insert_row_above()
                app._key_buffer = ""
                return
            case "iR":
                self._insert_row_below()
                app._key_buffer = ""
                return
            case "ic":
                self._insert_col_left()
                app._key_buffer = ""
                return
            case "iC":
                self._insert_col_right()
                app._key_buffer = ""
                return
            case "dr":
                self._delete_row()
                app._key_buffer = ""
                return
            case "dc":
                self._delete_col()
                app._key_buffer = ""
                return
            case "yr":
                self._yank_row()
                app._key_buffer = ""
                return
            case "yc":
                self._yank_col()
                app._key_buffer = ""
                return
            case "sR":
                self._hide_row()
                app._key_buffer = ""
                return
            case "sC":
                self._hide_col()
                app._key_buffer = ""
                return
            case "sr":
                self._show_row()
                app._key_buffer = ""
                return
            case "sc":
                self._show_col()
                app._key_buffer = ""
                return

            # Yank chords
            case "yy":
                self._yank_cell(formula=True)
                app._key_buffer = ""
                return
            case "YY":
                self._yank_cell(formula=False)
                app._key_buffer = ""
                return
            case "dd":
                self._cut_row()
                app._key_buffer = ""
                return

            case "zl":
                self._lock_cell(True)
                app._key_buffer = ""
                return
            case "zL":
                self._lock_cell(False)
                app._key_buffer = ""
                return

            # Fold / group
            case "zc":
                app._fold_group("close")
                app._key_buffer = ""
                return
            case "zo":
                app._fold_group("open")
                app._key_buffer = ""
                return
            case "za":
                app._fold_group("toggle")
                app._key_buffer = ""
                return
            case "zR":
                app._fold_group("open_all")
                app._key_buffer = ""
                return
            case "zM":
                app._fold_group("close_all")
                app._key_buffer = ""
                return
            case "zC":
                app._fold_col_group("close")
                app._key_buffer = ""
                return
            case "zO":
                app._fold_col_group("open")
                app._key_buffer = ""
                return
            case "zA":
                app._fold_col_group("toggle")
                app._key_buffer = ""
                return
            case "zr":
                app._fold_group("remove")
                app._key_buffer = ""
                return
            case "ZR":
                app._fold_col_group("remove")
                app._key_buffer = ""
                return

            # z-enter / z. / z-  — scroll cell to top/center/bottom
            case "zenter":
                app.grid.scroll_cell_to_top()
                app._key_buffer = ""
                return
            case "z.":
                app.grid.scroll_cell_to_center()
                app._key_buffer = ""
                return
            case "z-":
                app.grid.scroll_cell_to_bottom()
                app._key_buffer = ""
                return

            # Row expand / collapse
            case "z_":
                app.grid.collapse_row(app.cursor_row)
                app._key_buffer = ""
                return
            case "z+":
                app.grid.expand_row(app.cursor_row)
                app._key_buffer = ""
                return

            # Horizontal scroll — viewport left/right one column
            case "zs":
                sx = int(app.grid.scroll_offset.x)
                cw = app.grid.get_col_width(app.grid.cursor_col) + 1
                app.grid.scroll_to(x=max(0, sx - cw), animate=False, force=True)
                app.grid.refresh()
                app._key_buffer = ""
                return
            case "ze":
                sx = int(app.grid.scroll_offset.x)
                cw = app.grid.get_col_width(app.grid.cursor_col) + 1
                app.grid.scroll_to(x=sx + cw, animate=False, force=True)
                app.grid.refresh()
                app._key_buffer = ""
                return

            # ZZ / ZQ
            case "ZZ":
                app._save_and_quit()
                app._key_buffer = ""
                return
            case "ZQ":
                app.exit()
                return

            # Pending prefixes (no standalone action for these)
            case (
                "c"
                | "gr"
                | "gc"
                | "gs"
                | "g"
                | "i"
                | "d"
                | "y"
                | "Y"
                | "s"
                | "t"
                | "z"
                | "Z"
                | "m"
                | "'"
                | "@"
                | '"'
                | "q"
            ):
                app._key_buffer = buf
                return

        # Unrecognised chord → single-key dispatch
        count = int(app._key_buffer) if app._key_buffer.isdigit() and app._key_buffer else 1
        app._key_buffer = ""

        match key:
            # ---- Navigation ------------------------------------------------
            case "h" | "left":
                app.grid.move_by(0, -1)
            case "l" | "right":
                app.grid.move_by(0, 1)
            case "j" | "down":
                app.grid.move_by(1, 0)
            case "k" | "up":
                app.grid.move_by(-1, 0)
            case "G":
                app.grid.move_to_last_row()
            case "0":
                app.grid.move_to_row_start()
            case "$":
                app.grid.move_to_row_end()
            case "^":
                app.grid.move_to_first_nonempty_in_row()
            case "w" | "ctrl+right":
                app.grid.jump_next_nonempty_right()
            case "b" | "ctrl+left":
                app.grid.jump_next_nonempty_left()
            case "ctrl+down":
                app.grid.jump_next_nonempty_down()
            case "ctrl+up":
                app.grid.jump_next_nonempty_up()
            case "ctrl+f" | "pagedown":
                app.grid.page_down()
            case "ctrl+b" | "pageup":
                app.grid.page_up()
            case "ctrl+d":
                app.grid.half_page_down()
            case "ctrl+u":
                app.grid.half_page_up()
            case "H":
                app.grid.go_to_visible_top()
            case "M":
                app.grid.go_to_visible_middle()
            case "L":
                app.grid.go_to_visible_bottom()
            case "ctrl+home":
                app.grid.move_to_first_cell()
            case "ctrl+end":
                app.grid.move_to_last_cell()

            # ---- Mode entry ------------------------------------------------
            case "=":
                app._enter_insert("right")
                app._insert_buffer = "="
                app._insert_cursor = 1
            case "\\":
                app._enter_insert("right")
            case "<":
                app._enter_insert("left")
            case ">":
                app._enter_insert("right")
            case "e":
                app.edit_handler.enter(at_end=True)
            case "E":
                app.edit_handler.enter(at_end=False)
            case "C":
                self._clear_cell()
                app._enter_insert("right")
            case "v":
                app.grid.start_visual(Mode.VISUAL)
                app.mode = Mode.VISUAL
            case "V":
                app.grid.start_visual(Mode.VISUAL_LINE)
                app.mode = Mode.VISUAL_LINE
            case "ctrl+v":
                app.grid.start_visual(Mode.VISUAL_BLOCK)
                app.mode = Mode.VISUAL_BLOCK
            case "A":
                cell = app.workbook.active_sheet.get_cell(app.cursor_row, app.cursor_col)
                if cell and cell.locked:
                    app.status_bar.show_message("Cell is locked — use 'zL' to unlock")
                else:
                    content = cell.formula or (
                        str(cell.value) if cell and cell.value is not None else ""
                    )
                    app._insert_buffer = content
                    app._insert_cursor = len(app._insert_buffer)
                    app._insert_align = "right"
                    app.mode = Mode.INSERT
            case "I":
                cell = app.workbook.active_sheet.get_cell(app.cursor_row, app.cursor_col)
                if cell and cell.locked:
                    app.status_bar.show_message("Cell is locked — use 'zL' to unlock")
                else:
                    content = cell.formula or (
                        str(cell.value) if cell and cell.value is not None else ""
                    )
                    app._insert_buffer = content
                    app._insert_cursor = 1 if content.startswith("=") else 0
                    app._insert_align = "left"
                    app.mode = Mode.INSERT
            case "S":
                self._clear_cell()
                app._enter_insert("left")
            case ":":
                app._enter_command_mode()

            # ---- Cell editing ----------------------------------------------
            case "x":
                self._clear_cell()
            case "X":
                self._clear_cell()
                app.grid.move_by(0, -1)
            case "D":
                self._delete_to_row_end()
            case "p":
                self._paste_relative()
            case "P":
                self._paste_absolute()

            # ---- Increment / decrement cell value --------------------------
            case "ctrl+a":
                self._increment_cell(1)
                app._last_action = ("incr", 1)
            case "ctrl+x":
                self._increment_cell(-1)
                app._last_action = ("incr", -1)

            # ---- Column resize ---------------------------------------------
            case "+":
                col = app.cursor_col
                sheet = app.workbook.active_sheet
                sheet.set_col_width(col, sheet.get_col_width(col) + count)
                app.grid.refresh_grid()
            case "-":
                col = app.cursor_col
                sheet = app.workbook.active_sheet
                sheet.set_col_width(col, sheet.get_col_width(col) - count)
                app.grid.refresh_grid()
            case "_":
                app.workbook.active_sheet.auto_fit_col(app.cursor_col)
                app.grid.refresh_grid()

            # ---- Undo/redo -------------------------------------------------
            case "u":
                if app.undo_stack.undo():
                    app.workbook.modified = True
                    app.grid.refresh_grid()
                    app.status_bar.show_message("Undo")
                else:
                    app.status_bar.show_message("Nothing to undo")
            case "ctrl+r":
                if app.undo_stack.redo():
                    app.workbook.modified = True
                    app.grid.refresh_grid()
                    app.status_bar.show_message("Redo")
                else:
                    app.status_bar.show_message("Nothing to redo")
            case "U":
                # Restore current cell to the value it had before the most recent edit
                r, c = app.cursor_row, app.cursor_col
                cell = app.workbook.active_sheet.get_cell(r, c)
                if cell and cell.history:
                    _, prev_val = cell.history[-1]
                    from vimsheet.model.undo import SetCellCommand

                    cmd = SetCellCommand(app.workbook.active_sheet, r, c, prev_val)
                    app.undo_stack.push(cmd)
                    app.workbook.modified = True
                    app.grid.refresh_grid()
                    app.status_bar.show_message(f"Restored cell to: {prev_val!r}")
                else:
                    app.status_bar.show_message("No history for this cell")

            # ---- Replace cell ------------------------------------------------
            case "r":
                self._clear_cell()
                app._enter_insert("right")

            # ---- Search ----------------------------------------------------
            case "/":
                app._enter_search_mode("/")
            case "?":
                app._enter_search_mode("?")
            case "n":
                if app._search_state is not None:
                    app._cmd_find_next()
                else:
                    app.status_bar.show_message("n — no active search pattern")
            case "N":
                if app._search_state is not None:
                    app._cmd_find_prev()
                else:
                    app.status_bar.show_message("N — no active search pattern")
            case "*":
                cell = app.workbook.active_sheet.get_cell(app.cursor_row, app.cursor_col)
                if cell and cell.display:
                    state = SearchState(pattern=cell.display, whole_cell=True)
                    searcher = Searcher(app.workbook.active_sheet)
                    matches = searcher.find_all(state)
                    state.matches = matches
                    app._search_state = state
                    if matches:
                        nxt = searcher.find_next(state, app.cursor)
                        state.current_match = nxt
                        idx = matches.index(nxt) + 1
                        app.grid.move_cursor(*nxt)
                        app.status_bar.show_message(f"/^{cell.display}$  [{idx}/{len(matches)}]")
                    else:
                        app.status_bar.show_message(f"Pattern not found: {cell.display!r}")
                    app.grid.set_search_state(matches, state.current_match, pattern=cell.display)
                else:
                    app.status_bar.show_message("* — empty cell")
            case "#":
                cell = app.workbook.active_sheet.get_cell(app.cursor_row, app.cursor_col)
                if cell and cell.display:
                    state = SearchState(pattern=cell.display, whole_cell=True)
                    searcher = Searcher(app.workbook.active_sheet)
                    matches = searcher.find_all(state)
                    state.matches = matches
                    app._search_state = state
                    if matches:
                        prv = searcher.find_prev(state, app.cursor)
                        state.current_match = prv
                        idx = matches.index(prv) + 1
                        app.grid.move_cursor(*prv)
                        app.status_bar.show_message(f"?^{cell.display}$  [{idx}/{len(matches)}]")
                    else:
                        app.status_bar.show_message(f"Pattern not found: {cell.display!r}")
                    app.grid.set_search_state(matches, state.current_match, pattern=cell.display)
                else:
                    app.status_bar.show_message("# — empty cell")

            # ---- Dot-repeat ------------------------------------------------
            case ".":
                app._repeat_last_action()

            # ---- Misc ------------------------------------------------------
            case "ctrl+g":
                app._show_file_info()
            case "ctrl+l":
                app.refresh()
            case "ctrl+e":
                sy = int(app.grid.scroll_offset.y)
                app.grid.scroll_to(y=sy + 1, animate=False)
            case "ctrl+y":
                sy = int(app.grid.scroll_offset.y)
                app.grid.scroll_to(y=max(0, sy - 1), animate=False)
            case "f1":
                app._dispatch_command("help")
            case "escape":
                app._key_buffer = ""
                app._pending_register = ""
                app.status_bar.set_persistent_message("")
                app._search_state = None
                app.grid.set_search_state([], None)

        self._end_key()

    def _end_key(self) -> None:
        app = self._app
        app._sync_formula_bar()
        app._sync_status_bar()

    # -----------------------------------------------------------------------
    # Operations (helpers that create Commands)
    # -----------------------------------------------------------------------

    def _check_lock(self) -> bool:
        """Return True if the current cell is locked (shows message, caller should skip)."""
        app = self._app
        cell = app.workbook.active_sheet.get_cell(app.cursor_row, app.cursor_col)
        if cell is not None and cell.locked:
            app.status_bar.show_message("Cell is locked — use 'zL' to unlock")
            return True
        return False

    def _clear_cell(self) -> None:
        if self._check_lock():
            return
        from vimsheet.model.undo import ClearCellCommand

        app = self._app
        r, c = app.cursor_row, app.cursor_col
        reg = app._pending_register
        cell = app.workbook.active_sheet.get_cell(r, c)
        entry = RegisterEntry(
            value=cell.value if cell else None,
            formula=cell.formula if cell else None,
            src_row=r,
            src_col=c,
            fmt=cell.fmt.copy() if cell else None,
            locked=cell.locked if cell else False,
            comment=cell.comment if cell else None,
        )
        if reg:
            app._registers[reg] = entry
            app.status_bar.show_message(f'Deleted → "{reg}')
        else:
            app._default_register = entry
        app._pending_register = ""
        cmd = ClearCellCommand(app.workbook.active_sheet, r, c)
        app.undo_stack.push(cmd)
        app.workbook.modified = True
        app.grid.refresh_grid()
        app._sync_formula_bar()
        app._last_action = ("clear_cell",)

    def _delete_to_row_end(self) -> None:
        if self._check_lock():
            return
        from vimsheet.model.undo import DeleteRangeCommand

        app = self._app
        sheet = app.workbook.active_sheet
        r, c = app.cursor_row, app.cursor_col
        if sheet.max_col >= c:
            rng = CellRange(r, c, r, sheet.max_col)
            # Yank to register before deleting
            range_data: list[list[tuple[Any, str | None, Any]]] = []
            for col in range(c, sheet.max_col + 1):
                cell = sheet.get_cell(r, col)
                range_data.append(
                    [
                        (
                            cell.value if cell else None,
                            cell.formula if cell else None,
                            cell.fmt.copy() if cell else None,
                        )
                    ]
                )
            app._default_register = RegisterEntry(
                value=None,
                formula=None,
                src_row=r,
                src_col=c,
                is_range=True,
                range_data=[range_data],
                range_src_top=r,
                range_src_left=c,
            )
            cmd = DeleteRangeCommand(sheet, rng)
            app.undo_stack.push(cmd)
            app.workbook.modified = True
            app.grid.refresh_grid()

    def _yank_cell(self, formula: bool = True) -> None:
        app = self._app
        r, c = app.cursor_row, app.cursor_col
        cell = app.workbook.active_sheet.get_cell(r, c)
        cell_value = cell.value if cell else None
        cell_formula = cell.formula if (cell and cell.formula and formula) else None

        entry = RegisterEntry(
            value=cell_value,
            formula=cell_formula,
            src_row=r,
            src_col=c,
            fmt=cell.fmt.copy() if cell else None,
            locked=cell.locked if cell else False,
            comment=cell.comment if cell else None,
        )
        reg = app._pending_register
        if reg == "+":
            self._to_clipboard([[cell_value]])
        elif reg:
            app._registers[reg] = entry
            app.status_bar.show_message(f'Yanked → "{reg}')
        else:
            app._default_register = entry
            note = "formula" if cell_formula else "value"
            app.status_bar.show_message(f"Yanked {note}")
        app._pending_register = ""

    def _cut_row(self) -> None:
        """dd — yank current row and delete it."""
        from vimsheet.model.undo import DeleteRowCommand

        app = self._app
        r = app.cursor_row
        sheet = app.workbook.active_sheet
        max_c = sheet.max_col
        range_data: list[list[tuple[Any, str | None, Any]]] = [[]]
        for c in range(max_c + 1):
            cell = sheet.get_cell(r, c)
            v = cell.value if cell else None
            f = cell.formula if cell else None
            fmt = cell.fmt.copy() if cell else None
            range_data[0].append((v, f, fmt))
        app._default_register = RegisterEntry(
            value=None,
            formula=None,
            src_row=r,
            src_col=0,
            is_range=True,
            range_data=range_data,
            range_src_top=r,
            range_src_left=0,
        )
        cmd = DeleteRowCommand(sheet, r)
        app.undo_stack.push(cmd)
        app.workbook.modified = True
        app.grid.refresh_grid()
        app.status_bar.show_message("Row cut (dd)")
        app._last_action = ("delete_row", r)

    def _yank_row(self) -> None:
        """yr — yank all cells in current row (into default register)."""
        app = self._app
        r = app.cursor_row
        sheet = app.workbook.active_sheet
        max_c = sheet.max_col
        range_data: list[list[tuple[Any, str | None, Any]]] = [[]]
        for c in range(max_c + 1):
            cell = sheet.get_cell(r, c)
            v = cell.value if cell else None
            f = cell.formula if cell else None
            fmt = cell.fmt.copy() if cell else None
            range_data[0].append((v, f, fmt))
        app._default_register = RegisterEntry(
            value=None,
            formula=None,
            src_row=r,
            src_col=0,
            is_range=True,
            range_data=range_data,
            range_src_top=r,
            range_src_left=0,
        )
        app.status_bar.show_message("Yanked row (yr)")

    def _yank_col(self) -> None:
        """yc — yank all cells in current column (into default register)."""
        app = self._app
        c = app.cursor_col
        sheet = app.workbook.active_sheet
        range_data: list[list[tuple[Any, str | None, Any]]] = []
        for r in range(sheet.max_row + 1):
            cell = sheet.get_cell(r, c)
            v = cell.value if cell else None
            f = cell.formula if cell else None
            fmt = cell.fmt.copy() if cell else None
            range_data.append([(v, f, fmt)])
        app._default_register = RegisterEntry(
            value=None,
            formula=None,
            src_row=0,
            src_col=c,
            is_range=True,
            range_data=range_data,
            range_src_top=0,
            range_src_left=c,
        )
        app.status_bar.show_message("Yanked column (yc)")

    def _increment_cell(self, delta: int) -> None:
        """Add *delta* to the numeric value of the current cell."""
        if self._check_lock():
            return
        app = self._app
        self._increment_cells([(app.cursor_row, app.cursor_col)], delta)
        app._sync_formula_bar()

    def _increment_cells(self, cells: list[tuple[int, int]], delta: int) -> None:
        """Add *delta* to every numeric cell in *cells*, silently skipping non-numeric ones."""
        from vimsheet.model.undo import CompositeCommand, SetCellCommand

        app = self._app
        sheet = app.workbook.active_sheet
        cmds = []
        for r, c in cells:
            cell = sheet.get_cell(r, c)
            current = cell.value if cell else None
            try:
                num = float(current)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                continue
            new_val: int | float = num + delta
            if new_val == int(new_val):
                new_val = int(new_val)
            cmds.append(SetCellCommand(sheet, r, c, new_val))
        if cmds:
            app.undo_stack.push(CompositeCommand(cmds))  # type: ignore[arg-type]
            app.workbook.modified = True
            app.grid.refresh_grid()

    def _paste_relative(self) -> None:
        """p — paste at cursor with formula adjustment."""
        if self._check_lock():
            return
        from vimsheet.formula.adjuster import adjust_formula
        from vimsheet.model.undo import PasteCommand, YankedCell

        app = self._app
        reg = app._pending_register
        app._pending_register = ""

        if reg == "+":
            data = self._from_clipboard()
            if not data:
                return
            r, c = app.cursor_row, app.cursor_col
            cmd = PasteCommand(app.workbook.active_sheet, r, c, data)
            app.undo_stack.push(cmd)
            app.workbook.modified = True
            app.grid.refresh_grid()
            app._last_action = ("paste", False, data)
            return

        entry: RegisterEntry | None = app._registers.get(reg) if reg else app._default_register
        if entry is None:
            return

        dst_row, dst_col = app.cursor_row, app.cursor_col

        if entry.is_range:
            data: list[list[Any]] = []
            for i, row_data in enumerate(entry.range_data):
                row: list[Any] = []
                for j, cell_data in enumerate(row_data):
                    value, formula, fmt = cell_data if len(cell_data) >= 3 else (*cell_data, None)
                    src_r = entry.range_src_top + i
                    src_c = entry.range_src_left + j
                    adjusted = adjust_formula(formula, dst_row + i, dst_col + j, src_r, src_c)
                    if formula is not None and adjusted is not None:
                        row.append(YankedCell(value=value, formula=adjusted, fmt=fmt))
                    else:
                        row.append(YankedCell(value=value, formula=None, fmt=fmt))
                data.append(row)
            cmd = PasteCommand(app.workbook.active_sheet, dst_row, dst_col, data)
            app.undo_stack.push(cmd)
            app.workbook.modified = True
            app.grid.refresh_grid()
            app._last_action = ("paste", False, data)
        else:
            adjusted_formula = adjust_formula(
                entry.formula, dst_row, dst_col, entry.src_row, entry.src_col
            )
            if entry.formula is not None and adjusted_formula is not None:
                paste_entry: Any = YankedCell(
                    value=entry.value,
                    formula=adjusted_formula,
                    fmt=entry.fmt,
                )
            else:
                paste_entry = YankedCell(
                    value=entry.value,
                    formula=None,
                    fmt=entry.fmt,
                )
            data = [[paste_entry]]
            cmd = PasteCommand(app.workbook.active_sheet, dst_row, dst_col, data)
            app.undo_stack.push(cmd)
            app.workbook.modified = True
            app.grid.refresh_grid()
            app._last_action = ("paste", False, data)

    def _paste_absolute(self) -> None:
        """P — paste at cursor without formula adjustment."""
        if self._check_lock():
            return
        from vimsheet.model.undo import PasteCommand, YankedCell

        app = self._app
        reg = app._pending_register
        app._pending_register = ""

        if reg == "+":
            data = self._from_clipboard()
            if not data:
                return
            r, c = app.cursor_row, app.cursor_col
            cmd = PasteCommand(app.workbook.active_sheet, r, c, data)
            app.undo_stack.push(cmd)
            app.workbook.modified = True
            app.grid.refresh_grid()
            app._last_action = ("paste", False, data)
            return

        entry: RegisterEntry | None = app._registers.get(reg) if reg else app._default_register
        if entry is None:
            return
        if not entry.is_range:
            self._paste_single_cell_absolute(entry)
            return

        dst_row, dst_col = app.cursor_row, app.cursor_col
        data: list[list[Any]] = []
        for row_data in entry.range_data:
            row: list[Any] = []
            for cell_data in row_data:
                value, _formula, fmt = cell_data if len(cell_data) >= 3 else (*cell_data, None)
                row.append(YankedCell(value=value, formula=None, fmt=fmt))
            data.append(row)
        cmd = PasteCommand(app.workbook.active_sheet, dst_row, dst_col, data)
        app.undo_stack.push(cmd)
        app.workbook.modified = True
        app.grid.refresh_grid()
        app._last_action = ("paste", False, data)

    def _paste_single_cell_absolute(self, entry: RegisterEntry) -> None:
        from vimsheet.model.undo import PasteCommand, YankedCell

        app = self._app
        dst_row, dst_col = app.cursor_row, app.cursor_col
        data = [[YankedCell(value=entry.value, formula=None, fmt=entry.fmt)]]
        cmd = PasteCommand(app.workbook.active_sheet, dst_row, dst_col, data)
        app.undo_stack.push(cmd)
        app.workbook.modified = True
        app.grid.refresh_grid()
        app._last_action = ("paste", False, data)

    def _toggle_fmt(self, attr: str) -> None:
        from vimsheet.model.undo import FormatCommand

        app = self._app
        r, c = app.cursor_row, app.cursor_col
        cell = app.workbook.active_sheet.get_cell(r, c)
        new_val = not getattr(cell.fmt, attr) if cell else True
        cmd = FormatCommand(app.workbook.active_sheet, r, c, **{attr: new_val})
        app.undo_stack.push(cmd)
        app.grid.refresh_grid()

    def _set_align(self, align: str) -> None:
        from vimsheet.model.undo import FormatCommand

        app = self._app
        r, c = app.cursor_row, app.cursor_col
        cmd = FormatCommand(app.workbook.active_sheet, r, c, align=align)
        app.undo_stack.push(cmd)
        app.grid.refresh_grid()

    def _lock_cell(self, locked: bool) -> None:
        from vimsheet.model.undo import LockCommand

        app = self._app
        r, c = app.cursor_row, app.cursor_col
        cmd = LockCommand(app.workbook.active_sheet, r, c, locked=locked)
        app.undo_stack.push(cmd)
        app.status_bar.show_message("Cell locked" if locked else "Cell unlocked")
        app._sync_formula_bar()

    def _valueize_cell(self) -> None:
        if self._check_lock():
            return
        app = self._app
        cell = app.workbook.active_sheet.get_cell(app.cursor_row, app.cursor_col)
        if cell and cell.formula:
            cell.formula = None
            app.grid.refresh_grid()

    def _insert_row_above(self) -> None:
        from vimsheet.model.undo import InsertRowCommand

        app = self._app
        cmd = InsertRowCommand(app.workbook.active_sheet, app.cursor_row)
        app.undo_stack.push(cmd)
        app.workbook.modified = True
        app.grid.refresh_grid()

    def _insert_row_below(self) -> None:
        from vimsheet.model.undo import InsertRowCommand

        app = self._app
        cmd = InsertRowCommand(app.workbook.active_sheet, app.cursor_row + 1)
        app.undo_stack.push(cmd)
        app.workbook.modified = True
        app.grid.refresh_grid()

    def _insert_col_left(self) -> None:
        from vimsheet.model.undo import InsertColCommand

        app = self._app
        cmd = InsertColCommand(app.workbook.active_sheet, app.cursor_col)
        app.undo_stack.push(cmd)
        app.workbook.modified = True
        app.grid.refresh_grid()

    def _insert_col_right(self) -> None:
        from vimsheet.model.undo import InsertColCommand

        app = self._app
        cmd = InsertColCommand(app.workbook.active_sheet, app.cursor_col + 1)
        app.undo_stack.push(cmd)
        app.workbook.modified = True
        app.grid.refresh_grid()

    def _delete_row(self) -> None:
        if self._check_lock():
            return
        from vimsheet.model.undo import DeleteRowCommand

        app = self._app
        r = app.cursor_row
        sheet = app.workbook.active_sheet
        max_c = sheet.max_col
        range_data: list[list[tuple[Any, str | None, Any]]] = [[]]
        for c in range(max_c + 1):
            cell = sheet.get_cell(r, c)
            v = cell.value if cell else None
            f = cell.formula if cell else None
            fmt = cell.fmt.copy() if cell else None
            range_data[0].append((v, f, fmt))
        app._default_register = RegisterEntry(
            value=None,
            formula=None,
            src_row=r,
            src_col=0,
            is_range=True,
            range_data=range_data,
            range_src_top=r,
            range_src_left=0,
        )
        cmd = DeleteRowCommand(sheet, r)
        app.undo_stack.push(cmd)
        app.workbook.modified = True
        app.grid.refresh_grid()
        app._last_action = ("delete_row",)

    def _delete_col(self) -> None:
        if self._check_lock():
            return
        from vimsheet.model.undo import DeleteColCommand

        app = self._app
        c = app.cursor_col
        sheet = app.workbook.active_sheet
        range_data: list[list[tuple[Any, str | None, Any]]] = []
        for r in range(sheet.max_row + 1):
            cell = sheet.get_cell(r, c)
            v = cell.value if cell else None
            f = cell.formula if cell else None
            fmt = cell.fmt.copy() if cell else None
            range_data.append([(v, f, fmt)])
        app._default_register = RegisterEntry(
            value=None,
            formula=None,
            src_row=0,
            src_col=c,
            is_range=True,
            range_data=range_data,
            range_src_top=0,
            range_src_left=c,
        )
        cmd = DeleteColCommand(sheet, c)
        app.undo_stack.push(cmd)
        app.workbook.modified = True
        app.grid.refresh_grid()
        app._last_action = ("delete_col",)

    def _hide_row(self) -> None:
        app = self._app
        app.workbook.active_sheet.hidden_rows.add(app.cursor_row)
        app.grid.refresh_grid()

    def _hide_col(self) -> None:
        app = self._app
        app.workbook.active_sheet.hidden_cols.add(app.cursor_col)
        app.grid.refresh_grid()

    def _show_row(self) -> None:
        app = self._app
        app.workbook.active_sheet.hidden_rows.discard(app.cursor_row)
        app.grid.refresh_grid()

    def _show_col(self) -> None:
        app = self._app
        app.workbook.active_sheet.hidden_cols.discard(app.cursor_col)
        app.grid.refresh_grid()

    def _shift_cell(self, dr: int, dc: int) -> None:
        """Move the current cell in direction (dr, dc), swapping with destination."""
        if self._check_lock():
            return
        from vimsheet.model.undo import CompositeCommand, SetCellCommand

        app = self._app
        r, c = app.cursor_row, app.cursor_col
        dst_r, dst_c = r + dr, c + dc
        if dst_r < 0 or dst_c < 0:
            return

        sheet = app.workbook.active_sheet
        src_cell = sheet.get_cell(r, c)
        src_val = src_cell.value if src_cell else None
        src_fml = src_cell.formula if src_cell else None

        cmds = []
        # Move source cell to destination
        if src_val is not None or src_fml is not None:
            cmds.append(SetCellCommand(sheet, dst_r, dst_c, src_val, new_formula=src_fml))
        # Clear source cell
        cmds.append(SetCellCommand(sheet, r, c, None))

        composite = CompositeCommand(cmds)
        app.undo_stack.push(composite)
        app.workbook.modified = True
        app.grid.move_cursor(dst_r, dst_c)
        app.grid.refresh_grid()

    def _goto_address(self, addr: str) -> None:
        from vimsheet.model.range import a1_to_rowcol

        app = self._app
        try:
            r, c = a1_to_rowcol(addr.strip().upper())
            app.grid.move_cursor(r, c)
        except ValueError:
            app.status_bar.show_message(f"Invalid address: {addr!r}")

    def _to_clipboard(self, data: list[list[Any]]) -> None:
        """Write a 2-D list of values to the system clipboard as TSV."""
        try:
            import subprocess

            tsv = "\n".join("\t".join(str(v) if v is not None else "" for v in row) for row in data)
            # Try xclip / xsel / pbcopy
            for cmd in (
                ["xclip", "-selection", "clipboard"],
                ["xsel", "--input", "--clipboard"],
                ["pbcopy"],
            ):
                try:
                    subprocess.run(cmd, input=tsv.encode(), check=True, timeout=2)
                    self._app.status_bar.show_message("Yanked to clipboard")
                    return
                except (FileNotFoundError, subprocess.SubprocessError):
                    continue
            self._app.status_bar.show_message("Clipboard tool not found (xclip/xsel/pbcopy)")
        except Exception:
            self._app.status_bar.show_message("Clipboard copy failed")

    def _from_clipboard(self) -> list[list[Any]]:
        """Read TSV from system clipboard."""
        try:
            import subprocess

            for cmd in (
                ["xclip", "-selection", "clipboard", "-o"],
                ["xsel", "--output", "--clipboard"],
                ["pbpaste"],
            ):
                try:
                    result = subprocess.run(cmd, capture_output=True, check=True, timeout=2)
                    tsv = result.stdout.decode(errors="replace")
                    from vimsheet.io.csv_adapter import _coerce as csv_coerce

                    return [
                        [csv_coerce(cell) for cell in row.split("\t")] for row in tsv.splitlines()
                    ]
                except (FileNotFoundError, subprocess.SubprocessError):
                    continue
        except Exception:
            pass
        return []
