"""Visual mode key handler."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pysheet.controller.mode import Mode
from pysheet.model.range import CellRange

if TYPE_CHECKING:
    from pysheet.app import PySheetApp


class VisualHandler:
    """Handles all key events while in any Visual mode (v / V / Ctrl+v)."""

    def __init__(self, app: PySheetApp) -> None:
        self._app = app

    def handle(self, key: str) -> None:
        app = self._app

        # ---- Active chord: handle second key before navigation ----
        chord = app._visual_chord
        if chord and key != "escape":
            app._visual_chord = ""
            if chord == "g" and key == "g":
                app.grid.move_to_first_row()
            elif chord == "f":
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
                        case "j":
                            self._shift_range_cells(sel, 1, 0)
                        case "k":
                            self._shift_range_cells(sel, -1, 0)
                        case "l":
                            self._shift_range_cells(sel, 0, 1)
                        case "h":
                            self._shift_range_cells(sel, 0, -1)
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

            # --- Formatting chord prefix ---
            case "f":
                app._visual_chord = "f"
                return

            # --- Enter command mode with range pre-filled ---
            case ":":
                sel = app.grid.visual_selection()
                range_str = (sel.to_a1() + " ") if sel else ""
                app._enter_command_mode(prefix=range_str)
                return

        app._visual_chord = ""
        app._sync_formula_bar()
        app._sync_status_bar()

    # -----------------------------------------------------------------------
    # Operations
    # -----------------------------------------------------------------------

    def _yank_range(self, cell_range: CellRange) -> None:
        app = self._app
        register = app._pending_register or ""
        data = app.workbook.active_sheet.get_range_values(cell_range)
        if register:
            app._registers[register] = data
            app._pending_register = ""
        else:
            app._default_register = data
        app.status_bar.show_message(
            f"Yanked {cell_range.num_rows}×{cell_range.num_cols}"
            + (f' → "{register}' if register else "")
        )

    def _delete_range(self, cell_range: CellRange) -> None:
        from pysheet.model.undo import DeleteRangeCommand

        app = self._app
        sheet = app.workbook.active_sheet
        app._default_register = sheet.get_range_values(cell_range)
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
        from pysheet.model.undo import CompositeCommand, SetCellCommand

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
        from pysheet.model.undo import CompositeCommand, FormatCommand

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
        """Move the selected block of cells by (dr, dc), overwriting destination."""
        from pysheet.model.undo import ShiftCellsCommand

        app = self._app
        dst_r = cell_range.start_row + dr
        dst_c = cell_range.start_col + dc
        if dst_r < 0 or dst_c < 0:
            return
        cmd = ShiftCellsCommand(app.workbook.active_sheet, cell_range, dr, dc)
        app.undo_stack.push(cmd)
        app.workbook.modified = True
        # Move visual anchor and cursor with the block
        app.grid.visual_anchor_row += dr
        app.grid.visual_anchor_col += dc
        app.grid.move_cursor(app.cursor_row + dr, app.cursor_col + dc)
        app.grid.refresh_grid()

    def _paste_into_selection(self, cell_range: CellRange) -> None:
        """Paste yanked data into the visual selection.

        Single-cell yank: fill every cell in the selection with that value.
        Multi-cell yank: paste the block starting at the top-left of the selection.
        """
        from pysheet.model.undo import PasteCommand

        app = self._app
        reg = app._pending_register
        if reg == "+":
            from pysheet.controller.normal_handler import NormalHandler

            data = NormalHandler(app)._from_clipboard()
        elif reg and reg in app._registers:
            data = app._registers[reg]
        else:
            data = app._default_register
        app._pending_register = ""

        if not data:
            app.status_bar.show_message("Nothing to paste")
            return

        src_rows = len(data)
        src_cols = max(len(r) for r in data)

        if src_rows == 1 and src_cols == 1:
            # Single-cell yank — broadcast to every cell in the selection
            entry = data[0][0]
            paste_data = [[entry] * cell_range.num_cols for _ in range(cell_range.num_rows)]
        else:
            # Multi-cell yank — paste block as-is from selection's top-left
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
