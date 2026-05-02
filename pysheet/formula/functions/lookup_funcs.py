"""Lookup and reference built-in functions."""

from __future__ import annotations

from typing import Any

from pysheet.formula.functions.registry import register

ERR = "#ERR"
NA = "#N/A"
REF = "#REF"
TYPE_ERR = "#TYPE"


def _flat2d(v: Any) -> list[list[Any]]:
    """Ensure v is a 2-D list."""
    if isinstance(v, list):
        if v and isinstance(v[0], list):
            return v
        return [v]
    return [[v]]


@register("VLOOKUP")
def fn_vlookup(val: Any, range_val: Any, col: Any, approx: Any = True) -> Any:
    table = _flat2d(range_val)
    try:
        col_idx = int(col) - 1
    except (TypeError, ValueError):
        return TYPE_ERR
    if not table or col_idx < 0:
        return REF

    exact = not _truthy(approx)
    last_match = NA

    for row in table:
        if not row:
            continue
        key = row[0]
        if exact:
            if key == val:
                return row[col_idx] if col_idx < len(row) else REF
        else:
            if key == val:
                return row[col_idx] if col_idx < len(row) else REF
            try:
                if float(key) <= float(val):
                    last_match = row[col_idx] if col_idx < len(row) else REF
            except (TypeError, ValueError):
                pass
    return last_match


@register("HLOOKUP")
def fn_hlookup(val: Any, range_val: Any, row_num: Any, approx: Any = True) -> Any:
    table = _flat2d(range_val)
    try:
        row_idx = int(row_num) - 1
    except (TypeError, ValueError):
        return TYPE_ERR
    if not table or not table[0]:
        return NA

    exact = not _truthy(approx)
    header = table[0]
    last_col = -1

    for ci, key in enumerate(header):
        if exact:
            if key == val:
                return (
                    table[row_idx][ci] if row_idx < len(table) and ci < len(table[row_idx]) else REF
                )
        else:
            if key == val:
                return table[row_idx][ci] if row_idx < len(table) else REF
            try:
                if float(key) <= float(val):
                    last_col = ci
            except (TypeError, ValueError):
                pass
    if last_col >= 0:
        return table[row_idx][last_col] if row_idx < len(table) else REF
    return NA


@register("INDEX")
def fn_index(range_val: Any, row_num: Any, col_num: Any = 1) -> Any:
    table = _flat2d(range_val)
    try:
        r, c = int(row_num) - 1, int(col_num) - 1
    except (TypeError, ValueError):
        return TYPE_ERR
    if r < 0 or c < 0 or r >= len(table):
        return REF
    row = table[r]
    if c >= len(row):
        return REF
    return row[c]


@register("MATCH")
def fn_match(val: Any, range_val: Any, match_type: Any = 1) -> Any:
    flat = []
    for row in _flat2d(range_val):
        flat.extend(row)
    try:
        mt = int(match_type)
    except (TypeError, ValueError):
        return TYPE_ERR

    if mt == 0:
        for i, v in enumerate(flat):
            if v == val:
                return i + 1
        return NA
    elif mt == 1:
        best = -1
        for i, v in enumerate(flat):
            try:
                if float(v) <= float(val):
                    best = i
            except (TypeError, ValueError):
                pass
        return best + 1 if best >= 0 else NA
    else:
        best = -1
        for i, v in enumerate(flat):
            try:
                if float(v) >= float(val) and best == -1:
                    best = i
            except (TypeError, ValueError):
                pass
        return best + 1 if best >= 0 else NA


@register("XLOOKUP")
def fn_xlookup(val: Any, lookup: Any, ret: Any, miss: Any = NA) -> Any:
    lu = []
    for row in _flat2d(lookup):
        lu.extend(row)
    rv = []
    for row in _flat2d(ret):
        rv.extend(row)
    for i, v in enumerate(lu):
        if v == val:
            return rv[i] if i < len(rv) else REF
    return miss


@register("CHOOSE")
def fn_choose(idx: Any, *vals: Any) -> Any:
    try:
        i = int(idx) - 1
        if 0 <= i < len(vals):
            return vals[i]
        return ERR
    except (TypeError, ValueError):
        return TYPE_ERR


@register("ROW")
def fn_row(cell: Any = None) -> Any:
    # When called without args in evaluator, row context is injected externally
    return 1  # placeholder; evaluator injects context


@register("COL")
def fn_col(cell: Any = None) -> Any:
    return 1  # placeholder


@register("ROWS")
def fn_rows(range_val: Any) -> Any:
    return len(_flat2d(range_val))


@register("COLS")
def fn_cols(range_val: Any) -> Any:
    table = _flat2d(range_val)
    return max(len(row) for row in table) if table else 0


@register("OFFSET")
def fn_offset(ref: Any, rows: Any, cols: Any, h: Any = 1, w: Any = 1) -> Any:
    # Returns a marker dict; evaluator resolves the actual range
    return {"__offset__": (ref, rows, cols, h, w)}


@register("INDIRECT")
def fn_indirect(addr: Any) -> Any:
    # Returns a marker; evaluator resolves
    return {"__indirect__": str(addr)}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _truthy(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, int | float):
        return v != 0
    if isinstance(v, str):
        return v.upper() not in ("FALSE", "0", "")
    return v is not None
