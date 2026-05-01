"""Unit tests for pysheet.model.validation."""

from __future__ import annotations

import datetime

import pytest

from pysheet.model.validation import SheetValidation, ValidationRule


class TestValidationRule:
    def test_any_accepts_all(self):
        rule = ValidationRule(rule_type="any")
        assert rule.validate(42)
        assert rule.validate("hello")
        assert rule.validate(None)

    def test_allow_blank_true(self):
        rule = ValidationRule(rule_type="number", allow_blank=True)
        assert rule.validate(None) is True
        assert rule.validate("") is True

    def test_allow_blank_false(self):
        rule = ValidationRule(rule_type="number", allow_blank=False)
        assert rule.validate(None) is False

    def test_number_between(self):
        rule = ValidationRule(rule_type="number", operator="between", value1=1, value2=10)
        assert rule.validate(5) is True
        assert rule.validate(1) is True
        assert rule.validate(10) is True
        assert rule.validate(0) is False
        assert rule.validate(11) is False

    def test_number_gt(self):
        rule = ValidationRule(rule_type="number", operator="gt", value1=0)
        assert rule.validate(1) is True
        assert rule.validate(0) is False
        assert rule.validate(-1) is False

    def test_integer_accepts_whole(self):
        rule = ValidationRule(rule_type="integer", operator="ge", value1=0)
        assert rule.validate(5) is True
        assert rule.validate(5.0) is True
        assert rule.validate(5.5) is False

    def test_text_type(self):
        rule = ValidationRule(rule_type="text")
        assert rule.validate("hello") is True
        assert rule.validate(42) is False

    def test_list_type(self):
        rule = ValidationRule(rule_type="list", choices=["red", "green", "blue"])
        assert rule.validate("red") is True
        assert rule.validate("yellow") is False

    def test_list_coercion(self):
        rule = ValidationRule(rule_type="list", choices=[1, 2, 3])
        assert rule.validate(1) is True
        assert rule.validate(4) is False

    def test_date_type(self):
        rule = ValidationRule(rule_type="date")
        assert rule.validate(datetime.date.today()) is True
        assert rule.validate("2024-01-01") is False  # string, not a date object

    def test_number_eq(self):
        rule = ValidationRule(rule_type="number", operator="eq", value1=42)
        assert rule.validate(42) is True
        assert rule.validate(43) is False

    def test_number_ne(self):
        rule = ValidationRule(rule_type="number", operator="ne", value1=0)
        assert rule.validate(1) is True
        assert rule.validate(0) is False


class TestSheetValidation:
    def test_add_and_get(self):
        sv = SheetValidation()
        rule = ValidationRule(rule_type="number", operator="gt", value1=0)
        sv.add(0, 0, rule)
        assert sv.get(0, 0) is rule

    def test_remove(self):
        sv = SheetValidation()
        rule = ValidationRule(rule_type="any")
        sv.add(0, 0, rule)
        sv.remove(0, 0)
        assert sv.get(0, 0) is None

    def test_remove_nonexistent(self):
        sv = SheetValidation()
        sv.remove(5, 5)  # should not raise

    def test_validate_passes(self):
        sv = SheetValidation()
        sv.add(0, 0, ValidationRule(rule_type="number", operator="gt", value1=0))
        ok, msg = sv.validate(0, 0, 5)
        assert ok is True
        assert msg == ""

    def test_validate_fails(self):
        sv = SheetValidation()
        sv.add(0, 0, ValidationRule(
            rule_type="number", operator="gt", value1=0, error_message="Must be positive"
        ))
        ok, msg = sv.validate(0, 0, -1)
        assert ok is False
        assert msg == "Must be positive"

    def test_validate_no_rule(self):
        sv = SheetValidation()
        ok, msg = sv.validate(0, 0, "anything")
        assert ok is True
        assert msg == ""

    def test_sheet_has_validation(self):
        from pysheet.model.workbook import Workbook
        wb = Workbook.blank()
        sheet = wb.active_sheet
        assert hasattr(sheet, "validation")
        assert isinstance(sheet.validation, SheetValidation)
