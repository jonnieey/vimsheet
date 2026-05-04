"""Base class for all VimSheet modal screens with vim-style scroll bindings."""

from __future__ import annotations

from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import ModalScreen


class VimModalScreen(ModalScreen[None]):
    """ModalScreen with vim keybindings for scrolling the inner VerticalScroll."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("q", "dismiss", "Close"),
        Binding("j", "scroll_down_line", "↓", show=False),
        Binding("k", "scroll_up_line", "↑", show=False),
        Binding("d", "scroll_down_half", "½↓", show=False),
        Binding("u", "scroll_up_half", "½↑", show=False),
        Binding("ctrl+d", "scroll_down_half", "½↓", show=False),
        Binding("ctrl+u", "scroll_up_half", "½↑", show=False),
        Binding("ctrl+f", "scroll_down_page", "↓↓", show=False),
        Binding("ctrl+b", "scroll_up_page", "↑↑", show=False),
        Binding("space", "scroll_down_page", "↓↓", show=False),
        Binding("g", "scroll_top", "⇈", show=False),
        Binding("G", "scroll_bottom", "⇊", show=False),
    ]

    def _scroller(self) -> VerticalScroll | None:
        try:
            return self.query_one(VerticalScroll)
        except Exception:
            return None

    def action_scroll_down_line(self) -> None:
        vs = self._scroller()
        if vs:
            vs.scroll_down(animate=False)

    def action_scroll_up_line(self) -> None:
        vs = self._scroller()
        if vs:
            vs.scroll_up(animate=False)

    def action_scroll_down_half(self) -> None:
        vs = self._scroller()
        if vs:
            vs.scroll_down(vs.size.height // 2, animate=False)

    def action_scroll_up_half(self) -> None:
        vs = self._scroller()
        if vs:
            vs.scroll_up(vs.size.height // 2, animate=False)

    def action_scroll_down_page(self) -> None:
        vs = self._scroller()
        if vs:
            vs.scroll_page_down(animate=False)

    def action_scroll_up_page(self) -> None:
        vs = self._scroller()
        if vs:
            vs.scroll_page_up(animate=False)

    def action_scroll_top(self) -> None:
        vs = self._scroller()
        if vs:
            vs.scroll_home(animate=False)

    def action_scroll_bottom(self) -> None:
        vs = self._scroller()
        if vs:
            vs.scroll_end(animate=False)
