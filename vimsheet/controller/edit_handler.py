"""Unified cell editor — vi-style line editing of cell content.

All cell entry keys (``\\``, ``=``, ``<``, ``>``, ``|``, ``A``, ``I``, ``C``,
``S``, ``r``, ``cw``, ``cc``, ``e``, ``E``) route into this one editor.  It has
two sub-modes:

* ``insert`` — plain typing (like Vim's insert mode)
* ``normal`` — vi motions/operators over the cell text

``Esc`` in the insert sub-mode drops back to the normal sub-mode; ``Enter``
commits from either sub-mode.  Commit interpretation depends on the entry
*intent*: ``"text"`` stores raw strings, ``"value"`` coerces numbers and
valueizes pure-literal formulas.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from vimsheet.controller.mode import Mode

if TYPE_CHECKING:
    from vimsheet.app import VimSheetApp


class EditHandler:
    """Handles all key events while the unified cell editor is active."""

    def __init__(self, app: VimSheetApp) -> None:
        self._app = app
        # sub-mode: "normal" (vi motion) or "insert" (typing)
        self._sub: str = "normal"
        self._orig_value: str = ""  # content when the editor was entered, for 'u'
        # Commit policy, set by enter()
        self._align: str | None = None  # alignment to apply, None = preserve
        self._intent: str = "value"  # "value" = coerce numbers, "text" = raw string
        self._auto_move: bool = False  # Enter follows config.enter_moves
        self._move: tuple[int, int] = (0, 0)  # explicit cursor move on commit

        # Formula autocomplete (cycling) state, used in insert sub-mode
        self._fn_completions: list[str] = []
        self._fn_idx: int = 0
        self._fn_prefix: str = ""
        self._fn_at: str = ""
        self._fn_suffix: str = ""

    # -----------------------------------------------------------------------
    # Entry
    # -----------------------------------------------------------------------

    def enter(
        self,
        *,
        start_sub: str = "normal",
        cursor: str = "end",
        prefill: str | None = None,
        align: str | None = None,
        intent: str = "value",
        auto_move: bool = False,
        move: tuple[int, int] = (0, 0),
    ) -> None:
        """Enter the unified editor on the current cell.

        *start_sub*   — sub-mode to begin in: ``"normal"`` or ``"insert"``
        *cursor*      — ``"end"``, ``"start"``, or ``"start_formula"``
                        (start, but after a leading ``=``)
        *prefill*     — initial buffer; ``None`` loads the cell content
        *align*       — alignment applied on commit; ``None`` preserves the cell's
        *intent*      — ``"value"`` coerces numeric text, ``"text"`` keeps strings
        *auto_move*   — Enter uses ``config.enter_moves`` (insert-style entries)
        *move*        — explicit ``(dr, dc)`` applied on Enter when not auto_move
        """
        app = self._app
        cell = app.workbook.active_sheet.get_cell(app.cursor_row, app.cursor_col)
        if cell is not None and cell.locked:
            app.status_bar.show_message("Cell is locked — use 'zL' to unlock")
            return

        if prefill is None:
            content = cell.formula if cell and cell.formula else ""
            if not content and cell is not None and cell.value is not None:
                content = str(cell.value)
        else:
            content = prefill

        app._edit_buffer = content
        self._orig_value = content
        if cursor == "end":
            app._edit_cursor = len(content)
        elif cursor == "start_formula":
            app._edit_cursor = 1 if content.startswith("=") else 0
        else:  # "start"
            app._edit_cursor = 0

        self._sub = "insert" if start_sub == "insert" else "normal"
        self._align = align
        self._intent = intent
        self._auto_move = auto_move
        self._move = move
        self._clear_completions()
        app.mode = Mode.EDIT
        app._sync_formula_bar()

    # -----------------------------------------------------------------------
    # Key dispatch
    # -----------------------------------------------------------------------

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
                # Restore to value when the editor was entered
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
                self._clear_completions()
                self._sub = "normal"
                # clamp cursor to last char position (vim behaviour)
                app._edit_cursor = (
                    max(0, min(pos, len(app._edit_buffer) - 1)) if app._edit_buffer else 0
                )
            case "alt+enter":
                self._clear_completions()
                app._edit_buffer = buf[:pos] + "\n" + buf[pos:]
                app._edit_cursor = pos + 1
            case "enter":
                self._clear_completions()
                self._commit(move=self._enter_move())
                return
            case "tab":
                if buf.startswith("=") and self._try_formula_complete(buf, pos):
                    pass  # completion handled inside _try_formula_complete
                elif self._auto_move:
                    self._clear_completions()
                    self._commit(move=(0, getattr(app.config, "tab_size", 1)))
                    return
            case "shift+enter":
                self._clear_completions()
                self._commit(move=(-1, 0))
                return
            case "shift+tab":
                self._clear_completions()
                self._commit(move=(0, -1))
                return
            case "backspace":
                self._clear_completions()
                if pos > 0:
                    app._edit_buffer = buf[: pos - 1] + buf[pos:]
                    app._edit_cursor = pos - 1
            case "delete":
                self._clear_completions()
                if pos < len(buf):
                    app._edit_buffer = buf[:pos] + buf[pos + 1 :]
            case "left":
                self._clear_completions()
                app._edit_cursor = max(0, pos - 1)
            case "right":
                self._clear_completions()
                app._edit_cursor = min(len(buf), pos + 1)
            case "home" | "ctrl+a":
                self._clear_completions()
                app._edit_cursor = 0
            case "end" | "ctrl+e":
                self._clear_completions()
                app._edit_cursor = len(buf)
            case "ctrl+w":
                self._clear_completions()
                i = pos - 1
                while i >= 0 and buf[i] == " ":
                    i -= 1
                while i >= 0 and buf[i] != " ":
                    i -= 1
                app._edit_buffer = buf[: i + 1] + buf[pos:]
                app._edit_cursor = i + 1
            case "ctrl+u":
                self._clear_completions()
                app._edit_buffer = ""
                app._edit_cursor = 0
            case _ if len(key) == 1 and key.isprintable():
                self._clear_completions()
                app._edit_buffer = buf[:pos] + key + buf[pos:]
                app._edit_cursor = pos + 1

        self._show_autocomplete_hint()

    # -----------------------------------------------------------------------
    # Commit
    # -----------------------------------------------------------------------

    def _enter_move(self) -> tuple[int, int]:
        """Cursor move applied when Enter commits an insert-style entry."""
        if not self._auto_move:
            return self._move
        em = getattr(self._app.config, "enter_moves", "down")
        if em == "right":
            return (0, 1)
        if em == "none":
            return (0, 0)
        return (1, 0)

    def _commit(self, move: tuple[int, int] | None = None) -> None:
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
            from vimsheet.formula.evaluator import Evaluator

            ev = Evaluator(sheet, getattr(sheet, "_workbook", None))
            deps = ev.collect_deps(raw)
            has_func = "(" in raw[1:]
            if deps or has_func:
                cmd = SetCellCommand(sheet, r, c, raw, new_formula=raw)
            else:
                val = ev.eval_formula(raw, r, c)
                valid, msg = sheet.validation.validate(r, c, val)
                if not valid:
                    self._abort_commit(msg)
                    return
                cmd = SetCellCommand(sheet, r, c, val)
        else:
            if self._intent == "text":
                val = raw
            else:
                try:
                    val = int(raw) if "." not in raw else float(raw)
                except ValueError:
                    val = raw
            valid, msg = sheet.validation.validate(r, c, val)
            if not valid:
                self._abort_commit(msg)
                return
            cmd = SetCellCommand(sheet, r, c, val)

        app.undo_stack.push(cmd)
        # Apply alignment hint
        cell = sheet.get_cell(r, c)
        if cell is not None and self._align is not None:
            cell.fmt.align = self._align  # type: ignore[assignment]

        app.workbook.modified = True
        dr, dc = self._enter_move() if move is None else move
        app.mode = Mode.NORMAL
        self._reset()
        if (dr, dc) != (0, 0):
            app.grid.move_by(dr, dc)
        app._sync_formula_bar()
        app._sync_status_bar()
        app._sync_grid_preview()
        app.grid.refresh_grid()

    def _abort_commit(self, msg: str) -> None:
        """Reject a commit (validation failure) and return to NORMAL."""
        app = self._app
        app.status_bar.show_message(f"Validation failed: {msg}")
        app.mode = Mode.NORMAL
        self._reset()
        app._sync_formula_bar()
        app._sync_status_bar()
        app._sync_grid_preview()

    def _reset(self) -> None:
        app = self._app
        app._edit_buffer = ""
        app._edit_cursor = 0
        app._edit_chord = ""
        self._sub = "normal"
        self._align = None
        self._intent = "value"
        self._auto_move = False
        self._move = (0, 0)
        self._clear_completions()

    # -----------------------------------------------------------------------
    # Formula autocomplete
    # -----------------------------------------------------------------------

    def _clear_completions(self) -> None:
        self._fn_completions = []
        self._fn_idx = 0
        self._fn_prefix = ""
        self._fn_at = ""
        self._fn_suffix = ""

    def _try_formula_complete(self, buf: str, pos: int) -> bool:
        """Tab-complete a formula function name at the cursor.

        Returns True if a completion was applied (tab consumed), False otherwise.
        First Tab builds the completion list; subsequent Tabs cycle through it
        using the stored prefix/suffix so cursor position after ``(`` doesn't
        confuse re-parsing.
        """
        if self._fn_completions:
            # Already cycling — advance and rewrite using stored context
            self._fn_idx = (self._fn_idx + 1) % len(self._fn_completions)
            self._apply_fn_completion()
            return True

        # First Tab — find the partial token before the cursor
        import re

        from vimsheet.formula.functions.registry import all_names

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
        self._app._edit_buffer = completed + self._fn_suffix
        self._app._edit_cursor = len(completed)

        total = len(self._fn_completions)
        if total > 1:
            peek = min(5, total)
            rest = [self._fn_completions[(self._fn_idx + i) % total] for i in range(1, peek)]
            self._app.status_bar.show_message(f"{name}  →  {'  '.join(rest)}")

    def _show_autocomplete_hint(self) -> None:
        """Show matching function names in status bar when typing a formula."""
        app = self._app
        buf = app._edit_buffer
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
            from vimsheet.formula.functions.registry import all_names

            matches = sorted(n for n in all_names() if n.startswith(token))[:6]
            if matches:
                app.status_bar.show_message("  ".join(matches))
        except Exception:
            pass


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
