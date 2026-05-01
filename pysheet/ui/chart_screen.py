"""Chart display overlay for PySheet."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.containers import VerticalScroll
from textual.widgets import Static


class ChartScreen(ModalScreen[None]):
    """Full-screen modal that displays a rendered ASCII chart."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("q", "dismiss", "Close"),
        Binding("space", "dismiss", "Close"),
    ]

    DEFAULT_CSS = """
    ChartScreen {
        align: center middle;
    }
    ChartScreen > VerticalScroll {
        background: $surface;
        border: thick $primary;
        padding: 1 2;
        width: 92%;
        height: 92%;
    }
    ChartScreen > VerticalScroll > Static {
        width: auto;
    }
    """

    def __init__(self, chart_text: str, title: str = "Chart") -> None:
        super().__init__()
        self._chart_text = chart_text
        self._title = title

    def compose(self) -> ComposeResult:
        content = (
            f"[bold cyan]{self._title}[/bold cyan]\n"
            f"{'─' * min(len(self._title), 60)}\n\n"
            f"{self._chart_text}\n\n"
            f"[dim]q / Escape / Space — close[/dim]"
        )
        with VerticalScroll():
            yield Static(content, markup=True)
