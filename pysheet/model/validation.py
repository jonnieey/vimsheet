"""Cell data-validation rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ValidationRule:
    """A rule that constrains what values a cell may hold.

    Attributes
    ----------
    rule_type:
        "any", "number", "integer", "text", "list", "date", "custom"
    operator:
        For numeric/date types: "between", "not_between", "eq", "ne",
        "lt", "le", "gt", "ge".
    value1, value2:
        Bounds for the rule (value2 used only for "between"/"not_between").
    choices:
        Allowed values when ``rule_type == "list"``.
    formula:
        Raw formula string when ``rule_type == "custom"``.
    error_message:
        User-visible error message shown on violation.
    allow_blank:
        Whether a blank / None value is accepted.
    """

    rule_type: str = "any"
    operator: str = "between"
    value1: Any = None
    value2: Any = None
    choices: list[Any] = field(default_factory=list)
    formula: str = ""
    error_message: str = "Invalid value"
    allow_blank: bool = True

    # -----------------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------------

    def validate(self, value: Any) -> bool:
        """Return True if *value* satisfies this rule."""
        if value is None or value == "":
            return self.allow_blank

        match self.rule_type:
            case "any":
                return True
            case "number":
                return self._check_numeric(value, float)
            case "integer":
                return self._check_numeric(value, int) and float(value) == int(float(value))
            case "text":
                return isinstance(value, str)
            case "list":
                return value in self.choices or str(value) in [str(c) for c in self.choices]
            case "date":
                import datetime
                return isinstance(value, (datetime.date, datetime.datetime))
            case _:
                return True

    def _check_numeric(self, value: Any, cast: type) -> bool:
        try:
            v = float(value)
        except (TypeError, ValueError):
            return False
        v1 = self.value1
        v2 = self.value2
        try:
            match self.operator:
                case "between":
                    return float(v1) <= v <= float(v2)
                case "not_between":
                    return not (float(v1) <= v <= float(v2))
                case "eq":
                    return v == float(v1)
                case "ne":
                    return v != float(v1)
                case "lt":
                    return v < float(v1)
                case "le":
                    return v <= float(v1)
                case "gt":
                    return v > float(v1)
                case "ge":
                    return v >= float(v1)
                case _:
                    return True
        except (TypeError, ValueError):
            return True


@dataclass
class SheetValidation:
    """Collection of validation rules keyed by (row, col)."""

    rules: dict[tuple[int, int], ValidationRule] = field(default_factory=dict)

    def add(self, row: int, col: int, rule: ValidationRule) -> None:
        self.rules[(row, col)] = rule

    def remove(self, row: int, col: int) -> None:
        self.rules.pop((row, col), None)

    def get(self, row: int, col: int) -> ValidationRule | None:
        return self.rules.get((row, col))

    def validate(self, row: int, col: int, value: Any) -> tuple[bool, str]:
        """Return (is_valid, error_message)."""
        rule = self.rules.get((row, col))
        if rule is None:
            return True, ""
        if rule.validate(value):
            return True, ""
        return False, rule.error_message
