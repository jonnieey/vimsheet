"""Logic built-in functions."""

from __future__ import annotations

from typing import Any

from vimsheet.formula.functions.registry import register

ERR = "#ERR"
NA = "#N/A"

_ERRORS = {"#ERR", "#DIV/0", "#REF", "#NAME", "#CIRC", "#TYPE", "#N/A"}


def _is_error(v: Any) -> bool:
    return isinstance(v, str) and v in _ERRORS


def _truthy(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, int | float):
        return v != 0
    if isinstance(v, str):
        return v.upper() not in ("FALSE", "0", "")
    return v is not None


@register("IF", desc="Conditional. =IF(A1>5,'yes','no')")
def fn_if(cond: Any, t: Any, f: Any = False) -> Any:
    return t if _truthy(cond) else f


@register("IFS", desc="Multiple conditions. =IFS(A1>5,'big',A1>0,'small')")
def fn_ifs(*args: Any) -> Any:
    if len(args) % 2 != 0:
        return ERR
    for i in range(0, len(args), 2):
        if _truthy(args[i]):
            return args[i + 1]
    return NA


@register("AND", desc="True if all args true")
def fn_and(*args: Any) -> Any:
    return all(_truthy(a) for a in args)


@register("OR", desc="True if any arg true")
def fn_or(*args: Any) -> Any:
    return any(_truthy(a) for a in args)


@register("NOT", desc="Invert boolean")
def fn_not(cond: Any) -> Any:
    return not _truthy(cond)


@register("XOR", desc="True if odd count of true")
def fn_xor(*args: Any) -> Any:
    return sum(1 for a in args if _truthy(a)) % 2 == 1


@register("IFERROR", desc="Fallback on error")
def fn_iferror(expr: Any, fallback: Any) -> Any:
    return fallback if _is_error(expr) else expr


@register("IFNA", desc="Fallback on #N/A")
def fn_ifna(expr: Any, fallback: Any) -> Any:
    return fallback if expr == NA else expr


@register("SWITCH", desc="Match value to cases")
def fn_switch(expr: Any, *args: Any) -> Any:
    # SWITCH(expr, val1, result1, val2, result2, ...[, default])
    i = 0
    default = None
    pairs = list(args)
    if len(pairs) % 2 == 1:
        default = pairs.pop()
    while i < len(pairs) - 1:
        if expr == pairs[i]:
            return pairs[i + 1]
        i += 2
    return default if default is not None else NA


@register("TRUE", desc="Returns TRUE")
def fn_true() -> Any:
    return True


@register("FALSE", desc="Returns FALSE")
def fn_false() -> Any:
    return False


@register("ISBLANK", desc="True if empty")
def fn_isblank(cell: Any) -> Any:
    return cell is None or cell == ""


@register("ISNUMBER", desc="True if numeric")
def fn_isnumber(cell: Any) -> Any:
    return isinstance(cell, int | float) and not isinstance(cell, bool)


@register("ISTEXT", desc="True if text")
def fn_istext(cell: Any) -> Any:
    return isinstance(cell, str) and not _is_error(cell)


@register("ISERROR", desc="True if error value")
def fn_iserror(cell: Any) -> Any:
    return _is_error(cell)
