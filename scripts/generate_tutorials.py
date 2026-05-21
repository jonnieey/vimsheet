#!/usr/bin/env python3
"""Generate all 21 tutorial .vimsheet originals."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "vimsheet" / "tutorials" / "originals"
VSCRIPT_DIR = Path(__file__).resolve().parent.parent / "examples" / "tutorial" / "_scripts"

# ── Colour palette ───────────────────────────────────────────────────
BLUE = "#61afef"
GREEN = "#98c379"
YELLOW = "#e5c07b"
CYAN = "#56b6c2"
RED = "#e06c75"
WHITE = "#ffffff"
GRAY = "#5c6370"
DGRAY = "#2c313a"

# ── Helpers ──────────────────────────────────────────────────────────


def c(row: int, col: int, value: str | int | float, **fmt) -> dict:
    d: dict = {"row": row, "col": col, "value": value}
    if fmt:
        d["fmt"] = {k: v for k, v in fmt.items() if v is not None}
    return d


def title_row(lesson: str, subtitle: str) -> list[dict]:
    return [
        c(0, 0, f"VIMSHEET TUTORIAL  —  {lesson}", bold=True, align="left", fg_color=BLUE),
        c(0, 1, subtitle, italic=True, align="left", fg_color=GREEN),
    ]


def header_row(cols: list[str]) -> list[dict]:
    return [c(2, i, label, bold=True, bg_color=DGRAY, align="left") for i, label in enumerate(cols)]


def sep_row(row: int, label: str = "") -> list[dict]:
    sep = "─" * 50
    return [c(row, 0, label or sep, bold=True, align="left", fg_color=GRAY)]


def wrap_text(text: str, width: int = 57) -> str:
    """Wrap each line at word boundaries, preserving existing ``\\n`` breaks."""
    out: list[str] = []
    for line in text.split("\n"):
        if len(line) <= width:
            out.append(line)
            continue
        parts: list[str] = []
        while line:
            if len(line) <= width:
                parts.append(line)
                break
            chunk = line[:width]
            if " " in chunk:
                brk = chunk.rfind(" ")
                parts.append(line[:brk])
                line = line[brk + 1 :]
            else:
                parts.append(chunk)
                line = line[width:]
        out.append("\n".join(parts))
    return "\n".join(out)


def note_row(row: int, text: str, **kw) -> list[dict]:
    return [c(row, 0, wrap_text(text), align="left", fg_color=kw.pop("fg", RED), italic=True, **kw)]


def step_row(
    row: int, instruction: str, *data: tuple[int, str | int | float], target_col: int | None = None
) -> list[dict]:
    """One step: instruction in col A, data cells in cols B+."""
    cells = [c(row, 0, wrap_text(instruction), align="left", fg_color=YELLOW)]
    for col_offset, val in data:
        fmt_kw = {"align": "right", "fg_color": WHITE}
        if target_col is not None and col_offset == target_col:
            fmt_kw["bg_color"] = RED
            fmt_kw["fg_color"] = WHITE
        cells.append(c(row, col_offset, val, **fmt_kw))
    return cells


def cmd_row(row: int, command: str, description: str) -> list[dict]:
    return [
        c(row, 0, command, align="left", fg_color=CYAN),
        c(row, 1, wrap_text(description), align="left", fg_color=GREEN),
    ]


def build_sheet(
    name: str,
    cells: list[dict],
    col_widths: dict[str, int] | None = None,
    freeze_rows: int = 3,
    freeze_cols: int = 1,
    cursor_row: int = 4,
    cursor_col: int = 0,
) -> dict:
    return {
        "name": name,
        "col_widths": col_widths
        or {
            "0": 60,
            "1": 15,
            "2": 15,
            "3": 15,
            "4": 15,
            "5": 15,
        },
        "freeze_rows": freeze_rows,
        "freeze_cols": freeze_cols,
        "cells": cells,
        "cursor_row": cursor_row,
        "cursor_col": cursor_col,
    }


def save(num: int, fname: str, data: dict) -> None:
    path = OUTPUT_DIR / f"{fname}.vimsheet"
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"  ✓ {num:2d}  {fname}")


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 00 — General
# ═══════════════════════════════════════════════════════════════════════
def lesson_00() -> dict:
    cells = title_row("GENERAL", "Overview of essential commands and shortcuts")
    cells += header_row(["Action", "Command", "Notes"])
    rows = [
        (3, "Show help screen", "f1  /  :help", "Opens the built-in help browser"),
        (4, "Show version", ":version", "Display version info"),
        (5, "Show file info", "Ctrl+g", "File name, path, sheet count"),
        (6, "Show messages", ":messages", "View recent message log"),
        (7, "List functions", ":funcs", "All registered formula functions"),
        (8, "", "", ""),
        (9, "── FILE OPERATIONS ──", "", ""),
        (10, "Save", ":w", "Write to current file path"),
        (11, "Save as", ":w {file}", "Save to a new file"),
        (12, "Open file", ":e {file}", "Load CSV, XLSX, .vimsheet, etc."),
        (13, "Export", ":ex {fmt} {file}", "fmt: csv tsv json xlsx mkd tex html"),
        (14, "Quit", ":q", "Warns if unsaved changes exist"),
        (15, "Force quit", ":q!", "Discard changes and quit"),
        (16, "Save & quit", ":wq / :x / ZZ", "Save then exit"),
        (17, "", "", ""),
        (18, "── EDITING ──", "", ""),
        (19, "Repeat last action", ".", "Replays the last edit or command"),
        (20, "Refresh screen", "Ctrl+l", "Redraw the terminal"),
        (21, "Open external editor", "gw", "Edit cell in $EDITOR / $VISUAL"),
        (22, "Auto-fit column", "_ / :autofit", "Resize column to content width"),
        (23, "Undo", "u", "Undo last change"),
        (24, "Redo", "Ctrl+r", "Redo last undone change"),
        (25, "", "", ""),
        (26, "── MODES ──", "", ""),
        (27, "Normal", "Esc", "Navigate and issue commands"),
        (28, "Insert", "\\ = < > A I S", "Type new content into a cell"),
        (29, "Edit", "e  E", "Modify existing cell content"),
        (30, "Command", ":", "Run colon commands"),
        (31, "Visual", "v  V  Ctrl+v", "Select a range of cells"),
        (32, "", "", ""),
        (39, "TIP: Press f1 at any time to open the help screen.", "", ""),
    ]
    for r, a, b, n in rows:
        if a:
            cells.append(c(r, 0, wrap_text(a, 40), align="left", fg_color=YELLOW))
        if b:
            cells.append(c(r, 1, b, align="left", fg_color=CYAN))
        if n:
            cells.append(c(r, 2, wrap_text(n, 40), align="left", fg_color=GREEN))
    return build_sheet(
        "General",
        cells,
        col_widths={"0": 45, "1": 28, "2": 44},
        freeze_rows=2,
        cursor_row=3,
        cursor_col=0,
    )


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 01 — Navigation
# ═══════════════════════════════════════════════════════════════════════
def lesson_01() -> dict:
    cells = title_row("NAVIGATION", "Move around the spreadsheet with vim keys")
    cells += header_row(["#  Instruction", "Q1", "Q2", "Q3", "Q4"])

    sales = [
        (3, 1200, 1450, 1100, 1600),
        (4, 2300, 2100, 2500, 2800),
        (5, 800, 950, 1050, 900),
        (6, 3100, 2900, 3300, 3500),
        (7, 1700, 1600, 1800, 2000),
        (8, 900, 1100, 1000, 1200),
        (9, 4200, 3900, 4500, 4800),
        (10, 550, 600, 650, 700),
        (11, 1300, 1400, 1350, 1500),
        (12, 2800, 2600, 2900, 3100),
        (13, 700, 750, 800, 850),
        (14, 5000, 4800, 5200, 5500),
        (15, 1100, 1200, 1150, 1300),
        (16, 3400, 3200, 3600, 3800),
        (17, 600, 650, 700, 750),
    ]
    for row_idx, q1, q2, q3, q4 in sales:
        cells.append(c(row_idx, 1, q1, align="right", fg_color=WHITE))
        cells.append(c(row_idx, 2, q2, align="right", fg_color=WHITE))
        cells.append(c(row_idx, 3, q3, align="right", fg_color=WHITE))
        cells.append(c(row_idx, 4, q4, align="right", fg_color=WHITE))

    # cursor_row=3 → starts on B4 (first data row, col B)
    steps = [
        (3, "1. Press l — move right one cell. h — left."),
        (4, "2. Press j — move down one row. k — move up."),
        (5, "3. Press w — skip right to next filled block. b — back."),
        (6, "4. Press $ — jump to the last cell in this row."),
        (7, "5. Press ^ — jump to the first data cell in the row."),
        (8, "6. Press 0 — go to column A (the instruction column)."),
        (9, "7. Press gg — first row of the sheet. G — last row."),
        (10, "8. Type 5G — jump to row 5. (Any number + G works.)"),
        (
            11,
            "9. Ctrl+f or PgDn — scroll one full page down.\n   Ctrl+b or PgUp — scroll one full page up.",  # noqa: E501
        ),
        (12, "10. Ctrl+d — half-page down. Ctrl+u — half-page up."),
        (13, "11. H — top of visible screen. M — middle. L — bottom."),
        (14, "12. Ctrl+e / Ctrl+y — scroll the view without\nmoving the cursor."),
        (15, "13. Type goC6 <enter> — jump directly to cell C6.\n    (Try goD12, goB9, etc.)"),
        (
            16,
            "14. Press ze - scroll the view right. zs - scroll the view left. (without moving cursor)",  # noqa: E501
        ),
        (17, "15. Ctrl+g — show file name and current position."),
        (18, "16. Ctrl+l — redraw the screen if it looks corrupted."),
    ]
    for instr_row, instr in steps:
        cells.append(c(instr_row, 0, wrap_text(instr), align="left", fg_color=YELLOW))

    instr_9_5 = "9.5. Ctrl+b or PgUp — scroll one full page up."
    cells.append(c(25, 0, wrap_text(instr_9_5), align="left", fg_color=YELLOW))

    cells += note_row(20, "Column A is frozen — it stays visible as you scroll right.")
    cells += note_row(21, "TIP: goADDRESS works with any A1 address: goA1, goE14, etc.")

    return build_sheet("Navigation", cells, cursor_row=3, cursor_col=1)


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 02 — Cell Editing
# ═══════════════════════════════════════════════════════════════════════
def lesson_02() -> dict:
    cells = title_row("CELL EDITING", "Enter, edit, and delete cell contents")
    cells += header_row(["#  Instruction", "Contact List"])

    # Each contact has a deliberate issue to fix — one per step.
    contacts = [
        (3, "Alice Chen"),  # step 1 — explore EDIT mode (e)
        (4, "Bob  Kumar"),  # step 2 — fix double space with e + x
        (5, "Charlie"),  # step 3 — append last name with A
        (6, "Engineer"),  # step 4 — insert prefix with I
        (7, "old placeholder"),  # step 5 — replace entire cell with r
        (8, "rewrite this"),  # step 6 — clear + re-enter with S
        (9, "cut me"),  # step 7 — cut with x
        (10, "delete this row"),  # step 9 — delete row with dd
    ]
    for row_idx, name in contacts:
        cells.append(c(row_idx, 1, name, align="left", fg_color=WHITE))

    # cursor_row=3 → starts on B4 (Alice Chen)
    steps = [
        (3, "1. Press e — EDIT mode. h/l moves inside the text.\nEsc exits without saving."),
        (
            4,
            "2. Go to B5. Press e — edit Bob Kumar.\nMove to the extra space. x deletes it. Enter saves.",  # noqa: E501
        ),
        (5, "3. Go to B6. Press A — append to end.\nType ' Smith', then Esc."),
        (
            6,
            "4. Go to B7. Press I — insert at beginning.\nType 'Sr. ', then Esc. Reads 'Sr. Engineer'.",  # noqa: E501
        ),
        (7, "5. Go to B8. Press r — replace mode.\nType new content, then Enter."),
        (8, "6. Go to B9. Press S — clear cell and enter INSERT.\nType new text, then Esc."),
        (9, "7. Go to B10. Press x — cut the cell to the register."),
        (10, "8. Go to B12 (empty). Press p — paste the cut value."),
        (11, "9. Go to B11. Press dd — delete the entire row.\nRows below shift up."),
        (12, "10. Press u — undo the delete. Ctrl+r — redo it."),
        (13, "11. Move to any cell. Press . — repeat the last action."),
    ]
    for row_idx, instr in steps:
        cells.append(c(row_idx, 0, wrap_text(instr), align="left", fg_color=YELLOW))

    cells += note_row(
        15,
        "x cuts one cell. dd deletes the whole row.\nBoth go to the register and can be pasted with p.",  # noqa: E501
    )
    cells += note_row(16, "e — EDIT (cursor at start).  E — EDIT (cursor at end).")

    return build_sheet("CellEditing", cells, cursor_row=3, cursor_col=1)


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 03 — Copy & Paste
# ═══════════════════════════════════════════════════════════════════════
def lesson_03() -> dict:
    cells = title_row("COPY, CUT & PASTE", "Yank, paste, cut, and named registers")
    cells += header_row(["#  Instruction", "Jan", "Feb", "=Jan+Feb"])

    # D column uses formulas — paste shows automatic reference adjustment.
    grid = [
        (3, 1000, 1200, "=B4+C4"),
        (4, 1500, 1800, ""),
        (5, 800, 950, ""),
        (6, 2200, 2400, ""),
        (7, 1100, 1300, ""),
    ]
    for row_idx, v1, v2, formula in grid:
        cells.append(c(row_idx, 1, v1, align="right", fg_color=WHITE))
        cells.append(c(row_idx, 2, v2, align="right", fg_color=WHITE))
        cells.append(c(row_idx, 3, formula, align="right", fg_color=CYAN))

    # cursor_row=3 → starts on B4
    steps = [
        (3, "1. Go to B4. Press yy — yank (copy) this cell."),
        (4, "2. Go to B10. Press p — paste. B10 now holds 1000."),
        (5, "3. Go to D4 (the =B4+C4 formula). Press yy — yank it."),
        (6, "4. Go to D5. Press p — paste.\nFormula becomes =B5+C5 — refs shift automatically!"),
        (
            7,
            "5. Go to D4 again. Press YY — yank the VALUE only\n(no formula). Number 2200 goes into the register.",  # noqa: E501
        ),
        (8, "6. Go to E4. Press P — paste. D11 gets 2200 as a\nplain number, not a formula."),
        (9, "7. Go to C5. Press x — cut the cell (it empties)."),
        (10, "8. Go to C10. Press p — paste. You moved the cell."),
        (11, "9. Go to row 4. Press yr — yank the entire row."),
        (12, "10. Go to row 12. Press p — paste the whole row."),
        (
            13,
            '11. Go to B4. Press "a yy — yank into register a.\n("a is a prefix; use "a through "z for 26 slots.)',  # noqa: E501
        ),
        (14, '12. Go to B14. Press "a p — paste from register a.'),
        (
            15,
            '13. Press "+ yy — yank to the system clipboard.\n(Requires clipboard support in your terminal.)',  # noqa: E501
        ),
    ]
    for row_idx, instr in steps:
        cells.append(c(row_idx, 0, wrap_text(instr), align="left", fg_color=YELLOW))

    cells += note_row(
        17,
        "yy copies with formula.  YY copies the displayed value.\nFormula refs shift on paste; value paste does not.",  # noqa: E501
    )
    cells += note_row(18, '"a – "z are 26 named registers.  "+ is the system clipboard.')

    return build_sheet("CopyPaste", cells, cursor_row=3, cursor_col=1)


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 04 — Undo / Redo
# ═══════════════════════════════════════════════════════════════════════
def lesson_04() -> dict:
    cells = title_row("UNDO, REDO & REPEAT", "Undo, redo, cell history, and dot-repeat")
    cells += header_row(["#  Instruction", "Value"])

    for i, v in enumerate([100, 200, 300, 400, 500, 600, 700, 800], 3):
        cells.append(c(i, 1, v, align="right", fg_color=WHITE))

    # cursor_row=3 → starts on B4 (value 200)
    steps = [
        (3, "1. Go to B5 (200). Ctrl+a — increment by 1 → 201."),
        (4, "2. Press 5 Ctrl+a — increment by 5 at once → 206."),
        (5, "3. Go to B6 (300). Ctrl+x — decrement by 1.\nPress 10 Ctrl+x — decrement by 10."),
        (6, "4. Press u — undo the last change.\nKeep pressing u to undo more steps."),
        (7, "5. Press Ctrl+r — redo the last undone change.\nPress repeatedly to redo further."),
        (8, "6. Go to B4. Press r, type 999, Enter\n— replaces B4 with 999."),
        (9, "7. Go to B5. Press . — dot-repeat.\nB5 is also replaced with 999."),
        (10, "8. Go to B6. Press . again.\n. repeats the last change on the current cell."),
        (
            11,
            "9. Press u three times — undoes all three replacements.\nAll original values restored.",  # noqa: E501
        ),
        (12, "10. Go to B4. Type :history Enter\n— shows the full change history for this cell."),
    ]
    for row_idx, instr in steps:
        cells.append(c(row_idx, 0, wrap_text(instr), align="left", fg_color=YELLOW))

    cells += note_row(
        14,
        "u = undo one step.  Ctrl+r = redo.\n. = repeat last change — no undo needed, just move and press dot.",  # noqa: E501
    )

    return build_sheet("UndoRedo", cells, cursor_row=3, cursor_col=1)


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 05 — Marks & Search
# ═══════════════════════════════════════════════════════════════════════
def lesson_05() -> dict:
    cells = title_row("MARKS & SEARCH", "Set marks, jump between them, search cells")
    cells += header_row(["#  Instruction", "Product", "Category", "Price"])

    catalog = [
        (3, "apple", "fruit", 0.99),
        (4, "banana", "fruit", 0.49),
        (5, "carrot", "vegetable", 0.79),
        (6, "apple cider", "beverage", 3.49),
        (7, "broccoli", "vegetable", 1.29),
        (8, "cherry", "fruit", 2.99),
        (9, "banana bread", "bakery", 4.99),
        (10, "spinach", "vegetable", 1.49),
        (11, "apple juice", "beverage", 2.49),
        (12, "peach", "fruit", 1.79),
    ]
    for row_idx, prod, cat, price in catalog:
        cells.append(c(row_idx, 1, prod, align="left", fg_color=WHITE))
        cells.append(c(row_idx, 2, cat, align="left", fg_color=GREEN))
        cells.append(c(row_idx, 3, price, align="right", fg_color=CYAN))

    # cursor_row=3 → starts on B4 (apple)
    steps = [
        (
            3,
            "1. Go to B4 (apple). Press m a — set mark a here.\nMarks are invisible bookmarks you can jump back to.",  # noqa: E501
        ),
        (4, "2. Press G — jump to the last row.\nNow press ' a — jump back to mark a instantly."),
        (5, "3. Go to B10 (banana bread). Press m b — set mark b."),
        (
            6,
            "4. Navigate anywhere, then press ' b — jump to banana bread.\nPress ' a — jump back to apple.",  # noqa: E501
        ),
        (7, "5. Press /apple Enter — search forward for 'apple'.\nAll matches are highlighted."),
        (
            8,
            "6. Press n — next match. Keep pressing to cycle forward.\nPress N — go to the previous match.",  # noqa: E501
        ),
        (9, "7. Press ?vegetable Enter — search backward.\nNotice n/N reverse direction with ?."),
        (
            10,
            "8. Go to B9 (cherry). Press * — search forward\nfor the exact value of the current cell.",  # noqa: E501
        ),
        (11, "9. Press # — search backward for the same value."),
    ]
    for row_idx, instr in steps:
        cells.append(c(row_idx, 0, wrap_text(instr), align="left", fg_color=YELLOW))

    cells += note_row(
        14,
        "Marks a–z persist until you quit. Set them on totals,\nheaders or reference rows you return to often.",  # noqa: E501
    )
    cells += note_row(
        15, "/ and ? support regex. Try /^apple to match cells\nthat start with 'apple'."
    )

    return build_sheet("Marks", cells, cursor_row=3, cursor_col=1)


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 06 — Modes
# ═══════════════════════════════════════════════════════════════════════
def lesson_06() -> dict:
    cells = title_row("MODES", "Understand VimSheet's five modes")
    cells += [
        c(2, 0, "Mode", bold=True, bg_color=DGRAY, align="left"),
        c(2, 1, "Enter via", bold=True, bg_color=DGRAY, align="left"),
        c(2, 2, "Purpose", bold=True, bg_color=DGRAY, align="left"),
    ]
    modes = [
        (3, "NORMAL  --NORMAL--", "Esc  (from any mode)", "Navigate, copy, paste, delete, undo"),
        (4, "INSERT  --INSERT--", "\\ = < > A I S", "Type new content into a cell"),
        (5, "EDIT    --EDIT--", "e  E", "Modify existing cell content"),
        (6, "COMMAND  --CMD--", ":", "Run colon commands (:w, :sort, :help)"),
        (7, "VISUAL  --VISUAL--", "v  V  Ctrl+v", "Select a range for operations"),
    ]
    for row_idx, mode, enter, purpose in modes:
        cells.append(c(row_idx, 0, mode, align="left", fg_color=CYAN))
        cells.append(c(row_idx, 1, enter, align="left", fg_color=YELLOW))
        cells.append(c(row_idx, 2, purpose, align="left", fg_color=GREEN))

    cells += sep_row(9)
    notes = [
        (
            10,
            "Press Esc from any mode to return to NORMAL.\nNORMAL is the home base — go here if unsure.",  # noqa: E501
        ),
        (
            11,
            "\\ = left-align INSERT.  = = right-align (formula prefix).\n< = left,  > = right,  A = append,  I = insert at start.",  # noqa: E501
        ),
        (
            12,
            "Press : to enter COMMAND. Type a command such as\n:w or :sort B asc then press Enter.",
        ),
        (
            13,
            "v = cell selection.  V = whole rows.\nCtrl+v = rectangular block. Move cursor to extend.",  # noqa: E501
        ),
        (14, "e = EDIT (cursor at start of cell text).\nE = EDIT with cursor at the END."),
    ]
    for row_idx, text in notes:
        cells.append(c(row_idx, 0, wrap_text(text), align="left", fg_color=YELLOW))

    cells += note_row(
        16,
        "Check the status bar (bottom-left) to always know\nwhich mode you are in. If a key misbehaves, press Esc first.",  # noqa: E501
    )

    return build_sheet(
        "Modes",
        cells,
        col_widths={"0": 50, "1": 32, "2": 50},
        cursor_row=3,
        cursor_col=0,
    )


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 07 — Insert & Edit Mode
# ═══════════════════════════════════════════════════════════════════════
def lesson_07() -> dict:
    cells = title_row("INSERT & EDIT", "Deep-dive into cell entry and editing")
    cells += header_row(["#  Instruction", "Name", "Score", "Grade"])

    students = [
        (3, "Alice Johnson", 88, "B+"),
        (4, "Bob Martinez", 74, "C"),
        (5, "Carol White", 95, "A"),
        (6, "Dave Brown", 61, "D"),
        (7, "Eve Nguyen", 82, "B"),
        (8, "Frank Lee", 90, "A-"),
    ]
    for row_idx, name, score, grade in students:
        cells.append(c(row_idx, 1, name, align="left", fg_color=WHITE))
        cells.append(c(row_idx, 2, score, align="right", fg_color=WHITE))
        cells.append(c(row_idx, 3, grade, align="left", fg_color=CYAN))

    # cursor_row=3 → starts on B4 (Alice Johnson)
    steps = [
        (
            3,
            "1. Go to B9 (empty, below the list).\nPress \\ — INSERT mode. Type a new name, Enter.",
        ),
        (
            4,
            "2. Cursor moved to B10. Type another name, Enter.\nThis is the natural multi-entry INSERT flow.",  # noqa: E501
        ),
        (5, "3. Go to C9. Press = — INSERT (right-aligned).\nType a score, e.g. 77, then Enter."),
        (
            6,
            "4. Go to B4 (Alice Johnson). Press e — EDIT mode.\nUse h and l to move inside the text.",  # noqa: E501
        ),
        (7, "5. In EDIT mode on B4: press w — jump word forward.\nPress b — jump word backward."),
        (8, "6. Press 0 — go to start of cell text.\nPress $ — go to end of cell text."),
        (9, "7. Position cursor on 'Johnson'. Press dw — delete word.\nPress Enter to save."),
        (
            10,
            "8. Go to B5. Press E — EDIT with cursor at the END.\nPress A — switch to INSERT at end.\nType ' Jr.', then Esc.",  # noqa: E501
        ),
        (11, "9. Go to B6. Press I — INSERT at the beginning.\nType 'Dr. ', then Esc."),
        (
            12,
            "10. Go to C6 (score 61). Press S — clear and INSERT.\nType the corrected score, then Esc.",  # noqa: E501
        ),
        (
            13,
            "11. In INSERT or EDIT mode: Alt+Enter inserts a\nnewline within the cell (multi-line content).",  # noqa: E501
        ),
    ]
    for row_idx, instr in steps:
        cells.append(c(row_idx, 0, wrap_text(instr), align="left", fg_color=YELLOW))

    cells += note_row(
        15,
        "EDIT mode motions: h l w b 0 $ move cursor.\nx deletes one char.  dw deletes a word.  d$ deletes to end.",  # noqa: E501
    )
    cells += note_row(
        16,
        "Tab in INSERT mode triggers formula auto-complete.\nType =SUM and press Tab to cycle through functions.",  # noqa: E501
    )

    return build_sheet("InsertEdit", cells, cursor_row=3, cursor_col=1)


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 08 — Visual Mode
# ═══════════════════════════════════════════════════════════════════════
def lesson_08() -> dict:
    cells = title_row("VISUAL MODE", "Select ranges, yank, delete, sort, and format")
    cells += header_row(["#  Instruction", "Name", "Dept"])

    employees = [
        (3, "Alice", "Engineering"),
        (4, "Bob", "Marketing"),
        (5, "Charlie", "Engineering"),
        (6, "Diana", "HR"),
        (7, "Eve", "Engineering"),
        (8, "Frank", "Marketing"),
        (9, "Grace", "HR"),
        (10, "Henry", "Engineering"),
    ]
    for row_idx, name, dept in employees:
        cells.append(c(row_idx, 1, name, align="left", fg_color=WHITE))
        cells.append(c(row_idx, 2, dept, align="left", fg_color=GREEN))

    # cursor_row=3 → starts on B4 (Bob)
    steps = [
        (
            3,
            "1. Go to B4. Press v — VISUAL mode.\nMove j/l to extend selection to D6 (3 rows).\nPress y — yank. Esc to deselect.",  # noqa: E501
        ),
        (4, "2. Go to B13. Press p — paste the 3-row block."),
        (
            5,
            "3. Go to row 4. Press V — VISUAL LINE mode (whole rows).\nPress j twice to select rows 4–6.\nPress d — delete all three rows.",  # noqa: E501
        ),
        (6, "4. Press u — undo. The rows come back."),
        (
            7,
            "5. Go to B4. Press Ctrl+v — VISUAL BLOCK mode.\nSelect B4:C6 (3 rows, 2 cols).\nPress > — shift the block one column right.",  # noqa: E501
        ),
        (8, "6. Press < — shift the block back left."),
        (
            9,
            "7. Select B4:B8 with v. Press ss — sort the selected\nrows by the first selected column.",  # noqa: E501
        ),
        (
            10,
            "8. Select D4:D11 a visual selection, press : — the command bar\nshows the range pre-filled. Type fill 0, Enter.\nAll selected cells become 0.",  # noqa: E501
        ),
        (11, "9. Press u to undo the fill."),
        (12, "10. Select C4:C11 with v. Press tb — toggle BOLD\nacross the entire selected range."),
    ]
    for row_idx, instr in steps:
        cells.append(c(row_idx, 0, wrap_text(instr), align="left", fg_color=YELLOW))

    cells += note_row(
        14,
        "v = cell range.  V = whole rows.  Ctrl+v = block.\nPress o inside a selection to flip the active corner.",  # noqa: E501
    )
    cells += note_row(
        15,
        "After v + y, paste with p. Formula refs in the range\nshift automatically — just like a single-cell paste.",  # noqa: E501
    )

    return build_sheet("VisualMode", cells, cursor_row=3, cursor_col=1)


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 09 — Row & Column Ops
# ═══════════════════════════════════════════════════════════════════════
def lesson_09() -> dict:
    cells = title_row("ROW & COLUMN OPS", "Insert, delete, hide, resize rows and columns")
    cells += header_row(["#  Instruction", "Name", "Age", "City"])

    grid = [
        (3, "Alice", 28, "Berlin"),
        (4, "Bob", 35, "Paris"),
        (5, "Charlie", 42, "London"),
        (6, "Diana", 31, "Madrid"),
        (7, "Eve", 26, "Rome"),
        (8, "Frank", 39, "Vienna"),
        (9, "Grace", 33, "Prague"),
    ]
    for row_idx, name, age, city in grid:
        cells.append(c(row_idx, 1, name, align="left", fg_color=WHITE))
        cells.append(c(row_idx, 2, age, align="right", fg_color=WHITE))
        cells.append(c(row_idx, 3, city, align="left", fg_color=WHITE))

    # cursor_row=3 → starts on B4 (Bob)
    steps = [
        (
            3,
            "1. Go to B6 (Charlie). Press ir — insert a blank row ABOVE.\nCharlie shifts down. Press u — undo.",  # noqa: E501
        ),
        (
            4,
            "2. Press iR — insert a blank row BELOW Charlie.\nType 'Temp' in B5, Esc. Press dr — delete the row.",  # noqa: E501
        ),
        (
            5,
            "3. Go to column C (Age). Press ic — insert a column LEFT.\n. Press dc — delete it. Press IC — insert a column RIGHT. Press u - undo.",  # noqa: E501
        ),
        (
            6,
            "4. Go to column B. Press + three times — widen column B.\nPress - three times — narrow it back.",  # noqa: E501
        ),
        (7, "5. Press _ (underscore) — auto-fit column B\nto the width of its widest value."),
        (
            8,
            "6. Press V to enter VISUAL LINE. Select rows 5–6\n(Charlie and Diana). Press sR — hide them.",  # noqa: E501
        ),
        (9, "7. The rows disappear but are NOT deleted.\nPress sr — show (unhide) them again."),
        (
            10,
            "8. Go to B4. Press yr — yank the entire row 4.\nGo to row 11. Press p — paste a copy of the row.\nUseful for duplicating a template row.",  # noqa: E501
        ),
        (
            11,
            "9. Press z_ — collapse the current row to minimum height.\nPress z+ — expand it back to normal height.",  # noqa: E501
        ),
        (12, "10. Go to B5. Press dc to delete the current column.\nPress u to undo."),
    ]
    for row_idx, instr in steps:
        cells.append(c(row_idx, 0, wrap_text(instr), align="left", fg_color=YELLOW))

    cells += note_row(
        14,
        "ir/iR = insert row above/below.  ic/iC = col left/right.\ndr/dc = delete row/col.  hr/hc = hide.  sr/sc = show.",  # noqa: E501
    )

    return build_sheet("RowColOps", cells, cursor_row=3, cursor_col=1)


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 10 — Formulas
# ═══════════════════════════════════════════════════════════════════════
def lesson_10() -> dict:
    cells = title_row("FORMULAS", "Write formulas using functions and cell references")
    cells += header_row(["#  Instruction", "Expense", "Category", "Result"])

    expenses = [
        (3, 1200, "Rent"),
        (4, 350, "Utilities"),
        (5, 800, "Groceries"),
        (6, 200, "Transport"),
        (7, 150, "Internet"),
        (8, 1500, "Loan payment"),
    ]
    for row_idx, val, label in expenses:
        cells.append(c(row_idx, 1, val, align="right", fg_color=WHITE))
        cells.append(c(row_idx, 2, label, align="left", fg_color=GRAY))

    # cursor_row=3 → starts on B4 (350, Utilities)
    steps = [
        (3, "1. Go to D4. Press = then type B4*1.1 Enter.\nAdds 10% to Rent. Result: 1320."),
        (4, "2. Go to D9. Press = then type SUM(B4:B9) Enter.\nTotals all expenses. Result: 4200."),
        (5, "3. Go to D10. Press = then type AVG(B4:B9) Enter.\nThe average expense per category."),
        (6, "4. Go to D11. Press = then type MAX(B4:B9) Enter.\nThe largest single expense."),
        (7, "5. Go to D12. Press = then type MIN(B4:B9) Enter.\nThe smallest expense."),
        (
            8,
            '6. Go to D13. Press = then type\nIF(B4>1000,"High","Low") Enter.\nReturns "High" if Rent > 1000, else "Low".',  # noqa: E501
        ),
        (
            9,
            "7. Go to D14. Press = then type ROUND(D10,0) Enter.\nRounds the average to no decimal places.",  # noqa: E501
        ),
        (
            10,
            "8. Go to B4. Change 1200 to 2000\n(press \\, type 2000, Enter).\nWatch D9 through D14 update instantly — live recalculation!",  # noqa: E501
        ),
    ]
    for row_idx, instr in steps:
        cells.append(c(row_idx, 0, wrap_text(instr), align="left", fg_color=YELLOW))

    cells += sep_row(12)
    cells.append(c(13, 0, "── QUICK REFERENCE ──", bold=True, align="left", fg_color=BLUE))
    funcs = [
        (14, "'=SUM(range)'", "Total of all values"),
        (15, "'=AVG(range)'", "Arithmetic mean"),
        (16, "'=MIN/MAX(range)'", "Smallest / largest value"),
        (17, "'=COUNT(range)'", "Count of numeric cells"),
        (18, "'=ROUND(val, n)'", "Round to n decimal places"),
        (19, "'=ABS(val)'", "Absolute value"),
        (20, '\'=IF(test,"a","b")\'', "Return a if true, b if false"),
        (21, "'=PROD(range)'", "Multiply all values"),
    ]
    for row_idx, func, desc in funcs:
        cells.append(c(row_idx, 0, func, align="left", fg_color=CYAN))
        cells.append(c(row_idx, 1, desc, align="left", fg_color=GREEN))

    cells += note_row(
        23, ":funcs lists every available function.\nf1 > Func tab shows full documentation."
    )

    return build_sheet("Formulas", cells, cursor_row=3, cursor_col=1)


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 11 — Advanced Formulas
# ═══════════════════════════════════════════════════════════════════════
def lesson_11() -> dict:
    cells = title_row("ADVANCED FORMULAS", "IF, VLOOKUP, CONCAT, date functions")
    cells += header_row(["#  Instruction", "ID", "Name", "Score", "Grade"])

    for i, h in enumerate(["ID", "Name", "Score"], 1):
        cells.append(c(3, i, h, bold=True, bg_color=DGRAY, align="left"))

    gradebook = [
        (4, 101, "Alice", 85),
        (5, 102, "Bob", 92),
        (6, 103, "Charlie", 78),
        (7, 104, "Diana", 95),
        (8, 105, "Eve", 88),
    ]
    for row_idx, id_, name, score in gradebook:
        cells.append(c(row_idx, 1, id_, align="right", fg_color=WHITE))
        cells.append(c(row_idx, 2, name, align="left", fg_color=WHITE))
        cells.append(c(row_idx, 3, score, align="right", fg_color=WHITE))

    # cursor_row=5 → starts on B5 (Alice, first data row)
    steps = [
        (
            4,
            '1. Go to E5. Press = then type\nIF(D5>90,"Pass","Fail") Enter.\nD5 is Alice\'s score (85). 85>90 is false → "Fail".',  # noqa: E501
        ),
        (
            5,
            '2. Go to E5. Press yy. Go to E6. Press p. (Formula refs shift on paste). Bob scored 92 → "Pass".',  # noqa: E501
        ),
        (
            6,
            "3. Go to B11. Press = then type\nCONCAT(C5,\" scored \",D5) Enter.\nResult: 'Alice scored 85'.",  # noqa: E501
        ),
        (
            7,
            "4. Go to B12. Press = then type\nVLOOKUP(103,B5:D9,2,false) Enter.\nLooks up ID 103 → returns 'Charlie'.",  # noqa: E501
        ),
        (
            8,
            '5. Go to B13. Press = then type\nXLOOKUP("Diana",C5:C9,D5:D9) Enter.\nLooks up Diana by name → returns 95.',  # noqa: E501
        ),
        (
            9,
            '6. Go to B14. Press = then type\nIFERROR(1/0,"Division error") Enter.\n1/0 would crash — IFERROR shows the message.',  # noqa: E501
        ),
        (
            10,
            "7. Go to B15. Press = then type TODAY() Enter.\nGo to B16 and type NOW() — adds the time.",  # noqa: E501
        ),
        (
            11,
            '8. Go to B17. Press = then type\nDATEDIF(B15,B16,"d") Enter.\nCalculates days between two dates.',  # noqa: E501
        ),
        (
            12,
            "9. Change Bob's score (D6) from 92 to 89.\nWatch E6 flip from 'Pass' to 'Fail' instantly.",  # noqa: E501
        ),
    ]
    for row_idx, instr in steps:
        cells.append(c(row_idx, 0, wrap_text(instr), align="left", fg_color=YELLOW))

    cells += note_row(
        13,
        "VLOOKUP(key, range, col_num, exact) — col_num counts from\nthe left of range. exact=false means exact match.",  # noqa: E501
    )
    cells += note_row(
        14,
        "XLOOKUP(key, search_range, return_range) — more flexible,\nno col_num needed, searches by value directly.",  # noqa: E501
    )

    return build_sheet(
        "AdvancedFormulas",
        cells,
        col_widths={"0": 60, "1": 12, "2": 12, "3": 12, "4": 12},
        cursor_row=5,
        cursor_col=1,
    )


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 12 — Sort & Filter
# ═══════════════════════════════════════════════════════════════════════
def lesson_12() -> dict:
    cells = title_row("SORT & FILTER", "Sort columns and filter rows by criteria")
    cells += header_row(["#  Instruction", "Product", "Price", "Stock"])

    products = [
        (3, "Orange", 1.20, 150),
        (4, "Apple", 0.80, 200),
        (5, "Banana", 0.50, 300),
        (6, "Grape", 2.50, 75),
        (7, "Cherry", 3.00, 40),
        (8, "Lemon", 1.00, 180),
        (9, "Peach", 1.80, 90),
        (10, "Pear", 1.10, 130),
    ]
    for row_idx, prod, price, stock in products:
        cells.append(c(row_idx, 1, prod, align="left", fg_color=WHITE))
        cells.append(c(row_idx, 2, price, align="right", fg_color=WHITE))
        cells.append(c(row_idx, 3, stock, align="right", fg_color=WHITE))

    # cursor_row=3 → starts on B4 (Apple)
    steps = [
        (3, "1. Type :sort B asc Enter — sort products A–Z.\nSee the product column reorder."),
        (
            4,
            "2. Type :sort C desc Enter — sort by price, highest first.\nGrape (2.50) and Cherry (3.00) move to the top.",  # noqa: E501
        ),
        (
            5,
            "3. Type :sort D asc Enter — sort by stock, lowest first.\nCherry (40) and Grape (75) are your low-stock items.",  # noqa: E501
        ),
        (6, "4. Type :sort B asc Enter — restore alphabetical order\nbefore filtering."),
        (
            7,
            "5. Type :filter C gt 1 Enter — show only products with\nPrice > 1. Others are hidden, not deleted.",  # noqa: E501
        ),
        (8, "6. Type :clearfilter Enter — all rows visible again.\nFiltering is non-destructive."),
        (
            9,
            "7. Type :filter D lt 100 Enter — show only items with\nStock < 100. These need reordering!",  # noqa: E501
        ),
        (10, "8. Type :clearfilter Enter — reset."),
        (
            11,
            "9. Go to B4. Press v, move to D11 to select all data.\nPress ss — sort rows by the first selected column.",  # noqa: E501
        ),
        (
            12,
            "10. With range still selected: sa — sort columns ascending,\nsd — sort columns descending.",  # noqa: E501
        ),
    ]
    for row_idx, instr in steps:
        cells.append(c(row_idx, 0, wrap_text(instr), align="left", fg_color=YELLOW))

    cells += note_row(
        14,
        "FILTER OPS: gt (>) lt (<) eq (=) ne (≠) contains starts ends\nExample: :filter B contains apple",  # noqa: E501
    )
    cells += note_row(15, "u undoes a sort and restores the original row order.")

    return build_sheet("SortFilter", cells, cursor_row=3, cursor_col=1)


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 13 — Formatting
# ═══════════════════════════════════════════════════════════════════════
def lesson_13() -> dict:
    cells = title_row("FORMATTING", "Cell formatting, alignment, colours, themes")
    cells += header_row(["#  Instruction", "Sample Text"])

    samples = [
        (3, "Make this bold"),
        (4, "Make this italic"),
        (5, "Add underline"),
        (6, "Align right"),
        (7, 42.5678),
        (8, "Colour this cell"),
        (9, 1234567),
        (10, "Multiple properties"),
    ]
    for row_idx, txt in samples:
        cells.append(c(row_idx, 1, txt, align="left", fg_color=WHITE))

    # cursor_row=3 → starts on B4 (Make this bold)
    steps = [
        (3, "1. Go to B4. Press tb — toggle BOLD.\nPress tb again to remove it."),
        (4, "2. Go to B5. Press ti — toggle ITALIC."),
        (5, "3. Go to B6. Press tu — toggle UNDERLINE."),
        (6, "4. Go to B7. Press tr — align RIGHT.\ntl — align LEFT.  tc — CENTER."),
        (7, "5. Type :format B8 num_decimals=2 Enter.\n42.5678 now shows as 42.57."),
        (8, "6. Type :format B9 fg=red bg=yellow Enter.\nRed text on yellow background."),
        (
            9,
            "7. Type :format B10 thousands_sep=true num_decimals=2 Enter.\n1234567 now shows as 1,234,567.00.",  # noqa: E501
        ),
        (
            10,
            "8. Type format B11 bold italic fg=#98c379 Enter.\nCombine multiple properties in one command.",  # noqa: E501
        ),
        (11, "9. Change the colour theme:\n:theme nord\n:theme gruvbox\n:theme dracula"),
        (12, "10. More themes to try:\n:theme dark\n:theme light\n:theme tokyo\n:theme monokai"),
    ]
    for row_idx, instr in steps:
        cells.append(c(row_idx, 0, wrap_text(instr), align="left", fg_color=YELLOW))

    cells += note_row(
        14,
        "FORMAT PROPS: bold italic underline align=left/right/center\nfg=COLOR bg=COLOR num_decimals=N thousands=true",  # noqa: E501
    )
    cells += note_row(15, "Set a theme permanently: :set theme=nord")
    cells += note_row(
        16,
        'TIP:  =100 enters a NUMBER.  \\100 enters the STRING "100".\nFormats like num_decimals only work on numeric cells.',  # noqa: E501
    )

    return build_sheet("Formatting", cells, cursor_row=3, cursor_col=1)


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 14 — Macros
# ═══════════════════════════════════════════════════════════════════════
def lesson_14() -> dict:
    cells = title_row("MACROS", "Record and replay sequences of actions")
    cells += header_row(["#  Instruction", "Raw Score"])

    for i, v in enumerate([72, 68, 85, 91, 60, 77, 83, 55, 88, 74], start=5):
        cells.append(c(i, 1, v, align="right", fg_color=WHITE))

    # cursor_row=3 → starts on B4 (68)
    # Scenario: add a 5-point bonus to each score using a macro.
    steps = [
        (
            3,
            "Scenario: add +5 to every score without editing each cell.\nWe record one action, then replay it.",  # noqa: E501
        ),
        (
            5,
            "1. Go to B6. Press q a — start recording into register a.\nREC appears in the status bar.",  # noqa: E501
        ),
        (6, "2. Press 5 Ctrl+a — add 5 to the current cell (68 → 73).\nPress j — move down to B5."),
        (7, "3. Press q — stop recording."),
        (8, "4. Press @ a — replay the macro once.\nB5 gets +5 and cursor moves to B6."),
        (9, "5. Press @@ — replay the last macro again.\n@@ is shorthand for 'repeat last @'."),
        (
            10,
            "6. Keep pressing @@ until all 10 scores are updated.\nThis is why macros exist — one recording, many replays.",  # noqa: E501
        ),
        (
            11,
            "7. Press u repeatedly to undo all macro applications\nand restore the original scores.",  # noqa: E501
        ),
        (
            12,
            "8. Record a formula macro: q b — start recording.\nGo to B4. Press S, type =B4+5, Enter, then j.\nStop with q.",  # noqa: E501
        ),
        (
            13,
            "9. Press @ b then @@ across all rows.\nThe formula version means if a raw score changes,\nthe adjusted value updates automatically.",  # noqa: E501
        ),
    ]
    for row_idx, instr in steps:
        cells.append(c(row_idx, 0, wrap_text(instr), align="left", fg_color=YELLOW))

    cells += note_row(
        14, "q{a-z} = start recording.  q = stop.  @{a-z} = replay.  @@ = replay last."
    )
    cells += note_row(
        15,
        "End each macro with j (or another move) so @@ can repeat\nwithout you having to reposition the cursor.",  # noqa: E501
    )

    return build_sheet("Macros", cells, cursor_row=3, cursor_col=1)


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 15 — Substitute
# ═══════════════════════════════════════════════════════════════════════
def lesson_15() -> dict:
    cells = title_row("SUBSTITUTE", "Find, replace, and substitute across cells")
    cells += header_row(["#  Instruction", "Product Name", "Status"])

    # A product database with inconsistencies to clean up.
    products = [
        (4, "widget", "active"),
        (5, "WIDGET PRO", "active"),
        (6, "gadget", "draft"),
        (7, "GADGET PLUS", "draft"),
        (8, "old-part-A", "active"),
        (9, "old-part-B", "active"),
        (10, "old-part-C", "active"),
        (11, "sprocket", "pending"),
        (12, "Sprocket Plus", "pending"),
        (13, "widget deluxe", "active"),
    ]
    for row_idx, name, status in products:
        cells.append(c(row_idx, 1, name, align="left", fg_color=WHITE))
        cells.append(c(row_idx, 2, status, align="left", fg_color=GRAY))

    cells.append(c(5, 3, "WIDGET", align="left", fg_color=WHITE))

    # cursor_row=5 → starts on B5 (first product "widget")
    steps = [
        (
            3,
            "1. Press /widget Enter — search for 'widget'.\nAll matches highlight. n = next.  N = previous.",  # noqa: E501
        ),
        (
            4,
            "2. Go to row 5 (first 'widget'). Type\n:s/widget/Widget/ Enter — replaces in this row only.",  # noqa: E501
        ),
        (
            5,
            "3. Go to row 6 (WIDGET PRO). Type\n:s/WIDGET/Widget/i Enter — /i = case-insensitive. Notice only whole cells are replaced",  # noqa: E501
        ),
        (6, "4. Go to column B. Type :cs/gadget/Gadget/i Enter.\ncs = column substitute."),
        (
            7,
            "5. Press V, select rows 9–11 (the old-part rows).\nPress : then type s/old/new/g Enter.\n (/g regex mode.",  # noqa: E501
        ),
        (
            8,
            "6. Rows 9–11 now read new-part-A/B/C.\nRange-substitute applied to each row in the selection.",  # noqa: E501
        ),
        (
            9,
            "7. Type :%s/draft/review/ Enter — % means whole sheet.\nBoth 'draft' entries in column C are replaced.",  # noqa: E501
        ),
        (
            10,
            "8. Type :replace pending approved Enter.\nWhole-cell exact match: only cells whose ENTIRE\ncontent is 'pending' get replaced.",  # noqa: E501
        ),
        (
            11,
            "9. Type /widget Enter then n to cycle — all 'widget'\nentries should now be capitalised 'Widget'.",  # noqa: E501
        ),
        (
            12,
            "10. Type :%s/Widget/WIDGET/g Enter — /g = regex mode.\nReverts every 'Widget' back to 'WIDGET' sheet-wide.",  # noqa: E501
        ),
    ]
    for row_idx, instr in steps:
        cells.append(c(row_idx, 0, wrap_text(instr), align="left", fg_color=YELLOW))

    cells += note_row(
        14,
        ":s/p/r/     current row only\n"
        ":cs/p/r/    current column\n"
        ":%s/p/r/    whole sheet\n"
        ":<r1,r2>s/  row range\n"
        ":replace X Y  whole-cell exact match",
    )
    cells += note_row(15, "FLAGS: /i = case-insensitive.  /g = regex mode.")

    return build_sheet("Substitute", cells, cursor_row=5, cursor_col=1)


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 16 — Freeze & Groups
# ═══════════════════════════════════════════════════════════════════════
def lesson_16() -> dict:
    cells = title_row("FREEZE & GROUPS", "Freeze panes, fold/unfold rows and columns")
    cells += header_row(["#  Instruction", "Month", "Revenue", "Costs"])

    months = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
        "Q1 Total",
        "Q2 Total",
        "Q3 Total",
        "Q4 Total",
        "Annual",
    ]
    for i, month in enumerate(months):
        row_idx = i + 3
        cells.append(c(row_idx, 1, month, align="left", fg_color=WHITE))
        cells.append(c(row_idx, 2, 10000 + i * 500, align="right", fg_color=GREEN))
        cells.append(c(row_idx, 3, 6000 + i * 300, align="right", fg_color=RED))

    # cursor_row=3 → starts on B4 (Jan)
    steps = [
        (
            3,
            "1. Type :freeze 3 Enter — freeze the top 3 rows.\nScroll down — title and headers stay pinned.",  # noqa: E501
        ),
        (
            4,
            "2. Type :freeze 3 1 Enter — freeze 3 rows AND 1 column.\nScroll right — column A stays visible too.",  # noqa: E501
        ),
        (5, "3. Type :unfreeze Enter — remove all frozen panes."),
        (
            6,
            "4. Type :rowgroup 3 6 Enter — group rows 4–7 (Jan–Apr).\nA fold indicator appears at the left margin.",  # noqa: E501
        ),
        (
            7,
            "5. Press zc — close (collapse) the group.\nRows disappear from view but are NOT deleted.",  # noqa: E501
        ),
        (8, "6. Press zo — open (expand) the group.\nPress za — toggle open/closed."),
        (
            9,
            "7. Type :colgroup B C Enter — group columns B and C.\nPress zC to collapse, zO to expand.",  # noqa: E501
        ),
        (
            10,
            "8. Type :rowgroup 7 10 Enter — a second group for rows 8–11.\nNow you have two independent collapsible groups.",  # noqa: E501
        ),
        (11, "9. Press zM — close ALL row groups at once.\nPress zR — open ALL row groups."),
        (
            12,
            "10. Type :rowgroup remove Enter — remove the row group at cursor.\nType :colgroup remove Enter — remove column group.",  # noqa: E501
        ),
    ]
    for row_idx, instr in steps:
        cells.append(c(row_idx, 0, wrap_text(instr), align="left", fg_color=YELLOW))

    cells += note_row(
        14,
        "ROW: zc close  zo open  za toggle  zM close all  zR open all.\nCOL: same but uppercase — zC  zO  zA.",  # noqa: E501
    )
    cells += note_row(
        15,
        "REAL USE: freeze headers in large sheets so column names\nare always visible while you scroll through data.",  # noqa: E501
    )

    return build_sheet(
        "FreezeGroups",
        cells,
        col_widths={"0": 60, "1": 14, "2": 14, "3": 14},
        cursor_row=3,
        cursor_col=1,
    )


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 17 — Command-Mode Ops
# ═══════════════════════════════════════════════════════════════════════
def lesson_17() -> dict:
    cells = title_row("COMMAND-MODE OPS", ":fill, :name, :validate, :swap, :goto")
    cells += header_row(["#  Instruction", "Value", "Notes"])

    seed = [
        (3, 10, "start"),
        (4, 20, ""),
        (5, 30, ""),
        (6, 40, ""),
        (7, 50, "end"),
        (8, "", ""),
        (9, "", ""),
        (10, "", ""),
    ]
    for row_idx, val, note in seed:
        if val != "":
            cells.append(c(row_idx, 1, val, align="right", fg_color=WHITE))
        if note:
            cells.append(c(row_idx, 2, note, align="left", fg_color=GRAY))

    # cursor_row=3 → starts on B4 (value 20)
    steps = [
        (3, "1. Type :B9:B13 fill 100 Enter — fills B9:B13 with 100."),
        (
            4,
            "2. Type :B9:B13 fill 1 1 Enter — fills with a sequence:\nB9=1, B10=2, B11=3, B12=4, B13=5.",  # noqa: E501
        ),
        (
            5,
            "3. Type :name BUDGET B4:B8 Enter — names range B4:B8.\nNamed ranges can be used anywhere a range is expected.",  # noqa: E501
        ),
        (
            6,
            "4. Go to D4. Press = then type SUM(BUDGET) Enter.\nD4 sums B4:B8 using the name — result: 150.\nNamed ranges make formulas readable and maintainable.",  # noqa: E501
        ),
        (
            7,
            "5. Type :goto D4 Enter — jump directly to cell D4.\n(goD4 in normal and visual mode works too.)",  # noqa: E501
        ),
        (
            8,
            "6. Go to B9. Type :validate list 1,2,3,4,5 Enter.\nRestricts B9 to those values only.\nTry entering 99 — you get an error.",  # noqa: E501
        ),
        (9, "7. Type :validate clear Enter — remove the validation rule."),
        (
            10,
            "8. Go to B6 (value 30). Type :swap B8 Enter.\nSwaps B6 and B8. B5 is now 50, B7 is now 30.",  # noqa: E501
        ),
        (
            11,
            "9. Go to row 4. Type :swap row 6 Enter.\nSwaps the entire rows 4 and 6 — all columns exchanged.",  # noqa: E501
        ),
    ]
    for row_idx, instr in steps:
        cells.append(c(row_idx, 0, wrap_text(instr), align="left", fg_color=YELLOW))

    cells += note_row(
        14,
        "Named ranges defined with :name can be used in formulas,\n:goto, :sort, :fill, and anywhere a range is accepted.",  # noqa: E501
    )
    cells += note_row(
        15,
        ":range fill VALUE          — constant fill\n"
        ":range fill START step N   — arithmetic sequence\n"
        ":range fill START seq d    — date sequence",
    )

    return build_sheet(
        "CommandMode",
        cells,
        col_widths={"0": 60, "1": 14, "2": 24},
        cursor_row=3,
        cursor_col=1,
    )


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 18 — Sheets & Buffers
# ═══════════════════════════════════════════════════════════════════════
def lesson_18() -> dict:
    cells = title_row("SHEETS & BUFFERS", "Multiple sheets, tabs, and buffers")
    cells += header_row(["#  Instruction", ""])

    steps = [
        (
            3,
            '1. Type :sheet add "Sales" Enter — add a new sheet.\nYou are switched to it automatically.',  # noqa: E501
        ),
        (4, "2. Press gt — switch to the next sheet.\nPress gT — go to the previous sheet."),
        (5, "3. Press g 1 — go to sheet 1.\ng 2 — sheet 2.  (Any number works.)"),
        (
            6,
            '4. Type :sheet rename "Q1 Sales" Enter — rename\nthe current sheet. Tab label updates immediately.',  # noqa: E501
        ),
        (7, "5. Type :sheet list Enter — list all sheets in\nthe current workbook."),
        (
            8,
            '6. Type :sheet copy "Q1 Sales" Enter — duplicate\nthe sheet. Useful as a Q2/Q3 template.',  # noqa: E501
        ),
        (
            9,
            '7. On the duplicate, type :sheet rename "Q2 Sales" Enter.\nNow two independent sheets exist.',  # noqa: E501
        ),
        (10, '8. Type :sheet delete "Q2 Sales" Enter — delete it.\nWorkbook returns to one sheet.'),
        (11, "9. Type :buffers (or :ls) Enter — list all files\ncurrently open in VimSheet."),
        (
            12,
            "10. To open a second file: type :e filename.csv Enter.\nSwitch buffers with :buffer NAME.",  # noqa: E501
        ),
        (
            13,
            "11. Type :bdelete Enter — close the current buffer.\nPrompted to confirm if unsaved changes exist.",  # noqa: E501
        ),
    ]
    for row_idx, instr in steps:
        cells.append(c(row_idx, 0, wrap_text(instr), align="left", fg_color=YELLOW))

    cells += note_row(
        15,
        "gt / gT = next / prev sheet.  g{N} = jump to sheet N.\nSheet names appear as tabs at the bottom of the screen.",  # noqa: E501
    )
    cells += note_row(
        16,
        "BUFFER = an open file.  SHEET = a tab inside a workbook.\nOne buffer can contain many sheets.",  # noqa: E501
    )

    return build_sheet("SheetsBuffers", cells, cursor_row=3, cursor_col=0)


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 19 — Plotting
# ═══════════════════════════════════════════════════════════════════════
def lesson_19() -> dict:
    cells = title_row("PLOTTING", "Create charts: bar, line, scatter, pie, histogram")
    cells += header_row(["#  Instruction", "Month", "Sales", "Expenses"])

    monthly = [
        (3, "Jan", 1200, 800),
        (4, "Feb", 1500, 900),
        (5, "Mar", 1100, 700),
        (6, "Apr", 1800, 950),
        (7, "May", 2100, 1100),
        (8, "Jun", 1900, 1000),
        (9, "Jul", 2300, 1200),
        (10, "Aug", 2500, 1150),
        (11, "Sep", 2000, 1050),
        (12, "Oct", 2200, 1100),
        (13, "Nov", 2600, 1300),
        (14, "Dec", 3000, 1400),
    ]
    for row_idx, month, sales, exp in monthly:
        cells.append(c(row_idx, 1, month, align="left", fg_color=WHITE))
        cells.append(c(row_idx, 2, sales, align="right", fg_color=GREEN))
        cells.append(c(row_idx, 3, exp, align="right", fg_color=RED))

    # cursor_row=3 → starts on B4 (Feb)
    steps = [
        (3, "NOTE: Plotting requires the 'plotext' package.\nInstall with: pip install plotext"),
        (4, "1. Type :plot bar C4:C15 Enter — bar chart of monthly sales.\nEach month is one bar."),
        (
            5,
            "2. Type :plot line B4:D15 Enter — line chart, two series:\nSales (col C) and Expenses (col D).\nCol B provides the X-axis labels.",  # noqa: E501
        ),
        (
            6,
            "3. Type :plot scatter C4:D15 Enter — scatter plot:\neach point is (Sales, Expenses) for one month.",  # noqa: E501
        ),
        (
            7,
            "4. Type :plot pie B4:C15 Enter — pie chart of sales.\nLargest slice = highest-revenue month.",  # noqa: E501
        ),
        (
            8,
            "5. Type :plot histogram C4:C15 Enter — distribution\nof sales values across the year.",
        ),
        (
            9,
            "6. Select C4:D15 with v. Press : — range is pre-filled.\nType plot bar Enter — range auto-inserted.",  # noqa: E501
        ),
        (10, "7. Add a title: :plot bar C4:C15 title=Monthly Sales Enter."),
        (
            11,
            "8. Change Dec sales to 5000. Re-run the plot command —\nthe chart updates with the new data.",  # noqa: E501
        ),
    ]
    for row_idx, instr in steps:
        cells.append(c(row_idx, 0, wrap_text(instr), align="left", fg_color=YELLOW))

    cells += note_row(
        13, "CHART TYPES: bar  line  scatter  pie  histogram\nSYNTAX: :plot TYPE RANGE [title=TEXT]"
    )
    cells += note_row(
        14,
        "Select a range with v first, then : and type 'plot bar'\n— the range is inserted automatically.",  # noqa: E501
    )

    return build_sheet("Plotting", cells, cursor_row=3, cursor_col=1)


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 20 — File I/O
# ═══════════════════════════════════════════════════════════════════════
def lesson_20() -> dict:
    cells = title_row("FILE I/O", "Save, open, export, import spreadsheet files")
    cells += header_row(["Action", "Command", "Notes"])
    rows = [
        (3, "Save", ":w", "Write to the current file path"),
        (4, "Save as", ":w {file}", "Save to a specific file"),
        (5, "Open a file", ":e {file}", "Loads CSV, XLSX, JSON, .vimsheet, etc."),
        (6, "Reload file", ":e!", "Discard changes and reload from disk"),
        (7, "Read into sheet", ":r {file}", "Import file content into current sheet"),
        (8, "", "", ""),
        (9, "── EXPORT ──", "", ""),
        (10, "CSV", ":ex csv {file}", "Comma-separated values"),
        (11, "TSV", ":ex tsv {file}", "Tab-separated values"),
        (12, "JSON", ":ex json {file}", "Plain JSON (no formatting)"),
        (13, "Excel", ":ex xlsx {file}", "Excel workbook (needs openpyxl)"),
        (14, "Markdown", ":ex mkd {file}", "Markdown table"),
        (15, "LaTeX", ":ex tex {file}", "LaTeX tabular environment"),
        (16, "HTML", ":ex html {file}", "HTML table"),
        (17, "", "", ""),
        (18, "Load text", ":loadtext {file}", "Each line → one cell downward"),
        (19, "Print to stdout", ":print", "Tab-separated text output"),
        (20, "", "", ""),
        (21, "── PRACTICE ──", "", ""),
        (22, "1. Save this file", ":w", "Practice: press : then w then Enter"),
        (23, "2. Export as CSV", ":ex csv /tmp/l20.csv", "Creates a CSV on disk"),
        (24, "3. Open the CSV", ":e /tmp/l20.csv", "Opens the exported file as a buffer"),
        (25, "4. List buffers", ":buffers", "See both open files"),
    ]
    for row_idx, a, b, n in rows:
        if a:
            cells.append(c(row_idx, 0, wrap_text(a, 38), align="left", fg_color=YELLOW))
        if b:
            cells.append(c(row_idx, 1, b, align="left", fg_color=CYAN))
        if n:
            cells.append(c(row_idx, 2, wrap_text(n, 38), align="left", fg_color=GREEN))

    cells += note_row(
        27,
        "Format is auto-detected from the file extension.\n:w myfile.xlsx saves directly as Excel.",
    )
    cells += note_row(
        28,
        ":ex csv - (dash) prints CSV to terminal stdout —\nuseful for scripting and piping to other tools.",  # noqa: E501
    )

    return build_sheet(
        "FileOps",
        cells,
        col_widths={"0": 40, "1": 32, "2": 44},
        freeze_rows=2,
        cursor_row=3,
        cursor_col=0,
    )


# ═══════════════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════════════
LESSONS: list[tuple[int, str, str]] = [
    (0, "00_General", "Overview, Help, and General Commands"),
    (1, "01_Navigation", "Movement Basics (hjkl, 0/$, gg/G, Ctrl+f/b)"),
    (2, "02_CellEditing", "Entering and Editing Cell Contents"),
    (3, "03_CopyPaste", "Yank, Paste, Cut, and Registers"),
    (4, "04_UndoRedo", "Undo, Redo, and Repeat"),
    (5, "05_Marks", "Marks and Search (/ ? n N * #)"),
    (6, "06_Modes", "VimSheet Modes Overview"),
    (7, "07_InsertEdit", "Insert and Edit Mode Deep-Dive"),
    (8, "08_VisualMode", "Visual Mode (v V Ctrl+v)"),
    (9, "09_RowColOps", "Row and Column Operations"),
    (10, "10_Formulas", "Formulas and Basic Functions"),
    (11, "11_AdvancedFormulas", "Advanced Formulas (IF, VLOOKUP, etc.)"),
    (12, "12_SortFilter", "Sort and Filter Commands"),
    (13, "13_Formatting", "Cell Formatting and Themes"),
    (14, "14_Macros", "Macro Recording and Replay"),
    (15, "15_Substitute", "Find, Replace, and Substitute"),
    (16, "16_FreezeGroups", "Freeze Panes and Row/Column Groups"),
    (17, "17_CommandMode", "Command-Mode Operations"),
    (18, "18_SheetsBuffers", "Sheets and Buffers"),
    (19, "19_Plotting", "Plotting Charts"),
    (20, "20_FileOps", "File I/O (save, open, export)"),
]

GENERATORS = [
    lesson_00,
    lesson_01,
    lesson_02,
    lesson_03,
    lesson_04,
    lesson_05,
    lesson_06,
    lesson_07,
    lesson_08,
    lesson_09,
    lesson_10,
    lesson_11,
    lesson_12,
    lesson_13,
    lesson_14,
    lesson_15,
    lesson_16,
    lesson_17,
    lesson_18,
    lesson_19,
    lesson_20,
]


def _save_vsheet(num: int, fname: str, title: str, sheet: dict) -> None:
    """Write a .vsheet regeneration script that approximates the tutorial setup."""
    lines = [
        f"# Regeneration script for {fname}.vimsheet",
        f"# Run: vimsheet --script {fname}.vsheet",
        f"# Or:  vimsheet --nocurses < {fname}.vsheet",
        "#",
        "# Note: Full formatting (colors, bold) is applied by the",
        "#       Python generator: python scripts/generate_tutorials.py",
        "",
        f"# --- {title} ---",
        "",
        'renamesheet "Sheet1" "Tutorial"',
        "",
    ]
    cw = sheet.get("col_widths", {})
    for col_idx_str, width in sorted(cw.items(), key=lambda x: int(x[0])):
        col_letter = chr(65 + int(col_idx_str))
        lines.append(f"colwidth {col_letter} {width}")
    fr = sheet.get("freeze_rows", 0)
    if fr:
        lines.append(f"freeze {fr}")
    lines.append("")
    for cell in sheet.get("cells", []):
        v = cell.get("value", "")
        if isinstance(v, str) and not v.startswith("VIMSHEET TUTORIAL"):
            continue
        lines.append(f'set A1 = "{v}"')
        break
    lines.append("")
    out_path = f"../{fname}.vimsheet"
    lines.append(f"save {out_path}")
    lines.append("")
    text = "\n".join(lines)
    path = VSCRIPT_DIR / f"{fname}.vsheet"
    path.write_text(text, encoding="utf-8")
    print(f"  → .vsheet  {fname}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="generate_tutorials")
    parser.add_argument(
        "--vsheet", action="store_true", help="Also generate .vsheet regeneration scripts"
    )
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if args.vsheet:
        VSCRIPT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Generating {len(GENERATORS)} tutorial files → {OUTPUT_DIR}")
    for (num, fname, title), gen in zip(LESSONS, GENERATORS, strict=False):
        sheet = gen()
        sheet.setdefault("freeze_rows", 3)
        workbook = {
            "version": 1,
            "active_sheet": 0,
            "sheets": [sheet],
        }
        save(num, fname, workbook)
        if args.vsheet:
            _save_vsheet(num, fname, title, sheet)
    print("\nDone.")


if __name__ == "__main__":
    main()
