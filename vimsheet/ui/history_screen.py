"""Cell history overlay — shown by :<range> history."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from vimsheet.ui.vim_modal import VimModalScreen

if TYPE_CHECKING:
    from vimsheet.model.sheet import Sheet


class HistoryScreen(VimModalScreen):
    """Modal overlay displaying cell change history for a range."""

    DEFAULT_CSS = """
    HistoryScreen {
        align: center middle;
    }
    HistoryScreen > VerticalScroll {
        width: 80%;
        height: 80%;
        background: $surface;
        border: round $primary;
        padding: 1 2;
    }
    HistoryScreen > VerticalScroll > Static {
        width: auto;
    }
    """

    def __init__(self, sheet: Sheet, range_str: str) -> None:
        super().__init__()
        self._sheet = sheet
        self._range_str = range_str

    def compose(self) -> ComposeResult:
        from vimsheet.model.range import CellRange, rowcol_to_a1

        lines: list[str] = []
        lines.append(f"[bold]Cell History — {self._range_str}[/bold]")
        lines.append("─" * 60)

        try:
            cr = CellRange.from_a1(self._range_str)
        except Exception:
            lines.append("[red]Invalid range[/red]")
        else:
            found = False
            for r in range(cr.start_row, cr.end_row + 1):
                for c in range(cr.start_col, cr.end_col + 1):
                    cell = self._sheet.get_cell(r, c)
                    if cell and cell.history:
                        found = True
                        addr = rowcol_to_a1(r, c)
                        lines.append(f"\n[bold]{addr}[/bold]")
                        for ts, val in cell.history[-10:]:
                            lines.append(f"  {ts.strftime('%Y-%m-%d %H:%M:%S')} = {val}")
                        lines.append(f"  [dim]current = {cell.value}[/dim]")
            if not found:
                lines.append("[dim]No history found in range[/dim]")

        lines.append("")
        lines.append("─" * 60)
        lines.append("[dim]q / Esc close[/dim]")

        with VerticalScroll():
            yield Static("\n".join(lines))
