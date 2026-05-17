"""Static help entries — key bindings and commands.

Add a register_help() call here when you add a new key binding or command.
Formula functions are auto-populated from the formula registry — no entry needed.
"""

from vimsheet.help_registry import register_help, register_section

# Register built-in tabs (order controls tab sequence)
register_section("NAV", "Nav", order=10)
register_section("EDIT", "Edit", order=20)
register_section("ROWS", "R/C", order=30)
register_section("VIS", "Vis", order=40)
register_section("MARKS", "Marks", order=50)
register_section("CMD", "Cmd", order=60)
register_section("MACRO", "Macro", order=70)
register_section("FUNC", "Func", order=80)

# ═══════════════════════════════════════════════════════════════════════════
# NAVIGATION
# ═══════════════════════════════════════════════════════════════════════════
register_help("NAV", "h / j / k / l", "Move cursor left/down/up/right", subgroup="Cursor", order=10)
register_help("NAV", "Arrow keys", "Move cursor", subgroup="Cursor", order=11)
register_help(
    "NAV", "w / b", "Jump right / left to next non-empty block", subgroup="Cursor", order=12
)
register_help(
    "NAV", "0 / $ / ^", "Jump to start / end / first non-empty of row", subgroup="Cursor", order=13
)
register_help(
    "NAV", "Ctrl+Home / Ctrl+End", "Jump to first / last cell in sheet", subgroup="Cursor", order=14
)
register_help("NAV", "Ctrl+d / Ctrl+u", "Half-page down / up", subgroup="Scrolling", order=20)
register_help("NAV", "Ctrl+f / Ctrl+b", "Page down / up", subgroup="Scrolling", order=21)
register_help("NAV", "Space", "Page down", subgroup="Scrolling", order=22)
register_help("NAV", "gg / G", "Jump to first / last row", subgroup="Jumps", order=30)
register_help(
    "NAV", "H / M / L", "Top / Middle / Bottom of visible rows", subgroup="Jumps", order=31
)
register_help("NAV", "nG", "Go to row n  (e.g. 10G)", subgroup="Jumps", order=32)
register_help("NAV", "go<addr> Enter", "Jump to address  (e.g. goC5)", subgroup="Jumps", order=33)
register_help("NAV", "Ctrl+↓/↑/→/←", "Jump to next non-empty block", subgroup="Jumps", order=34)
register_help("NAV", "gt / gT / g<digit>", "Next / prev / Nth sheet", subgroup="Jumps", order=35)

