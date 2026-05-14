"""Status bar widget — mode, position, stats, file status, clock."""

from __future__ import annotations

import contextlib
import time
from collections import deque
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from vimsheet.controller.mode import Mode

if TYPE_CHECKING:
    pass


@dataclass
class MessageEntry:
    """A single status bar message stored in history."""

    text: str
    timestamp: float
    level: str  # "info", "error", "success"


class StatusBar(Widget):
    """Bottom status bar displaying context-sensitive information."""

    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        layout: horizontal;
        background: $surface;
        color: $text;
    }
    StatusBar .segment {
        padding: 0 1;
        content-align: left middle;
    }
    StatusBar #status-mode {
        width: 10;
        background: $primary;
        content-align: center middle;
        text-style: bold;
    }
    StatusBar #status-sheet {
        width: 16;
        background: $primary-darken-1;
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
        color: $text-warning;
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
    sheet_name: reactive[str] = reactive("")
    cell_address: reactive[str] = reactive("A1")
    row: reactive[int] = reactive(0)
    col: reactive[int] = reactive(0)
    used_rows: reactive[int] = reactive(0)
    filename: reactive[str] = reactive("")
    file_modified: reactive[bool] = reactive(False)
    message: reactive[str] = reactive("")

    # Message priority: higher values = more important.
    #   0 = empty/default
    #   1 = confirm prompts ([y/N])
    #   2 = input prompts (gx:, go:, :, /, ?, digit count)
    #   3 = transient notifications (show_message)
    _priority: int = 0

    _last_level: str = "info"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.message_history: deque[MessageEntry] = deque(maxlen=200)

    def set_history_size(self, size: int) -> None:
        """Change the max length of the message history deque."""
        old = self.message_history
        self.message_history = deque(old, maxlen=max(size, 10))

    def compose(self) -> ComposeResult:
        """Lay out status segments."""
        yield Static("NORMAL", id="status-mode", classes="segment")
        yield Static("", id="status-sheet", classes="segment")
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
        self.query_one("#status-clock", Static).update(time.strftime("%H:%M:%S"))

    def watch_mode(self, value: Mode) -> None:
        """Update mode label."""
        self.query_one("#status-mode", Static).update(value.label())

    def watch_sheet_name(self, value: str) -> None:
        self.query_one("#status-sheet", Static).update(value)

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

    _ERROR_KEYWORDS = frozenset(
        [
            "error",
            "fail",
            "invalid",
            "not found",
            "unknown",
            "nothing",
            "cannot",
            "no match",
            "no history",
            "#ref",
            "#http",
            "#timeout",
            "#fetch",
            "usage:",
            "not set",
            "cell is locked",
            "validation failed",
            "bad range",
            "bad address",
            "unknown command",
            "script error",
            "script timed out",
            "file not found",
            "no data loaded",
            "no messages",
            "no buffer",
            "no active",
            "not defined",
        ]
    )

    _SUCCESS_KEYWORDS = frozenset(
        [
            "sorted by",
            "written:",
            "saved",
            "deleted",
            "added",
            "filled",
            "yanked",
            "pasted",
            "redo",
            "replaced",
            "frozen",
            "unfrozen",
            "filter cleared",
            "recalculated",
            "restored",
            "moved",
            "renamed",
            "copied",
            "duplicated",
            "macro recorded",
            "undo!",
        ]
    )

    @classmethod
    def _detect_level(cls, text: str) -> str:
        """Auto-detect message level from text content."""
        lower = text.lower()
        for kw in cls._ERROR_KEYWORDS:
            if kw in lower:
                return "error"
        for kw in cls._SUCCESS_KEYWORDS:
            if kw in lower:
                return "success"
        return "info"

    def show_message(
        self,
        text: str,
        duration: float = 3.0,
        priority: int = 3,
        level: str | None = None,
    ) -> None:
        """Show a transient message.

        Skipped if a higher-priority message is currently displayed.

        *level* is ``"info"``, ``"error"``, or ``"success"`` — controls the
        display colour and is stored in the message history.

        If *level* is ``None`` (default), it is auto-detected from the message
        text using keyword matching.
        """
        if priority < self._priority:
            return
        if level is None:
            level = self._detect_level(text)
        self._last_level = level
        self.message_history.append(MessageEntry(text, time.time(), level))
        self._write_message(text, priority)
        self.set_timer(duration, self._clear_message)

    def set_persistent_message(self, text: str, priority: int = 2) -> None:
        """Show a message with no auto-clear timer (for prompts).

        Skipped if a higher-priority message is currently displayed.
        Pass empty string + appropriate priority to clear.
        """
        if text and priority < self._priority:
            return
        self._write_message(text, priority)

    def _write_message(self, text: str, priority: int = 3) -> None:
        """Write text to the message widget and update priority."""
        self._priority = priority if text else 0
        self.message = text
        with contextlib.suppress(Exception):
            msg = self.query_one("#status-message", Static)
            color = (
                "red"
                if self._last_level == "error"
                else "green"
                if self._last_level == "success"
                else "yellow"
            )
            msg.styles.color = color
            msg.update(text)

    def _clear_message(self) -> None:
        """Auto-clear timer callback — skip if a higher-priority message is active."""
        if self._priority > 3:
            return
        self._write_message("")

    def update_cursor(self, row: int, col: int, address: str) -> None:
        """Convenience method to update all cursor-position fields."""
        self.row = row
        self.col = col
        self.cell_address = address
