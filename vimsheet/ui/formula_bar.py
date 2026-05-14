"""Formula bar widget — address, formula/value display, mode indicator."""

from __future__ import annotations

import contextlib

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from vimsheet.controller.mode import Mode
from vimsheet.ui.grid_palette import GridPalette


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

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._palette: GridPalette = GridPalette()

    def set_palette(self, palette: GridPalette) -> None:
        self._palette = palette
        self._redraw()

    def _mode_color(self) -> str:
        return {
            Mode.NORMAL: self._palette.mode_normal,
            Mode.INSERT: self._palette.mode_insert,
            Mode.EDIT: self._palette.mode_edit,
            Mode.COMMAND: self._palette.mode_command,
            Mode.SEARCH: self._palette.mode_command,
            Mode.VISUAL: self._palette.mode_visual,
            Mode.VISUAL_LINE: self._palette.mode_visual,
            Mode.VISUAL_BLOCK: self._palette.mode_visual,
        }.get(self.mode, "white")

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
        color = self._mode_color()

        t = Text(no_wrap=True, overflow="ellipsis")
        t.append(f" {addr} ", style="bold yellow on default")
        t.append("│ ", style="dim")

        text = self.formula_text or ""
        pos = self.cursor_pos
        if pos >= 0:
            # Show only the current line (after last \n)
            last_nl = text.rfind("\n", 0, pos)
            display_text = text[last_nl + 1 :]
            display_pos = pos - (last_nl + 1)
            before = display_text[:display_pos]
            at = display_text[display_pos] if display_pos < len(display_text) else " "
            after = display_text[display_pos + 1 :] if display_pos < len(display_text) else ""
            t.append(before, style="white")
            if self.mode == Mode.INSERT:
                t.append(at, style=f"underline white on {self._palette.formula_cursor_bg}")
            else:
                t.append(at, style=f"bold white on {self._palette.formula_cursor_bg}")
            t.append(after, style="white")
        else:
            # Show only last line when no cursor
            last_nl = text.rfind("\n")
            display_text = text[last_nl + 1 :] if last_nl >= 0 else text
            t.append(display_text, style="white")

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
