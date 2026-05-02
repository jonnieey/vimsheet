"""Tests for row/col grouping and fold/unfold."""

from __future__ import annotations

from pysheet.model.sheet import Sheet


class TestRowGroups:
    def test_add_row_group(self):
        sheet = Sheet(name="S1")
        sheet.row_groups.append((2, 5))
        assert (2, 5) in sheet.row_groups

    def test_fold_group_hides_rows(self):
        sheet = Sheet(name="S1")
        for r in range(8):
            sheet.set_cell_value(r, 0, r)
        sheet.row_groups.append((2, 4))
        # simulate zc: hide rows in group
        r1, r2 = 2, 4
        for r in range(r1, r2 + 1):
            sheet.hidden_rows.add(r)
        assert sheet.hidden_rows == {2, 3, 4}

    def test_unfold_group_shows_rows(self):
        sheet = Sheet(name="S1")
        sheet.row_groups.append((2, 4))
        sheet.hidden_rows = {2, 3, 4}
        rows_in_group = set(range(2, 5))
        sheet.hidden_rows -= rows_in_group
        assert not sheet.hidden_rows

    def test_toggle_fold(self):
        sheet = Sheet(name="S1")
        sheet.row_groups.append((1, 3))
        rows = set(range(1, 4))
        # First toggle: hide
        sheet.hidden_rows |= rows
        assert sheet.hidden_rows == {1, 2, 3}
        # Second toggle: show
        sheet.hidden_rows -= rows
        assert not sheet.hidden_rows

    def test_open_all_clears_hidden(self):
        sheet = Sheet(name="S1")
        sheet.row_groups.append((0, 2))
        sheet.hidden_rows = {0, 1, 2}
        sheet.hidden_rows.clear()
        assert not sheet.hidden_rows


class TestColGroups:
    def test_add_col_group(self):
        sheet = Sheet(name="S1")
        sheet.col_groups.append((1, 3))
        assert (1, 3) in sheet.col_groups


class TestJsonRoundTrip:
    def test_groups_preserved_in_json(self, tmp_path):
        from pysheet.io.json_adapter import JSONAdapter
        from pysheet.model.workbook import Workbook

        wb = Workbook.blank()
        wb.active_sheet.row_groups.append((2, 5))
        wb.active_sheet.col_groups.append((1, 3))

        path = tmp_path / "groups.pysheet"
        JSONAdapter().write(wb, path)

        wb2 = JSONAdapter().read(path)
        assert (2, 5) in wb2.active_sheet.row_groups
        assert (1, 3) in wb2.active_sheet.col_groups