# ═══════════════════════════════════════════════════════════════════════════
# EDITING
# ═══════════════════════════════════════════════════════════════════════════
register_help(
    "EDIT",
    "= / \\ / > / <",
    "Insert mode (right / left / right / default align)",
    subgroup="Sheet",
    order=10,
)
register_help("EDIT", "e / E", "Edit cell (cursor at end / start)", subgroup="Sheet", order=11)
register_help(
    "EDIT", "gx / gX", "Swap cell with target address (X keeps cursor)", subgroup="Sheet", order=11
)
register_help("EDIT", "grx / grX", "Swap row with target row number", subgroup="Sheet", order=11)
register_help(
    "EDIT", "gcx / gcX", "Swap column with target column letter", subgroup="Sheet", order=11
)
register_help("EDIT", "cw / cc / C", "Clear cell and enter INSERT mode", subgroup="Sheet", order=11)
register_help("EDIT", "dw", "Clear cell content", subgroup="Sheet", order=11)
register_help(
    "EDIT", "d$ / D", "Delete cell content to end of formula bar", subgroup="Sheet", order=11
)
register_help("EDIT", "gw", "Open cell in $EDITOR / $VISUAL", subgroup="Sheet", order=12)
register_help("EDIT", "A / I", "Insert mode at end / start of cell", subgroup="Sheet", order=12)
register_help("EDIT", "S", "Clear cell and enter insert (left-aligned)", subgroup="Sheet", order=13)
register_help("EDIT", "x / X", "Clear cell / clear and move left", subgroup="Sheet", order=14)
register_help(
    "EDIT", "gv", "Replace formula with current computed value", subgroup="Sheet", order=15
)
register_help("EDIT", "zl / zL", "Lock / unlock cell", subgroup="Sheet", order=16)
register_help("EDIT", "Alt+Enter", "Insert newline in cell content", subgroup="Sheet", order=17)
register_help(
    "EDIT",
    "A / I",
    "Jump to end / start of formula bar and insert",
    subgroup="Formula Bar",
    order=20,
)
register_help("EDIT", "h / l", "Move cursor in formula bar", subgroup="Formula Bar", order=21)
register_help(
    "EDIT",
    "w / b / e",
    "Word forward / backward / end in formula bar",
    subgroup="Formula Bar",
    order=22,
)
register_help("EDIT", "D", "Delete to end of line in formula bar", subgroup="Formula Bar", order=23)
register_help(
    "EDIT", "x", "Delete char under cursor in formula bar", subgroup="Formula Bar", order=24
)
register_help("EDIT", "Enter / Esc", "Confirm / cancel edit", subgroup="Formula Bar", order=25)
register_help("EDIT", "yy / YY", "Yank cell formula / value", subgroup="Yank/Paste", order=30)
register_help("EDIT", "p", "Paste with formula adjustment", subgroup="Yank/Paste", order=31)
register_help("EDIT", "P", "Paste exact formula (no adjustment)", subgroup="Yank/Paste", order=32)
register_help(
    "EDIT",
    '"{a-z}yy / "{a-z}p',
    "Yank / paste to/from named register",
    subgroup="Yank/Paste",
    order=33,
)
register_help("EDIT", "dd", "Clear cell value", subgroup="Yank/Paste", order=34)
register_help("EDIT", "u / Ctrl+r", "Undo / Redo", subgroup="Undo", order=40)
register_help("EDIT", "U", "Restore cell from history", subgroup="Undo", order=41)
register_help(
    "EDIT", "gsj / gsk / gsl / gsh", "Shift cell down/up/right/left", subgroup="Undo", order=42
)
register_help("EDIT", ".", "Repeat last action", subgroup="Undo", order=43)
register_help("EDIT", "Ctrl+g", "Show file info", subgroup="Misc", order=50)
register_help("EDIT", "f1", "Open help screen", subgroup="Misc", order=51)
register_help("EDIT", "z_ / z+", "Collapse / expand current row", subgroup="Misc", order=52)

# ═══════════════════════════════════════════════════════════════════════════
# ROWS & COLUMNS
# ═══════════════════════════════════════════════════════════════════════════
register_help("ROWS", "ir / iR", "Insert row above / below", subgroup="Insert", order=10)
register_help("ROWS", "ic / iC", "Insert column left / right", subgroup="Insert", order=11)
register_help("ROWS", "dr / dc", "Delete row / column", subgroup="Delete", order=20)
register_help("ROWS", "hr / hc", "Hide row / column", subgroup="Hide/Show", order=25)
register_help("ROWS", "sr / sc", "Show row / column", subgroup="Hide/Show", order=26)
register_help("ROWS", "+ / - / _", "Widen / narrow / auto-fit column", subgroup="Resize", order=30)
register_help("ROWS", "z_ / z+", "Collapse / expand row height", subgroup="Resize", order=31)
register_help(
    "ROWS", "zc / zo / za", "Close / open / toggle row group", subgroup="Groups", order=40
)
register_help("ROWS", "zR / zM", "Open / close all row groups", subgroup="Groups", order=41)

