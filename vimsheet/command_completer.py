"""Tab-completion engine for command mode.

Completion contexts
-------------------
1. Command name          :w<tab>  :fetch<tab>
2. File / path arg       :w /tmp/<tab>  :e ./dat<tab>
3. Range + command       :A1:B5 fetch<tab>  :A1 sort<tab>
4. Formula function      =@SU<tab>  (inside insert/edit buffer)
5. Sheet name            :delsheet <tab>  :renamesheet <tab>
6. Theme name            :load theme <tab>
7. Sort order            :sort A <tab>
8. Plot type             :plot <tab>
"""

from __future__ import annotations

import glob
import os
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vimsheet.app import VimSheetApp

# ── Static completion lists ───────────────────────────────────────────────────

_ALL_COMMANDS = sorted(
    [
        "addsheet",
        "af",
        "autofit",
        "bd",
        "bd!",
        "bdel",
        "bdel!",
        "bdelete",
        "bdelete!",
        "be",
        "bg",
        "bgroup",
        "bn",
        "bp",
        "buf",
        "buffers",
        "bw",
        "bw!",
        "cf",
        "clearfilter",
        "colf",
        "colfit",
        "colgroup",
        "colwidth",
        "comment",
        "cw",
        "delsheet",
        "e",
        "edit",
        "ex",
        "export",
        "fetchlist",
        "fetchnow",
        "fetchstop",
        "fill",
        "filter",
        "find",
        "findnext",
        "findprev",
        "fmt",
        "format",
        "freeze",
        "func",
        "funcs",
        "functions",
        "g",
        "goto",
        "help",
        "ls",
        "hidecol",
        "hiderow",
        "history",
        "mess",
        "messages",
        "loadtext",
        "lt",
        "macro",
        "name",
        "newsheet",
        "nextsheet",
        "note",
        "plot",
        "prevsheet",
        "q",
        "q!",
        "r",
        "recalc",
        "renamesheet",
        "cs",
        "rs",
        "replace",
        "replaceall",
        "rowgroup",
        "rowf",
        "rowfit",
        "set",
        "sheet",
        "sheet+",
        "sheet-",
        "showcol",
        "showrow",
        "sort",
        "sp",
        "split",
        "theme",
        "undodelsheet",
        "unfreeze",
        "validate",
        "version",
        "w",
        "wq",
        "write",
        "x",
    ]
)

# Commands that accept a range prefix  (parts[0]=range, parts[1]=command)
_RANGE_COMMANDS = sorted(
    [
        "fetchnow",
        "fetchstop",
        "sort",
        "filter",
        "fill",
        "format",
        "fmt",
        "cond",
        "condformat",
        "cf",
        "name",
        "comment",
        "note",
        "hide",
        "show",
        "colwidth",
        "cw",
        "autofit",
        "af",
        "colf",
        "colfit",
        "rowf",
        "rowfit",
        "validate",
        "history",
        "clearfilter",
    ]
)

_FILE_COMMANDS = {
    "w",
    "write",
    "e",
    "edit",
    "ex",
    "export",
    "r",
    "loadtext",
    "lt",
    "func",
    "sp",
    "split",
}

_THEME_NAMES = sorted(
    [
        "dark",
        "light",
        "nord",
        "gruvbox",
        "dracula",
        "tokyo",
        "monokai",
        "solarized",
        "solarized-light",
        "catppuccin",
        "rose-pine",
    ]
)

_PALETTE_FIELDS: list[str] = []
_COLORSCHEME_SUBCOMMANDS = ["reset", "save"]
_PLOT_TYPES = ["bar", "histogram", "line", "pie", "scatter"]
_SORT_ORDERS = ["asc", "desc"]

_RANGE_RE = re.compile(r"^([A-Za-z]+\d+(?::[A-Za-z]+\d+)?\s+)(\S*)$")


# ── Completer ─────────────────────────────────────────────────────────────────


