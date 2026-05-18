"""Visual mode key handler."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from vimsheet.controller.mode import Mode
from vimsheet.model.range import CellRange
from vimsheet.model.register import RegisterEntry

if TYPE_CHECKING:
    from vimsheet.app import VimSheetApp


class VisualHandler:
    """Handles all key events while in any Visual mode (v / V / Ctrl+v)."""

    def __init__(self, app: VimSheetApp) -> None:
        self._app = app

    def handle(self, key: str) -> None:
        app = self._app

        # ---- goto address accumulator (go<addr><Enter>) — checked before digit buffer ----
        if app._visual_goto_buf is not None:
            if key == "escape":
                app._visual_goto_buf = None
                app.status_bar.set_persistent_message("", priority=2)
            elif key in ("enter", "\r", "\n"):
                self._goto_extend(app._visual_goto_buf)
                app._visual_goto_buf = None
                app.status_bar.set_persistent_message("", priority=2)
            elif key == "backspace":
                app._visual_goto_buf = app._visual_goto_buf[:-1]
                app.status_bar.set_persistent_message(f"go: {app._visual_goto_buf}", priority=2)
            elif len(key) == 1 and key.isprintable():
                app._visual_goto_buf += key
                app.status_bar.set_persistent_message(f"go: {app._visual_goto_buf}", priority=2)
            app._sync_formula_bar()
            app._sync_status_bar()
            return

        # ---- Digit prefix: buffer digits for count-aware operations ----
        if key.isdigit() and not app._visual_chord and (key != "0" or app._key_buffer):
            app._key_buffer += key
            app.status_bar.set_persistent_message(app._key_buffer)
            return
        count = int(app._key_buffer) if app._key_buffer.isdigit() and app._key_buffer else 1
        app._key_buffer = ""

        # ---- Active chord: handle second key before navigation ----
        chord = app._visual_chord
        if chord and key != "escape":
            app._visual_chord = ""
            if chord == "g" and key == "g":
                app.grid.move_to_first_row()
            elif chord == "g" and key == "o":
                app._visual_goto_buf = ""
                app.status_bar.set_persistent_message("go: ", priority=2)
            elif chord == "g" and key == "s":
                app._visual_chord = "gs"
                return
            elif chord == "t":
                sel = app.grid.visual_selection()
                if sel:
                    self._apply_fmt(sel, key)
            elif chord == "s":
                sel = app.grid.visual_selection()
                if sel:
                    match key:
                        case "s":
                            self._sort_range(sel)
                            app.mode = Mode.NORMAL
                        case "a":
                            self._sort_range_columns(sel, ascending=True)
                            app.mode = Mode.NORMAL
                        case "d":
                            self._sort_range_columns(sel, ascending=False)
                            app.mode = Mode.NORMAL
            elif chord == "gs":
                sel = app.grid.visual_selection()
                if sel:
                    match key:
                        case "j":
                            self._shift_range_cells(sel, 1, 0)
                        case "k":
                            self._shift_range_cells(sel, -1, 0)
                        case "l":
                            self._shift_range_cells(sel, 0, 1)
                        case "h":
                            self._shift_range_cells(sel, 0, -1)
            elif chord == "z":
                sel = app.grid.visual_selection()
                match key:
                    case "_":
                        if sel:
                            for r in range(sel.start_row, sel.end_row + 1):
                                app.grid.collapse_row(r)
                    case "+":
                        if sel:
                            for r in range(sel.start_row, sel.end_row + 1):
                                app.grid.expand_row(r)
                app.mode = Mode.NORMAL
            app._sync_formula_bar()
            app._sync_status_bar()
            return

        match key:
            case "escape":
                app.mode = Mode.NORMAL

            # --- Navigation (extends selection) ---
            case "h" | "left":
                app.grid.move_by(0, -1)
            case "l" | "right":
                app.grid.move_by(0, 1)
            case "j" | "down":
                app.grid.move_by(1, 0)
            case "k" | "up":
                app.grid.move_by(-1, 0)
            case "G":
                app.grid.move_to_last_row()
            case "g":
                app._visual_chord = "g"
                return
            case "0":
                app.grid.move_to_row_start()
            case "$":
                app.grid.move_to_row_end()
            case "w" | "ctrl+right":
                app.grid.jump_next_nonempty_right()
            case "b" | "ctrl+left":
                app.grid.jump_next_nonempty_left()
            case "ctrl+down":
                app.grid.jump_next_nonempty_down()
            case "ctrl+up":
                app.grid.jump_next_nonempty_up()
            case "ctrl+d":
                app.grid.half_page_down()
            case "ctrl+u":
                app.grid.half_page_up()
            case "ctrl+f" | "pagedown":
                app.grid.page_down()
            case "ctrl+b" | "pageup":
                app.grid.page_up()

            # --- Swap anchor ---
            case "o":
                ar, ac = app.grid.visual_anchor_row, app.grid.visual_anchor_col
                app.grid.visual_anchor_row = app.cursor_row
                app.grid.visual_anchor_col = app.cursor_col
                app.grid.move_cursor(ar, ac)

            # --- Yank ---
            case "y":
                sel = app.grid.visual_selection()
                if sel:
                    self._yank_range(sel)
                app.mode = Mode.NORMAL

            # --- Paste into selection ---
            case "p":
                sel = app.grid.visual_selection()
                if sel:
                    self._paste_into_selection(sel)
                app.mode = Mode.NORMAL

            # --- Delete / clear ---
            case "d" | "x":
                sel = app.grid.visual_selection()
                if sel:
                    self._delete_range(sel)
                app.mode = Mode.NORMAL

            # --- Fill down/right (=) ---
            case "=":
                sel = app.grid.visual_selection()
                if sel:
                    self._fill_range(sel)
                app.mode = Mode.NORMAL

            # --- s-chord prefix: ss=sort, sj/sk/sl/sh=shift ---
            case "s":
                app._visual_chord = "s"
                return

            # --- Shift right/left ---
            case ">":
                sel = app.grid.visual_selection()
                if sel:
                    self._shift_range(sel, 1)
            case "<":
                sel = app.grid.visual_selection()
                if sel:
                    self._shift_range(sel, -1)

            # --- Widen / narrow columns in selection ---
            case "+":
                sel = app.grid.visual_selection()
                if sel:
                    sheet = app.workbook.active_sheet
                    for c in range(sel.start_col, sel.end_col + 1):
                        sheet.set_col_width(c, sheet.get_col_width(c) + count)
                    app.grid.refresh_grid()
            case "-":
                sel = app.grid.visual_selection()
                if sel:
                    sheet = app.workbook.active_sheet
                    for c in range(sel.start_col, sel.end_col + 1):
                        sheet.set_col_width(c, sheet.get_col_width(c) - count)
                    app.grid.refresh_grid()
            case "_":
                sel = app.grid.visual_selection()
                if sel:
                    sheet = app.workbook.active_sheet
                    for c in range(sel.start_col, sel.end_col + 1):
                        sheet.auto_fit_col(c)
                    app.grid.refresh_grid()

            # --- Row expand / collapse chord prefix ---
            case "z":
                app._visual_chord = "z"
                return

            # --- Formatting chord prefix ---
            case "t":
                app._visual_chord = "t"
                return

            # --- Increment / decrement all numeric cells in selection ---
            case "ctrl+a":
                sel = app.grid.visual_selection()
                if sel:
                    app.normal_handler._increment_cells(list(sel.iter_cells()), count)
            case "ctrl+x":
                sel = app.grid.visual_selection()
                if sel:
                    app.normal_handler._increment_cells(list(sel.iter_cells()), -count)

            # --- Enter command mode with range pre-filled ---
            case ":":
                sel = app.grid.visual_selection()
                range_str = (sel.to_a1() + " ") if sel else ""
                app._enter_command_mode(prefix=range_str)
                return

        app._visual_chord = ""
        app.status_bar.set_persistent_message("")
        app._sync_formula_bar()
        app._sync_status_bar()

    # -----------------------------------------------------------------------
    # Operations
    # -----------------------------------------------------------------------

    def _yank_range(self, cell_range: CellRange) -> None:
        app = self._app
        register = app._pending_register or ""
        sheet = app.workbook.active_sheet
        data: list[list[tuple[Any, str | None, Any]]] = []
        for r in range(cell_range.start_row, cell_range.end_row + 1):
            row_data: list[tuple[Any, str | None, Any]] = []
            for c in range(cell_range.start_col, cell_range.end_col + 1):
                cell = sheet.get_cell(r, c)
                row_data.append(
                    (
                        cell.value if cell else None,
                        cell.formula if cell else None,
                        cell.fmt.copy() if cell else None,
                    )
                )
            data.append(row_data)
        entry = RegisterEntry(
            value=None,
            formula=None,
            src_row=cell_range.start_row,
            src_col=cell_range.start_col,
            is_range=True,
            range_data=data,
            range_src_top=cell_range.start_row,
            range_src_left=cell_range.start_col,
        )
        if register:
            app._registers[register] = entry
            app._pending_register = ""
        else:
            app._default_register = entry
        app.status_bar.show_message(
            f"Yanked {cell_range.num_rows}×{cell_range.num_cols}"
            + (f' → "{register}' if register else "")
        )

    def _delete_range(self, cell_range: CellRange) -> None:
        from vimsheet.model.undo import DeleteRangeCommand

        app = self._app
        sheet = app.workbook.active_sheet
        range_data: list[list[tuple[Any, str | None, Any]]] = []
        for r in range(cell_range.start_row, cell_range.end_row + 1):
            row_data: list[tuple[Any, str | None, Any]] = []
            for c in range(cell_range.start_col, cell_range.end_col + 1):
                cell = sheet.get_cell(r, c)
                row_data.append(
                    (
                        cell.value if cell else None,
                        cell.formula if cell else None,
                        cell.fmt.copy() if cell else None,
                    )
                )
            range_data.append(row_data)
        app._default_register = RegisterEntry(
            value=None,
            formula=None,
            src_row=cell_range.start_row,
            src_col=cell_range.start_col,
            is_range=True,
            range_data=range_data,
            range_src_top=cell_range.start_row,
            range_src_left=cell_range.start_col,
        )
        cmd = DeleteRangeCommand(sheet, cell_range)
        app.undo_stack.push(cmd)
        app.workbook.modified = True
        app.grid.refresh_grid()

    def _sort_range(self, cell_range: CellRange) -> None:
        """Sort rows in selection by the first column of the selection."""
        app = self._app
        sheet = app.workbook.active_sheet
        r1, c1, r2, c2 = (
            cell_range.start_row,
            cell_range.start_col,
            cell_range.end_row,
            cell_range.end_col,
        )
        rows: list[list[Any]] = []
        for r in range(r1, r2 + 1):
            row = [sheet.cells.get((r, c)) for c in range(c1, c2 + 1)]
            rows.append(row)

        def sort_key(row: list[Any]) -> tuple[int, Any]:
            cell = row[0]
            val = cell.value if cell else None
            if val is None:
                return (1, "")
            if isinstance(val, int | float):
                return (0, val)
            return (0, str(val))

        rows.sort(key=sort_key)

        # Write back
        for ri, row in enumerate(rows):
            for ci, cell in enumerate(row):
                r, c = r1 + ri, c1 + ci
                if cell is None:
                    sheet.clear_cell(r, c)
                else:
                    sheet.set_cell_value(r, c, cell.value, cell.formula)
        app.workbook.modified = True
        app.grid.refresh_grid()

    def _sort_range_columns(self, cell_range: CellRange, ascending: bool = True) -> None:
        """Sort each column in the selected range independently (columnar sort)."""
        app = self._app
        sheet = app.workbook.active_sheet
        r1, c1, r2, c2 = (
            cell_range.start_row,
            cell_range.start_col,
            cell_range.end_row,
            cell_range.end_col,
        )
        sort_keys = [(c, ascending) for c in range(c1, c2 + 1)]
        sheet.sort_range_columns(r1, c1, r2, c2, sort_keys)
        app.workbook.modified = True
        app.grid.refresh_grid()

    def _shift_range(self, cell_range: CellRange, delta: int) -> None:
        """Shift selection right (delta=1) or left (delta=-1) by one column."""
        app = self._app
        sheet = app.workbook.active_sheet
        if delta == 1:
            sheet.insert_col(cell_range.start_col)
        elif delta == -1 and cell_range.start_col > 0:
            sheet.delete_col(cell_range.start_col - 1)
        app.workbook.modified = True
        app.grid.refresh_grid()

    def _fill_range(self, cell_range: CellRange) -> None:
        """Fill the selection by replicating the top-left cell downward/rightward."""
        from vimsheet.model.undo import CompositeCommand, SetCellCommand

        app = self._app
        sheet = app.workbook.active_sheet
        src = sheet.get_cell(cell_range.start_row, cell_range.start_col)
        if src is None:
            return
        cmds = []
        for r in range(cell_range.start_row, cell_range.end_row + 1):
            for c in range(cell_range.start_col, cell_range.end_col + 1):
                if r == cell_range.start_row and c == cell_range.start_col:
                    continue
                cmds.append(SetCellCommand(sheet, r, c, src.value, new_formula=src.formula))
        if cmds:
            app.undo_stack.push(CompositeCommand(cmds))  # type: ignore[arg-type]
            app.workbook.modified = True
            app.grid.refresh_grid()

    def _apply_fmt(self, cell_range: CellRange, fmt_key: str) -> None:
        """Apply a format shortcut to all cells in the selection."""
        from vimsheet.model.undo import CompositeCommand, FormatCommand

        app = self._app
        sheet = app.workbook.active_sheet
        cmds: list[FormatCommand] = []
        # For toggleable attributes, use the first cell's state to decide direction
        first_cell = sheet.get_cell(*next(iter(cell_range.iter_cells()), (0, 0)))
        toggle_on = {
            "b": not (first_cell.fmt.bold if first_cell else False),
            "i": not (first_cell.fmt.italic if first_cell else False),
            "u": not (first_cell.fmt.underline if first_cell else False),
        }
        for r, c in cell_range.iter_cells():
            match fmt_key:
                case "b":
                    cmds.append(FormatCommand(sheet, r, c, bold=toggle_on["b"]))
                case "i":
                    cmds.append(FormatCommand(sheet, r, c, italic=toggle_on["i"]))
                case "u":
                    cmds.append(FormatCommand(sheet, r, c, underline=toggle_on["u"]))
                case "l":
                    cmds.append(FormatCommand(sheet, r, c, align="left"))
                case "r":
                    cmds.append(FormatCommand(sheet, r, c, align="right"))
                case "c":
                    cmds.append(FormatCommand(sheet, r, c, align="center"))
        if cmds:
            composite = CompositeCommand(cmds)  # type: ignore[arg-type]
            app.undo_stack.push(composite)
            app.grid.refresh_grid()

    def _shift_range_cells(self, cell_range: CellRange, dr: int, dc: int) -> None:
        """Move the selected block of cells by (dr, dc), overwriting destination.

        Each cell in the selection is moved independently (set-and-clear),
        not cascaded — matching Excel's cut+paste behavior.
        """
        from vimsheet.model.undo import CompositeCommand, SetCellCommand

        app = self._app
        sheet = app.workbook.active_sheet
        dst_r = cell_range.start_row + dr
        dst_c = cell_range.start_col + dc
        if dst_r < 0 or dst_c < 0:
            return

        cmds: list[SetCellCommand] = []
        for r, c in cell_range.iter_cells():
            src_cell = sheet.get_cell(r, c)
            src_val = src_cell.value if src_cell else None
            src_fml = src_cell.formula if src_cell else None
            if src_val is not None or src_fml is not None:
                cmds.append(
                    SetCellCommand(
                        sheet,
                        dst_r + (r - cell_range.start_row),
                        dst_c + (c - cell_range.start_col),
                        src_val,
                        new_formula=src_fml,
                    )
                )
            cmds.append(SetCellCommand(sheet, r, c, None))

        if cmds:
            composite = CompositeCommand(cmds)
            app.undo_stack.push(composite)
            app.workbook.modified = True

        app.grid.visual_anchor_row += dr
        app.grid.visual_anchor_col += dc
        app.grid.move_cursor(app.cursor_row + dr, app.cursor_col + dc)
        app.grid.refresh_grid()

    def _goto_extend(self, addr: str) -> None:
        """Move cursor to *addr*, extending the visual selection (anchor stays fixed)."""
        from vimsheet.model.range import a1_to_rowcol

        app = self._app
        try:
            r, c = a1_to_rowcol(addr.strip().upper())
            app.grid.move_cursor(r, c)
        except ValueError:
            app.status_bar.show_message(f"Invalid address: {addr!r}")

    def _paste_into_selection(self, cell_range: CellRange) -> None:
        """Paste yanked data into the visual selection.

        Single-cell yank: fill every cell in the selection with that value.
        Multi-cell yank: paste the block starting at the top-left of the selection.
        """
        from vimsheet.formula.adjuster import adjust_formula
        from vimsheet.model.undo import PasteCommand, YankedCell

        app = self._app
        reg = app._pending_register
        if reg == "+":
            from vimsheet.controller.normal_handler import NormalHandler

            data = NormalHandler(app)._from_clipboard()
            if not data:
                app.status_bar.show_message("Nothing to paste")
                return
            src_rows = len(data)
            src_cols = max(len(r) for r in data)
            if src_rows == 1 and src_cols == 1:
                paste_data = [
                    [data[0][0]] * cell_range.num_cols for _ in range(cell_range.num_rows)
                ]
            else:
                paste_data = data
            cmd = PasteCommand(
                app.workbook.active_sheet,
                cell_range.start_row,
                cell_range.start_col,
                paste_data,
            )
            app.undo_stack.push(cmd)
            app.workbook.modified = True
            app.grid.refresh_grid()
            app.status_bar.show_message(f"Pasted into {cell_range.num_rows}×{cell_range.num_cols}")
            return

        entry: RegisterEntry | None = app._registers.get(reg) if reg else app._default_register
        app._pending_register = ""
        if entry is None:
            app.status_bar.show_message("Nothing to paste")
            return

        dst_row, dst_col = cell_range.start_row, cell_range.start_col

        if entry.is_range:
            paste_data: list[list[Any]] = []
            for _, row_data in enumerate(entry.range_data):
                row: list[Any] = []
                for _, (value, formula) in enumerate(row_data):
                    adjusted = adjust_formula(
                        formula, dst_row, dst_col, entry.range_src_top, entry.range_src_left
                    )
                    if formula is not None and adjusted is not None:
                        row.append(YankedCell(value=value, formula=adjusted))
                    else:
                        row.append(value)
                paste_data.append(row)
        else:
            # Single-cell yank — broadcast adjusted formula to every cell
            adjusted_formula = adjust_formula(
                entry.formula, dst_row, dst_col, entry.src_row, entry.src_col
            )
            if entry.formula is not None and adjusted_formula is not None:
                single_entry: Any = YankedCell(value=entry.value, formula=adjusted_formula)
            else:
                single_entry = entry.value
            paste_data = [[single_entry] * cell_range.num_cols for _ in range(cell_range.num_rows)]

        cmd = PasteCommand(
            app.workbook.active_sheet,
            cell_range.start_row,
            cell_range.start_col,
            paste_data,
        )
        app.undo_stack.push(cmd)
        app.workbook.modified = True
        app.grid.refresh_grid()
        app.status_bar.show_message(f"Pasted into {cell_range.num_rows}×{cell_range.num_cols}")
