"""Full-screen help overlay for PySheet."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from pysheet.ui.vim_modal import VimModalScreen

_HELP_TEXT = """\
[bold cyan]NORMAL MODE[/bold cyan]
  h / j / k / l          Move cursor left/down/up/right
  Arrow keys              Move cursor
  gg / G                  Jump to first / last row
  0 / $                   Jump to start / end of row
  w / b                   Jump right / left to next non-empty block
  Ctrl+↓/↑/→/←           Jump to next non-empty block in direction
  Ctrl+d / Ctrl+u         Half-page down / up
  Ctrl+f / Ctrl+b         Page down / up
  H / M / L               Top / Middle / Bottom of visible rows
  nG                      Go to row n  (e.g. 10G)

[bold cyan]EDITING[/bold cyan]
  =                       Insert mode (right-align)
  \\ / > / <              Insert mode (left / right / default align)
  e / E                   Edit cell (cursor at end / start)
  x                       Clear cell
  dd / yy / p             Delete row / yank / paste
  u / Ctrl+r              Undo / Redo

[bold cyan]ROWS & COLUMNS[/bold cyan]
  ir / iR                 Insert row above / below
  ic / iC                 Insert column left / right
  dr / dc                 Delete row / column
  + / - / _               Widen / narrow / auto-fit column

[bold cyan]VISUAL MODE[/bold cyan]
  v / V / Ctrl+v          Enter visual (cell / row / block)
  y / d / x               Yank / delete / clear selection
  = / s                   Fill / sort selection
  f b/i/u/l/r/c           Format selection

[bold cyan]MARKS & SEARCH[/bold cyan]
  m<a-z>                  Set mark
  '<a-z>                  Jump to mark
  / pattern               Search forward
  ? pattern               Search backward
  n / N                   Next / previous match
  *                       Search for current cell value

[bold cyan]COMMAND MODE  (:)[/bold cyan]
  :w <file>               Save
  :e <file>               Open file
  :ex <fmt> <file>        Export (csv/tsv/json/xlsx/mkd/tex/html)
  :sort A asc             Sort by column
  :filter A gt 10         Filter rows
  :clearfilter            Clear filter
  :find / :replace        Find / replace
  :freeze row N           Freeze rows
  :name <id> <range>      Named range
  :plot <type> [range]    Plot chart (bar/line/scatter/pie/histogram)
  :func <NAME> <script>   Register script function
  :format <cell> …        Format cell
  :cond <range> …         Conditional format
  :newsheet / :delsheet   Add / remove sheet
  :load theme <name>      Change theme (dracula/light/gruvbox/nord)
  :help                   Show this screen
  :q / :q! / ZZ / ZQ     Quit

[bold cyan]MACROS[/bold cyan]
  q<a-z>                  Start recording macro
  q                       Stop recording
  @<a-z>                  Replay macro
  "<a-z>y / "<a-z>p       Yank / paste to/from named register

[dim]Press q, Escape, or Space to close[/dim]
"""


class HelpScreen(VimModalScreen):
    """Modal overlay displaying key bindings."""

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
        with VerticalScroll():
            yield Static(_HELP_TEXT, markup=True)

