.. _reference/commands:

Commands
========

VimSheet commands are entered after pressing ``:`` in NORMAL mode.
Commands can be prefixed with a range in visual mode (e.g.,
``:A1:B10 fill 1`` or ``:A1:B10 plot line``).

File Operations
---------------

.. list-table::
   :header-rows: 1

   * - Command
     - Description
   * - ``:e <path>``
     - Open a file
   * - ``:w``
     - Save current workbook
   * - ``:w <path>``
     - Save to a specific path
   * - ``:wq``
     - Save and quit
   * - ``:x``
     - Save and quit (alias for ``:wq``)
   * - ``:q``
     - Quit (fails if there are unsaved buffers)
   * - ``:q!``
     - Force quit without saving
   * - ``:sp <file>``
     - Open file in a split buffer
   * - ``:ex <file>``
     - Export to file (format detected by extension)
   * - ``:ex <format> <file>``
     - Export with explicit format (``csv``, ``json``, ``html``, ``md``, ``tex``)

Buffer Management
-----------------

.. list-table::
   :header-rows: 1

   * - Command
     - Description
   * - ``:buffers`` / ``:bufs`` / ``:ls``
     - List all open buffers
   * - ``:buf <n>``
     - Switch to buffer number *n*
    * - ``:bd`` / ``:bdel`` / ``:bdelete``
      - Delete current buffer
   * - ``:f`` / ``:file``
     - Show current file info

Cell Operations
---------------

.. list-table::
   :header-rows: 1

   * - Command
     - Description
   * - ``:clear <range>``
     - Clear cell values in range
   * - ``:fill <value>``
     - Fill selected range with constant value
   * - ``:fill <start> <step>``
     - Fill selected range with arithmetic sequence
   * - ``:fmt <addr> <prop>=<val> …``
      - Format a cell — supports ``bg=red fg=white bold align=left num_decimals=2``, or old syntax ``:fmt <addr> <prop> [val]`` for single properties
   * - ``:<range> fmt <prop>=<val> …``
      - Format every cell in a range (supports multiple properties)
   * - ``:<range> <FUNC> [args]``
      - Apply scalar function element-wise to each cell in range
        (e.g., ``:A1:B10 UPPER`` uppercases every cell).
        Aggregate functions (SUM, AVG, etc.) yank total to register instead.
   * - ``:comment <text>``
      - Add comment to current cell
   * - ``:<range> comment <text>``
      - Add comment to every cell in range
   * - ``:comment``
     - Show comment on current cell
   * - ``:history [addr]``
      - Show value history for a cell
   * - ``:<range> history``
      - Show cell change history for range (modal screen)
   * - ``:validate <type> [args]``
     - Set data validation rule on current cell
   * - ``:validate clear``
      - Remove validation from current cell
   * - ``:<range> validate <type> [args]``
      - Apply validation rule to every cell in range
   * - ``:name <NAME> <range>``
     - Define a named range
   * - ``:name <NAME>``
     - Show value of a named range
   * - ``:goto <addr>``
     - Jump to cell address (e.g., ``:goto Z100``)

Search and Replace
------------------

.. list-table::
   :header-rows: 1

   * - Command
     - Description
   * - ``/pattern``
     - Search forward for pattern
   * - ``?pattern``
     - Search backward for pattern
   * - ``:find <pattern>``
     - Search for pattern
   * - ``:findnext``
     - Jump to next match
   * - ``:findprev``
     - Jump to previous match
   * - ``:replace <pat> <repl>``
     - Replace all whole-cell exact matches
   * - ``:%s/pat/repl/[gi]``
     - Whole-sheet substitute (``/g`` = regex, ``/i`` = case-insensitive)
   * - ``:cs/pat/repl/[gi]``
     - Column substitute (current column, ``/g`` = regex)
   * - ``:csB/pat/repl/[gi]``
     - Column substitute in column B
   * - ``:rs/pat/repl/[gi]``
     - Row substitute (current row, ``/g`` = regex)
   * - ``:A1:B10 cs/pat/repl/[gi]``
     - Range-prefixed substitute

Sheet Operations
----------------

.. list-table::
   :header-rows: 1

   * - Command
     - Description
   * - ``:sa [name]`` / ``:sheetadd [name]``
     - Add a new sheet
   * - ``:sd [name]`` / ``:sheetdel [name]``
     - Delete a sheet by name (or current sheet if no name)
   * - ``:sr <newname>``
     - Rename current sheet
   * - ``:sr <oldname> <newname>`` / ``:sheetrename``
     - Rename a sheet by name
   * - ``:sdup [name]`` / ``:sc [name]`` / ``:sheet copy [name]``
     - Duplicate a sheet (appends " (copy)" suffix)
   * - ``:sl`` / ``:sheets`` / ``:sheetlist``
     - List all sheets
   * - ``:sheet <name>``
     - Switch to named sheet
   * - ``:nextsheet``
     - Go to next sheet
   * - ``:prevsheet``
     - Go to previous sheet
   * - ``:undodelsheet``
     - Restore the last deleted sheet

