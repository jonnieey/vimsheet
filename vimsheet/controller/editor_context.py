"""Editor contexts for the unified line editor.

``EditHandler`` owns the buffer, the insert/normal sub-modes and the vi
motions.  An ``EditorContext`` supplies everything mode-specific:

* what text to load on entry,
* what ``Enter`` commits,
* what ``Esc`` from the normal sub-mode does (commit vs cancel),
* ``Tab`` completion,
* history navigation (``Up``/``Down`` in insert, ``k``/``j`` in normal),
* the optional status-bar hint.

Three contexts exist: cells (:class:`CellEditContext`), colon commands
(:class:`CommandEditContext`) and search prompts (:class:`SearchEditContext`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from vimsheet.controller.mode import Mode

if TYPE_CHECKING:
    from vimsheet.app import VimSheetApp


class EditorContext:
    """Base context: describes how the generic editor behaves for a target."""

    mode: Mode = Mode.EDIT
    prompt_prefix: str = ""
    record_macro: bool = False

    def __init__(self, app: VimSheetApp) -> None:
        self._app = app

    # ---- Entry / exit -----------------------------------------------------

    def load(self) -> str | None:
        """Return the initial buffer, or ``None`` to refuse entry."""
        return ""

    def commit(self, text: str, move: tuple[int, int] | None = None) -> None:
        """Handle ``Enter``/commit.  The editor resets itself afterwards."""

    def cancel(self) -> None:
        """Handle ``Esc`` from the normal sub-mode when it should abort."""

    def normal_escape(self) -> str:
        """Return ``"commit"`` or ``"cancel"`` for ``Esc`` in normal sub-mode."""
        return "commit"

    # ---- Insert sub-mode hooks -------------------------------------------

    def complete(self, text: str, cursor: int) -> tuple[str, int] | None:
        """Return an updated ``(text, cursor)`` for ``Tab``, or ``None``."""
        return None

    def reset_completion(self) -> None:
        """Discard any in-progress completion state."""

    def hint(self, text: str) -> None:
        """Optionally show a status-bar hint while typing."""
        return None

    def enter_move(self) -> tuple[int, int]:
        """Cursor move applied on a plain ``Enter``."""
        return (0, 0)

    def tab_move(self) -> tuple[int, int] | None:
        """Cursor move applied on ``Tab`` without a completion, or ``None``."""
        return None

    def shift_enter_move(self) -> tuple[int, int]:
        return (0, 0)

    def shift_tab_move(self) -> tuple[int, int]:
        return (0, 0)

    # ---- History ----------------------------------------------------------

    def history(self, direction: str) -> str | None:
        """Return the buffer for ``"prev"``/``"next"`` history, or ``None``."""
        return None


class CellEditContext(EditorContext):
    """Editor context for cell content (the original unified editor)."""

    mode = Mode.EDIT
    record_macro = True

    def __init__(
        self,
        app: VimSheetApp,
        *,
        prefill: str | None = None,
        align: str | None = None,
        intent: str = "value",
        auto_move: bool = False,
        move: tuple[int, int] = (0, 0),
    ) -> None:
        super().__init__(app)
        self._prefill = prefill
        self._align = align
        self._intent = intent
        self._auto_move = auto_move
        self._move = move

        # Formula autocomplete (cycling) state
        self._fn_completions: list[str] = []
        self._fn_idx: int = 0
        self._fn_prefix: str = ""
        self._fn_at: str = ""
        self._fn_suffix: str = ""

    # ---- Entry ------------------------------------------------------------

    def load(self) -> str | None:
        app = self._app
        cell = app.workbook.active_sheet.get_cell(app.cursor_row, app.cursor_col)
        if cell is not None and cell.locked:
            app.status_bar.show_message("Cell is locked — use 'zL' to unlock")
            return None
        if self._prefill is not None:
            return self._prefill
        content = cell.formula if cell and cell.formula else ""
        if not content and cell is not None and cell.value is not None:
            content = str(cell.value)
        return content

    # ---- Commit -----------------------------------------------------------

    def _effective_move(self, move: tuple[int, int] | None) -> tuple[int, int]:
        if move is not None:
            return move
        if not self._auto_move:
            return self._move
        em = getattr(self._app.config, "enter_moves", "down")
        if em == "right":
            return (0, 1)
        if em == "none":
            return (0, 0)
        return (1, 0)

    def commit(self, text: str, move: tuple[int, int] | None = None) -> None:
        app = self._app
        raw = text
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
                    self._abort(msg)
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
                self._abort(msg)
                return
            cmd = SetCellCommand(sheet, r, c, val)

        app.undo_stack.push(cmd)
        # Apply alignment hint
        cell = sheet.get_cell(r, c)
        if cell is not None and self._align is not None:
            cell.fmt.align = self._align  # type: ignore[assignment]

        app.workbook.modified = True
        dr, dc = self._effective_move(move)
        app.mode = Mode.NORMAL
        if (dr, dc) != (0, 0):
            app.grid.move_by(dr, dc)

    def _abort(self, msg: str) -> None:
        app = self._app
        app.status_bar.show_message(f"Validation failed: {msg}")
        app.mode = Mode.NORMAL

    # ---- Insert hooks -----------------------------------------------------

    def enter_move(self) -> tuple[int, int]:
        return self._effective_move(None)

    def tab_move(self) -> tuple[int, int] | None:
        if not self._auto_move:
            return None
        return (0, getattr(self._app.config, "tab_size", 1))

    def shift_enter_move(self) -> tuple[int, int]:
        return (-1, 0)

    def shift_tab_move(self) -> tuple[int, int]:
        return (0, -1)

    def complete(self, text: str, cursor: int) -> tuple[str, int] | None:
        if text.startswith("=") and self._try_formula_complete(text, cursor):
            return (self._app._edit_buffer, self._app._edit_cursor)
        return None

    def reset_completion(self) -> None:
        self._clear_completions()

    def hint(self, text: str) -> None:
        app = self._app
        if not text.startswith("="):
            return
        import re

        partial = re.search(r"([A-Za-z]+)$", text)
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

    # ---- Formula autocomplete --------------------------------------------

    def _clear_completions(self) -> None:
        self._fn_completions = []
        self._fn_idx = 0
        self._fn_prefix = ""
        self._fn_at = ""
        self._fn_suffix = ""

    def _try_formula_complete(self, buf: str, pos: int) -> bool:
        """Tab-complete a formula function name at the cursor."""
        if self._fn_completions:
            self._fn_idx = (self._fn_idx + 1) % len(self._fn_completions)
            self._apply_fn_completion()
            return True

        import re

        from vimsheet.formula.functions.registry import all_names

        before = buf[:pos]
        m = re.search(r"(@?)([A-Za-z]\w*)$", before)
        if not m:
            return False

        at_sign = m.group(1)
        partial = m.group(2).upper()

        matches = sorted(n for n in all_names() if n.startswith(partial))
        if not matches:
            return False

        self._fn_prefix = before[: m.start()]
        self._fn_at = at_sign
        self._fn_suffix = buf[pos:]
        self._fn_completions = matches
        self._fn_idx = 0
        self._apply_fn_completion()
        return True

    def _apply_fn_completion(self) -> None:
        name = self._fn_completions[self._fn_idx]
        completed = self._fn_prefix + self._fn_at + name + "("
        self._app._edit_buffer = completed + self._fn_suffix
        self._app._edit_cursor = len(completed)

        total = len(self._fn_completions)
        if total > 1:
            peek = min(5, total)
            rest = [self._fn_completions[(self._fn_idx + i) % total] for i in range(1, peek)]
            self._app.status_bar.show_message(f"{name}  →  {'  '.join(rest)}")


class CommandEditContext(EditorContext):
    """Editor context for colon commands (``:``)."""

    mode = Mode.COMMAND
    prompt_prefix = ":"

    def __init__(self, app: VimSheetApp, initial: str = "") -> None:
        super().__init__(app)
        self._initial = initial

    def load(self) -> str:
        return self._initial

    def normal_escape(self) -> str:
        return "cancel"

    def commit(self, text: str, move: tuple[int, int] | None = None) -> None:
        app = self._app
        app._cmd_completer.reset()
        app._cmd_history.reset_browse()
        app._search_history.reset_browse()
        cmd = text.strip()
        if cmd:
            app._cmd_history.push(cmd)
            app._save_history()
        app._pre_command_mode = None
        app.grid.show_visual = False
        app.mode = Mode.NORMAL
        if cmd:
            app._dispatch_command(cmd)

    def cancel(self) -> None:
        app = self._app
        app._cmd_completer.reset()
        app._cmd_history.reset_browse()
        app._search_history.reset_browse()
        if app._pre_command_mode is not None:
            app.mode = app._pre_command_mode
            app._pre_command_mode = None
        else:
            app.grid.show_visual = False
            app.mode = Mode.NORMAL
        app.status_bar.set_persistent_message("")

    def complete(self, text: str, cursor: int) -> tuple[str, int] | None:
        completed = self._app._cmd_completer.tab(text)
        return (completed, len(completed))

    def reset_completion(self) -> None:
        self._app._cmd_completer.reset()

    def history(self, direction: str) -> str | None:
        hist = self._app._cmd_history
        if direction == "prev":
            return hist.prev()
        nxt = hist.next()
        return nxt if nxt is not None else ""


class SearchEditContext(EditorContext):
    """Editor context for search prompts (``/`` and ``?``)."""

    mode = Mode.SEARCH

    def __init__(self, app: VimSheetApp, prefix: str = "/") -> None:
        super().__init__(app)
        self.prompt_prefix = prefix if prefix in ("/", "?") else "/"

    def load(self) -> str:
        return ""

    def normal_escape(self) -> str:
        return "cancel"

    def commit(self, text: str, move: tuple[int, int] | None = None) -> None:
        app = self._app
        cmd = text.strip()
        prefix = self.prompt_prefix
        if cmd:
            app._search_history.push(cmd)
            app._save_history()
            app._search_history.reset_browse()
        app.mode = Mode.NORMAL
        app.status_bar.set_persistent_message("")
        if cmd:
            app._dispatch_command(prefix + cmd)

    def cancel(self) -> None:
        app = self._app
        app.mode = Mode.NORMAL
        app.status_bar.set_persistent_message("")

    def history(self, direction: str) -> str | None:
        hist = self._app._search_history
        if direction == "prev":
            return hist.prev()
        nxt = hist.next()
        return nxt if nxt is not None else ""