# ═══════════════════════════════════════════════════════════════════════════
# VISUAL MODE
# ═══════════════════════════════════════════════════════════════════════════
register_help(
    "VIS",
    "v / V / Ctrl+v",
    "Enter visual mode (cell / row / block)",
    subgroup="Selection",
    order=10,
)
register_help(
    "VIS", "o", "Move cursor to opposite corner of selection", subgroup="Selection", order=11
)
register_help(
    "VIS", "H / M / L", "Top / middle / bottom of visible area", subgroup="Selection", order=12
)
register_help("VIS", "Esc", "Exit visual mode", subgroup="Selection", order=13)
register_help("VIS", "go<addr>", "Extend selection to address", subgroup="Selection", order=14)
register_help("VIS", "y", "Yank selection", subgroup="Operations", order=20)
register_help("VIS", "d / x", "Delete / clear selection", subgroup="Operations", order=21)
register_help("VIS", "p", "Paste into selection", subgroup="Operations", order=22)
register_help("VIS", "ss", "Sort rows by first column", subgroup="Operations", order=23)
register_help("VIS", "sa / sd", "Sort each column asc / desc", subgroup="Operations", order=24)
register_help(
    "VIS",
    "gsj / gsk / gsl / gsh",
    "Shift selection down/up/right/left",
    subgroup="Operations",
    order=25,
)
register_help(
    "VIS", "> / <", "Shift selection right / left 1 column", subgroup="Operations", order=26
)
register_help(
    "VIS",
    "Ctrl+a / Ctrl+x",
    "Increment / decrement all numeric cells",
    subgroup="Operations",
    order=27,
)
register_help(
    "VIS",
    "+ / - / _",
    "Widen / narrow / auto-fit columns in selection",
    subgroup="Operations",
    order=28,
)
register_help(
    "VIS", "z_ / z+", "Collapse / expand all selected rows", subgroup="Operations", order=29
)
register_help(
    "VIS", "= (visual)", "Fill selection with value / sequence", subgroup="Operations", order=26
)
register_help(
    "VIS",
    ": (in visual)",
    "Pre-fill command line with selected range",
    subgroup="Operations",
    order=27,
)
register_help(
    "VIS", "tb / ti / tu", "Bold / italic / underline formatting", subgroup="Formatting", order=30
)
register_help("VIS", "tl / tr / tc", "Align left / right / center", subgroup="Formatting", order=31)

# ═══════════════════════════════════════════════════════════════════════════
# MARKS & SEARCH
# ═══════════════════════════════════════════════════════════════════════════
register_help("MARKS", "m<a-z>", "Set mark at current cell", subgroup="Marks", order=10)
register_help("MARKS", "'<a-z>", "Jump to mark", subgroup="Marks", order=11)
register_help("MARKS", "/ pattern", "Search forward", subgroup="Find", order=20)
register_help("MARKS", "? pattern", "Search backward", subgroup="Find", order=21)
register_help("MARKS", "n / N", "Next / previous match", subgroup="Find", order=22)
register_help(
    "MARKS", "* / #", "Search for current cell value forward / backward", subgroup="Find", order=23
)

