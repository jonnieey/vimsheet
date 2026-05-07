"""Static help entries — key bindings and commands.

Add a register_help() call here when you add a new key binding or command.
Formula functions are auto-populated from the formula registry — no entry needed.
"""

from vimsheet.help_registry import register_help

# ── NAVIGATION ────────────────────────────────────────────────────────────────
_S = "NAVIGATION"
register_help(_S, "h / j / k / l", "Move cursor left/down/up/right", order=10)
register_help(_S, "Arrow keys", "Move cursor", order=11)
register_help(_S, "gg / G", "Jump to first / last row", order=20)
register_help(_S, "0 / $", "Jump to start / end of row", order=21)
register_help(_S, "w / b", "Jump right / left to next non-empty block", order=22)
register_help(_S, "Ctrl+↓/↑/→/←", "Jump to next non-empty block", order=23)
register_help(_S, "Ctrl+d / Ctrl+u", "Half-page down / up", order=30)
register_help(_S, "Ctrl+f / Ctrl+b", "Page down / up", order=31)
register_help(_S, "H / M / L", "Top / Middle / Bottom of visible rows", order=40)
register_help(_S, "nG", "Go to row n  (e.g. 10G)", order=41)
register_help(_S, "go<addr> Enter", "Jump to address  (e.g. goC5)", order=42)

# ── EDITING ───────────────────────────────────────────────────────────────────
_S = "EDITING"
register_help(_S, "=", "Insert mode (right-align)", order=10)
register_help(_S, "\\ / > / <", "Insert left-align / right-align / default", order=11)
register_help(_S, "e / E", "Edit cell (cursor at end / start)", order=20)
register_help(_S, "ge", "Open cell in $EDITOR / $VISUAL", order=21)
register_help(_S, "x", "Clear cell", order=30)
register_help(_S, "yy / YY", "Yank cell formula / value", order=40)
register_help(_S, "p", "Paste yanked cell", order=41)
register_help(_S, "dd", "Cut (delete) row", order=42)
register_help(_S, "u / Ctrl+r", "Undo / Redo", order=50)
register_help(_S, "sj / sk / sl / sh", "Shift cell down/up/right/left", order=55)
register_help(_S, "rv", "Detach formula — keep value", order=60)
register_help(_S, "rl / ru", "Lock / unlock cell", order=61)

# ── EDIT MODE (inside e/E) ────────────────────────────────────────────────────
_S = "EDIT MODE"
register_help(_S, "h / l  (normal sub)", "Move cursor in text", order=10)
register_help(_S, "A / I", "Jump to end / start and insert", order=11)
register_help(_S, "w / b / e", "Word forward / backward / end", order=12)
register_help(_S, "D", "Delete to end of line", order=20)
register_help(_S, "x", "Delete char under cursor", order=21)
register_help(_S, "Enter / Esc", "Confirm edit", order=30)

# ── ROWS & COLUMNS ────────────────────────────────────────────────────────────
_S = "ROWS & COLUMNS"
register_help(_S, "ir / iR", "Insert row above / below", order=10)
register_help(_S, "ic / iC", "Insert column left / right", order=11)
register_help(_S, "dr / dc", "Delete row / column", order=20)
register_help(_S, "+ / - / _", "Widen / narrow / auto-fit column", order=30)

# ── VISUAL MODE ───────────────────────────────────────────────────────────────
_S = "VISUAL MODE"
register_help(_S, "v / V / Ctrl+v", "Enter visual (cell / row / block)", order=10)
register_help(_S, "y / d / x", "Yank / delete / clear selection", order=20)
register_help(_S, "= / ss / sa / sd", "Fill / sort rows / sort cols asc/desc", order=21)
register_help(_S, "sj / sk / sl / sh", "Shift selection down/up/right/left", order=22)
register_help(_S, "fb / fi / fu", "Bold / italic / underline selection", order=30)
register_help(_S, "fl / fr / fc", "Align left / right / center", order=31)
register_help(_S, "o", "Move cursor to opposite corner", order=40)
register_help(_S, ": (in visual)", "Pre-fill command with selected range", order=41)
register_help(_S, "Esc", "Exit visual mode", order=50)

# ── MARKS & SEARCH ────────────────────────────────────────────────────────────
_S = "MARKS & SEARCH"
register_help(_S, "m<a-z>", "Set mark", order=10)
register_help(_S, "'<a-z>", "Jump to mark", order=11)
register_help(_S, "/ pattern", "Search forward", order=20)
register_help(_S, "? pattern", "Search backward", order=21)
register_help(_S, "n / N", "Next / previous match", order=22)
register_help(_S, "*", "Search for current cell value", order=23)