Sort and Filter
---------------

.. list-table::
   :header-rows: 1

   * - Command
     - Description
   * - ``:sort [col] [asc|desc] [<col> [asc|desc] ...]``
      - Sort by one or more columns (letter or number)
   * - ``:<range> sort [col] [asc|desc] ...``
      - Sort columns within range (columnar, independent per column)
   * - ``:filter <col> <op> <value>``
     - Add column filter (ops: ``gt``, ``lt``, ``eq``, ``ne``, ``ge``, ``le``)
    * - ``:clearfilter``
      - Remove all filters
   * - ``:<range> clearfilter``
      - Clear filter on columns in range (e.g., ``:A:C clearfilter``)

Column and Row Management
-------------------------

.. list-table::
   :header-rows: 1

   * - Command
     - Description
   * - ``:colwidth <n>``
      - Set current column width to *n* characters
   * - ``:<range> colwidth <n>``
      - Set width for all columns in range
   * - ``:autofit``
      - Auto-fit current column to content
   * - ``:colfit`` / ``:colf``
      - Auto-fit current column to content (alias)
   * - ``:rowfit`` / ``:rowf``
      - Expand current row to fit content
   * - ``:<range> autofit [col|row|both]``
      - Fit columns/rows in range (default both)
   * - ``:<range> colfit`` / ``:colf``
      - Fit columns in range (alias)
   * - ``:<range> rowfit`` / ``:rowf``
      - Expand collapsed rows in range (alias)
   * - ``:freeze [rows] [cols]``
      - Freeze panes at given row/col (rows stays pinned when scrolling down, columns pinned when scrolling right)
   * - ``:unfreeze``
     - Unfreeze all panes
   * - ``:hiderow [n]``
      - Hide current or specified row
   * - ``:<range> hide``
      - Hide all rows in range
   * - ``:showrow [n]``
      - Show hidden row
   * - ``:<range> show``
      - Show hidden rows in range
   * - ``:hidecol [col]``
     - Hide current or specified column
   * - ``:showcol [col]``
     - Show hidden column
   * - ``:rowgroup [n]``
     - Toggle row group fold at row *n*
   * - ``:colgroup [n]``
     - Toggle column group fold at column *n*

Conditional Formatting
----------------------

.. list-table::
   :header-rows: 1

   * - Command
     - Description
   * - ``:cond <range> <op> <value> [color #hex] [bg #hex] [bold]``
      - Add conditional formatting rule
   * - ``:<range> cond <op> <value> [color #hex] [bg #hex] [bold]``
      - Conditional format rule scoped to range (range-prefix syntax)
   * - ``:cond clear``
     - Clear all conditional formatting rules

Plotting
--------

.. list-table::
   :header-rows: 1

   * - Command
     - Description
   * - ``:plot [range] <type> [title]``
     - Plot a chart (types: ``bar``, ``line``, ``scatter``, ``pie``, ``histogram``)
   * - ``:A1:B10 plot bar``
     - Plot range as bar chart (range-prefix syntax)

HTTP Fetching
-------------

.. list-table::
   :header-rows: 1

   * - Command
     - Description
   * - ``:fetchnow``
     - Force immediate refresh of all HTTP-fetched cells
   * - ``:fetchstop``
     - Stop all background HTTP fetches
   * - ``:fetchlist``
     - Show all active HTTP fetch cells

Configuration
-------------

.. list-table::
   :header-rows: 1

   * - Command
     - Description
   * - ``:set <option>=<value>``
     - Set a configuration option
   * - ``:set``
     - Show current setting for an option
   * - ``:theme <name>``
     - Switch theme (``dark``, ``light``, ``nord``, ``gruvbox``, ``dracula``,
       ``tokyo``, ``monokai``, ``solarized``, ``catppuccin``, ``rose-pine``)
   * - ``:colorscheme``
     - Show all current palette field values
   * - ``:colorscheme <field> <value>``
     - Set a palette field (hex, named colour, or ``$variable``)
   * - ``:colorscheme reset [field]``
     - Reset palette to theme defaults
   * - ``:colorscheme save``
     - Persist current overrides to :file:`config.json`
   * - ``:recalc``
     - Force full recalculation of all formulas

Scripting
---------

.. list-table::
   :header-rows: 1

   * - Command
     - Description
   * - ``:funcs [filter]``
     - List all available formula functions
   * - ``:loadtext <file>``
     - Load text file content into current cell

Miscellaneous
-------------

.. list-table::
   :header-rows: 1

   * - Command
     - Description
   * - ``:help [topic]``
     - Show help
    * - ``:version``
      - Show version information
    * - ``:messages`` / ``:mess``
      - Show message history panel
