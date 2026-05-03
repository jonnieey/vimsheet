"""GridWidget — virtual-scrolling spreadsheet grid."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rich.segment import Segment
from rich.style import Style
from textual.geometry import Size
from textual.message import Message
from textual.reactive import reactive
from textual.scroll_view import ScrollView
from textual.strip import Strip

from pysheet.controller.mode import Mode
from pysheet.model.range import CellRange, col_index_to_letters
from pysheet.model.sheet import Sheet

if TYPE_CHECKING:
    from pysheet.model.workbook import Workbook

ROW_HEADER_WIDTH = 6
DEFAULT_COL_WIDTH = 10


class GridWidget(ScrollView):
    """Virtual-scrolling spreadsheet grid.

    The column-header row is *frozen* at viewport y=0 regardless of scroll
    position. Data rows start at viewport y=1.
    """

    # Suppress all ScrollView default bindings so our App.on_key gets clean events.
    BINDINGS = []  # type: ignore[assignment]

    DEFAULT_CSS = """
    GridWidget {
        background: $surface;
        border: none;
        height: 1fr;
        scrollbar-size-horizontal: 0;
        scrollbar-size-vertical: 1;
    }
    """

    # -----------------------------------------------------------------------
    # Messages
    # -----------------------------------------------------------------------

    class CursorMoved(Message):
        """Emitted whenever the cursor row/col changes."""

        def __init__(self, row: int, col: int) -> None:
            super().__init__()
            self.row = row
            self.col = col

    # -----------------------------------------------------------------------
    # State
    # -----------------------------------------------------------------------

    cursor_row: reactive[int] = reactive(0)
    cursor_col: reactive[int] = reactive(0)
    mode: reactive[Mode] = reactive(Mode.NORMAL)
    visual_anchor_row: reactive[int] = reactive(0)
    visual_anchor_col: reactive[int] = reactive(0)

    def __init__(self, workbook: Workbook, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.workbook = workbook

    def on_mount(self) -> None:
        w = ROW_HEADER_WIDTH + sum(self.get_col_width(c) + 1 for c in range(26))
        h = max(self.sheet.max_row + 200, 1000)
        self.virtual_size = Size(w, h)

    # -----------------------------------------------------------------------
    # Shortcuts
    # -----------------------------------------------------------------------

    @property
    def sheet(self) -> Sheet:
        return self.workbook.active_sheet

    def get_col_width(self, col: int) -> int:
        return self.sheet.col_widths.get(col, DEFAULT_COL_WIDTH)

    # -----------------------------------------------------------------------
    # Virtual size — header is frozen, so virtual height = data rows only
    # -----------------------------------------------------------------------

    def get_content_width(self, container: Size, viewport: Size) -> int:
        max_col = max(self.sheet.max_col, self.cursor_col, 25)
        total = ROW_HEADER_WIDTH
        for c in range(max_col + 1):
            total += self.get_col_width(c) + 1  # +1 for column divider
        return total

    def get_content_height(self, container: Size, viewport: Size, width: int) -> int:
        # Virtual height covers only data rows (header is painted at y=0 always).
        return max(self.sheet.max_row, self.cursor_row, 99) + 3

    # -----------------------------------------------------------------------
    # Rendering
    # -----------------------------------------------------------------------

    def render_line(self, y: int) -> Strip:
        """Render viewport line *y* (0 = frozen column-header row)."""
        scroll_x = int(self.scroll_offset.x)
        width = self.size.width

        if y == 0:
            # Frozen header — not affected by vertical scroll
            return self._render_header_row(scroll_x, width)

        # Data rows: y=1 shows data_row scroll_y, y=2 shows scroll_y+1, etc.
        scroll_y = int(self.scroll_offset.y)
        data_row = (y - 1) + scroll_y
        return self._render_data_row(data_row, scroll_x, width)

    def _render_header_row(self, scroll_x: int, width: int) -> Strip:
        hdr = Style(bgcolor="grey23", color="grey74", bold=True)
        div = Style(bgcolor="grey23", color="grey35")
        # Corner cell — always pinned at left regardless of horizontal scroll
        corner = Strip([Segment(" " * ROW_HEADER_WIDTH, hdr)])
        data_width = width - ROW_HEADER_WIDTH
        segs: list[Segment] = []
        x = 0
        col = 0
        while x < scroll_x + data_width:
            cw = self.get_col_width(col)
            if col not in self.sheet.hidden_cols:
                label = col_index_to_letters(col).center(cw)
                segs.append(Segment(label[:cw], hdr))
                segs.append(Segment("│", div))
            x += cw + 1
            col += 1
            if col > 702:
                break
        return corner + Strip(segs).crop(scroll_x, scroll_x + data_width)

    def _render_data_row(self, row: int, scroll_x: int, width: int) -> Strip:
        is_cursor_row = row == self.cursor_row
        is_hidden = row in self.sheet.hidden_rows
        freeze_rows = self.sheet.freeze_rows

        # Frozen-row separator: a visible divider after the last frozen row
        if freeze_rows > 0 and row == freeze_rows and not is_hidden:
            sep_style = Style(bgcolor="steel_blue3", color="steel_blue3")
            return Strip([Segment("─" * width, sep_style)])

        is_frozen_row = freeze_rows > 0 and row < freeze_rows
        row_hdr_style = Style(bgcolor="grey23", color="grey62")
        if is_cursor_row:
            row_hdr_style = Style(bgcolor="steel_blue", color="white", bold=True)
        elif is_frozen_row:
            row_hdr_style = Style(bgcolor="grey27", color="grey82", bold=True)

        # Show fold indicator when this row is the start of a group
        fold_indicator = self._fold_indicator(row)
        row_label = str(row + 1).rjust(ROW_HEADER_WIDTH - 2) + fold_indicator + " "

        # Row number — always pinned at left regardless of horizontal scroll
        row_hdr_strip = Strip([Segment(row_label, row_hdr_style)])
        data_width = width - ROW_HEADER_WIDTH

        if is_hidden:
            hidden_label = "…" + " " * (ROW_HEADER_WIDTH - 1)
            return Strip([Segment(hidden_label, row_hdr_style)]) + Strip(
                [Segment(" " * data_width)]
            )

        segs: list[Segment] = []
        x = 0
        freeze_cols = self.sheet.freeze_cols
        col = 0
        while x < scroll_x + data_width:
            cw = self.get_col_width(col)
            if col in self.sheet.hidden_cols:
                x += cw
                col += 1
                continue
            # Frozen-col separator: insert a divider segment after last frozen col
            if freeze_cols > 0 and col == freeze_cols:
                segs.append(Segment("│", Style(color="steel_blue3", bgcolor=None)))
            cell = self.sheet.get_cell(row, col)
            text = (cell.display or "") if cell else ""
            style = self._cell_style(row, col, cell)
            # Slightly dimmer background for frozen cells (not cursor, not selected)
            if freeze_cols > 0 and col < freeze_cols and not is_cursor_row:
                from pysheet.model.cell import Cell as _CT

                if not isinstance(cell, _CT) or (cell.fmt.bg_color is None):
                    style = style + Style(bgcolor="grey11")
            if len(text) > cw - 1:
                text = text[: cw - 2] + "…"
            align = cell.fmt.align if cell else "right"
            if align == "center":
                text = text.center(cw)
            elif align == "left":
                text = text.ljust(cw)
            else:
                text = text.rjust(cw)
            segs.append(Segment(text, style))
            # Column divider (1 char wide, neutral colour)
            div_bg = "grey19" if row % 2 == 1 else None
            segs.append(Segment("│", Style(color="grey30", bgcolor=div_bg)))
            x += cw + 1
            col += 1
            if col > 702:
                break
        return row_hdr_strip + Strip(segs).crop(scroll_x, scroll_x + data_width)

    def _cell_style(self, row: int, col: int, cell: object) -> Style:
        from pysheet.model.cell import Cell as CellType

        is_cursor = row == self.cursor_row and col == self.cursor_col
        in_visual = self._in_visual_selection(row, col)

        if is_cursor:
            return Style(bgcolor="steel_blue1", color="white", bold=True)
        if in_visual:
            return Style(bgcolor="slate_blue1", color="white")

        bg = fg = None
        bold = italic = underline = False

        if isinstance(cell, CellType):
            fmt = cell.fmt
            bold, italic, underline = fmt.bold, fmt.italic, fmt.underline
            fg, bg = fmt.fg_color, fmt.bg_color
            for rule in self.sheet.cond_formats:
                try:
                    cr = CellRange.from_a1(rule.range_str)
                except ValueError:
                    continue
                if cr.contains(row, col) and rule.matches(cell.value):
                    if rule.fmt.bg_color:
                        bg = rule.fmt.bg_color
                    if rule.fmt.fg_color:
                        fg = rule.fmt.fg_color
                    if rule.fmt.bold:
                        bold = True
            if isinstance(cell.value, str) and cell.value.startswith("#"):
                fg = "red"

        style = Style(
            bold=bold or None,
            italic=italic or None,
            underline=underline or None,
            color=fg,
            bgcolor=bg,
        )
        if bg is None and row % 2 == 1:
            style = style + Style(bgcolor="grey19")
        return style

    def _fold_indicator(self, row: int) -> str:
        """Return a 1-char fold indicator for the row header."""
        for r1, r2 in self.sheet.row_groups:
            if row == r1:
                rows_hidden = any(r in self.sheet.hidden_rows for r in range(r1, r2 + 1))
                return "▶" if rows_hidden else "▼"
        return " "

    def _in_visual_selection(self, row: int, col: int) -> bool:
        if not self.mode.is_visual():
            return False
        r1 = min(self.visual_anchor_row, self.cursor_row)
        r2 = max(self.visual_anchor_row, self.cursor_row)
        c1 = min(self.visual_anchor_col, self.cursor_col)
        c2 = max(self.visual_anchor_col, self.cursor_col)
        match self.mode:
            case Mode.VISUAL_LINE:
                return r1 <= row <= r2
            case _:
                return r1 <= row <= r2 and c1 <= col <= c2

    # -----------------------------------------------------------------------
    # Cursor movement
    # -----------------------------------------------------------------------

    def move_cursor(self, row: int, col: int) -> None:
        row = max(0, row)
        col = max(0, col)
        self.cursor_row = row
        self.cursor_col = col
        # Expand virtual space so scroll_to() isn't clamped at initial boundary
        min_height = row + 200
        if min_height > self.virtual_size.height:
            self.virtual_size = Size(self.virtual_size.width, min_height)
        # Expand horizontal virtual space if needed
        x = ROW_HEADER_WIDTH
        for c in range(col + 1):
            x += self.get_col_width(c)
        min_width = x + 100
        if min_width > self.virtual_size.width:
            self.virtual_size = Size(min_width, self.virtual_size.height)
        self._scroll_cursor_into_view()
        self.post_message(self.CursorMoved(row, col))
        self.refresh()

    def move_by(self, drow: int, dcol: int) -> None:
        self.move_cursor(self.cursor_row + drow, self.cursor_col + dcol)

    def move_to_row_start(self) -> None:
        self.move_cursor(self.cursor_row, 0)

    def move_to_first_nonempty_in_row(self) -> None:
        r = self.cursor_row
        mx = self.sheet.max_col
        for c in range(mx + 1):
            if self.sheet.get_cell(r, c) is not None:
                self.move_cursor(r, c)
                return
        self.move_cursor(r, 0)

    def move_to_row_end(self) -> None:
        last = 0
        for r, c in self.sheet.cells:
            if r == self.cursor_row:
                last = max(last, c)
        self.move_cursor(self.cursor_row, last)

    def move_to_first_row(self) -> None:
        self.move_cursor(0, self.cursor_col)

    def move_to_last_row(self) -> None:
        self.move_cursor(self.sheet.max_row, self.cursor_col)

    def move_to_first_cell(self) -> None:
        self.move_cursor(0, 0)

    def move_to_last_cell(self) -> None:
        self.move_cursor(self.sheet.max_row, self.sheet.max_col)

    def jump_next_nonempty_right(self) -> None:
        r, c = self.cursor_row, self.cursor_col
        mx = self.sheet.max_col
        while c <= mx and self.sheet.get_cell(r, c) is not None:
            c += 1
        while c <= mx and self.sheet.get_cell(r, c) is None:
            c += 1
        self.move_cursor(r, min(c, mx))

    def jump_next_nonempty_left(self) -> None:
        r, c = self.cursor_row, self.cursor_col - 1
        while c >= 0 and self.sheet.get_cell(r, c) is None:
            c -= 1
        while c > 0 and self.sheet.get_cell(r, c - 1) is not None:
            c -= 1
        self.move_cursor(r, max(c, 0))

    def jump_next_nonempty_down(self) -> None:
        r, c = self.cursor_row, self.cursor_col
        mx = self.sheet.max_row
        while r <= mx and self.sheet.get_cell(r, c) is not None:
            r += 1
        while r <= mx and self.sheet.get_cell(r, c) is None:
            r += 1
        self.move_cursor(min(r, mx), c)

    def jump_next_nonempty_up(self) -> None:
        r, c = self.cursor_row - 1, self.cursor_col
        while r >= 0 and self.sheet.get_cell(r, c) is None:
            r -= 1
        while r > 0 and self.sheet.get_cell(r - 1, c) is not None:
            r -= 1
        self.move_cursor(max(r, 0), c)

    def page_down(self) -> None:
        self.move_cursor(self.cursor_row + max(1, self.size.height - 2), self.cursor_col)

    def page_up(self) -> None:
        self.move_cursor(max(0, self.cursor_row - max(1, self.size.height - 2)), self.cursor_col)

    def half_page_down(self) -> None:
        self.move_cursor(self.cursor_row + max(1, (self.size.height - 2) // 2), self.cursor_col)

    def half_page_up(self) -> None:
        self.move_cursor(
            max(0, self.cursor_row - max(1, (self.size.height - 2) // 2)), self.cursor_col
        )

    def go_to_visible_top(self) -> None:
        self.move_cursor(int(self.scroll_offset.y), self.cursor_col)

    def go_to_visible_middle(self) -> None:
        top = int(self.scroll_offset.y)
        self.move_cursor(top + (self.size.height - 2) // 2, self.cursor_col)

    def go_to_visible_bottom(self) -> None:
        top = int(self.scroll_offset.y)
        self.move_cursor(top + self.size.height - 3, self.cursor_col)

    # -----------------------------------------------------------------------
    # Visual selection
    # -----------------------------------------------------------------------

    def start_visual(self, mode: Mode) -> None:
        self.visual_anchor_row = self.cursor_row
        self.visual_anchor_col = self.cursor_col
        self.mode = mode

    def visual_selection(self) -> CellRange | None:
        if not self.mode.is_visual():
            return None
        r1 = min(self.visual_anchor_row, self.cursor_row)
        r2 = max(self.visual_anchor_row, self.cursor_row)
        c1 = min(self.visual_anchor_col, self.cursor_col)
        c2 = max(self.visual_anchor_col, self.cursor_col)
        match self.mode:
            case Mode.VISUAL_LINE:
                return CellRange(r1, 0, r2, max(self.sheet.max_col, 0))
            case _:
                return CellRange(r1, c1, r2, c2)

    # -----------------------------------------------------------------------
    # Scroll helper — frozen header means data area = height-1 rows
    # -----------------------------------------------------------------------

    def _scroll_cursor_into_view(self) -> None:
        scroll_y = int(self.scroll_offset.y)
        data_rows_visible = max(1, self.size.height - 1)  # subtract frozen header

        if self.cursor_row < scroll_y:
            self.scroll_to(y=self.cursor_row, animate=False)
        elif self.cursor_row >= scroll_y + data_rows_visible:
            self.scroll_to(y=self.cursor_row - data_rows_visible + 1, animate=False)

        # Horizontal (+1 per col for divider)
        x = ROW_HEADER_WIDTH
        for c in range(self.cursor_col):
            x += self.get_col_width(c) + 1
        cw = self.get_col_width(self.cursor_col)
        scroll_x = int(self.scroll_offset.x)
        vis_w = self.size.width
        if x < scroll_x + ROW_HEADER_WIDTH:
            self.scroll_to(x=max(0, x - ROW_HEADER_WIDTH), animate=False)
        elif x + cw > scroll_x + vis_w:
            self.scroll_to(x=x + cw - vis_w, animate=False)

    # -----------------------------------------------------------------------
    # Reactive watchers
    # -----------------------------------------------------------------------

    def watch_cursor_row(self, _v: int) -> None:
        self.refresh()

    def watch_cursor_col(self, _v: int) -> None:
        self.refresh()

    def watch_mode(self, _v: Mode) -> None:
        self.refresh()

    def refresh_grid(self) -> None:
        self.refresh()
