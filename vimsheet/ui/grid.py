"""GridWidget — virtual-scrolling spreadsheet grid with variable row heights."""

from __future__ import annotations

import bisect
from typing import TYPE_CHECKING, Any

from rich.segment import Segment
from rich.style import Style
from textual.geometry import Size
from textual.message import Message
from textual.reactive import reactive
from textual.scroll_view import ScrollView
from textual.strip import Strip

from vimsheet.controller.mode import Mode
from vimsheet.model.range import CellRange, col_index_to_letters
from vimsheet.model.sheet import Sheet
from vimsheet.ui.grid_palette import GridPalette

if TYPE_CHECKING:
    from vimsheet.model.workbook import Workbook

ROW_HEADER_WIDTH = 6
DEFAULT_COL_WIDTH = 10


class GridWidget(ScrollView):
    """Virtual-scrolling spreadsheet grid.

    Each data row occupies a variable number of virtual lines based on the
    maximum newline count across all cells in that row.  A live preview
    override allows insert/edit mode to show uncommitted multi-line content.

    The column-header row is *frozen* at viewport y=0 regardless of scroll
    position.  Data rows start at viewport y=1.
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
    show_visual: reactive[bool] = reactive(False)

    def __init__(self, workbook: Workbook, config: Any = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.workbook = workbook
        self._config = config
        self._palette: GridPalette = GridPalette()

        # Variable row heights
        self._row_heights: list[int] = []
        self._total_virtual_lines: int = 0
        self._row_prefix: list[int] | None = None  # lazy prefix sum
        self._needs_height_rebuild: bool = True
        self._collapsed_rows: set[int] = set()

        # Live preview during insert/edit mode
        self._preview_row: int | None = None
        self._preview_col: int | None = None
        self._preview_text: str = ""

        # Search highlight state
        self._search_matches: list[tuple[int, int]] = []
        self._search_current_match: tuple[int, int] | None = None
        self._search_matches_set: set[tuple[int, int]] = set()
        self._search_pattern: str = ""

    def set_search_state(
        self, matches: list[tuple[int, int]], current: tuple[int, int] | None, pattern: str = ""
    ) -> None:
        self._search_matches = matches
        self._search_current_match = current
        self._search_matches_set = set(matches)
        self._search_pattern = pattern
        self.refresh()

    def on_mount(self) -> None:
        self._rebuild_heights()
        w = ROW_HEADER_WIDTH + sum(self.get_col_width(c) + 1 for c in range(26))
        self.virtual_size = Size(w, self._total_virtual_lines + 200)

    # -----------------------------------------------------------------------
    # Shortcuts
    # -----------------------------------------------------------------------

    @property
    def sheet(self) -> Sheet:
        return self.workbook.active_sheet

    def get_col_width(self, col: int) -> int:
        default_w = (
            self._config.default_col_width if self._config is not None else DEFAULT_COL_WIDTH
        )
        return self.sheet.col_widths.get(col, default_w)

    def update_config(self, config: Any) -> None:
        self._config = config
        self.refresh()

    def set_palette(self, palette: GridPalette) -> None:
        self._palette = palette
        self.refresh()

    # -----------------------------------------------------------------------
    # Variable row heights — public API
    # -----------------------------------------------------------------------

    def set_preview(self, row: int | None, col: int | None, text: str) -> None:
        self._preview_row = row
        self._preview_col = col
        self._preview_text = text

    def collapse_row(self, row: int) -> None:
        self._collapsed_rows.add(row)
        self._rebuild_heights()
        self.refresh()

    def expand_row(self, row: int) -> None:
        self._collapsed_rows.discard(row)
        self._rebuild_heights()
        self.refresh()

    def _rebuild_heights(self) -> None:
        max_data_row = max(self.sheet.max_row, self.cursor_row, 99)
        heights = []
        for r in range(max_data_row + 1):
            max_lines = 1
            if r <= self.sheet.max_row:
                for c in range(self.sheet.max_col + 1):
                    cell = self.sheet.get_cell(r, c)
                    text = (cell.display or "") if cell else ""
                    lines = text.count("\n") + 1
                    if lines > max_lines:
                        max_lines = lines
            # Live preview overrides the preview row's height
            if self._preview_row is not None and r == self._preview_row:
                preview_lines = self._preview_text.count("\n") + 1
                if preview_lines > max_lines:
                    max_lines = preview_lines
            if r in self._collapsed_rows:
                max_lines = 1
            if r in self.sheet.hidden_rows:
                max_lines = 0
            heights.append(max_lines)
        self._row_heights = heights
        self._total_virtual_lines = sum(heights)
        self._row_prefix = None  # invalidate

    def _get_prefix(self) -> list[int]:
        if self._row_prefix is None:
            prefix = [0]
            for h in self._row_heights:
                prefix.append(prefix[-1] + h)
            self._row_prefix = prefix
        return self._row_prefix

    def _row_virtual_y(self, row: int) -> int:
        return self._get_prefix()[row]

    def _virtual_y_to_row(self, vy: int) -> tuple[int, int]:
        prefix = self._get_prefix()
        idx = bisect.bisect_right(prefix, vy) - 1
        idx = max(0, min(idx, len(self._row_heights) - 1))
        sub = vy - prefix[idx]
        return (idx, sub)

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
        freeze_rows = self.sheet.freeze_rows
        prefix = self._get_prefix()
        frozen_height = prefix[freeze_rows] if freeze_rows > 0 else 0
        return max(1, self._total_virtual_lines + 1 - frozen_height)

    # -----------------------------------------------------------------------
    # Rendering
    # -----------------------------------------------------------------------

    def render_line(self, y: int) -> Strip:
        """Render viewport line *y* (0 = frozen column-header row)."""
        scroll_x = int(self.scroll_offset.x)
        width = self.size.width

        if y == 0:
            return self._render_header_row(scroll_x, width)

        freeze_rows = self.sheet.freeze_rows
        scroll_y = int(self.scroll_offset.y)
        prefix = self._get_prefix()
        frozen_height = prefix[freeze_rows] if freeze_rows > 0 else 0

        if freeze_rows > 0:
            if y - 1 < frozen_height:
                virtual_y = y - 1
            elif y - 1 == frozen_height:
                row_hdr = Segment(
                    " " * ROW_HEADER_WIDTH,
                    Style(bgcolor=self._palette.frozen_header_bg),
                )
                data_sep = Segment(
                    "─" * (width - ROW_HEADER_WIDTH),
                    Style(color=self._palette.frozen_sep),
                )
                return Strip([row_hdr]) + Strip([data_sep])
            else:
                virtual_y = (y - 1 - 1) + scroll_y
        else:
            virtual_y = (y - 1) + scroll_y

        data_row, sub_line = self._virtual_y_to_row(virtual_y)
        return self._render_data_row(data_row, scroll_x, width, sub_line=sub_line)

    def _render_header_row(self, scroll_x: int, width: int) -> Strip:
        if self._config is not None and not self._config.show_col_headers:
            return Strip([Segment(" " * width)])
        hdr = Style(bgcolor=self._palette.header_bg, color=self._palette.header_fg, bold=True)
        div = Style(bgcolor=self._palette.header_bg, color=self._palette.header_divider)
        corner = Strip([Segment(" " * ROW_HEADER_WIDTH, hdr)])
        data_width = width - ROW_HEADER_WIDTH
        freeze_cols = self.sheet.freeze_cols

        frozen_segs: list[Segment] = []
        frozen_width = 0
        col = 0
        while col < freeze_cols:
            cw = self.get_col_width(col)
            if col not in self.sheet.hidden_cols:
                label = col_index_to_letters(col).center(cw)
                # Column group fold indicator
                for c1, c2 in self.sheet.col_groups:
                    if col == c1:
                        hidden = any(c in self.sheet.hidden_cols for c in range(c1, c2 + 1))
                        label = label[:-1] + ("▶" if hidden else "▼")
                        break
                frozen_segs.append(Segment(label[:cw], hdr))
                frozen_segs.append(Segment("│", div))
            if col not in self.sheet.hidden_cols:
                frozen_width += cw + 1
            col += 1

        scrollable_segs: list[Segment] = []
        x = 0
        while x < max(0, scroll_x - frozen_width) + data_width - frozen_width:
            cw = self.get_col_width(col)
            if col not in self.sheet.hidden_cols:
                label = col_index_to_letters(col).center(cw)
                # Column group fold indicator
                for c1, c2 in self.sheet.col_groups:
                    if col == c1:
                        hidden = any(c in self.sheet.hidden_cols for c in range(c1, c2 + 1))
                        label = label[:-1] + ("▶" if hidden else "▼")
                        break
                scrollable_segs.append(Segment(label[:cw], hdr))
                no_lines = self._config is not None and not self._config.show_grid_lines
                div_char = " " if no_lines else "│"
                scrollable_segs.append(Segment(div_char, div))
            if col not in self.sheet.hidden_cols:
                x += cw + 1
            col += 1
            if col > 702:
                break
        crop_start = max(0, scroll_x - frozen_width)
        crop_end = crop_start + data_width - frozen_width
        return corner + Strip(frozen_segs) + Strip(scrollable_segs).crop(crop_start, crop_end)

    def _cell_display_text(self, row: int, col: int, sub_line: int) -> str:
        """Return the text to display for one cell at a given sub-line."""
        if self._preview_row is not None and row == self._preview_row and col == self._preview_col:
            text = self._preview_text
        else:
            cell = self.sheet.get_cell(row, col)
            text = (cell.display or "") if cell else ""
        lines = text.split("\n")
        result = lines[sub_line] if sub_line < len(lines) else ""
        if row in self._collapsed_rows and len(lines) > 1:
            result += "…"
        return result

    def _render_data_row(self, row: int, scroll_x: int, width: int, sub_line: int = 0) -> Strip:
        is_cursor_row = row == self.cursor_row
        is_hidden = row in self.sheet.hidden_rows
        freeze_rows = self.sheet.freeze_rows

        is_frozen_row = freeze_rows > 0 and row < freeze_rows

        if sub_line == 0:
            row_hdr_style = Style(bgcolor=self._palette.header_bg, color=self._palette.header_fg)
            if is_cursor_row:
                row_hdr_style = Style(
                    bgcolor=self._palette.cursor_header_bg,
                    color=self._palette.cursor_header_fg,
                    bold=True,
                )
            elif is_frozen_row:
                row_hdr_style = Style(
                    bgcolor=self._palette.frozen_header_bg,
                    color=self._palette.header_fg,
                    bold=True,
                )
            fold_indicator = self._fold_indicator(row)
            row_label = str(row + 1).rjust(ROW_HEADER_WIDTH - 2) + fold_indicator + " "
            if self._config is not None and not self._config.show_row_headers:
                row_label = " " * ROW_HEADER_WIDTH
                row_hdr_style = Style()
            row_hdr_strip = Strip([Segment(row_label, row_hdr_style)])
        else:
            # Continuation header: blank but same bgcolor
            cont_style = Style(bgcolor=self._palette.header_bg)
            if is_cursor_row:
                cont_style = Style(bgcolor=self._palette.cursor_header_bg)
            elif is_frozen_row:
                cont_style = Style(bgcolor=self._palette.frozen_header_bg)
            row_hdr_strip = Strip([Segment(" " * ROW_HEADER_WIDTH, cont_style)])

        data_width = width - ROW_HEADER_WIDTH

        if is_hidden:
            hdr = Style(bgcolor=self._palette.header_bg, color=self._palette.frozen_sep)
            label = str(row + 1).rjust(ROW_HEADER_WIDTH - 2) + " " + self._fold_indicator(row) + " "
            return Strip([Segment(label, hdr)]) + Strip([Segment(" " * data_width)])

        freeze_cols = self.sheet.freeze_cols

        # Helper: build one cell's segments (text + divider) into a list
        def _cell_segments(dest: list[Segment], row: int, col: int, cw: int) -> None:
            raw = self._cell_display_text(row, col, sub_line)
            style = self._cell_style(row, col, self.sheet.get_cell(row, col))
            has_more = row in self._collapsed_rows and raw.endswith("…")
            if has_more:
                raw = raw[:-1]
            if len(raw) > cw - 1:
                raw = raw[: cw - 2] + "…"
            effective_cw = cw - 1 if has_more else cw

            # Word-level search match highlight
            pat = self._search_pattern
            p = -1
            is_match = (row, col) in self._search_matches_set
            if pat and is_match:
                p = raw.lower().find(pat.lower())
            if p != -1:
                m_end = p + len(pat)
                hl_bg = (
                    self._palette.search_current_bg
                    if self._search_current_match == (row, col)
                    else self._palette.search_highlight_bg
                )
                hl_style = Style(color=self._palette.search_highlight_fg, bgcolor=hl_bg)

                before_part = raw[:p]
                match_part = raw[p:m_end]
                after_part = raw[m_end:]
                text_width = len(before_part) + len(match_part) + len(after_part)
                pad = effective_cw - text_width

                cell = self.sheet.get_cell(row, col)
                align = cell.fmt.align if cell else "right"
                left_pad = pad if align == "left" else (pad // 2 if align == "center" else 0)
                right_pad = pad - left_pad

                if left_pad:
                    dest.append(Segment(" " * left_pad, style))
                if before_part:
                    dest.append(Segment(before_part, style))
                dest.append(Segment(match_part, hl_style))
                if after_part:
                    dest.append(Segment(after_part, style))
                if right_pad:
                    dest.append(Segment(" " * right_pad, style))
            else:
                cell = self.sheet.get_cell(row, col)
                align = cell.fmt.align if cell else "right"
                if align == "center":
                    raw = raw.center(effective_cw)
                elif align == "left":
                    raw = raw.ljust(effective_cw)
                else:
                    raw = raw.rjust(effective_cw)
                dest.append(Segment(raw, style))
            if has_more:
                dest.append(Segment("…", Style(color=self._palette.collapsed_fg)))
            div_bg = self._palette.alt_row_bg if row % 2 == 1 else None
            no_lines = self._config is not None and not self._config.show_grid_lines
            divider = " " if no_lines else "│"
            divider_style = (
                Style() if no_lines else Style(color=self._palette.gridline, bgcolor=div_bg)
            )
            dest.append(Segment(divider, divider_style))

        # Compute frozen columns pixel width (visible columns only)
        frozen_width = 0
        for c in range(freeze_cols):
            if c not in self.sheet.hidden_cols:
                frozen_width += self.get_col_width(c) + 1

        # Build frozen column segments (cols 0..freeze_cols-1)
        frozen_segs: list[Segment] = []
        for c in range(freeze_cols):
            if c in self.sheet.hidden_cols:
                continue
            cw = self.get_col_width(c)
            _cell_segments(frozen_segs, row, c, cw)
        # Frozen separator
        if freeze_cols > 0:
            frozen_segs.append(Segment("│", Style(color=self._palette.frozen_sep, bgcolor=None)))

        # Build scrollable column segments
        scrollable_segs: list[Segment] = []
        col = freeze_cols
        sx = 0
        while sx < max(0, scroll_x - frozen_width) + data_width - frozen_width:
            cw = self.get_col_width(col)
            if col in self.sheet.hidden_cols:
                col += 1
                continue
            _cell_segments(scrollable_segs, row, col, cw)
            sx += cw + 1
            col += 1
            if col > 702:
                break

        crop_start = max(0, scroll_x - frozen_width)
        crop_end = crop_start + data_width - frozen_width
        return (
            row_hdr_strip + Strip(frozen_segs) + Strip(scrollable_segs).crop(crop_start, crop_end)
        )

    def _cell_style(self, row: int, col: int, cell: object) -> Style:
        from vimsheet.model.cell import Cell as CellType

        is_cursor = row == self.cursor_row and col == self.cursor_col
        in_visual = self._in_visual_selection(row, col)

        if is_cursor:
            return Style(
                bgcolor=self._palette.cursor_cell_bg, color=self._palette.cursor_cell_fg, bold=True
            )
        if in_visual:
            return Style(bgcolor=self._palette.visual_sel_bg, color=self._palette.visual_sel_fg)

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
                fg = self._palette.error_fg

        freeze_rows = self.sheet.freeze_rows
        freeze_cols = self.sheet.freeze_cols

        # Frozen zone text — use dedicated fg for contrast
        if (
            fg is None
            and freeze_rows > 0
            and row < freeze_rows
            and freeze_cols > 0
            and col < freeze_cols
        ):
            fg = self._palette.frozen_cell_fg

        # Frozen zone bg — only in the intersection of frozen rows + columns
        if bg is None:
            freeze_rows = self.sheet.freeze_rows
            freeze_cols = self.sheet.freeze_cols
            if freeze_rows > 0 and row < freeze_rows and freeze_cols > 0 and col < freeze_cols:
                bg = self._palette.frozen_cell_bg

        style = Style(
            bold=bold or None,
            italic=italic or None,
            underline=underline or None,
            color=fg,
            bgcolor=bg,
        )
        if bg is None and row % 2 == 1:
            style = style + Style(bgcolor=self._palette.alt_row_bg)
        return style

    def _fold_indicator(self, row: int) -> str:
        for r1, r2 in self.sheet.row_groups:
            if row == r1:
                rows_hidden = any(r in self.sheet.hidden_rows for r in range(r1, r2 + 1))
                return "▶" if rows_hidden else "▼"
        return "…" if row in self._collapsed_rows else " "

    def _in_visual_selection(self, row: int, col: int) -> bool:
        if not (self.mode.is_visual() or self.show_visual):
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
        # Skip hidden columns — find nearest visible column in movement direction
        hidden = self.sheet.hidden_cols
        if col in hidden:
            dr = 1 if col >= self.cursor_col else -1
            for d in (dr, -dr):
                found = -1
                c = col
                while 0 <= c <= self.sheet.max_col:
                    c += d
                    if 0 <= c <= self.sheet.max_col and c not in hidden:
                        found = c
                        break
                if found >= 0:
                    col = found
                    break
        self.cursor_row = row
        self.cursor_col = col
        self.sheet.cursor_row = row
        self.sheet.cursor_col = col
        min_height = self._row_virtual_y(row) + 200
        if min_height > self.virtual_size.height:
            self.virtual_size = Size(self.virtual_size.width, min_height)
        # Expand virtual width so scroll_x can reach the cursor
        hidden = self.sheet.hidden_cols
        x = ROW_HEADER_WIDTH
        for c in range(col + 1):
            if c not in hidden:
                x += self.get_col_width(c) + 1
        if x + 100 > self.virtual_size.width:
            self.virtual_size = Size(x + 100, self.virtual_size.height)
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
        freeze_rows = self.sheet.freeze_rows
        frozen_height = self._get_prefix()[freeze_rows] if freeze_rows > 0 else 0
        vy = frozen_height + int(self.scroll_offset.y)
        row, _ = self._virtual_y_to_row(vy)
        self.move_cursor(row, self.cursor_col)

    def go_to_visible_middle(self) -> None:
        freeze_rows = self.sheet.freeze_rows
        frozen_height = self._get_prefix()[freeze_rows] if freeze_rows > 0 else 0
        visible_data = max(1, self.size.height - frozen_height - 2)
        vy = frozen_height + int(self.scroll_offset.y) + visible_data // 2
        row, _ = self._virtual_y_to_row(vy)
        self.move_cursor(row, self.cursor_col)

    def go_to_visible_bottom(self) -> None:
        freeze_rows = self.sheet.freeze_rows
        frozen_height = self._get_prefix()[freeze_rows] if freeze_rows > 0 else 0
        visible_data = max(1, self.size.height - frozen_height - 2)
        vy = frozen_height + int(self.scroll_offset.y) + visible_data - 1
        row, _ = self._virtual_y_to_row(vy)
        self.move_cursor(row, self.cursor_col)

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
        virtual_y = self._row_virtual_y(self.cursor_row)
        scroll_y = int(self.scroll_offset.y)
        freeze_rows = self.sheet.freeze_rows
        prefix = self._get_prefix()
        frozen_height = prefix[freeze_rows] if freeze_rows > 0 else 0
        data_rows_visible = max(1, self.size.height - frozen_height - 2)

        if virtual_y < scroll_y + frozen_height:
            self.scroll_to(y=max(0, virtual_y - frozen_height), animate=False)
        elif virtual_y >= scroll_y + frozen_height + data_rows_visible:
            self.scroll_to(y=virtual_y - frozen_height - data_rows_visible + 1, animate=False)

        x = ROW_HEADER_WIDTH
        hidden = self.sheet.hidden_cols
        for c in range(self.cursor_col):
            if c not in hidden:
                x += self.get_col_width(c) + 1
        cw = self.get_col_width(self.cursor_col)
        scroll_x = int(self.scroll_offset.x)
        vis_w = self.size.width
        freeze_cols = self.sheet.freeze_cols
        frozen_width = sum(self.get_col_width(c) + 1 for c in range(freeze_cols) if c not in hidden)
        if x < scroll_x + ROW_HEADER_WIDTH:
            self.scroll_to(x=max(0, x - ROW_HEADER_WIDTH), animate=False)
        elif x + cw > scroll_x + vis_w - frozen_width:
            self.scroll_to(x=x + cw - (vis_w - frozen_width), animate=False)

    def scroll_cell_to_top(self) -> None:
        freeze_rows = self.sheet.freeze_rows
        frozen_height = self._get_prefix()[freeze_rows] if freeze_rows > 0 else 0
        self.scroll_to(
            y=max(0, self._row_virtual_y(self.cursor_row) - frozen_height), animate=False
        )

    def scroll_cell_to_center(self) -> None:
        freeze_rows = self.sheet.freeze_rows
        frozen_height = self._get_prefix()[freeze_rows] if freeze_rows > 0 else 0
        virtual_y = self._row_virtual_y(self.cursor_row)
        data_rows_visible = max(1, self.size.height - frozen_height - 2)
        half = data_rows_visible // 2
        self.scroll_to(y=max(0, virtual_y - frozen_height - half), animate=False)

    def scroll_cell_to_bottom(self) -> None:
        freeze_rows = self.sheet.freeze_rows
        frozen_height = self._get_prefix()[freeze_rows] if freeze_rows > 0 else 0
        virtual_y = self._row_virtual_y(self.cursor_row)
        data_rows_visible = max(1, self.size.height - frozen_height - 2)
        self.scroll_to(y=max(0, virtual_y - frozen_height - data_rows_visible + 1), animate=False)

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
        self._rebuild_heights()
        hidden = self.sheet.hidden_cols
        visible_w = sum(
            self.get_col_width(c) + 1 for c in range(self.sheet.max_col + 1) if c not in hidden
        )
        w = ROW_HEADER_WIDTH + visible_w
        self.virtual_size = Size(w, max(self._total_virtual_lines + 200, 1000))
        self.refresh()