# ── COMMAND MODE ─────────────────────────────────────────────────────────────
_S = "COMMAND MODE  (:)"
register_help(_S, ":w <file>", "Save", order=10)
register_help(_S, ":e <file>", "Open / reload file", order=11)
register_help(_S, ":ex <fmt> <file>", "Export  (csv/tsv/json/xlsx/mkd/tex/html)", order=12)
register_help(_S, ":r <file>", "Import file into current sheet", order=13)
register_help(_S, ":q / :q! / ZZ / ZQ", "Quit / force-quit / save+quit", order=20)
register_help(_S, ':newsheet "Name"', "Add sheet", order=30)
register_help(_S, ':delsheet "Name"', "Remove sheet", order=31)
register_help(_S, ':renamesheet "Name"', "Rename active sheet", order=32)
register_help(_S, ":nextsheet / :prevsheet", "Switch sheets", order=33)
register_help(_S, ":sort <col> asc|desc", "Sort columns (supports A:D, A,B,C ranges)", order=40)
register_help(_S, ":<range> sort <col> ...", "Sort columns within range", order=41)
register_help(_S, "sa / sd (visual)", "Sort selection columns asc/desc", order=42)
register_help(_S, ":filter <col> <op> <v>", "Filter rows  (gt/lt/eq/contains/…)", order=41)
register_help(_S, ":clearfilter", "Clear active filter", order=42)
register_help(_S, ":find <pat>", "Highlight matches", order=50)
register_help(_S, ":replace <old> <new>", "Find and replace (whole-value match)", order=51)
register_help(_S, ":cs/pat/repl/", "Column substitute — whole-cell literal, current col", order=52)
register_help(_S, ":cs/pat/repl/g", "Column substitute — regex global replace", order=53)
register_help(_S, ":csB/pat/repl/[g]", "Column substitute — col B or :cs2/… (1-based #)", order=54)
register_help(_S, ":A,Ccs/pat/repl/[g]", "Column substitute — col range A to C", order=55)
register_help(_S, ":rs/pat/repl/", "Row substitute — whole-cell literal, current row", order=56)
register_help(_S, ":rs/pat/repl/g", "Row substitute — regex global replace", order=57)
register_help(_S, ":rs3/pat/repl/[g]", "Row substitute — row 3 or :1,3rs/… (range)", order=58)
register_help(_S, ":A1:B5 cs/pat/repl/[g]", "Substitute within range (cs or rs)", order=59)
register_help(_S, ":freeze row N", "Freeze top N rows", order=60)
register_help(_S, ":unfreeze", "Remove freeze", order=61)
register_help(_S, ":name <id> <range>", "Create named range", order=70)
register_help(_S, ":plot <type> <range>", "Chart  (bar/line/scatter/pie/histogram)", order=80)
register_help(_S, ":func <NAME> <script>", "Register script formula function", order=90)
register_help(_S, ":format <cell> …", "Format cell  (color/bg/bold/italic/…)", order=100)
register_help(_S, ":cond <range> …", "Conditional format", order=101)
register_help(_S, ':comment "text"', "Add comment to cell", order=110)
register_help(_S, ":history <cell>", "Show cell change history", order=111)
register_help(_S, ":theme <name>", "Change theme  (dracula/light/gruvbox/nord)", order=120)
register_help(_S, ":loadtext <file>", "Fill cells from plain-text file", order=121)
register_help(_S, ":fill <n> <value>", "Fill N cells with value/range", order=122)
register_help(_S, ":set autocalc", "Toggle auto-recalculation", order=130)
register_help(_S, ":set key=value", "Set/save a config value  (e.g. :set theme=nord)", order=131)
register_help(_S, ":recalc", "Force full recalculation", order=131)
register_help(_S, ":fetchnow <cell>", "Force immediate re-fetch of FETCH cell", order=140)
register_help(_S, ":fetchstop <cell|all>", "Cancel FETCH refresh timer", order=141)
register_help(_S, ":fetchlist", "Show all active FETCH cells", order=142)
register_help(_S, ":funcs", "List registered formula functions", order=150)
register_help(_S, ":help", "Show this screen", order=160)

# ── MACROS ────────────────────────────────────────────────────────────────────
_S = "MACROS"
register_help(_S, "q<a-z>", "Start recording macro into register", order=10)
register_help(_S, "q  (while recording)", "Stop recording", order=11)
register_help(_S, "@<a-z>", "Replay macro", order=20)
register_help(_S, "@@", "Replay last macro again", order=21)
register_help(_S, ":macro start <name>", "Start named macro recording", order=30)
register_help(_S, ":macro stop", "Stop recording", order=31)
register_help(_S, ":macro run <name>", "Execute named macro", order=32)
register_help(_S, '"<a-z>yy / "<a-z>p', "Yank / paste to/from named register", order=40)
