"""Message history overlay — shown by :messages / :mess."""

from __future__ import annotations

from datetime import datetime

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from vimsheet.ui.status_bar import MessageEntry
from vimsheet.ui.vim_modal import VimModalScreen


class MessagesScreen(VimModalScreen):
    """Modal overlay displaying the status bar message history."""

    DEFAULT_CSS = """
    MessagesScreen {
        align: center middle;
    }
    MessagesScreen > VerticalScroll {
        width: 80%;
        height: 80%;
        background: $surface;
        border: round $primary;
        padding: 1 2;
    }
    MessagesScreen > VerticalScroll > Static {
        width: auto;
    }
    """

    def __init__(self, messages: list[MessageEntry]) -> None:
        super().__init__()
        self._messages = messages

    def compose(self) -> ComposeResult:
        lines: list[str] = []
        lines.append("[bold]Message History[/bold]")
        lines.append("─" * 60)

        if not self._messages:
            lines.append("[dim]No messages yet[/dim]")
        else:
            for m in reversed(self._messages):
                ts = datetime.fromtimestamp(m.timestamp).strftime("%H:%M:%S")
                color = (
                    "red" if m.level == "error" else "green" if m.level == "success" else "yellow"
                )
                lines.append(f"[{color}][{ts}] {m.text}[/]")

        lines.append("")
        lines.append("─" * 60)
        lines.append("[dim]q / Esc close[/dim]")

        with VerticalScroll():
            yield Static("\n".join(lines))
