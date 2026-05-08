"""Workbook model — a collection of sheets with session state."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from vimsheet.model.sheet import Sheet


@dataclass
class Workbook:
    """Top-level container: sheets, filepath, and modification state."""

    sheets: list[Sheet] = field(default_factory=list)
    active_sheet_idx: int = 0
    filepath: Path | None = None
    modified: bool = False
    global_named_ranges: dict[str, str] = field(default_factory=dict)

    # -----------------------------------------------------------------------
    # Sheet access
    # -----------------------------------------------------------------------

    @property
    def active_sheet(self) -> Sheet:
        """Return the currently active sheet."""
        return self.sheets[self.active_sheet_idx]

    def get_sheet(self, name: str) -> Sheet | None:
        """Return the sheet with the given name, or None."""
        for sheet in self.sheets:
            if sheet.name == name:
                return sheet
        return None

    def get_sheet_index(self, name: str) -> int | None:
        """Return the index of the sheet with *name*, or None."""
        for i, sheet in enumerate(self.sheets):
            if sheet.name == name:
                return i
        return None

    # -----------------------------------------------------------------------
    # Sheet management
    # -----------------------------------------------------------------------

    def add_sheet(self, name: str | None = None) -> Sheet:
        """Append a new blank sheet and return it."""
        if name is None:
            name = f"Sheet{len(self.sheets) + 1}"
        if self.get_sheet(name) is not None:
            raise ValueError(f"Sheet {name!r} already exists")
        sheet = Sheet(name=name)
        sheet._workbook = self
        if self.sheets:
            sheet.autocalc = self.sheets[0].autocalc
        self.sheets.append(sheet)
        self.modified = True
        return sheet

    def delete_sheet(self, name: str) -> None:
        """Delete a sheet by name. Raises ValueError if it is the only sheet."""
        if len(self.sheets) <= 1:
            raise ValueError("Cannot delete the only sheet")
        idx = self.get_sheet_index(name)
        if idx is None:
            raise KeyError(f"Sheet {name!r} not found")
        self.sheets.pop(idx)
        if self.active_sheet_idx >= len(self.sheets):
            self.active_sheet_idx = len(self.sheets) - 1
        self.modified = True

    def rename_sheet(self, old_name: str, new_name: str) -> None:
        """Rename a sheet."""
        sheet = self.get_sheet(old_name)
        if sheet is None:
            raise KeyError(f"Sheet {old_name!r} not found")
        if self.get_sheet(new_name) is not None:
            raise ValueError(f"Sheet {new_name!r} already exists")
        sheet.name = new_name
        self.modified = True

    def duplicate_sheet(self, name: str | None = None) -> Sheet:
        """Duplicate a sheet by name (or active sheet if None). Appends with suffix."""
        import copy as _copy

        from vimsheet.model.sheet import CondFormatRule, Sheet
        from vimsheet.model.validation import SheetValidation

        src = self.active_sheet if name is None else self.get_sheet(name)
        if src is None:
            raise KeyError(f"Sheet {name!r} not found")

        base = src.name
        new_name = f"{base} (copy)"
        counter = 2
        while self.get_sheet(new_name) is not None:
            new_name = f"{base} (copy {counter})"
            counter += 1

        new_sheet = Sheet(name=new_name)
        new_sheet.cells = {pos: cell.copy() for pos, cell in src.cells.items()}
        new_sheet.col_widths = dict(src.col_widths)
        new_sheet.row_heights = dict(src.row_heights)
        new_sheet.hidden_rows = set(src.hidden_rows)
        new_sheet.hidden_cols = set(src.hidden_cols)
        new_sheet.row_groups = list(src.row_groups)
        new_sheet.col_groups = list(src.col_groups)
        new_sheet.freeze_rows = src.freeze_rows
        new_sheet.freeze_cols = src.freeze_cols
        new_sheet.named_ranges = _copy.deepcopy(src.named_ranges)
        new_sheet.cond_formats = [
            CondFormatRule(r.range_str, r.operator, r.value, r.value2, r.fmt.copy())
            for r in src.cond_formats
        ]
        new_sheet.filters = dict(src.filters)
        new_sheet.sort_state = _copy.deepcopy(src.sort_state)
        new_sheet.max_row = src.max_row
        new_sheet.max_col = src.max_col
        new_sheet.validation = SheetValidation(rules=dict(src.validation.rules))
        new_sheet._workbook = self
        new_sheet.autocalc = src.autocalc

        self.sheets.append(new_sheet)
        self.active_sheet_idx = len(self.sheets) - 1
        self.modified = True
        return new_sheet

    def _bind_sheets(self) -> None:
        """Set _workbook back-reference on all sheets (called after IO load)."""
        for sheet in self.sheets:
            sheet._workbook = self

    def set_autocalc(self, value: bool) -> None:
        """Propagate autocalc setting to all sheets."""
        for sheet in self.sheets:
            sheet.autocalc = value

    def go_to_next_sheet(self) -> None:
        """Switch to the next sheet, wrapping around."""
        self.active_sheet_idx = (self.active_sheet_idx + 1) % len(self.sheets)

    def go_to_prev_sheet(self) -> None:
        """Switch to the previous sheet, wrapping around."""
        self.active_sheet_idx = (self.active_sheet_idx - 1) % len(self.sheets)

    def go_to_sheet(self, idx: int) -> None:
        """Switch to sheet at *idx* (0-based). Clamps to valid range."""
        self.active_sheet_idx = max(0, min(len(self.sheets) - 1, idx))

    # -----------------------------------------------------------------------
    # Factory helpers
    # -----------------------------------------------------------------------

    @classmethod
    def blank(cls, sheet_name: str = "Sheet1") -> Workbook:
        """Create a new blank workbook with one empty sheet."""
        wb = cls()
        sheet = Sheet(name=sheet_name)
        sheet._workbook = wb
        wb.sheets.append(sheet)
        return wb
