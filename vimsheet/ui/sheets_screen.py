"""Sheet list overlay — shown by :sl / :sheets / :sheet list."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from vimsheet.ui.vim_modal import VimModalScreen

if TYPE_CHECKING:
    from vimsheet.model.workbook import Workbook


def _sheet_line(idx: int, name: str, active_idx: int, rows: int, cols: int) -> str:
    active = "%" if idx == active_idx else " "
    return f" {idx + 1:3d} {active}  {name}  ({rows}×{cols})"


class SheetsScreen(VimModalScreen):
    """Modal overlay listing all sheets in the active workbook."""

    DEFAULT_CSS = """
    SheetsScreen {
        align: center middle;
    }
    SheetsScreen > VerticalScroll {
        width: 64%;
        height: 60%;
        background: $surface;
        border: round $primary;
        padding: 1 2;
    }
    SheetsScreen > VerticalScroll > Static {
        width: auto;
    }
    """

    def __init__(self, workbook: Workbook, active_idx: int) -> None:
        super().__init__()
        self._workbook = workbook
        self._active_idx = active_idx

    def compose(self) -> ComposeResult:
        header = " Num  A  Name  (rows×cols)\n" + "─" * 50
        rows = "\n".join(
            _sheet_line(i, s.name, self._active_idx, s.max_row + 1, s.max_col + 1)
            for i, s in enumerate(self._workbook.sheets)
        )
        footer = "\n" + "─" * 50 + "\n [q/Esc] close   [:sheet <name>] switch"
        with VerticalScroll():
            yield Static(f"{header}\n{rows}{footer}")
