"""Status bar widget — mode, position, stats, file status, clock."""

from __future__ import annotations

import time

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from pysheet.controller.mode import Mode


class StatusBar(Widget):
    """Bottom status bar displaying context-sensitive information."""

    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        layout: horizontal;
        background: $primary;
        color: $background;
    }
    StatusBar .segment {
        padding: 0 1;
        content-align: left middle;
    }
    StatusBar #status-mode {
        width: 10;
        background: $primary-darken-2;
        content-align: center middle;
        text-style: bold;
    }
    StatusBar #status-pos {
        width: 14;
    }
    StatusBar #status-stats {
        width: 12;
    }
    StatusBar #status-message {
        width: 1fr;
        color: $warning;
    }
    StatusBar #status-file-state {
        width: 10;
    }
    StatusBar #status-filename {
        width: 24;
    }
    StatusBar #status-clock {
        width: 10;
    }
    """

    mode: reactive[Mode] = reactive(Mode.NORMAL)
    cell_address: reactive[str] = reactive("A1")
    row: reactive[int] = reactive(0)
    col: reactive[int] = reactive(0)
    used_rows: reactive[int] = reactive(0)
    filename: reactive[str] = reactive("")
    file_modified: reactive[bool] = reactive(False)
    message: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        """Lay out status segments."""
        yield Static("NORMAL", id="status-mode", classes="segment")
        yield Static("A1", id="status-pos", classes="segment")
        yield Static("", id="status-stats", classes="segment")
        yield Static("", id="status-message", classes="segment")
        yield Static("", id="status-file-state", classes="segment")
        yield Static("", id="status-filename", classes="segment")
        yield Static("", id="status-clock", classes="segment")

    def on_mount(self) -> None:
        """Start the clock timer."""
        self.set_interval(1, self._tick_clock)
        self._tick_clock()

    def _tick_clock(self) -> None:
        """Update the clock display."""
        self.query_one("#status-clock", Static).update(
            time.strftime("%H:%M:%S")
        )

    def watch_mode(self, value: Mode) -> None:
        """Update mode label."""
        self.query_one("#status-mode", Static).update(value.label())

    def watch_cell_address(self, value: str) -> None:
        """Update cell address label."""
        pos = f"R{self.row + 1} C{self.col + 1}  {value}"
        self.query_one("#status-pos", Static).update(pos)

    def watch_row(self, _value: int) -> None:
        self.watch_cell_address(self.cell_address)

    def watch_col(self, _value: int) -> None:
        self.watch_cell_address(self.cell_address)

    def watch_used_rows(self, value: int) -> None:
        """Update stats label."""
        self.query_one("#status-stats", Static).update(f"{value} rows")

    def watch_filename(self, value: str) -> None:
        """Update filename label."""
        self.query_one("#status-filename", Static).update(value or "[no file]")

    def watch_file_modified(self, value: bool) -> None:
        """Update file-state label."""
        label = "Modified" if value else "Saved"
        self.query_one("#status-file-state", Static).update(label)

    def watch_message(self, value: str) -> None:
        """Update transient message label."""
        self.query_one("#status-message", Static).update(value)

    def show_message(self, text: str, duration: float = 3.0) -> None:
        """Show a transient message that auto-clears after *duration* seconds."""
        self._write_message(text)
        self.set_timer(duration, self._clear_message)

    def set_persistent_message(self, text: str) -> None:
        """Show a message with no auto-clear timer (for command mode prompt)."""
        self._write_message(text)

    def _write_message(self, text: str) -> None:
        """Write text directly to the message widget, bypassing reactive batching."""
        self.message = text
        try:
            self.query_one("#status-message", Static).update(text)
        except Exception:
            pass

    def _clear_message(self) -> None:
        self._write_message("")

    def update_cursor(self, row: int, col: int, address: str) -> None:
        """Convenience method to update all cursor-position fields."""
        self.row = row
        self.col = col
        self.cell_address = address
