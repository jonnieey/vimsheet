.. _reference/keybindings:

Keybindings
===========

Complete keybinding reference organized by mode. Numeric prefixes work
with most commands (e.g., ``5j`` moves down 5 cells).

Normal Mode
-----------

.. list-table::
   :header-rows: 1

   * - Key
     - Action
   * - ``h`` / ``j`` / ``k`` / ``l``
     - Move left / down / up / right
   * - ``Arrow keys``
     - Move cursor
   * - ``w``
     - Jump forward to next edge of data
   * - ``b``
     - Jump backward to previous edge of data
   * - ``gg`` / ``G``
     - Go to first / last cell of the column
    * - ``{n}G``
      - Go to row *n*
    * - ``0`` / ``$``
      - First / last column of row
    * - ``^``
      - First non-empty cell in row
    * - ``Ctrl+Home`` / ``Ctrl+End``
      - Jump to first / last cell in sheet
   * - ``H`` / ``M`` / ``L``
     - Top / middle / bottom of visible viewport
   * - ``Ctrl+f`` / ``Ctrl+b``
     - Page down / page up
   * - ``Ctrl+d`` / ``Ctrl+u``
     - Half page down / half page up
   * - ``Ctrl+e`` / ``Ctrl+y``
     - Scroll down / up one line (cursor does not move)
   * - ``zs`` / ``ze``
     - Scroll viewport left / right by one column
   * - ``z Enter`` / ``z.`` / ``z-``
     - Scroll cell to top / center / bottom
   * - ``:``
     - Enter COMMAND mode
   * - ``/`` / ``?``
     - Search forward / backward
   * - ``n`` / ``N``
     - Next / previous search match
   * - ``*`` / ``#``
     - Search forward / backward for word under cursor

   * - ``\``
     - Enter cell editor — **string** value (left-aligned)
   * - ``<``
     - Enter cell editor — **string**, left-aligned
   * - ``>``
     - Enter cell editor — **string**, right-aligned
   * - ``|``
     - Enter cell editor — **string**, center-aligned
   * - ``=``
     - Enter cell editor — **number or formula** (``=100`` → number, ``=SUM(…)`` → formula)
   * - ``e`` / ``E``
      - Enter cell editor in normal sub-mode (cursor at end / start)
   * - ``r``
      - Clear cell and enter editor (replace)
   * - ``A``
     - Enter cell editor at end of content (insert sub-mode)
   * - ``I``
     - Enter cell editor at start of content (insert sub-mode)
   * - ``S``
     - Clear cell and enter editor (string, left-aligned)

   * - ``v`` / ``V`` / ``Ctrl+v``
     - Enter VISUAL / VISUAL LINE / VISUAL BLOCK mode
   * - ``u``
     - Undo last change
   * - ``Ctrl+r``
     - Redo last undone change
   * - ``.``
     - Repeat last change

   * - ``cw`` / ``cc``
     - Clear cell and enter editor (insert sub-mode)
   * - ``dw``
     - Delete (cut) current cell content
   * - ``d$``
     - Delete cell content to end of formula bar
   * - ``yy``
     - Yank (copy) current cell
   * - ``yr`` / ``yc``
     - Yank entire current row / column
   * - ``dd``
     - Delete (cut) current cell
   * - ``x``
     - Cut current cell content
   * - ``p``
     - Paste below / right
   * - ``P``
     - Paste above / left
   * - ``D``
     - Delete cell content (leaves formula)
   * - ``C``
     - Clear cell and enter editor (insert sub-mode)
   * - ``X``
     - Delete character before cursor (in cell)

   * - ``Ctrl+a``
     - Increment number under cursor
   * - ``Ctrl+x``
     - Decrement number under cursor
   * - ``gv``
     - Valueize — replace formula with its current value

   * - ``m[a-z]``
     - Set marker at current cell
   * - ``'[a-z]``
     - Jump to marker
   * - ``go<addr>Enter``
     - Goto cell address (e.g., ``goB42``)

   * - ``q[a-z]``
     - Start recording macro to register
   * - ``@[a-z]``
     - Play macro from register
   * - ``@@``
     - Repeat last played macro

   * - ``"[a-z]``
     - Select named register (prefix before yank/paste)

   * - ``ir`` / ``iR``
     - Insert row below / above current row
   * - ``ic`` / ``iC``
     - Insert column right / left of current column
    * - ``dr`` / ``dc``
      - Delete current row / column
    * - ``sR`` / ``sC``
      - Hide current row / column
    * - ``sr`` / ``sc``
      - Show hidden row / column
    * - ``zl`` / ``zL``
      - Lock / unlock current cell
    * - ``z_`` / ``z+``
      - Collapse / expand row height

    * - ``gsj`` / ``gsk`` / ``gsl`` / ``gsh``
      - Shift cells down / up / right / left

    * - ``zc`` / ``zo``
      - Close / open fold at cursor
    * - ``za``
      - Toggle fold at cursor
    * - ``zR`` / ``zM``
      - Open all folds / close all folds
    * - ``zC`` / ``zO`` / ``zA``
      - Close / open / toggle column group at cursor
    * - ``zr`` / ``ZR``
      - Remove row / column group at cursor

   * - ``tb`` / ``ti`` / ``tu`` / ``tl`` / ``tr`` / ``tc``
     - Toggle bold / italic / underline / left-align / right-align / center

   * - ``gt`` / ``gT``
     - Next sheet / previous sheet
   * - ``gx`` / ``gX``
     - Swap cell with target address (X keeps cursor at source)
   * - ``grx`` / ``grX``
     - Swap row with target row number
   * - ``gcx`` / ``gcX``
     - Swap column with target column letter
   * - ``g{n}``
     - Go to sheet number *n*
   * - ``ZZ``
     - Save and quit
   * - ``ZQ``
     - Quit without saving
    * - ``gw``
      - Open current cell in external editor (``$EDITOR``)

    * - ``Ctrl+g``
      - Show file info
    * - ``f1``
      - Open help screen
    * - ``U``
      - Restore previous cell value from history

