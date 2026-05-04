"""Sheet tab strip — rendered inline via Rich Text, scrollable via mouse wheel."""

from __future__ import annotations

from rich.style import Style
from rich.text import Text
from textual.events import Click
from textual.message import Message
from textual.widget import Widget


class SheetTabs(Widget):
    """Horizontal strip of clickable sheet tabs rendered as Rich text."""

    DEFAULT_CSS = """
    SheetTabs {
        height: 1;
        background: $panel;
    }
    """

    class SheetSelected(Message):
        def __init__(self, index: int) -> None:
            super().__init__()
            self.index = index

    class AddSheet(Message):
        pass

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._sheet_names: list[str] = []
        self._active_index: int = 0
        self._scroll_pos: int = 0
        self._tab_regions: list[tuple[int, int, int]] = []
        self._add_region: tuple[int, int] = (0, 3)

    def set_sheets(self, names: list[str], active: int) -> None:
        self._sheet_names = list(names)
        self._active_index = active
        if self._scroll_pos >= len(self._sheet_names):
            self._scroll_pos = max(0, len(self._sheet_names) - 1)
        if self._active_index < self._scroll_pos:
            self._scroll_pos = self._active_index
        self.refresh()

    def render(self) -> Text:
        width = self.size.width
        add_w = 3
        max_tabs_w = width - add_w

        self._tab_regions = []
        self._add_region = (0, add_w)
        result = Text()
        x = 0

        for i in range(self._scroll_pos, len(self._sheet_names)):
            name = self._sheet_names[i]
            tw = len(name) + 2
            if x + tw > max_tabs_w:
                break
            self._tab_regions.append((x, x + tw, i))
            x += tw
            if i == self._active_index:
                st = Style(bgcolor="#4488ff", color="#ffffff", bold=True)
            else:
                st = Style(bgcolor="#555555", color="#cccccc")
            result.append(f" {name} ", style=st)

        self._add_region = (x, x + add_w)
        result.append(" + ", style=Style(bgcolor="#777777", color="#ffffff", bold=True))
        return result

    def on_click(self, event: Click) -> None:
        x = event.x
        for start, end, idx in self._tab_regions:
            if start <= x < end:
                self.post_message(self.SheetSelected(idx))
                return
        if self._add_region[0] <= x < self._add_region[1]:
            self.post_message(self.AddSheet())

    def on_mouse_scroll_down(self, event: object) -> None:
        if self._scroll_pos < len(self._sheet_names) - 1:
            self._scroll_pos += 1
            self.refresh()

    def on_mouse_scroll_up(self, event: object) -> None:
        if self._scroll_pos > 0:
            self._scroll_pos -= 1
            self.refresh()
