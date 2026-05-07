"""Adjust cell references inside a formula string by a row/column offset."""

from __future__ import annotations

import re

from vimsheet.model.range import col_index_to_letters, col_letters_to_index

# Matches optional $ before col letters, col letters, optional $ before row digits, row digits
_CELL_REF_RE = re.compile(r"(\$?)([A-Za-z]{1,3})(\$?)([0-9]+)")

_STRING_PAT = re.compile(r'"(?:[^"\\]|\\.)*"')

# Sheet-prefixed reference: SheetName!A1 or SheetName!A1:B2
_SHEET_PREFIX_PAT = re.compile(
    r"([A-Za-z_][A-Za-z0-9_ .]*)!"  # sheet prefix
    r"(\$?[A-Za-z]{1,3}\$?\d+(?::\$?[A-Za-z]{1,3}\$?\d+)?)"  # cell or range ref
)


def _protect_strings(formula: str) -> tuple[str, list[str]]:
    """Replace quoted strings with placeholders, return (modified, originals).

    Uses separator underscores in placeholders so they don't match _CELL_REF_RE.
    """
    placeholders: list[str] = []

    def replacer(m: re.Match) -> str:
        placeholders.append(m.group(0))
        return f"__STR_{len(placeholders) - 1}_"

    result = _STRING_PAT.sub(replacer, formula)
    return result, placeholders


def _restore_strings(formula: str, originals: list[str]) -> str:
    for i, orig in enumerate(originals):
        formula = formula.replace(f"__STR_{i}_", orig)
    return formula


def _protect_sheet_prefixes(body: str) -> tuple[str, list[tuple[str, str]]]:
    """Replace sheet-prefixed refs with placeholders.

    Returns (modified_body, list_of_(original, cell_part)).
    The cell part will be adjusted later and recombined.
    """
    placeholders: list[tuple[str, str]] = []

    def replacer(m: re.Match) -> str:
        _ = m.group(1)
        cell_part = m.group(2)
        placeholders.append((m.group(0), cell_part))
        return f"__SHEET_{len(placeholders) - 1}_"

    result = _SHEET_PREFIX_PAT.sub(replacer, body)
    return result, placeholders


def _restore_sheet_prefixes(
    body: str,
    originals: list[tuple[str, str]],
    dst_row: int,
    col_offset: int,
    same_row: bool,
) -> str:
    for i, (orig, cell_part) in enumerate(originals):
        adjusted_cell = _adjust_ref_str(cell_part, dst_row, col_offset, same_row)
        sheet_prefix = orig[: orig.index("!") + 1]
        body = body.replace(f"__SHEET_{i}_", f"{sheet_prefix}{adjusted_cell}")
    return body


def _adjust_ref_str(ref_str: str, dst_row: int, col_offset: int, same_row: bool) -> str:
    """Adjust a single cell/range reference string (e.g. 'B2' or 'A1:C3')."""

    def replacer(m: re.Match) -> str:
        return _adjust_ref(m, dst_row, col_offset, same_row)

    return _CELL_REF_RE.sub(replacer, ref_str)


def _adjust_ref(match: re.Match, dst_row: int, col_offset: int, same_row: bool) -> str:
    col_abs = match.group(1) == "$"
    col_str = match.group(2).upper()
    row_abs = match.group(3) == "$"
    row_str = match.group(4)

    col_idx = col_letters_to_index(col_str)

    new_col = col_idx if col_abs else col_idx + col_offset
    if row_abs:
        new_row = int(row_str) - 1  # keep absolute row
    elif same_row:
        new_row = int(row_str) - 1  # dst == src — keep original row
    else:
        new_row = dst_row  # set to destination row

    if new_col < 0:
        return "#REF"

    col_prefix = "$" if col_abs else ""
    row_prefix = "$" if row_abs else ""
    return f"{col_prefix}{col_index_to_letters(new_col)}{row_prefix}{new_row + 1}"


def adjust_formula(
    formula: str | None,
    dst_row: int,
    dst_col: int,
    src_row: int,
    src_col: int,
) -> str | None:
    """Return *formula* with references adjusted for paste from
        *(src_row, src_col)* to *(dst_row, dst_col)*.

    Non-absolute row references are SET to the destination row number (dst_row + 1 in 1-based).
    Non-absolute column references are shifted by the column offset.

    Rules:
    - $B$2  → never adjusted (both axes locked)
    - $B2   → col locked, row set to destination row
    - B$2   → row locked, col shifted by col offset
    - B2    → row set to dst row, col shifted by col offset

    If formula does not start with '=', returns it unchanged.
    Returns None when formula is None.
    """
    if not formula or not formula.startswith("="):
        return formula
    col_offset = dst_col - src_col
    if col_offset == 0 and dst_row == src_row:
        return formula
    same_row = dst_row == src_row

    body = formula[1:]  # strip leading =
    body, sheet_refs = _protect_sheet_prefixes(body)
    body, strings = _protect_strings(body)

    body = _adjust_ref_str(body, dst_row, col_offset, same_row)

    body = _restore_strings(body, strings)
    body = _restore_sheet_prefixes(body, sheet_refs, dst_row, col_offset, same_row)
    return "=" + body
