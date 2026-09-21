"""Unified line editor — vi-style editing shared by cells, commands, search.

The editor owns the buffer, the insert/normal sub-modes and the vi motions.
Mode-specific behaviour is delegated to an :class:`EditorContext`
(see ``editor_context.py`):

* cell content — ``\\``, ``=``, ``<``, ``>``, ``|``, ``A``, ``I``, ``C``,
  ``S``, ``r``, ``cw``, ``cc``, ``e``, ``E``,
* colon commands — ``:``,
* search prompts — ``/`` and ``?``.

``Esc`` in the insert sub-mode drops back to the normal sub-mode.  From the
normal sub-mode, ``Enter`` commits and ``Esc`` either commits (cells) or
cancels (commands/search) — see ``EditorContext.normal_escape``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from vimsheet.controller.editor_context import CellEditContext, EditorContext

if TYPE_CHECKING:
    from vimsheet.app import VimSheetApp


class EditHandler:
    """Handles all key events while the unified line editor is active."""

    def __init__(self, app: VimSheetApp) -> None:
        self._app = app
        self._context: EditorContext | None = None
        # sub-mode: "normal" (vi motion) or "insert" (typing)
        self._sub: str = "normal"
        self._orig_value: str = ""  # content when the editor was entered, for 'u'

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
        """Enter the editor on the current cell (see ``CellEditContext``)."""
        context = CellEditContext(
            self._app,
            prefill=prefill,
            align=align,
            intent=intent,
            auto_move=auto_move,
            move=move,
        )
        self.enter_context(context, start_sub=start_sub, cursor=cursor)

    def enter_context(
        self,
        context: EditorContext,
        *,
        start_sub: str = "normal",
        cursor: str = "end",
    ) -> None:
        """Enter the editor with an arbitrary context.

        *cursor* is ``"end"``, ``"start"`` or ``"start_formula"`` (start, but
        after a leading ``=``).
        """
        app = self._app
        text = context.load()
        if text is None:
            return  # refused (e.g. locked cell)

        self._context = context
        self._orig_value = text
        app._edit_buffer = text
        if cursor == "end":
            app._edit_cursor = len(text)
        elif cursor == "start_formula":
            app._edit_cursor = 1 if text.startswith("=") else 0
        else:  # "start"
            app._edit_cursor = 0

        self._sub = "insert" if start_sub == "insert" else "normal"
        context.reset_completion()
        app.mode = context.mode
        app._sync_formula_bar()

    # -----------------------------------------------------------------------
    # Key dispatch
    # -----------------------------------------------------------------------

    def handle(self, key: str) -> None:
        app = self._app
        context = self._context
        if context is None:
            return
        if context.record_macro:
            app.macro_recorder.record_key(key)
        if key != "tab":
            context.reset_completion()

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

        # Pending r{char}: the next printable key is the replacement character
        if app._edit_chord == "r":
            app._edit_chord = ""
            if len(key) == 1 and key.isprintable() and pos < len(buf):
                app._edit_buffer = buf[:pos] + key + buf[pos + 1 :]
            return

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
            case "enter":
                self._commit()
            case "escape":
                if self._context is not None and self._context.normal_escape() == "cancel":
                    self._cancel()
                else:
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
            case "j":
                self._history("next")
            case "k":
                self._history("prev")
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
                app._edit_buffer = self._orig_value
                app._edit_cursor = len(self._orig_value)
            case "d" | "c":
                app._edit_chord = key
            case " ":
                app._edit_buffer = buf[:pos] + " " + buf[pos:]
                app._edit_cursor = pos + 1
            case _ if len(key) == 1 and key.isprintable():
                # Buffer single char for chord detection (e.g. r{char})
                app._edit_chord = key

    # -----------------------------------------------------------------------
    # Sub-mode: insert (typing)
    # -----------------------------------------------------------------------

    def _handle_insert_sub(self, key: str) -> None:
        app = self._app
        context = self._context
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
                move = context.enter_move() if context else (0, 0)
                self._commit(move=move)
                return
            case "tab":
                result = context.complete(buf, pos) if context else None
                if result is not None:
                    app._edit_buffer, app._edit_cursor = result
                else:
                    tab_move = context.tab_move() if context else None
                    if tab_move is not None:
                        self._commit(move=tab_move)
                        return
            case "shift+enter":
                move = context.shift_enter_move() if context else (0, 0)
                self._commit(move=move)
                return
            case "shift+tab":
                move = context.shift_tab_move() if context else (0, 0)
                self._commit(move=move)
                return
            case "up":
                self._history("prev")
            case "down":
                self._history("next")
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

        if context is not None:
            context.hint(app._edit_buffer)

    # -----------------------------------------------------------------------
    # Commit / cancel / history
    # -----------------------------------------------------------------------

    def _commit(self, move: tuple[int, int] | None = None) -> None:
        context = self._context
        if context is None:
            return
        context.commit(self._app._edit_buffer, move)
        self._finish()

    def _cancel(self) -> None:
        context = self._context
        if context is None:
            return
        context.cancel()
        self._finish()

    def _history(self, direction: str) -> None:
        context = self._context
        if context is None:
            return
        text = context.history(direction)
        if text is None:
            return
        self._app._edit_buffer = text
        self._app._edit_cursor = len(text)
        context.reset_completion()

    def _finish(self) -> None:
        app = self._app
        app._edit_buffer = ""
        app._edit_cursor = 0
        app._edit_chord = ""
        self._sub = "normal"
        self._context = None
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
    while pos < n and (s[pos].isalnum() or s[pos] == "_"):
        pos += 1
    while pos < n and s[pos] == " ":
        pos += 1
    return pos


def _word_backward(s: str, pos: int) -> int:
    """Return position of previous word start (vim 'b')."""
    if pos <= 0:
        return 0
    pos -= 1
    while pos > 0 and s[pos] == " ":
        pos -= 1
    while pos > 0 and (s[pos - 1].isalnum() or s[pos - 1] == "_"):
        pos -= 1
    return pos


def _word_end(s: str, pos: int) -> int:
    """Return position one past the end of the current/next word (vim 'e'/'dw')."""
    n = len(s)
    if pos >= n:
        return n
    while pos < n and s[pos] == " ":
        pos += 1
    while pos < n and (s[pos].isalnum() or s[pos] == "_"):
        pos += 1
    return pos
