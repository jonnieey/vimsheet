"""FetchListScreen — modal listing all active FETCH cells."""

from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from pysheet.model.range import col_index_to_letters
from pysheet.ui.vim_modal import VimModalScreen


def _cell_addr(key: tuple[str, int, int]) -> str:
    _, row, col = key
    return f"{col_index_to_letters(col)}{row + 1}"


class FetchListScreen(VimModalScreen):
    """Modal listing active FETCH cells with URL, interval, status, and last value."""

    DEFAULT_CSS = """
    FetchListScreen {
        align: center middle;
    }
    FetchListScreen > VerticalScroll {
        background: $surface;
        border: thick $primary;
        padding: 1 2;
        width: 90;
        height: 80%;
    }
    FetchListScreen > VerticalScroll > Static {
        width: auto;
    }
    """

    def __init__(self, entries: list[tuple[Any, Any]]) -> None:
        super().__init__()
        self._entries = entries

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Static(self._build_text(), markup=True)

    def _build_text(self) -> str:
        if not self._entries:
            return "[dim]No active fetches.[/dim]"

        n = len(self._entries)
        plural = "es" if n != 1 else ""
        lines: list[str] = [
            f"[bold]{n} active fetch{plural}[/bold]  [dim](q/Esc to close)[/dim]\n",
        ]

        col_w = 6
        url_w = 38
        int_w = 8

        header = (
            f"  [bold]{'Cell':<{col_w}}  {'URL':<{url_w}}  {'Refresh':>{int_w}}  "
            f"{'Status':<8}  Last Value[/bold]"
        )
        lines.append(header)
        lines.append("  " + "─" * 80)

        for key, entry in self._entries:
            sheet_name, _r, _c = key
            addr = f"{sheet_name}!{_cell_addr(key)}"
            url_trunc = (
                entry.url[:url_w] if len(entry.url) <= url_w else entry.url[: url_w - 1] + "…"
            )
            interval_str = f"{entry.interval}s" if entry.interval else "once"
            status_color = {
                "ok": "green",
                "error": "red",
                "loading": "yellow",
                "pending": "dim",
            }.get(entry.status, "white")
            last_val = str(entry.last_value)
            if len(last_val) > 30:
                last_val = last_val[:29] + "…"

            lines.append(
                f"  [cyan]{addr:<{col_w + 8}}[/cyan]"
                f"  [white]{url_trunc:<{url_w}}[/white]"
                f"  [dim]{interval_str:>{int_w}}[/dim]"
                f"  [{status_color}]{entry.status:<8}[/{status_color}]"
                f"  [yellow]{last_val}[/yellow]"
            )

        return "\n".join(lines)
