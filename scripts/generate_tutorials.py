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


def wrap_text(text: str, width: int = 60) -> str:
    """Insert ``\\n`` at word boundaries to keep lines under *width* chars."""
    if len(text) <= width:
        return text
    result: list[str] = []
    while text:
        if len(text) <= width:
            result.append(text)
            break
        chunk = text[:width]
        if " " in chunk:
            break_at = chunk.rfind(" ")
            result.append(text[:break_at])
            text = text[break_at + 1 :]
        else:
            result.append(chunk)
            text = text[width:]
    return "\n".join(result)


def note_row(row: int, text: str, **kw) -> list[dict]:
    return [
        c(row, 0, wrap_text(text), align="left", fg_color=kw.pop("fg", GRAY), italic=True, **kw)
    ]


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
) -> dict:
    return {
        "name": name,
        "col_widths": col_widths
        or {
            "0": 68,
            "1": 15,
            "2": 15,
            "3": 15,
            "4": 15,
            "5": 15,
        },
        "freeze_rows": freeze_rows,
        "freeze_cols": freeze_cols,
        "cells": cells,
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
        (6, "Show messages", ":messages", "View message history log"),
        (7, "List functions", ":funcs", "All registered formula functions"),
        (8, "", "", ""),
        (9, "── FILE OPERATIONS ──", "", ""),
        (10, "Save file", ":w", "Writes to current file path"),
        (11, "Save as…", ":w {file}", "Save to a new file name"),
        (12, "Open file", ":e {file}", "Load a spreadsheet file"),
        (13, "Export", ":ex {fmt} {file}", "fmt: csv|tsv|json|xlsx|mkd|tex|html"),
        (14, "Quit", ":q", "Warns if unsaved changes"),
        (15, "Force quit", ":q!", "Discard changes and quit"),
        (16, "Save & quit", ":wq  /  :x  /  ZZ", "Save then quit"),
        (17, "", "", ""),
        (18, "── GENERAL COMMANDS ──", "", ""),
        (19, "Repeat last action", ".", "Replays the last edit/command"),
        (20, "Refresh screen", "Ctrl+l", "Redraw the terminal"),
        (21, "Open external editor", "gw", "Edit cell in $EDITOR / $VISUAL"),
        (22, "Auto-fit column", "_  /  :autofit", "Resize column to content"),
        (23, "Undo", "u", "Undo last change"),
        (24, "Redo", "Ctrl+r", "Redo last undone change"),
        (25, "", "", ""),
        (26, "── MODES ──", "", ""),
        (27, "Normal mode", "Esc", "Default — navigate & command"),
        (28, "Insert mode", "\\ = < > A I S", "Enter new cell content"),
        (29, "Edit mode", "e  E", "Modify existing cell content"),
        (30, "Command mode", ":", "Colon commands"),
        (31, "Visual mode", "v  V  Ctrl+v", "Select cells/rows/block"),
        (32, "", "", ""),
        (33, "TIP: Press  f1  at any time to open the help screen.", "", ""),
    ]
    for r, a, b, n in rows:
        if a:
            cells.append(c(r, 0, wrap_text(a, 48), align="left", fg_color=YELLOW))
        if b:
            cells.append(c(r, 1, b, align="left", fg_color=CYAN))
        if n:
            cells.append(c(r, 2, wrap_text(n, 48), align="left", fg_color=GREEN))
    return build_sheet(
        "General",
        cells,
        col_widths={
            "0": 50,
            "1": 30,
            "2": 50,
        },
        freeze_rows=2,
    )


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 01 — Navigation
# ═══════════════════════════════════════════════════════════════════════
def lesson_01() -> dict:
    cells = title_row("NAVIGATION", "Move around the spreadsheet with vim keys")
    cells += header_row(["#  Instruction", "A", "B", "C", "D", "E"])
    # 15 steps with data grid — every cell in B-E gets a number
    steps = [
        (3, "1. Press  l  or →  to move right across the numbers"),
        (4, "2. Press  h  or ←  to move left"),
        (5, "3. Press  j  or ↓  to move down"),
        (6, "4. Press  k  or ↑  to move up"),
        (7, "5. Press  w  to jump right to the next non-empty block"),
        (8, "6. Press  b  to jump left to the previous non-empty block"),
        (9, "7. Press  0  (zero) to go to column A (the frozen instruction column)"),
        (10, "8. Press  $  to go to the last data column in this row"),
        (11, "9. Press  ^  to go to the first data cell (column B)"),
        (12, "10. Press  gg  to go to the first row of the sheet"),
        (13, "11. Press  G  (Shift+g) to go to the last row with data"),
        (14, "12. Press  10G  to jump to row 10"),
        (15, "13. Press  Ctrl+f  (PgDn) to scroll a page down"),
        (16, "14. Press  Ctrl+b  (PgUp) to scroll a page up"),
        (17, "15. Press  H / M / L  to move to top/middle/bottom of screen"),
    ]
    for instr_row, instr in steps:
        cells += step_row(instr_row, instr)
    # Fill data grid from row 3 to row 17, cols 1-4 (B-E)
    for row_idx in range(3, 18):
        for col_idx in range(1, 5):  # columns B, C, D, E
            val = (row_idx - 3) * 4 + col_idx + 1  # unique number per cell
            cells.append(c(row_idx, col_idx, val, align="right", fg_color=WHITE))
    # Notes
    cells += note_row(19, "NOTE: Column A is frozen — it stays visible when you scroll right.")
    cells += note_row(20, "      h / l  navigate unfrozen cells;  0  jumps back to column A.")
    cells += note_row(22, "TIP: Use  Ctrl+d / Ctrl+u  for half-page scroll")
    cells += note_row(23, "TIP: Use  Ctrl+e / Ctrl+y  to scroll without moving cursor")
    return build_sheet("Navigation", cells)


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 02 — Cell Editing
# ═══════════════════════════════════════════════════════════════════════
def lesson_02() -> dict:
    cells = title_row("CELL EDITING", "Enter, edit, and delete cell contents")
    cells += header_row(["#  Instruction", "Practice", "", ""])
    # Data grid with sample values
    data_vals = [
        (3, "John Doe"),
        (4, "Jane Smith"),
        (5, "Bob Wilson"),
        (6, "Alice Brown"),
        (7, "42"),
        (8, "3.14159"),
    ]
    for row_idx, val in data_vals:
        cells.append(c(row_idx, 1, val, align="left", fg_color=WHITE))
    steps = [
        (3, "1. Go to B3. Press  \\  (backslash) to enter INSERT mode, then type a new name"),
        (4, "2. Press Enter to edit return to NORMAL mode"),
        (5, "3. Go to B4. Press  e  to EDIT the cell — use  w / b / 0 / $  to move within it"),
        (6, "4. Press  Enter or Esc when done editing to commit"),
        (7, "5. Go to B5. Press  A  to append at the end of the cell"),
        (8, "6. Go to B6. Press  I  to insert at the beginning of the cell"),
        (9, "7. Go to B7. Press  x  to clear the cell (cut to register)"),
        (10, "8. Go to B8. Press  dd  to delete the cell"),
        (11, "9. Press  u  to undo the last delete"),
        (12, "10. Press  Ctrl+r  to redo the delete"),
        (13, "11. Go to B7. Press  r  5  to replace the cell content with '5'"),
        (14, "12. Press  .  (dot) to repeat the replace — watch it work on next cell"),
        (15, "13. Go to B7. Press  S  to clear cell and enter INSERT mode (left-aligned)"),
        (16, "14. Go to B8. Press  C  to clear to end and enter INSERT mode"),
    ]
    for row_idx, instr in steps:
        cells += step_row(row_idx, instr)
    cells += note_row(18, "Note: Cells that were cleared can be pasted back with  p")
    return build_sheet("CellEditing", cells)


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 03 — Copy & Paste
# ═══════════════════════════════════════════════════════════════════════
def lesson_03() -> dict:
    cells = title_row("COPY & PASTE", "Yank, paste, cut, and registers")
    cells += header_row(["#  Instruction", "Col B", "Col C", "Col D"])
    # Data grid cols B-D rows 3-8
    grid = [
        (3, 10, 20, 30),
        (4, 40, 50, 60),
        (5, 70, 80, 90),
        (6, 100, 110, 120),
        (7, 130, 140, 150),
        (8, 160, 170, 180),
    ]
    for row_idx, v1, v2, v3 in grid:
        cells.append(c(row_idx, 1, v1, align="right", fg_color=WHITE))
        cells.append(c(row_idx, 2, v2, align="right", fg_color=WHITE))
        cells.append(c(row_idx, 3, v3, align="right", fg_color=WHITE))
    steps = [
        (3, "1. Go to B3. Press  yy  to yank (copy) this cell"),
        (4, "2. Go to B9. Press  p  to paste"),
        (5, "3. Go to B3. Press  YY  to yank the cell's VALUE (not formula)"),
        (6, "4. Go to B10. Press  P  to paste above the current cell"),
        (7, "5. Go to C3. Press  yc  to yank the entire column C"),
        (8, "6. Go to E3. Press  p  to paste the column"),
        (9, "7. Go to row 3. Press  yr  to yank the entire row 3"),
        (10, "8. Go to row 11. Press  p  to paste the row"),
        (11, "9. Go to B5. Press  dd  to cut (delete) this cell into register"),
        (12, "10. Go to B12. Press  p  to paste the cut value"),
        (13, '11. Go to B3. Press  "a yy  to yank into register  a'),
        (14, '12. Go to B13. Press  "a p  to paste from register  a'),
        (15, '13. Press  "+ yy  to yank to system clipboard (if supported)'),
    ]
    for row_idx, instr in steps:
        cells += step_row(row_idx, instr)
    cells += note_row(17, 'TIP: Use  "{a-z}  for 26 named registers.  "+  is the system clipboard.')
    return build_sheet("CopyPaste", cells)


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 04 — Undo / Redo
# ═══════════════════════════════════════════════════════════════════════
def lesson_04() -> dict:
    cells = title_row("UNDO & REDO", "Undo, redo, cell history, and repeat")
    cells += header_row(["#  Instruction", "Value"])
    # Some initial values
    for i, v in enumerate([100, 200, 300, 400, 500, 600, 700, 800, 900, 1000], 3):
        cells.append(c(i, 1, v, align="right", fg_color=WHITE))
    steps = [
        (3, "1. Go to B3. Press  +  (plus) to increment the value by 1"),
        (4, "2. Go to B4. Press  5 +  to increment by 5"),
        (5, "3. Go to B5. Press  -  (minus) to decrement"),
        (6, "4. Go to B6. Press  Ctrl+a  to increment by 1 (alt key)"),
        (7, "5. Go to B7. Press  Ctrl+x  to decrement by 1"),
        (8, "6. Press  u  to undo the last action"),
        (9, "7. Press  u  again to undo another step"),
        (10, "8. Press  Ctrl+r  to redo what you just undid"),
        (11, "9. Go to B3. Type a new value. Press  .  (dot) to repeat that change on B4"),
        (12, "10. Press  .  again to repeat on B5"),
        (13, "11. Go to B8. Press  U  to restore the cell from history"),
        (14, "12. Go to B9. Press  :history  Enter  to see cell change history"),
    ]
    for row_idx, instr in steps:
        cells += step_row(row_idx, instr)
    cells += note_row(17, "TIP:  u  undoes,  Ctrl+r  redoes.  .  repeats the last change.")
    return build_sheet("UndoRedo", cells)


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 05 — Marks
# ═══════════════════════════════════════════════════════════════════════
def lesson_05() -> dict:
    cells = title_row("MARKS & SEARCH", "Set marks, jump between them, search cells")
    cells += header_row(["#  Instruction", "A", "B", "C"])
    # Fill grid
    for r_idx in range(3, 13):
        for c_idx in range(1, 4):
            cells.append(c(r_idx, c_idx, (r_idx - 3) * 3 + c_idx, align="right", fg_color=WHITE))
    # Some distinct text values for search practice
    cells += [
        c(3, 1, "apple", align="left", fg_color=WHITE),
        c(5, 1, "banana", align="left", fg_color=WHITE),
        c(5, 2, "apple", align="left", fg_color=WHITE),
        c(8, 3, "cherry", align="left", fg_color=WHITE, bg_color=RED),
        c(10, 1, "banana", align="left", fg_color=WHITE),
    ]
    steps = [
        (3, "1. Go to the cell with 'apple' (B3). Press  m a  to set mark  a"),
        (4, "2. Navigate away (e.g. to row 15). Press  ' a  to jump back to mark  a"),
        (5, "3. Go to the second 'banana'. Press  m b  to set mark  b"),
        (6, "4. Press  ' b  to jump to mark  b"),
        (7, "5. Press  / apple  Enter  to search forward for 'apple'"),
        (8, "6. Press  n  to jump to the next match"),
        (9, "7. Press  N  to jump to the previous match"),
        (10, "8. Press  ? cherry  Enter  to search backward for 'cherry'"),
        (11, "9. Go to the 'cherry' cell. Press  *  to search for its value forward"),
        (12, "10. Press  #  to search for the cell's value backward"),
    ]
    for row_idx, instr in steps:
        cells += step_row(row_idx, instr)
    cells += note_row(14, "TIP: Marks persist until you quit.  /  and  ?  support regex patterns.")
    return build_sheet("Marks", cells)


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
        (
            3,
            "NORMAL  --NORMAL--",
            "Esc  (from any mode)",
            "Navigate, copy, paste, delete, undo/redo",
        ),
        (4, "INSERT  --INSERT--", "\\  =  <  >  A  I  S", "Type new content into a cell"),
        (5, "EDIT    --EDIT--", "e  E", "Modify existing cell content"),
        (6, "COMMAND  --CMD--", ":", "Run colon commands (:help, :w, :q)"),
        (7, "VISUAL  --VISUAL--", "v  V  Ctrl+v", "Select cells for yank/delete/format"),
    ]
    for row_idx, mode, enter, purpose in modes:
        cells.append(c(row_idx, 0, mode, align="left", fg_color=CYAN))
        cells.append(c(row_idx, 1, enter, align="left", fg_color=YELLOW))
        cells.append(c(row_idx, 2, purpose, align="left", fg_color=GREEN))
    cells += sep_row(9)
    notes = [
        (10, "To enter NORMAL from other modes, press  Esc  (or Ctrl+c)."),
        (11, "To enter INSERT, press  \\  (backslash). The status bar shows the current mode."),
        (12, "To enter COMMAND mode, press  :  then type a command followed by Enter."),
        (
            13,
            "To enter VISUAL mode, press  v  for cell selection,  V  for rows,  Ctrl+v  for block.",
        ),
        (14, "To enter EDIT mode, press  e  — the formula bar becomes editable with vim keys."),
    ]
    for row_idx, text in notes:
        cells.append(c(row_idx, 0, text, align="left", fg_color=YELLOW))
    cells += note_row(16, "KEY INSIGHT: always check the status bar to know which mode you are in.")
    return build_sheet(
        "Modes",
        cells,
        col_widths={
            "0": 55,
            "1": 35,
            "2": 55,
        },
    )


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 07 — Insert & Edit Mode
# ═══════════════════════════════════════════════════════════════════════
def lesson_07() -> dict:
    cells = title_row("INSERT & EDIT", "Deep-dive into cell entry and editing")
    cells += header_row(["#  Instruction", "Practice"])
    data = ["Hello World", "VimSheet", "Spreadsheet", "Edit me!", "Another one"]
    for i, v in enumerate(data, 3):
        cells.append(c(i, 1, v, align="left", fg_color=WHITE))
    steps = [
        (3, "1. Go to B3. Press  \\  (backslash) to enter INSERT — type something new, then Esc"),
        (4, "2. Go to B4. Press  =  to enter INSERT (right-aligned, formula prefix)"),
        (5, "3. Go to B5. Press  e  to EDIT the cell. Use  h / l  to move within the value"),
        (6, "4. In EDIT mode, press  w  to jump word-forward,  b  to jump word-backward"),
        (7, "5. In EDIT mode, press  d w  to delete a word,  d $  to delete to end"),
        (8, "6. In EDIT mode, press  C  to delete from cursor to end and enter INSERT"),
        (9, "7. In EDIT mode, press  i  to enter INSERT mode at the cursor position"),
        (10, "8. In EDIT mode, press  a  to enter INSERT mode after the cursor"),
        (11, "9. In EDIT mode, press  r {char}  to replace one character (e.g.  r X)"),
        (12, "10. Go to B6. Press  E  to enter EDIT mode with cursor at end of cell"),
        (13, "11. Go to B7. Press  S  to clear the cell and enter INSERT (left-aligned)"),
        (14, "12. In EDIT mode, press  Esc  or  Enter  to commit changes"),
    ]
    for row_idx, instr in steps:
        cells += step_row(row_idx, instr)
    cells += note_row(16, "TIP: Edit-mode commands mirror vim:  h/l/w/b/0/$/x/dw/d$/C/i/a/r")
    return build_sheet("InsertEdit", cells)


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 08 — Visual Mode
# ═══════════════════════════════════════════════════════════════════════
def lesson_08() -> dict:
    cells = title_row("VISUAL MODE", "Select ranges, yank, delete, sort, and format")
    cells += header_row(["#  Instruction", "A", "B", "C", "D"])
    # Fill grid
    for r_idx in range(3, 12):
        for c_idx in range(1, 5):
            cells.append(c(r_idx, c_idx, (r_idx - 3) * 4 + c_idx, align="right", fg_color=WHITE))
    steps = [
        (3, "1. Go to B3. Press  v  to enter VISUAL mode. Move with  j / l  to select B3:D5"),
        (4, "2. Press  y  to yank (copy) the selection"),
        (5, "3. Go to B12. Press  p  to paste"),
        (6, "4. Go to E3. Press  V  to enter VISUAL LINE mode. Press  j  twice to select 3 rows"),
        (7, "5. Press  d  to delete the selected rows"),
        (8, "6. Press  u  to undo"),
        (9, "7. Go to B3. Press  Ctrl+v  to enter VISUAL BLOCK mode. Select B3:C5"),
        (10, "8. Press  >  to shift the block right by one column"),
        (11, "9. Press  <  to shift it back left"),
        (12, "10. Select a range. Press  =  100  Enter  to fill selection with 100"),
        (13, "11. Select a range. Press  ss  to sort rows by first column"),
        (14, "12. Select a range. Press  y  then go to another cell and press  P  (shift+p)"),
    ]
    for row_idx, instr in steps:
        cells += step_row(row_idx, instr)
    cells += note_row(
        16, "TIP:  v = cell,  V = row,  Ctrl+v = block.  o  flips the selection corner."
    )
    return build_sheet("VisualMode", cells)


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
    steps = [
        (3, "1. Go to B3. Press  ir  to insert a row above"),
        (4, "2. Press  iR  to insert a row below"),
        (5, "3. Go to column C. Press  ic  to insert a column to the left"),
        (6, "4. Press  iC  to insert a column to the right"),
        (7, "5. Go to a row. Press  dr  to delete it"),
        (8, "6. Go to column D. Press  dc  to delete it"),
        (9, "7. Select a row with  V . Press  hr  to hide the selected rows"),
        (10, "8. Press  sr  to show (unhide) the rows"),
        (11, "9. Press  +  to widen the current column"),
        (12, "10. Press  -  to narrow the current column"),
        (13, "11. Press  _  (underscore) to auto-fit the column width"),
        (14, "12. Press  z_  (z + underscore) to collapse the current row group"),
        (15, "13. Press  z+  to expand the row group"),
    ]
    for row_idx, instr in steps:
        cells += step_row(row_idx, instr)
    cells += note_row(
        17, "TIP:  ir/iR = insert row,  ic/iC = insert col,  dr/dc = delete,  hr/hc = hide"
    )
    return build_sheet("RowColOps", cells)


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 10 — Formulas
# ═══════════════════════════════════════════════════════════════════════
def lesson_10() -> dict:
    cells = title_row("FORMULAS", "Write formulas using functions and cell references")
    cells += header_row(["#  Instruction", "Values", "", "Result"])
    # Data
    for i, v in enumerate([10, 20, 30, 40, 50], 3):
        cells.append(c(i, 1, v, align="right", fg_color=WHITE))
    cells += [
        c(7, 1, 15, align="right", fg_color=WHITE),
        c(8, 1, 25, align="right", fg_color=WHITE),
    ]
    steps = [
        (3, "1. Go to B3. Type  =  to enter formula mode. Type  B3 + 5  Enter"),
        (4, "2. Go to B4. Press  =  then type  SUM(B3:B5)  Enter  — sum of B3:B5"),
        (5, "3. Go to B5. Press  =  then type  AVG(B3:B5)  Enter  — average"),
        (6, "4. Go to B6. Press  =  then type  MIN(B3:B5)  Enter  — minimum"),
        (7, "5. Go to B7. Press  =  then type  MAX(B3:B5)  Enter  — maximum"),
        (8, "6. Go to B8. Press  =  then type  COUNT(B3:B5)  Enter  — count of numbers"),
    ]
    for row_idx, instr in steps:
        cells += step_row(row_idx, instr)

    cells += sep_row(9)
    cells.append(
        c(10, 0, "── BUILT-IN FUNCTIONS TO TRY ──", bold=True, align="left", fg_color=BLUE)
    )

    funcs = [
        (11, "=SUM(range)", "Sum of all values in range"),
        (12, "=AVG(range)", "Arithmetic mean"),
        (13, "=MIN(range)", "Smallest value"),
        (14, "=MAX(range)", "Largest value"),
        (15, "=COUNT(range)", "Count of numeric cells"),
        (16, "=PROD(range)", "Product (multiplication)"),
        (17, "=ABS(cell)", "Absolute value"),
        (18, "=ROUND(c,n)", "Round cell to n decimals"),
    ]
    for row_idx, func, desc in funcs:
        cells += [
            c(row_idx, 0, func, align="left", fg_color=CYAN),
            c(row_idx, 1, desc, align="left", fg_color=GREEN),
        ]
    cells += note_row(
        20, "TIP:  :funcs  lists every available function.  f1 > Func tab for details."
    )
    return build_sheet("Formulas", cells)


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 11 — Advanced Formulas
# ═══════════════════════════════════════════════════════════════════════
def lesson_11() -> dict:
    cells = title_row("ADVANCED FORMULAS", "IF, VLOOKUP, CONCAT, date functions")
    cells += header_row(["#  Instruction", "Data", "", "", ""])
    # Sample data table for VLOOKUP
    headers = ["ID", "Name", "Score"]
    for i, h in enumerate(headers, 1):
        cells.append(c(3, i, h, bold=True, bg_color=DGRAY, align="left"))
    vlookup_data = [
        (4, 101, "Alice", 85),
        (5, 102, "Bob", 92),
        (6, 103, "Charlie", 78),
        (7, 104, "Diana", 95),
        (8, 105, "Eve", 88),
    ]
    for row_idx, id_, name, score in vlookup_data:
        cells.append(c(row_idx, 1, id_, align="right", fg_color=WHITE))
        cells.append(c(row_idx, 2, name, align="left", fg_color=WHITE))
        cells.append(c(row_idx, 3, score, align="right", fg_color=WHITE))
    steps = [
        (9, '1. Go to B9.  Press  =  then type  IF(B4 > 90, "Pass", "Fail")  Enter'),
        (10, '2. Go to B10. Press  =  then type  CONCAT(B4, " got ", D4)  Enter'),
        (11, "3. Go to B11. Press  =  then type  VLOOKUP(103, B4:D8, 2, false)  Enter"),
        (12, '4. Go to B12. Press  =  then type  XLOOKUP("Diana", C4:C8, D4:D8)  Enter'),
        (13, '5. Go to B13. Press  =  then type  IFERROR(1/0, "Oops!")  Enter'),
        (14, "6. Go to B14. Press  =  then type  TODAY()  Enter  — today's date"),
        (15, "7. Go to B15. Press  =  then type  NOW()  Enter  — current date+time"),
        (16, '8. Go to B16. Press  =  then type  DATEDIF(B14, B15, "d")  Enter'),
    ]
    for row_idx, instr in steps:
        cells += step_row(row_idx, instr)
    cells += note_row(
        18, "TIP:  :funcs  shows all functions. Use  f1 > Func tab  for documentation."
    )
    return build_sheet(
        "AdvancedFormulas",
        cells,
        col_widths={
            "0": 70,
            "1": 18,
            "2": 18,
            "3": 18,
            "4": 18,
        },
    )


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 12 — Sort & Filter
# ═══════════════════════════════════════════════════════════════════════
def lesson_12() -> dict:
    cells = title_row("SORT & FILTER", "Sort columns and filter rows by criteria")
    cells += header_row(["#  Instruction", "Product", "Price", "Stock"])
    unsorted = [
        (3, "Orange", 1.20, 150),
        (4, "Apple", 0.80, 200),
        (5, "Banana", 0.50, 300),
        (6, "Grape", 2.50, 75),
        (7, "Cherry", 3.00, 40),
        (8, "Lemon", 1.00, 180),
        (9, "Peach", 1.80, 90),
        (10, "Pear", 1.10, 130),
    ]
    for row_idx, prod, price, stock in unsorted:
        cells.append(c(row_idx, 1, prod, align="left", fg_color=WHITE))
        cells.append(c(row_idx, 2, price, align="right", fg_color=WHITE))
        cells.append(c(row_idx, 3, stock, align="right", fg_color=WHITE))
    steps = [
        (3, "1. Go to B3. Press  :sort B asc  Enter  — sort products alphabetically"),
        (4, "2. Press  :sort C desc  Enter  — sort by price descending"),
        (5, "3. Press  :sort D asc  Enter  — sort by stock ascending"),
        (6, "4. Press  :filter C gt 1  Enter  — show only products with price > 1"),
        (7, "5. Press  :clearfilter  Enter  — remove the filter"),
        (8, "6. Press  :filter D lt 100  Enter  — show only products with stock < 100"),
        (9, "7. Press  :clearfilter"),
        (10, "8. Select range B3:D10. Press  v  then  ss  to sort rows by first column"),
        (11, "9. With selection active, press  sa  to sort columns ascending"),
        (12, "10. Press  sd  to sort columns descending"),
    ]
    for row_idx, instr in steps:
        cells += step_row(row_idx, instr)
    cells += note_row(
        14, "TIP:  :filter {col} {op} {value}   ops: gt / lt / eq / contains / starts / ends"
    )
    return build_sheet("SortFilter", cells)


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 13 — Formatting
# ═══════════════════════════════════════════════════════════════════════
def lesson_13() -> dict:
    cells = title_row("FORMATTING", "Cell formatting, alignment, colours, themes")
    cells += header_row(["#  Instruction", "Sample"])
    samples = [
        (3, "Plain text"),
        (4, "Bold text"),
        (5, "Italic text"),
        (6, "Right aligned"),
        (7, "42.5678"),
        (8, "Coloured text"),
        (9, "42"),
    ]
    for row_idx, txt in samples:
        cells.append(c(row_idx, 1, txt, align="left", fg_color=WHITE))
    steps = [
        (3, "1. Go to B3. Press  tb  to toggle bold"),
        (4, "2. Go to B4. Press  ti  to toggle italic"),
        (5, "3. Go to B5. Press  tu  to toggle underline"),
        (6, "4. Go to B6. Press  tr  to align right"),
        (7, "5. Press  tl  to align left,  tc  to center"),
        (8, "6. Go to B7. Press  +  to increase decimal places,  -  to decrease"),
        (9, "7. Go to B8. Press  :format B8 fg=red bg=yellow  Enter"),
        (10, "8. Go to B9. Press  Ctrl+a  repeatedly to increment"),
        (11, "9. Press  :theme nord  Enter  — try different themes"),
        (12, "10. Press  :theme gruvbox  Enter"),
        (13, "11. Press  :theme dracula  Enter"),
        (14, "12. Press  :theme default  Enter  — restore default"),
    ]
    for row_idx, instr in steps:
        cells += step_row(row_idx, instr)
    cells += note_row(
        16, "TIP: Themes: dark / light / nord / gruvbox / dracula / tokyo / monokai / solarized"
    )
    return build_sheet("Formatting", cells)


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 14 — Macros
# ═══════════════════════════════════════════════════════════════════════
def lesson_14() -> dict:
    cells = title_row("MACROS", "Record and replay sequences of actions")
    cells += header_row(["#  Instruction", "Data"])
    for i, v in enumerate([1, 1, 1, 1, 1, 1, 1, 1, 1, 1], 3):
        cells.append(c(i, 1, v, align="right", fg_color=WHITE))
    steps = [
        (3, "1. Go to B3. Press  q a  to start recording into register  a"),
        (4, "2. Press  Ctrl+a  to increment the cell value by 1"),
        (5, "3. Press  j  to move down to the next cell"),
        (6, "4. Press  q  to stop recording"),
        (7, "5. Press  @ a  to replay the macro — B4 increments and cursor moves down"),
        (8, "6. Press  @@  to repeat the last macro again"),
        (9, "7. Keep pressing  @@  to fill all cells with incrementing values"),
        (10, "8. Press  u  repeatedly to undo all the macro applications"),
        (11, "9. Record a new macro  q b : go to B3, press  dd  to delete, press  j, press  q"),
        (12, "10. Press  @ b  to replay: it deletes B3, moves down"),
        (13, "11. Keep pressing  @@  to delete remaining cells"),
        (14, "12. Record a macro that sets a formula, then replay across a range"),
    ]
    for row_idx, instr in steps:
        cells += step_row(row_idx, instr)
    cells += note_row(
        16, "TIP: Macros are stored in registers  a-z.  @@  replays the last @ command."
    )
    return build_sheet("Macros", cells)


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 15 — Substitute
# ═══════════════════════════════════════════════════════════════════════
def lesson_15() -> dict:
    cells = title_row("SUBSTITUTE", "Find, replace, and substitute across cells")
    cells += header_row(["#  Instruction", "Text"])
    texts = [
        (3, "Hello world"),
        (4, "Hello there"),
        (5, "Goodbye world"),
        (6, "hello again"),
        (7, "Hello World!"),
        (8, "Say hello to everyone"),
        (9, "world of vimsheet"),
    ]
    for row_idx, txt in texts:
        cells.append(c(row_idx, 1, txt, align="left", fg_color=WHITE))
    steps = [
        (3, "1. Press  :find hello  Enter  — highlights all cells containing 'hello'"),
        (4, "2. Press  :findnext  /  :findprev  to cycle through matches"),
        (5, "3. Press  :replace hello hi  Enter  — replaces whole-cell matches"),
        (6, "4. Press  :cs/hello/hi/  Enter  — column substitute, whole-cell literal"),
        (7, "5. Press  :cs/hello/hi/g  Enter  — column substitute, regex global"),
        (8, "6. Press  :rs/hello/hi/  Enter  — row substitute (current row)"),
        (9, "7. Press  :%s/world/earth/g  Enter  — whole-sheet regex substitute"),
        (10, "8. Select range B3:B9 with  v . Press  :  then  s/hello/hi/g  Enter"),
    ]
    for row_idx, instr in steps:
        cells += step_row(row_idx, instr)
    cells += note_row(
        12, "TIP:  :cs = column sub,  :rs = row sub,  :%s = whole sheet.  /g = regex mode."
    )
    return build_sheet("Substitute", cells)


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 16 — Freeze & Groups
# ═══════════════════════════════════════════════════════════════════════
def lesson_16() -> dict:
    cells = title_row("FREEZE & GROUPS", "Freeze headers, create row/column groups")
    cells += header_row(["#  Instruction", "A", "B", "C"])
    # Big data grid
    for r_idx in range(3, 30):
        for c_idx in range(1, 4):
            cells.append(c(r_idx, c_idx, r_idx * 100 + c_idx, align="right", fg_color=WHITE))
    steps = [
        (3, "1. Press  :freeze 3  Enter  — freeze top 3 rows (header area)"),
        (4, "2. Scroll down — notice rows 0-2 stay visible"),
        (5, "3. Press  :unfreeze  Enter  — remove freeze"),
        (6, "4. Press  :freeze 1 2  Enter  — freeze 1 row and 2 columns"),
        (7, "5. Press  :unfreeze"),
        (8, "6. Go to row 3. Press  zc  to collapse row groups (close all)"),
        (9, "7. Press  zo  to expand row groups (open all)"),
        (10, "8. Press  za  to toggle row group at cursor"),
        (11, "9. Press  zR  to open all row groups"),
        (12, "10. Press  zM  to close all row groups"),
        (13, "11. Select rows 10-12 with  V . Press  :rowgroup 11 13  Enter"),
        (14, "12. Press  :colgroup 0 2  Enter  — group columns A-C"),
    ]
    for row_idx, instr in steps:
        cells += step_row(row_idx, instr)
    cells += note_row(16, "TIP:  zc=close, zo=open, za=toggle, zR=open all, zM=close all")
    return build_sheet(
        "FreezeGroups",
        cells,
        col_widths={
            "0": 75,
            "1": 14,
            "2": 14,
            "3": 14,
        },
    )


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 17 — Command-Mode Ops
# ═══════════════════════════════════════════════════════════════════════
def lesson_17() -> dict:
    cells = title_row("COMMAND-MODE OPS", ":fill, :swap, :name, :validate, :goto, :loadtext")
    cells += header_row(["#  Instruction", "Data"])
    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    for i, v in enumerate(data, 3):
        cells.append(c(i, 1, v, align="right", fg_color=WHITE))
    steps = [
        (3, "1. Go to B3. Press  :fill 5 100  Enter  — fill 5 cells with 100"),
        (4, "2. Go to B8. Press  :fill 3 step 1  Enter  — fill 3 cells stepping by 1"),
        (5, "3. Go to B11. Press  :fill 5 seq d  Enter  — fill 5 cells with a date sequence"),
        (6, "4. Go to B3. Press  :swap B10  Enter  — swap contents of B3 and B10"),
        (7, "5. Go to any row. Press  :swap row 5  Enter  — swap current row with row 5"),
        (8, "6. Press  :name MYDATA B3:B7  Enter  — name a range"),
        (9, "7. Press  :goto MYDATA  Enter  — jump to the named range"),
        (10, "8. Go to B3. Press  :validate list 1 2 3  Enter  — restrict to list values"),
        (11, "9. Press  :validate clear  Enter  — clear validation"),
        (12, "10. Press  :goto C5  Enter  — jump directly to cell C5"),
    ]
    for row_idx, instr in steps:
        cells += step_row(row_idx, instr)
    cells += note_row(14, "TIP:  :fill supports: number, step {n}, seq d (dates), seq t (times)")
    return build_sheet("CommandMode", cells)


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 18 — Sheets & Buffers
# ═══════════════════════════════════════════════════════════════════════
def lesson_18() -> dict:
    cells = title_row("SHEETS & BUFFERS", "Multiple sheets, tabs, buffers")
    cells += header_row(["#  Instruction", ""])
    steps = [
        (3, '1. Press  :sheet add "Sheet2"  Enter  — add a new sheet'),
        (4, "2. Press  gt  to switch to the next sheet"),
        (5, "3. Press  gT  to switch to the previous sheet"),
        (6, "4. Press  g 1  to go to sheet 1,  g 2  for sheet 2"),
        (7, '5. Press  :sheet rename "MySheet"  Enter  — rename current sheet'),
        (8, "6. Press  :sheet list  Enter  — list all sheets"),
        (9, '7. Press  :sheet delete "Sheet2"  Enter  — remove a sheet'),
        (10, '8. Press  :sheet copy "MySheet"  Enter  — duplicate a sheet'),
        (11, "9. Press  :buffers  (or  :ls)  Enter  — list open buffers"),
        (12, "10. Press  :buffer example.vimsheet  Enter  — switch to another buffer"),
        (13, "11. Press  :split  Enter  — open current file in a new buffer/sheet"),
        (14, "12. Press  :bdelete  Enter  — close current buffer"),
    ]
    for row_idx, instr in steps:
        cells += step_row(row_idx, instr)
    cells += note_row(
        16, "TIP:  gt / gT / g{N}  for sheet navigation.  :buffers  to see all open files."
    )
    return build_sheet("SheetsBuffers", cells)


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 19 — Plotting
# ═══════════════════════════════════════════════════════════════════════
def lesson_19() -> dict:
    cells = title_row("PLOTTING", "Create charts: bar, line, scatter, pie, histogram")
    cells += header_row(["#  Instruction", "Month", "Sales", "Expenses"])
    data = [
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
    for row_idx, month, sales, exp in data:
        cells.append(c(row_idx, 1, month, align="left", fg_color=WHITE))
        cells.append(c(row_idx, 2, sales, align="right", fg_color=WHITE))
        cells.append(c(row_idx, 3, exp, align="right", fg_color=WHITE))
    steps = [
        (3, "1. Press  :plot bar B3:C14  Enter  — bar chart of monthly sales"),
        (4, "2. Press  :plot line B3:D14  Enter  — line chart, sales + expenses"),
        (5, "3. Press  :plot scatter B3:C14  Enter  — scatter plot"),
        (6, "4. Press  :plot pie B3:C14  Enter  — pie chart of sales"),
        (7, "5. Press  :plot histogram B3:B14  Enter  — histogram"),
        (8, "6. Select data with  v , then press  :plot bar  Enter  — range auto-filled"),
        (9, "7. Press  :plot bar  Enter  — plot currently selected data"),
    ]
    for row_idx, instr in steps:
        cells += step_row(row_idx, instr)
    cells += note_row(
        16, "TIP: Chart types: bar, line, scatter, pie, histogram.  :plot {type} {range}"
    )
    return build_sheet("Plotting", cells)


# ═══════════════════════════════════════════════════════════════════════
#  Lesson 20 — File I/O
# ═══════════════════════════════════════════════════════════════════════
def lesson_20() -> dict:
    cells = title_row("FILE I/O", "Save, open, export, import spreadsheet files")
    cells += header_row(["Action", "Command", "Notes"])
    rows = [
        (3, "Save (current path)", ":w", "Writes to the current file path"),
        (4, "Save as…", ":w {file}", "Save to a specific file"),
        (5, "Open a file", ":e {file}", "Loads CSV, XLSX, JSON, .vimsheet, etc."),
        (6, "Reload current file", ":e!", "Discard changes and reload"),
        (7, "Import into sheet", ":r {file}", "Read file into current sheet"),
        (8, "", "", ""),
        (9, "── EXPORT FORMATS ──", "", ""),
        (10, "Export to CSV", ":ex csv {file}", "Comma-separated values"),
        (11, "Export to TSV", ":ex tsv {file}", "Tab-separated values"),
        (12, "Export to JSON", ":ex json {file}", "Plain JSON (no formatting)"),
        (13, "Export to XLSX", ":ex xlsx {file}", "Excel workbook"),
        (14, "Export to Markdown", ":ex mkd {file}", "Markdown table"),
        (15, "Export to LaTeX", ":ex tex {file}", "LaTeX table"),
        (16, "Export to HTML", ":ex html {file}", "HTML table"),
        (17, "", "", ""),
        (18, "Load text into cells", ":loadtext {file}", "Each line fills one cell down"),
        (19, "Print sheet to stdout", ":print", "Tab-separated text output"),
        (20, "", "", ""),
        (21, "── TUTORIAL → PRACTICE ──", "", ""),
        (22, "Save this lesson", ":w", "Practice saving"),
        (23, "Export as CSV", ":ex csv lesson20.csv", "Try an export"),
        (24, "Re-open the CSV", ":e lesson20.csv", "Open what you exported"),
    ]
    for row_idx, a, b, n in rows:
        if a:
            cells.append(c(row_idx, 0, wrap_text(a, 48), align="left", fg_color=YELLOW))
        if b:
            cells.append(c(row_idx, 1, b, align="left", fg_color=CYAN))
        if n:
            cells.append(c(row_idx, 2, wrap_text(n, 48), align="left", fg_color=GREEN))
    cells += note_row(26, "TIP:  The adapter auto-detects format from the file extension.")
    return build_sheet(
        "FileOps",
        cells,
        col_widths={
            "0": 45,
            "1": 35,
            "2": 50,
        },
        freeze_rows=2,
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
    # Column widths
    cw = sheet.get("col_widths", {})
    for col_idx_str, width in sorted(cw.items(), key=lambda x: int(x[0])):
        col_letter = chr(65 + int(col_idx_str))
        lines.append(f"colwidth {col_letter} {width}")
    # Freeze rows
    fr = sheet.get("freeze_rows", 0)
    if fr:
        lines.append(f"freeze {fr}")
    lines.append("")
    # Title row (simple text)
    for cell in sheet.get("cells", []):
        v = cell.get("value", "")
        if isinstance(v, str) and not v.startswith("VIMSHEET TUTORIAL"):
            continue
        lines.append(f'set A1 = "{v}"')
        break
    lines.append("")
    # Save as .vimsheet
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
