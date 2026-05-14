"""Edit mode key handler — vi-style line editing of existing cell content."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from vimsheet.controller.mode import Mode

if TYPE_CHECKING:
    from vimsheet.app import VimSheetApp


class EditHandler:
    """Handles all key events while in Edit mode."""

    def __init__(self, app: VimSheetApp) -> None:
        self._app = app
        # Edit mode has a sub-mode: "normal" (vi motion) or "insert" (typing)
        self._sub: str = "normal"
        self._orig_value: str = ""  # content when edit mode was entered, for 'u' undo

    def enter(self, at_end: bool = True) -> None:
        """Switch app to Edit mode, loading current cell content."""
        app = self._app
        cell = app.workbook.active_sheet.get_cell(app.cursor_row, app.cursor_col)
        if cell is not None and cell.locked:
            app.status_bar.show_message("Cell is locked — use 'ru' to unlock")
            return
        app._edit_buffer = ""
        if cell is not None:
            app._edit_buffer = cell.formula or (str(cell.value) if cell.value is not None else "")
        self._orig_value = app._edit_buffer
        app._edit_cursor = len(app._edit_buffer) if at_end else 0
        self._sub = "normal"
        app.mode = Mode.EDIT
        app._sync_formula_bar()

    def handle(self, key: str) -> None:
        app = self._app
        app.macro_recorder.record_key(key)

        if self._sub == "insert":
            self._handle_insert_sub(key)
        else:
            self._handle_normal_sub(key)

        app._sync_formula_bar()
        app._sync_status_bar()
        app._sync_grid_preview()

    # -----------------------------------------------------------------------
    # Sub-mode: normal (vi motion within the line)
    # -----------------------------------------------------------------------

    def _handle_normal_sub(self, key: str) -> None:
        app = self._app
        buf, pos = app._edit_buffer, app._edit_cursor

        # Two-char chords in edit normal sub-mode
        chord = app._edit_chord + key
        app._edit_chord = ""

        match chord:
            case "dw":
                end = _word_end(buf, pos)
                app._edit_buffer = buf[:pos] + buf[end:]
                return
            case "d$" | "D":
                app._edit_buffer = buf[:pos]
                return
            case "d0":
                app._edit_buffer = buf[pos:]
                app._edit_cursor = 0
                return
            case "cw":
                end = _word_end(buf, pos)
                app._edit_buffer = buf[:pos] + buf[end:]
                self._sub = "insert"
                return
            case "c$" | "C":
                app._edit_buffer = buf[:pos]
                self._sub = "insert"
                return

        # Single-char or pending chord
        match key:
            case "escape" | "enter":
                self._commit()
            case "h" | "left":
                app._edit_cursor = max(0, pos - 1)
            case "l" | "right":
                app._edit_cursor = min(len(buf), pos + 1)
            case "w":
                app._edit_cursor = _word_forward(buf, pos)
            case "b":
                app._edit_cursor = _word_backward(buf, pos)
            case "e":
                app._edit_cursor = _word_end(buf, pos) - 1
            case "0":
                app._edit_cursor = 0
            case "$":
                app._edit_cursor = len(buf)
            case "i":
                self._sub = "insert"
            case "a":
                app._edit_cursor = min(len(buf), pos + 1)
                self._sub = "insert"
            case "A":
                app._edit_cursor = len(buf)
                self._sub = "insert"
            case "I":
                app._edit_cursor = 0
                self._sub = "insert"
            case "s":
                if pos < len(buf):
                    app._edit_buffer = buf[:pos] + buf[pos + 1 :]
                self._sub = "insert"
            case "S":
                app._edit_buffer = ""
                app._edit_cursor = 0
                self._sub = "insert"
            case "x":
                if pos < len(buf):
                    app._edit_buffer = buf[:pos] + buf[pos + 1 :]
            case "u":
                # Restore to value when edit mode was entered
                app._edit_buffer = self._orig_value
                app._edit_cursor = len(self._orig_value)
            case "d" | "c":
                # Start chord
                app._edit_chord = key
            case " ":
                app._edit_buffer = buf[:pos] + " " + buf[pos:]
                app._edit_cursor = pos + 1
            case _ if len(key) == 1 and key.isprintable():
                # r{char} — replace char under cursor
                if chord and chord[0] == "r":
                    if pos < len(buf):
                        app._edit_buffer = buf[:pos] + key + buf[pos + 1 :]
                    return
                # Otherwise buffer single char for chord detection
                app._edit_chord = key

    # -----------------------------------------------------------------------
    # Sub-mode: insert (typing)
    # -----------------------------------------------------------------------

    def _handle_insert_sub(self, key: str) -> None:
        app = self._app
        buf, pos = app._edit_buffer, app._edit_cursor

        match key:
            case "escape":
                self._sub = "normal"
                # clamp cursor to last char position (vim behaviour)
                app._edit_cursor = (
                    max(0, min(pos, len(app._edit_buffer) - 1)) if app._edit_buffer else 0
                )
            case "alt+enter":
                app._edit_buffer = buf[:pos] + "\n" + buf[pos:]
                app._edit_cursor = pos + 1
            case "enter":
                self._commit()
            case "backspace":
                if pos > 0:
                    app._edit_buffer = buf[: pos - 1] + buf[pos:]
                    app._edit_cursor = pos - 1
            case "delete":
                if pos < len(buf):
                    app._edit_buffer = buf[:pos] + buf[pos + 1 :]
            case "left":
                app._edit_cursor = max(0, pos - 1)
            case "right":
                app._edit_cursor = min(len(buf), pos + 1)
            case "home" | "ctrl+a":
                app._edit_cursor = 0
            case "end" | "ctrl+e":
                app._edit_cursor = len(buf)
            case "ctrl+w":
                i = pos - 1
                while i >= 0 and buf[i] == " ":
                    i -= 1
                while i >= 0 and buf[i] != " ":
                    i -= 1
                app._edit_buffer = buf[: i + 1] + buf[pos:]
                app._edit_cursor = i + 1
            case "ctrl+u":
                app._edit_buffer = ""
                app._edit_cursor = 0
            case _ if len(key) == 1 and key.isprintable():
                app._edit_buffer = buf[:pos] + key + buf[pos:]
                app._edit_cursor = pos + 1

    # -----------------------------------------------------------------------
    # Commit
    # -----------------------------------------------------------------------

    def _commit(self) -> None:
        app = self._app
        raw = app._edit_buffer
        sheet = app.workbook.active_sheet
        r, c = app.cursor_row, app.cursor_col

        # Cancel any FETCH running on this cell if it's being overwritten
        old = sheet.get_cell(r, c)
        if (
            old
            and old.formula
            and "FETCH" in old.formula.upper()
            and (not raw.startswith("=") or "FETCH" not in raw.upper())
        ):
            app.fetch_manager.cancel((sheet.name, r, c))

        from vimsheet.model.undo import SetCellCommand

        val: Any
        if raw.startswith("="):
            cmd = SetCellCommand(sheet, r, c, raw, new_formula=raw)
        else:
            try:
                val = int(raw) if "." not in raw else float(raw)
            except ValueError:
                val = raw
            valid, msg = sheet.validation.validate(r, c, val)
            if not valid:
                app.status_bar.show_message(f"Validation failed: {msg}")
                app.mode = Mode.NORMAL
                app._edit_buffer = ""
                app._edit_cursor = 0
                app._edit_chord = ""
                self._sub = "normal"
                app._sync_formula_bar()
                app._sync_grid_preview()
                return
            cmd = SetCellCommand(sheet, r, c, val)

        app.undo_stack.push(cmd)
        app.workbook.modified = True
        app.mode = Mode.NORMAL
        app._edit_buffer = ""
        app._edit_cursor = 0
        app._edit_chord = ""
        self._sub = "normal"
        app._sync_formula_bar()
        app._sync_status_bar()
        app._sync_grid_preview()
        app.grid.refresh_grid()


# ---------------------------------------------------------------------------
# Word-motion helpers (operate on the edit buffer string)
# ---------------------------------------------------------------------------


def _word_forward(s: str, pos: int) -> int:
    """Return position after next word boundary (vim 'w')."""
    n = len(s)
    if pos >= n:
        return n
    # skip current word chars
    while pos < n and (s[pos].isalnum() or s[pos] == "_"):
        pos += 1
    # skip spaces
    while pos < n and s[pos] == " ":
        pos += 1
    return pos


def _word_backward(s: str, pos: int) -> int:
    """Return position of previous word start (vim 'b')."""
    if pos <= 0:
        return 0
    pos -= 1
    # skip spaces
    while pos > 0 and s[pos] == " ":
        pos -= 1
    # skip word chars
    while pos > 0 and (s[pos - 1].isalnum() or s[pos - 1] == "_"):
        pos -= 1
    return pos


def _word_end(s: str, pos: int) -> int:
    """Return position one past the end of the current/next word (vim 'e'/'dw')."""
    n = len(s)
    if pos >= n:
        return n
    # skip spaces
    while pos < n and s[pos] == " ":
        pos += 1
    # skip word chars
    while pos < n and (s[pos].isalnum() or s[pos] == "_"):
        pos += 1
    return pos