class CommandCompleter:
    """Stateful tab completer for the command buffer.

    Call :meth:`tab` each time Tab is pressed; call :meth:`reset` on any
    non-Tab key so the next Tab re-analyses the current buffer.
    """

    def __init__(self, app: VimSheetApp) -> None:
        self._app = app
        self._completions: list[str] = []  # full buffer for each candidate
        self._idx: int = 0

    def reset(self) -> None:
        self._completions = []
        self._idx = 0

    def tab(self, buf: str) -> str:
        """Return the next completed buffer, cycling on repeated presses."""
        if not self._completions:
            self._completions = self._build(buf)
            self._idx = 0
            if not self._completions:
                return buf
        result = self._completions[self._idx]
        self._idx = (self._idx + 1) % len(self._completions)
        return result

    # ── Builder ───────────────────────────────────────────────────────────────

    def _build(self, buf: str) -> list[str]:
        """Analyse *buf* and return a list of candidate complete buffers."""

        # ── 1. Range prefix: "A1:B5 partial"
        m = _RANGE_RE.match(buf)
        if m:
            prefix, partial = m.group(1), m.group(2).upper()
            candidates = [c for c in _RANGE_COMMANDS if c.upper().startswith(partial)]
            # Also include any formula-function names for power users
            candidates += [
                n for n in self._formula_names() if n.startswith(partial) and n not in candidates
            ]
            return [prefix + c for c in candidates]

        parts = buf.split()
        has_trailing_space = buf.endswith(" ")

        # ── 2. Still typing the command name (no space yet)
        if len(parts) <= 1 and not has_trailing_space:
            partial = (parts[0] if parts else "").lower()
            candidates = [c for c in _ALL_COMMANDS if c.startswith(partial)]
            return candidates

        cmd = parts[0].lower()

        # ── 3. File path argument
        if cmd in _FILE_COMMANDS:
            path_partial = parts[1] if len(parts) > 1 else ""
            # If there's a space after the first arg, don't re-complete
            if len(parts) > 2:
                return []
            files = self._complete_path(path_partial)
            return [f"{cmd} {f}" for f in files]

        # ── 4. theme <name>
        if cmd == "theme":
            partial = (parts[1] if len(parts) > 1 else "").lower()
            return [f"theme {t}" for t in _THEME_NAMES if t.startswith(partial)]

        # ── 4b. colorscheme
        if cmd == "colorscheme":
            if has_trailing_space:
                # "colorscheme " or "colorscheme save " — show fields or subcommands
                return _colorscheme_completions("", _PALETTE_FIELDS)
            if len(parts) == 2 and not has_trailing_space:
                partial = parts[1].lower()
                return _colorscheme_completions(partial, _PALETTE_FIELDS)
            return []

        # ── 5. Sheet name argument
        if cmd in {"delsheet", "sheet-", "renamesheet", "renames"}:
            partial = (parts[1] if len(parts) > 1 else "").strip('"')
            names = [s.name for s in self._app.workbook.sheets if s.name.startswith(partial)]
            return [f'{cmd} "{n}"' for n in names]

        # ── 6. Plot type
        if cmd == "plot":
            partial = (parts[1] if len(parts) > 1 else "").lower()
            return [f"plot {t}" for t in _PLOT_TYPES if t.startswith(partial)]

        # ── 7. Sort order
        if cmd == "sort":
            if len(parts) == 2 and not has_trailing_space:
                return []  # typing column — nothing to suggest
            completing_order = (len(parts) == 2 and has_trailing_space) or (
                len(parts) == 3 and not has_trailing_space
            )
            if completing_order:
                partial = (parts[2] if len(parts) == 3 else "").lower()
                return [f"sort {parts[1]} {o}" for o in _SORT_ORDERS if o.startswith(partial)]

        # ── 8. set <key>=<value> — cycle through config fields
        if cmd == "set":
            from dataclasses import fields as _dc_fields

            from vimsheet.model.config import Config

            try:
                cfg_fields = [
                    (f.name, getattr(self._app.config, f.name)) for f in _dc_fields(Config)
                ]
            except Exception:
                return []
            if len(parts) == 1 and has_trailing_space:
                # "set " → offer all keys with current values
                return [f"set {name}={val!r}".replace("'", "") for name, val in cfg_fields]
            elif len(parts) == 2 and not has_trailing_space:
                # "set au" → filter by partial key (handle "key=val" syntax)
                partial_key = parts[1].split("=")[0].lower()
                return [
                    f"set {name}={val!r}".replace("'", "")
                    for name, val in cfg_fields
                    if name.startswith(partial_key)
                ]
            return []

        return []

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _complete_path(self, partial: str) -> list[str]:
        """Return filesystem completions for *partial*."""
        if not partial:
            pattern = "./*"
        elif partial.endswith("/") or partial.endswith(os.sep):
            pattern = partial + "*"
        else:
            pattern = partial + "*"

        try:
            raw = glob.glob(pattern)
        except Exception:
            return []

        results: list[str] = []
        for p in sorted(raw):
            if os.path.isdir(p) and not p.endswith("/"):
                p += "/"
            results.append(p)
        return results

    def _formula_names(self) -> list[str]:
        try:
            from vimsheet.formula.functions.registry import all_names

            return all_names()
        except Exception:
            return []


# ── Module-level helper for colorscheme completions ─────────────────────


def _colorscheme_completions(partial: str, field_cache: list[str]) -> list[str]:
    """Build completions for ``:colorscheme``."""
    if not field_cache:
        from dataclasses import fields as _dcf

        from vimsheet.ui.grid_palette import GridPalette

        field_cache.extend(sorted(f.name for f in _dcf(GridPalette)))
    subcommands = [f"colorscheme {s}" for s in _COLORSCHEME_SUBCOMMANDS if s.startswith(partial)]
    fields = [f"colorscheme {f}" for f in field_cache if f.startswith(partial)]
    # Common color value suggestions (shown after a field name is typed)
    color_values = [
        "$primary",
        "$surface",
        "$text",
        "$text-muted",
        "$error",
        "$success",
        "$warning",
        "$accent",
    ]
    if partial in field_cache:
        return [f"colorscheme {partial} {v}" for v in color_values]
    return subcommands + fields