Cell Editor — Insert Sub-mode
-----------------------------

All cell entry keys (``\``, ``=``, ``<``, ``>``, ``|``, ``A``, ``I``, ``C``,
``S``, ``r``, ``cw``, ``cc``) open this editor ready to type.

.. list-table::
   :header-rows: 1

   * - Key
     - Action
   * - ``Escape``
     - Leave insert sub-mode for normal sub-mode (buffer preserved)
   * - ``Enter``
     - Commit cell value, move down
   * - ``Tab``
     - Confirm cell value, move right
   * - ``Backspace``
     - Delete character before cursor
   * - ``Delete``
     - Delete character at cursor
   * - ``Arrow keys``
     - Move cursor within cell text
   * - ``Ctrl+w``
     - Delete word before cursor
   * - ``Ctrl+u``
     - Clear entire cell content
    * - ``Tab`` in formula
      - Autocomplete ``@FUNCTION_NAME``
    * - ``Alt+Enter``
      - Insert newline within cell content

Cell Editor — Normal Sub-mode
-----------------------------

Opened directly by ``e`` / ``E``, or reached by pressing ``Escape`` while in
the insert sub-mode.  Provides vi motions and operators over the cell text.

Normal sub-mode:

.. list-table::
   :header-rows: 1

   * - Key
     - Action
   * - ``h`` / ``l``
     - Move cursor left / right
   * - ``w`` / ``b``
     - Word forward / backward
   * - ``e``
     - End of word forward
   * - ``0`` / ``$``
     - Start / end of line
   * - ``i`` / ``a``
     - Enter insert sub-mode (before / after cursor)
   * - ``A`` / ``I``
     - Append at end / insert at start
   * - ``x``
     - Delete character at cursor
   * - ``s`` / ``S``
     - Substitute character / substitute whole line
   * - ``D`` / ``dw`` / ``cw``
     - Delete to end / delete word / change word
   * - ``u``
     - Undo within edit
   * - ``r{char}``
     - Replace character at cursor
   * - ``Enter`` / ``Escape``
     - Commit cell value and return to NORMAL mode

Visual Modes
------------

.. list-table::
   :header-rows: 1

   * - Key
     - Action
    * - ``h`` / ``j`` / ``k`` / ``l``
      - Extend selection
    * - ``w`` / ``b``
      - Extend by word
    * - ``0`` / ``$``
      - Extend to start / end of row
    * - ``gg`` / ``G``
      - Extend to top / bottom
    * - ``H`` / ``M`` / ``L``
      - Top / middle / bottom of visible viewport
    * - ``Ctrl+f`` / ``Ctrl+b``
      - Page down / page up
    * - ``Ctrl+d`` / ``Ctrl+u``
      - Half page down / half page up
   * - ``Ctrl+e`` / ``Ctrl+y``
      - Scroll down / up one line (cursor stays)
   * - ``zs`` / ``ze``
      - Scroll viewport left / right by one column (cursor stays)
   * - ``:``
      - Execute command on selection (``:fill``, ``:sort``, ``:plot``, etc.)
    * - ``tb`` / ``ti`` / ``tu``
      - Bold / italic / underline formatting
    * - ``tl`` / ``tr`` / ``tc``
      - Align left / right / center
    * - ``gsj`` / ``gsk`` / ``gsl`` / ``gsh``
      - Shift selection down / up / right / left
    * - ``!``
      - Pipe selection through external command
    * - ``Escape``
      - Return to NORMAL mode
