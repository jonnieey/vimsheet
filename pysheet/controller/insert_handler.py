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
        self._fn_completions: list[str] = []  # cycling formula completions
        self._fn_idx: int = 0
        self._fn_prefix: str = ""  # buffer text before the completed token
        self._fn_at: str = ""  # "@" or "" captured from original token
        self._fn_suffix: str = ""  # buffer text after cursor when cycling started

    def handle(self, key: str) -> None:
        app = self._app
        app.macro_recorder.record_key(key)
        buf = app._insert_buffer
        pos = app._insert_cursor

        match key:
            case "escape":
                self._fn_completions = []
                app.mode = Mode.NORMAL
                app._insert_buffer = ""
                app._insert_cursor = 0
            case "enter":
                self._fn_completions = []
                self._commit(move=(1, 0))
                return
            case "tab":
                if buf.startswith("=") and self._try_formula_complete(buf, pos):
                    pass  # completion handled inside _try_formula_complete
                else:
                    self._fn_completions = []
                    self._commit(move=(0, 1))
                    return
            case "shift+enter":
                self._commit(move=(-1, 0))
                return
            case "shift+tab":
                self._commit(move=(0, -1))
                return
            case "backspace":
                self._fn_completions = []
                if pos > 0:
                    app._insert_buffer = buf[: pos - 1] + buf[pos:]
                    app._insert_cursor = pos - 1
            case "delete":
                self._fn_completions = []
                if pos < len(buf):
                    app._insert_buffer = buf[:pos] + buf[pos + 1 :]
            case "left" | "ctrl+b":
                self._fn_completions = []
                app._insert_cursor = max(0, pos - 1)
            case "right" | "ctrl+f":
                self._fn_completions = []
                app._insert_cursor = min(len(buf), pos + 1)
            case "home" | "ctrl+a":
                self._fn_completions = []
                app._insert_cursor = 0
            case "end" | "ctrl+e":
                self._fn_completions = []
                app._insert_cursor = len(buf)
            case "ctrl+w":
                self._fn_completions = []
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
                self._fn_completions = []
                app._insert_buffer = ""
                app._insert_cursor = 0
            case _ if len(key) == 1 and key.isprintable():
                self._fn_completions = []
                app._insert_buffer = buf[:pos] + key + buf[pos:]
                app._insert_cursor = pos + 1

        app._sync_formula_bar()
        app._sync_status_bar()
        self._show_autocomplete_hint()

    def _try_formula_complete(self, buf: str, pos: int) -> bool:
        """Tab-complete a formula function name at the cursor.

        Returns True if a completion was applied (tab consumed), False otherwise.
        First Tab builds the completion list; subsequent Tabs cycle through it
        using the stored prefix/suffix so cursor position after `(` doesn't
        confuse re-parsing.
        """
        if self._fn_completions:
            # Already cycling — advance and rewrite using stored context
            self._fn_idx = (self._fn_idx + 1) % len(self._fn_completions)
            self._apply_fn_completion()
            return True

        # First Tab — find the partial token before the cursor
        import re

        from pysheet.formula.functions.registry import all_names

        before = buf[:pos]
        m = re.search(r"(@?)([A-Za-z]\w*)$", before)
        if not m:
            return False

        at_sign = m.group(1)  # "@" or ""
        partial = m.group(2).upper()

        matches = sorted(n for n in all_names() if n.startswith(partial))
        if not matches:
            return False

        self._fn_prefix = before[: m.start()]  # everything before @WORD
        self._fn_at = at_sign
        self._fn_suffix = buf[pos:]  # everything after cursor
        self._fn_completions = matches
        self._fn_idx = 0
        self._apply_fn_completion()
        return True

    def _apply_fn_completion(self) -> None:
        """Write the current cycling candidate into the buffer."""
        name = self._fn_completions[self._fn_idx]
        completed = self._fn_prefix + self._fn_at + name + "("
        self._app._insert_buffer = completed + self._fn_suffix
        self._app._insert_cursor = len(completed)

        total = len(self._fn_completions)
        if total > 1:
            peek = min(5, total)
            rest = [self._fn_completions[(self._fn_idx + i) % total] for i in range(1, peek)]
            self._app.status_bar.show_message(f"{name}  →  {'  '.join(rest)}")

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
