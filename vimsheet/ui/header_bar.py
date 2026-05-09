"""Header bar — app name and version at the top of the UI."""

from __future__ import annotations

from textual.widgets import Static

from vimsheet import __version__


class HeaderBar(Static):
    """One-line header showing "VimSheet <version>" (left-aligned, subtle)."""

    DEFAULT_CSS = """
    HeaderBar {
        height: 1;
        background: $surface;
        color: $text-disabled;
        content-align: left middle;
        padding: 0 2;
    }
    """

    def __init__(self, **kwargs: object) -> None:
        super().__init__(f"VimSheet {__version__}", **kwargs)