# ═══════════════════════════════════════════════════════════════════════════
# COMMAND MODE
# ═══════════════════════════════════════════════════════════════════════════
register_help("CMD", ":w <file>", "Save workbook", subgroup="File", order=10)
register_help("CMD", ":e <file>", "Open / reload file", subgroup="File", order=11)
register_help(
    "CMD", ":ex <fmt> <file>", "Export (csv/tsv/json/xlsx/mkd/tex/html)", subgroup="File", order=12
)
register_help("CMD", ":r <file>", "Import file into current sheet", subgroup="File", order=13)
register_help(
    "CMD", ":q / :q! / ZZ / ZQ", "Quit / force-quit / save+quit", subgroup="File", order=14
)
register_help("CMD", ':sa "Name" / :sheet add "Name"', "Add new sheet", subgroup="Sheets", order=20)
register_help(
    "CMD", ':sd "Name" / :sheet delete "Name"', "Remove sheet", subgroup="Sheets", order=21
)
register_help(
    "CMD",
    ':sr "NewName" / :sheet rename "NewName"',
    "Rename active sheet",
    subgroup="Sheets",
    order=22,
)
register_help(
    "CMD",
    ':sr "Old" "New" / :sheet rename "Old" "New"',
    "Rename named sheet",
    subgroup="Sheets",
    order=23,
)
register_help("CMD", ":sl / :sheet list", "List all sheets", subgroup="Sheets", order=24)
register_help(
    "CMD",
    ':sdup "Name" / :sc "Name" / :sheet copy "Name"',
    "Duplicate a sheet",
    subgroup="Sheets",
    order=25,
)
register_help(
    "CMD", ":nextsheet / :prevsheet", "Switch between sheets", subgroup="Sheets", order=23
)
register_help(
    "CMD", ":buffers / :bufs / :ls", "List open buffers / sheets", subgroup="Sheets", order=24
)
register_help(
    "CMD", ":buffer / :buf <name>", "Switch to buffer / sheet", subgroup="Sheets", order=25
)
register_help("CMD", ":bd / :bdel / :bdelete", "Close buffer / sheet", subgroup="Sheets", order=26)
register_help("CMD", ":split / :sp", "Split and open in new sheet", subgroup="Sheets", order=27)
register_help(
    "CMD",
    ":sort <col> asc|desc",
    "Sort columns (supports A:D, A,B,C ranges)",
    subgroup="Data",
    order=30,
)
register_help(
    "CMD", ":<range> sort <col> ...", "Sort columns within a range", subgroup="Data", order=31
)
register_help(
    "CMD", ":filter <col> <op> <v>", "Filter rows (gt/lt/eq/contains/…)", subgroup="Data", order=32
)
register_help("CMD", ":clearfilter", "Clear active filter", subgroup="Data", order=33)
register_help("CMD", ":swap <addr>", "Swap current cell with address", subgroup="Data", order=33)
register_help("CMD", ":swap row <n>", "Swap current row with row n", subgroup="Data", order=33)
register_help("CMD", ":swap col <c>", "Swap current col with col c", subgroup="Data", order=33)
register_help("CMD", ":find <pat>", "Highlight matching cells", subgroup="Data", order=34)
register_help("CMD", ":findnext / n", "Jump to next search match", subgroup="Data", order=34)
register_help("CMD", ":findprev / N", "Jump to previous search match", subgroup="Data", order=34)
register_help(
    "CMD", ":replace <old> <new>", "Find and replace (whole-value match)", subgroup="Data", order=35
)
register_help(
    "CMD",
    ":cs/pat/repl/",
    "Column substitute — whole-cell literal, current col",
    subgroup="Data",
    order=36,
)
register_help(
    "CMD", ":cs/pat/repl/g", "Column substitute — regex global replace", subgroup="Data", order=37
)
register_help(
    "CMD",
    ":csB/pat/repl/[g]",
    "Column substitute — col B or :cs2/… (1-based #)",
    subgroup="Data",
    order=38,
)
register_help(
    "CMD", ":A,Ccs/pat/repl/[g]", "Column substitute — col range A to C", subgroup="Data", order=39
)
register_help(
    "CMD",
    ":rs/pat/repl/",
    "Row substitute — whole-cell literal, current row",
    subgroup="Data",
    order=40,
)
register_help(
    "CMD", ":rs/pat/repl/g", "Row substitute — regex global replace", subgroup="Data", order=41
)
register_help(
    "CMD",
    ":rs3/pat/repl/[g]",
    "Row substitute — row 3 or :1,3rs/… (range)",
    subgroup="Data",
    order=42,
)
register_help(
    "CMD", ":A1:B5 cs/pat/repl/[g]", "Substitute within range (cs or rs)", subgroup="Data", order=43
)
register_help("CMD", ":name <id> <range>", "Create named range", subgroup="Data", order=44)
register_help(
    "CMD", ":fill <n> <value>", "Fill N cells with value/range", subgroup="Data", order=45
)
register_help("CMD", ":autofit / :af", "Auto-fit column at cursor", subgroup="Data", order=45)
register_help(
    "CMD", ":colfit / :colf", "Auto-fit column at cursor (alias)", subgroup="Data", order=45
)
register_help(
    "CMD", ":rowfit / :rowf", "Expand/collapsed row to fit content", subgroup="Data", order=45
)
register_help(
    "CMD",
    ":<range> autofit [col|row|both]",
    "Fit columns/rows in range (default both)",
    subgroup="Data",
    order=45,
)
register_help(
    "CMD",
    ":<range> colfit",
    "Fit columns in range (alias for :range autofit col)",
    subgroup="Data",
    order=45,
)
register_help(
    "CMD",
    ":<range> rowfit",
    "Fit rows in range (alias for :range autofit row)",
    subgroup="Data",
    order=45,
)
register_help("CMD", ":colwidth / :cw <n>", "Set column width at cursor", subgroup="Data", order=45)
register_help("CMD", ":freeze row N", "Freeze top N rows", subgroup="Data", order=46)
register_help("CMD", ":unfreeze", "Remove freeze", subgroup="Data", order=47)
register_help(
    "CMD",
    ":plot <type> <range>",
    "Chart (bar/line/scatter/pie/histogram)",
    subgroup="Data",
    order=48,
)
register_help(
    "CMD", ":format <cell> …", "Format cell (color/bg/bold/italic/…)", subgroup="Format", order=50
)
register_help("CMD", ":cond <range> …", "Conditional format", subgroup="Format", order=51)
register_help("CMD", ':comment "text"', "Add comment to cell", subgroup="Format", order=52)
register_help("CMD", ":history <cell>", "Show cell change history", subgroup="Format", order=53)
register_help(
    "CMD", ":theme <name>", "Change theme (dracula/light/gruvbox/nord)", subgroup="Format", order=54
)
register_help(
    "CMD", ":loadtext <file>", "Fill cells from plain-text file", subgroup="Format", order=55
)
register_help(
    "CMD",
    ":<range> fmt <prop> [val]",
    "Format every cell in range (color/bg/bold/…)",
    subgroup="Format",
    order=56,
)
register_help(
    "CMD",
    ":<range> cond <op> <val> …",
    "Conditional format rule scoped to range",
    subgroup="Format",
    order=57,
)
register_help(
    "CMD",
    ':range comment "text"',
    "Set comment on every cell in range",
    subgroup="Format",
    order=58,
)
register_help(
    "CMD",
    ":<range> hide",
    "Hide all rows in range",
    subgroup="Format",
    order=59,
)
register_help(
    "CMD",
    ":<range> show",
    "Unhide all rows in range",
    subgroup="Format",
    order=60,
)
register_help(
    "CMD",
    ":<range> <FUNC> [args]",
    "Apply scalar function element-wise to each cell in range",
    subgroup="Format",
    order=61,
)
register_help(
    "CMD",
    ":<range> colwidth <n>",
    "Set width for all columns in range",
    subgroup="Format",
    order=62,
)
register_help(
    "CMD",
    ":<range> autofit",
    "Auto-fit all columns in range",
    subgroup="Format",
    order=63,
)
register_help(
    "CMD",
    ":<range> validate <type> [args]",
    "Apply validation rule to every cell in range",
    subgroup="Format",
    order=64,
)
register_help(
    "CMD",
    ":<range> history",
    "Show cell change history for range",
    subgroup="Format",
    order=65,
)
register_help(
    "CMD",
    ":<range> clearfilter",
    "Clear filter on columns in range",
    subgroup="Format",
    order=66,
)
register_help("CMD", ":set autocalc", "Toggle auto-recalculation", subgroup="Config", order=60)
register_help(
    "CMD",
    ":set key=value",
    "Set/save a config value (e.g. :set theme=nord)",
    subgroup="Config",
    order=61,
)
register_help("CMD", ":recalc", "Force full recalculation", subgroup="Config", order=62)
register_help(
    "CMD", ":func <NAME> <script>", "Register script formula function", subgroup="Config", order=63
)
register_help(
    "CMD", ":fetchnow <cell>", "Force immediate re-fetch of FETCH cell", subgroup="Config", order=64
)
register_help(
    "CMD", ":fetchstop <cell|all>", "Cancel FETCH refresh timer", subgroup="Config", order=65
)
register_help("CMD", ":fetchlist", "Show all active FETCH cells", subgroup="Config", order=66)
register_help("CMD", ":funcs", "List registered formula functions", subgroup="Config", order=67)
register_help("CMD", ":help", "Show this screen", subgroup="Config", order=68)
register_help(
    "CMD", ":rowgroup <open|close|toggle> <row>", "Manage row groups", subgroup="Config", order=69
)
register_help(
    "CMD",
    ":colgroup <open|close|toggle> <col>",
    "Manage column groups",
    subgroup="Config",
    order=70,
)
register_help("CMD", ":messages", "Show message history", subgroup="Config", order=71)
register_help(
    "CMD", ":validate <cell>", "Show validation rules for cell", subgroup="Config", order=72
)
register_help("CMD", ":version", "Show application version", subgroup="Config", order=73)
register_help("CMD", ":undodelsheet", "Restore last deleted sheet", subgroup="Config", order=74)

# ═══════════════════════════════════════════════════════════════════════════
# MACROS
# ═══════════════════════════════════════════════════════════════════════════
register_help(
    "MACRO", "q<a-z>", "Start recording macro into register", subgroup="Recording", order=10
)
register_help("MACRO", "q (while recording)", "Stop recording", subgroup="Recording", order=11)
register_help(
    "MACRO", ":macro start <name>", "Start named macro recording", subgroup="Recording", order=12
)
register_help("MACRO", ":macro stop", "Stop recording", subgroup="Recording", order=13)
register_help("MACRO", "@<a-z>", "Replay macro", subgroup="Playback", order=20)
register_help("MACRO", "@@", "Replay last macro again", subgroup="Playback", order=21)
register_help("MACRO", ":macro run <name>", "Execute named macro", subgroup="Playback", order=22)
