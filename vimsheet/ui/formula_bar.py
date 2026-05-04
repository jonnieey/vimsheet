"""Formula bar widget — address, formula/value display, mode indicator."""

from __future__ import annotations

import contextlib

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from vimsheet.controller.mode import Mode

_MODE_COLORS = {
    Mode.NORMAL: "bright_green",
    Mode.INSERT: "yellow",
    Mode.EDIT: "red",
    Mode.COMMAND: "cyan",
    Mode.VISUAL: "magenta",
    Mode.VISUAL_LINE: "magenta",
    Mode.VISUAL_BLOCK: "magenta",
}


class FormulaBar(Widget):
    """One-line bar: [address] [content …] [mode]"""

    DEFAULT_CSS = """
    FormulaBar {
        height: 1;
        background: $surface;
        color: $text;
        padding: 0;
    }
    FormulaBar Static {
        height: 1;
        background: transparent;
    }
    """

    cell_address: reactive[str] = reactive("A1")
    formula_text: reactive[str] = reactive("")
    cursor_pos: reactive[int] = reactive(-1)  # -1 = no cursor shown
    mode: reactive[Mode] = reactive(Mode.NORMAL)
    is_modified: reactive[bool] = reactive(False)
    is_locked: reactive[bool] = reactive(False)

    def compose(self) -> ComposeResult:
        yield Static("", id="fbar-content")

    # Redraw on any reactive change
    def watch_cell_address(self, _v: str) -> None:
        self._redraw()

    def watch_formula_text(self, _v: str) -> None:
        self._redraw()

    def watch_cursor_pos(self, _v: int) -> None:
        self._redraw()

    def watch_mode(self, _v: Mode) -> None:
        self._redraw()

    def watch_is_modified(self, _v: bool) -> None:
        self._redraw()

    def watch_is_locked(self, _v: bool) -> None:
        self._redraw()

    def _redraw(self) -> None:
        """Rebuild the single-line content string."""
        from rich.text import Text

        addr = self.cell_address.ljust(6)
        lock = " 🔒" if self.is_locked else ""
        dirty = " ●" if self.is_modified else ""
        mode_label = self.mode.label()
        color = _MODE_COLORS.get(self.mode, "white")

        t = Text(no_wrap=True, overflow="ellipsis")
        t.append(f" {addr} ", style="bold yellow on default")
        t.append("│ ", style="dim")

        text = self.formula_text or ""
        pos = self.cursor_pos
        if pos >= 0:
            # Split text at cursor and render a block cursor character between them
            before = text[:pos]
            at = text[pos] if pos < len(text) else " "
            after = text[pos + 1 :] if pos < len(text) else ""
            t.append(before, style="white")
            t.append(at, style="bold white on steel_blue1")
            t.append(after, style="white")
        else:
            t.append(text, style="white")

        t.append(lock, style="dim")
        t.append(dirty, style="red")
        t.append(" │ ", style="dim")
        t.append(f" {mode_label} ", style=f"bold {color}")
        with contextlib.suppress(Exception):
            self.query_one("#fbar-content", Static).update(t)  # not yet mounted

    def update_cell(
        self,
        address: str,
        formula_or_value: str,
        locked: bool = False,
        cursor_pos: int = -1,
    ) -> None:
        """Convenience: update address and content together."""
        self.is_locked = locked
        self.cell_address = address
        self.formula_text = formula_or_value
        self.cursor_pos = cursor_pos
