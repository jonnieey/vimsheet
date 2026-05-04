"""Full-screen help overlay for VimSheet — content auto-generated from registry."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from vimsheet.ui.vim_modal import VimModalScreen


class HelpScreen(VimModalScreen):
    """Modal overlay displaying key bindings and formula functions."""

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
    }
    HelpScreen > VerticalScroll {
        width: 84%;
        height: 92%;
        background: $surface;
        border: round $primary;
        padding: 1 2;
    }
    HelpScreen > VerticalScroll > Static {
        width: auto;
    }
    """

    def compose(self) -> ComposeResult:
        from vimsheet.help_registry import build_help_text

        with VerticalScroll():
            yield Static(build_help_text(), markup=True)
