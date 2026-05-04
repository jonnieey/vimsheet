"""Buffer list overlay — shown by :buffers / :bufs / :ls."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from vimsheet.ui.vim_modal import VimModalScreen

if TYPE_CHECKING:
    from vimsheet.model.workbook import Workbook


def _buf_line(idx: int, wb: Workbook, active_idx: int) -> str:
    active = "%" if idx == active_idx else " "
    modified = "+" if wb.modified else " "
    name = str(wb.filepath) if wb.filepath else "[No Name]"
    sheets = len(wb.sheets)
    sheet_info = f"{sheets} sheet{'s' if sheets != 1 else ''}"
    return f" {idx + 1:3d} {active}{modified}  {name}  ({sheet_info})"


class BuffersScreen(VimModalScreen):
    """Modal overlay listing all open buffers."""

    DEFAULT_CSS = """
    BuffersScreen {
        align: center middle;
    }
    BuffersScreen > VerticalScroll {
        width: 72%;
        height: 60%;
        background: $surface;
        border: round $primary;
        padding: 1 2;
    }
    BuffersScreen > VerticalScroll > Static {
        width: auto;
    }
    """

    def __init__(self, buffers: list[Workbook], active_idx: int) -> None:
        super().__init__()
        self._buffers = buffers
        self._active_idx = active_idx

    def compose(self) -> ComposeResult:
        header = " Num  A+  Name\n" + "─" * 60
        rows = "\n".join(_buf_line(i, wb, self._active_idx) for i, wb in enumerate(self._buffers))
        footer = "\n" + "─" * 60 + "\n [q/Esc] close   [:buf N] switch   [:bd] close buffer"
        with VerticalScroll():
            yield Static(f"{header}\n{rows}{footer}")
