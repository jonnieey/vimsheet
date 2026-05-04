"""Normal mode key handler — all vim-like Normal mode bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from vimsheet.controller.mode import Mode
from vimsheet.model.range import CellRange

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
                app.status_bar.set_persistent_message("")
                return
            case s if s.endswith("ctrl+x") and s[: -len("ctrl+x")].isdigit():
                self._increment_cell(-int(s[: -len("ctrl+x")]))
                app._key_buffer = ""
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
                app.status_bar.show_message("go: ")
                return
            case s if s.startswith("go") and len(s) > 2:
                if key == "escape":
                    app._key_buffer = ""
                    app.status_bar.show_message("")
                elif key in ("enter", "\r", "\n"):
                    addr = app._key_buffer[2:]
                    self._goto_address(addr)
                    app._key_buffer = ""
                elif key == "backspace":
                    app._key_buffer = buf[:-1] if len(buf) > 2 else "go"
                    app.status_bar.show_message(f"go: {app._key_buffer[2:]}")
                else:
                    app._key_buffer = s
                    app.status_bar.show_message(f"go: {app._key_buffer[2:]}")
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

            # ge — open cell in $EDITOR / $VISUAL
            case "ge":
                app._key_buffer = ""
                app.open_in_external_editor()
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
                    try:
                        app._replay_keys(keys)
                    finally:
                        app._replaying_macros.discard(actual_reg)
                else:
                    app.status_bar.show_message(f"No macro in register '{reg}'")
                app._key_buffer = ""
                return

            # Named register: "{a-z/+} prefix for yank/paste
            case s if len(s) == 2 and s[0] == '"' and (s[1].isalpha() or s[1] == "+"):
                app._pending_register = s[1]
                app._key_buffer = ""
                # Next key is the operation — let it fall through
                return

            # System clipboard prefix "+
            case '"+':
                app._pending_register = "+"
                app._key_buffer = ""
                return

            # Format chords
            case "fb":
                self._toggle_fmt("bold")
                app._key_buffer = ""
                return
            case "fi":
                self._toggle_fmt("italic")
                app._key_buffer = ""
                return
            case "fu":
                self._toggle_fmt("underline")
                app._key_buffer = ""
                return
            case "fl":
                self._set_align("left")
                app._key_buffer = ""
                return
            case "fr":
                self._set_align("right")
                app._key_buffer = ""
                return
            case "fc":
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
            case "hr":
                self._hide_row()
                app._key_buffer = ""
                return
            case "hc":
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

            # Cell-state chords
            case "rl":
                self._lock_cell(True)
                app._key_buffer = ""
                return
            case "ru":
                self._lock_cell(False)
                app._key_buffer = ""
                return
            case "rv":
                self._valueize_cell()
                app._key_buffer = ""
                return

            # r{char} — replace char under cursor with next typed char
            case s if len(s) == 2 and s[0] == "r" and s[1] not in ("l", "u", "v"):
                self._replace_char(s[1])
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

            # ZZ / ZQ
            case "ZZ":
                app._save_and_quit()
                app._key_buffer = ""
                return
            case "ZQ":
                app.exit()
                return

            # Shift cell
            case "sj":
                self._shift_cell(1, 0)
                app._key_buffer = ""
                return
            case "sk":
                self._shift_cell(-1, 0)
                app._key_buffer = ""
                return
            case "sl":
                self._shift_cell(0, 1)
                app._key_buffer = ""
                return
            case "sh":
                self._shift_cell(0, -1)
                app._key_buffer = ""
                return

            # Pending prefixes (no standalone action for these)
            case (
                "g"
                | "f"
                | "i"
                | "d"
                | "y"
                | "Y"
                | "r"
                | "z"
                | "Z"
                | "m"
                | "'"
                | "@"
                | '"'
                | "q"
                | "s"
            ):
                app._key_buffer = buf
                return

        # Unrecognised chord → single-key dispatch
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
            case "=" | "\\":
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
                self._paste(after=True)
            case "P":
                if app._yanked_formula and not app._pending_register:
                    self._paste_formula(app._yanked_formula)
                else:
                    self._paste(after=False)

            # ---- Increment / decrement cell value --------------------------
            case "ctrl+a":
                self._increment_cell(1)
            case "ctrl+x":
                self._increment_cell(-1)

            # ---- Column resize ---------------------------------------------
            case "+":
                col = app.cursor_col
                sheet = app.workbook.active_sheet
                sheet.set_col_width(col, sheet.get_col_width(col) + 1)
                app.grid.refresh_grid()
            case "-":
                col = app.cursor_col
                sheet = app.workbook.active_sheet
                sheet.set_col_width(col, sheet.get_col_width(col) - 1)
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

            # ---- Search ----------------------------------------------------
            case "/":
                app._enter_command_mode(prefix="/")
            case "?":
                app._enter_command_mode(prefix="?")
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
                # Search forward for the current cell's display value
                cell = app.workbook.active_sheet.get_cell(app.cursor_row, app.cursor_col)
                if cell and cell.display:
                    app._cmd_find(cell.display)
                    app._cmd_find_next()
                else:
                    app.status_bar.show_message("* — empty cell")
            case "#":
                # Search backward for the current cell's display value
                cell = app.workbook.active_sheet.get_cell(app.cursor_row, app.cursor_col)
                if cell and cell.display:
                    app._cmd_find(cell.display)
                    app._cmd_find_prev()
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
            case "f1":
                app._dispatch_command("help")
            case "escape":
                app._key_buffer = ""
                app._pending_register = ""
                app.status_bar.set_persistent_message("")

        self._end_key()

    def _end_key(self) -> None:
        app = self._app
        app._sync_formula_bar()
        app._sync_status_bar()

    # -----------------------------------------------------------------------
    # Operations (helpers that create Commands)
    # -----------------------------------------------------------------------

    def _clear_cell(self) -> None:
        from vimsheet.model.undo import ClearCellCommand

        app = self._app
        r, c = app.cursor_row, app.cursor_col
        cmd = ClearCellCommand(app.workbook.active_sheet, r, c)
        app.undo_stack.push(cmd)
        app.workbook.modified = True
        app.grid.refresh_grid()
        app._sync_formula_bar()
        app._last_action = ("clear_cell",)

    def _delete_to_row_end(self) -> None:
        from vimsheet.model.undo import DeleteRangeCommand

        app = self._app
        sheet = app.workbook.active_sheet
        r, c = app.cursor_row, app.cursor_col
        if sheet.max_col >= c:
            rng = CellRange(r, c, r, sheet.max_col)
            cmd = DeleteRangeCommand(sheet, rng)
            app.undo_stack.push(cmd)
            app.workbook.modified = True
            app.grid.refresh_grid()

    def _yank_cell(self, formula: bool = True) -> None:
        from vimsheet.model.undo import YankedCell

        app = self._app
        cell = app.workbook.active_sheet.get_cell(app.cursor_row, app.cursor_col)
        if cell and cell.formula and formula:
            entry: Any = YankedCell(value=cell.value, formula=cell.formula)
            note = "formula"
        else:
            entry = cell.value if cell else None
            note = "value"
        data = [[entry]]
        reg = app._pending_register
        if reg == "+":
            self._to_clipboard([[cell.value if cell else None]])
        elif reg:
            app._registers[reg] = data
            app.status_bar.show_message(f'Yanked {note} → "{reg}')
        else:
            app._default_register = data
            app.status_bar.show_message(f"Yanked {note}")
        app._pending_register = ""

    def _cut_row(self) -> None:
        """dd — yank current row and delete it."""
        from vimsheet.model.undo import DeleteRowCommand

        app = self._app
        r = app.cursor_row
        sheet = app.workbook.active_sheet
        # Snapshot for register
        max_c = sheet.max_col
        row_data = [[sheet.get_cell(r, c) and sheet.get_cell(r, c).value for c in range(max_c + 1)]]
        app._default_register = row_data
        cmd = DeleteRowCommand(sheet, r)
        app.undo_stack.push(cmd)
        app.workbook.modified = True
        app.grid.refresh_grid()
        app.status_bar.show_message("Row cut (dd)")
        app._last_action = ("delete_row", r)

    def _increment_cell(self, delta: int) -> None:
        """Add *delta* to the numeric value of the current cell."""
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

    def _paste_formula(self, formula: str) -> None:
        """Paste a formula string into the current cell (from P after range-func yank)."""
        from vimsheet.model.undo import SetCellCommand

        app = self._app
        r, c = app.cursor_row, app.cursor_col
        cmd = SetCellCommand(app.workbook.active_sheet, r, c, formula, new_formula=formula)
        app.undo_stack.push(cmd)
        app.workbook.modified = True
        app.grid.refresh_grid()
        app._yanked_formula = None

    def _paste(self, after: bool = True) -> None:
        from vimsheet.model.undo import PasteCommand

        app = self._app
        reg = app._pending_register
        if reg == "+":
            data = self._from_clipboard()
        elif reg and reg in app._registers:
            data = app._registers[reg]
        else:
            data = app._default_register
        app._pending_register = ""
        if not data:
            return
        dr = 1 if after else 0
        r, c = app.cursor_row + dr, app.cursor_col
        cmd = PasteCommand(app.workbook.active_sheet, r, c, data)
        app.undo_stack.push(cmd)
        app.workbook.modified = True
        app.grid.refresh_grid()
        app._last_action = ("paste", after, data)

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
        app = self._app
        cell = app.workbook.active_sheet.get_cell(app.cursor_row, app.cursor_col)
        if cell and cell.formula:
            cell.formula = None
            app.grid.refresh_grid()

    def _replace_char(self, char: str) -> None:
        """r{char} — replace single character under cursor in cell content."""
        from vimsheet.model.undo import SetCellCommand

        app = self._app
        r, c = app.cursor_row, app.cursor_col
        cell = app.workbook.active_sheet.get_cell(r, c)
        old = (cell.formula or str(cell.value) if cell else "") or ""
        # Replace first char
        new_val = char + old[1:] if old else char
        cmd = SetCellCommand(app.workbook.active_sheet, r, c, new_val)
        app.undo_stack.push(cmd)
        app.workbook.modified = True
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
        from vimsheet.model.undo import DeleteRowCommand

        app = self._app
        cmd = DeleteRowCommand(app.workbook.active_sheet, app.cursor_row)
        app.undo_stack.push(cmd)
        app.workbook.modified = True
        app.grid.refresh_grid()

    def _delete_col(self) -> None:
        from vimsheet.model.undo import DeleteColCommand

        app = self._app
        cmd = DeleteColCommand(app.workbook.active_sheet, app.cursor_col)
        app.undo_stack.push(cmd)
        app.workbook.modified = True
        app.grid.refresh_grid()

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
        """Move the current cell in direction (dr, dc), overwriting destination."""
        from vimsheet.model.range import CellRange
        from vimsheet.model.undo import ShiftCellsCommand

        app = self._app
        r, c = app.cursor_row, app.cursor_col
        dst_r, dst_c = r + dr, c + dc
        if dst_r < 0 or dst_c < 0:
            return
        src = CellRange(r, c, r, c)
        cmd = ShiftCellsCommand(app.workbook.active_sheet, src, dr, dc)
        app.undo_stack.push(cmd)
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
