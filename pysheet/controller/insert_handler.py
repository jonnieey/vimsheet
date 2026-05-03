"""Insert mode key handler."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pysheet.controller.mode import Mode

if TYPE_CHECKING:
    from pysheet.app import PySheetApp


class InsertHandler:
    """Handles all key events while in Insert mode."""

    def __init__(self, app: PySheetApp) -> None:
        self._app = app

    def handle(self, key: str) -> None:
        app = self._app
        app.macro_recorder.record_key(key)
        buf = app._insert_buffer
        pos = app._insert_cursor

        match key:
            case "escape":
                app.mode = Mode.NORMAL
                app._insert_buffer = ""
                app._insert_cursor = 0
            case "enter":
                self._commit(move=(1, 0))
                return
            case "tab":
                self._commit(move=(0, 1))
                return
            case "shift+enter":
                self._commit(move=(-1, 0))
                return
            case "shift+tab":
                self._commit(move=(0, -1))
                return
            case "backspace":
                if pos > 0:
                    app._insert_buffer = buf[: pos - 1] + buf[pos:]
                    app._insert_cursor = pos - 1
            case "delete":
                if pos < len(buf):
                    app._insert_buffer = buf[:pos] + buf[pos + 1 :]
            case "left" | "ctrl+b":
                app._insert_cursor = max(0, pos - 1)
            case "right" | "ctrl+f":
                app._insert_cursor = min(len(buf), pos + 1)
            case "home" | "ctrl+a":
                app._insert_cursor = 0
            case "end" | "ctrl+e":
                app._insert_cursor = len(buf)
            case "ctrl+w":
                # Delete word before cursor
                before = buf[:pos]
                stripped = before.rstrip()
                # Find start of last word
                i = len(stripped) - 1
                while i >= 0 and (stripped[i].isalnum() or stripped[i] == "_"):
                    i -= 1
                new_before = stripped[: i + 1]
                app._insert_buffer = new_before + buf[pos:]
                app._insert_cursor = len(new_before)
            case "ctrl+u":
                app._insert_buffer = ""
                app._insert_cursor = 0
            case _ if len(key) == 1 and key.isprintable():
                app._insert_buffer = buf[:pos] + key + buf[pos:]
                app._insert_cursor = pos + 1

        app._sync_formula_bar()
        app._sync_status_bar()
        self._show_autocomplete_hint()

    def _show_autocomplete_hint(self) -> None:
        """Show matching function names in status bar when typing a formula."""
        app = self._app
        buf = app._insert_buffer
        if not buf.startswith("="):
            return
        # Extract the partial function name being typed (after last non-word char)
        import re

        partial = re.search(r"([A-Za-z]+)$", buf)
        if not partial:
            return
        token = partial.group(1).upper()
        if len(token) < 2:
            return
        try:
            from pysheet.formula.functions.registry import all_names

            matches = sorted(n for n in all_names() if n.startswith(token))[:6]
            if matches:
                app.status_bar.show_message("  ".join(matches))
        except Exception:
            pass

    def _commit(self, move: tuple[int, int] = (1, 0)) -> None:
        app = self._app
        raw = app._insert_buffer
        sheet = app.workbook.active_sheet
        r, c = app.cursor_row, app.cursor_col

        # Cancel any FETCH running on this cell if it's being overwritten
        old = sheet.get_cell(r, c)
        if old and old.formula and "FETCH" in old.formula.upper():
            app.fetch_manager.cancel((sheet.name, r, c))

        from pysheet.model.undo import SetCellCommand

        if raw.startswith("="):
            cmd = SetCellCommand(sheet, r, c, raw, new_formula=raw)
        else:
            val: Any = _coerce(raw)
            cmd = SetCellCommand(sheet, r, c, val)
        app.undo_stack.push(cmd)
        # Apply alignment hint
        cell = sheet.get_cell(r, c)
        if cell is not None:
            cell.fmt.align = "left" if app._insert_align == "left" else "right"  # type: ignore[assignment]

        app.workbook.modified = True
        app.mode = Mode.NORMAL
        app._insert_buffer = ""
        app._insert_cursor = 0
        dr, dc = move
        app.grid.move_by(dr, dc)
        app._sync_formula_bar()
        app._sync_status_bar()
        app.grid.refresh_grid()


def _coerce(raw: str) -> Any:
    """Parse raw string as int, float, or keep as str."""
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
