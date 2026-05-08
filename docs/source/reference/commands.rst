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
   * - ``:bd``
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
   * - ``:fmt <addr> <prop> [value]``
     - Format a cell (``color``, ``bg``, ``bold``, ``italic``, ``underline``)
   * - ``:comment <text>``
     - Add comment to current cell
   * - ``:comment``
     - Show comment on current cell
   * - ``:history [addr]``
     - Show value history for a cell
   * - ``:validate <type> [args]``
     - Set data validation rule on current cell
   * - ``:validate clear``
     - Remove validation from current cell
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
     - Replace all occurrences
   * - ``:cs/pat/repl/``
     - Column substitute (replace in current column)
   * - ``:rs/pat/repl/``
     - Row substitute (replace in current row)

Sheet Operations
----------------

.. list-table::
   :header-rows: 1

   * - Command
     - Description
   * - ``:sheet <name>``
     - Switch to named sheet
   * - ``:addsheet [name]``
     - Add a new sheet
   * - ``:delsheet [name]``
     - Delete a sheet
   * - ``:renamesheet <name>``
     - Rename current sheet
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

Column and Row Management
-------------------------

.. list-table::
   :header-rows: 1

   * - Command
     - Description
   * - ``:colwidth <n>``
     - Set current column width to *n* characters
   * - ``:autofit``
     - Auto-fit current column to content
   * - ``:freeze [rows] [cols]``
     - Freeze panes at given row/col
   * - ``:unfreeze``
     - Unfreeze all panes
   * - ``:hiderow [n]``
     - Hide current or specified row
   * - ``:showrow [n]``
     - Show hidden row
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
