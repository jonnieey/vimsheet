"""Text built-in functions."""

from __future__ import annotations

from typing import Any

from vimsheet.formula.functions.registry import register

ERR = "#ERR"
TYPE_ERR = "#TYPE"
NA = "#N/A"


@register("CONCAT", "CONCATENATE", desc="Join strings together")
def fn_concat(*args: Any) -> Any:
    return "".join(str(a) if a is not None else "" for a in args)


@register("LEN", desc="Length of string")
def fn_len(s: Any) -> Any:
    return len(str(s)) if s is not None else 0


@register("UPPER", desc="Convert to uppercase")
def fn_upper(s: Any) -> Any:
    return str(s).upper() if s is not None else ""


@register("LOWER", desc="Convert to lowercase")
def fn_lower(s: Any) -> Any:
    return str(s).lower() if s is not None else ""


@register("PROPER", desc="Title case each word")
def fn_proper(s: Any) -> Any:
    return str(s).title() if s is not None else ""


@register("TRIM", desc="Remove leading/trailing spaces")
def fn_trim(s: Any) -> Any:
    return str(s).strip() if s is not None else ""


@register("LEFT", desc="First N chars. =LEFT('hello',2)->'he'")
def fn_left(s: Any, n: Any = 1) -> Any:
    return str(s)[: int(n)] if s is not None else ""


@register("RIGHT", desc="Last N chars")
def fn_right(s: Any, n: Any = 1) -> Any:
    return str(s)[-int(n) :] if s is not None else ""


@register("MID", desc="Chars from middle")
def fn_mid(s: Any, start: Any, n: Any) -> Any:
    try:
        st = int(start) - 1  # 1-based
        return str(s)[st : st + int(n)] if s is not None else ""
    except (TypeError, ValueError):
        return TYPE_ERR


@register("FIND", desc="Position of substring")
def fn_find(find: Any, s: Any, start: Any = 1) -> Any:
    try:
        idx = str(s).find(str(find), int(start) - 1)
        return idx + 1 if idx >= 0 else NA
    except (TypeError, ValueError):
        return TYPE_ERR


@register("REPLACE", desc="Replace chars at position")
def fn_replace(s: Any, start: Any, n: Any, new: Any) -> Any:
    try:
        sv = str(s) if s is not None else ""
        st = int(start) - 1
        return sv[:st] + str(new) + sv[st + int(n) :]
    except (TypeError, ValueError):
        return TYPE_ERR


@register("SUBSTITUTE", desc="Replace substring")
def fn_substitute(s: Any, old: Any, new: Any, occurrence: Any = None) -> Any:
    sv = str(s) if s is not None else ""
    ov, nv = str(old), str(new)
    if occurrence is None:
        return sv.replace(ov, nv)
    try:
        n = int(occurrence)
        count = 0
        idx = 0
        while True:
            found = sv.find(ov, idx)
            if found == -1:
                break
            count += 1
            if count == n:
                return sv[:found] + nv + sv[found + len(ov) :]
            idx = found + len(ov)
        return sv
    except (TypeError, ValueError):
        return TYPE_ERR


@register("TEXT", desc="Format number as text")
def fn_text(val: Any, fmt: Any) -> Any:
    try:
        return format(val, str(fmt))
    except Exception:
        return str(val)


@register("VALUE", desc="Convert text to number")
def fn_value(s: Any) -> Any:
    sv = str(s).strip() if s is not None else ""
    try:
        return int(sv)
    except ValueError:
        pass
    try:
        return float(sv)
    except ValueError:
        return TYPE_ERR


@register("REPT", "REPEAT", desc="Repeat string N times")
def fn_rept(s: Any, n: Any) -> Any:
    try:
        return str(s) * int(n)
    except (TypeError, ValueError):
        return TYPE_ERR


@register("EXACT", desc="True if strings match")
def fn_exact(a: Any, b: Any) -> Any:
    return str(a) == str(b)


@register("CHAR", desc="Char from ASCII code")
def fn_char(n: Any) -> Any:
    try:
        return chr(int(n))
    except (TypeError, ValueError, OverflowError):
        return ERR


@register("CODE", desc="ASCII code of first char")
def fn_code(s: Any) -> Any:
    sv = str(s) if s is not None else ""
    if not sv:
        return ERR
    return ord(sv[0])
