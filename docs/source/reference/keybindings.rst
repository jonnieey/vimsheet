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
   * - ``e``
     - Jump to end of current word/data block
   * - ``gg`` / ``G``
     - Go to first / last cell
   * - ``{n}G``
     - Go to row *n*
   * - ``0`` / ``$``
     - First / last column of row
   * - ``^``
     - First non-empty cell in row
   * - ``H`` / ``M`` / ``L``
     - Top / middle / bottom of visible viewport
   * - ``Ctrl+f`` / ``Ctrl+b``
     - Page down / page up
   * - ``Ctrl+d`` / ``Ctrl+u``
     - Half page down / half page up
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

   * - ``i``
     - Enter INSERT mode (insert before cursor)
   * - ``e`` / ``E``
     - Enter EDIT mode (edit cell content)
   * - ``=``
     - Enter INSERT mode (prepends ``=`` for formulas)
   * - ``\``
     - Enter INSERT mode (clears cell first)
   * - ``<`` / ``>``
     - Enter INSERT mode (adds ``'`` prefix / clears and enters)

   * - ``v`` / ``V`` / ``Ctrl+v``
     - Enter VISUAL / VISUAL LINE / VISUAL BLOCK mode
   * - ``u``
     - Undo last change
   * - ``Ctrl+r``
     - Redo last undone change
   * - ``.``
     - Repeat last change

   * - ``yy``
     - Yank (copy) current cell
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
     - Clear cell and enter INSERT mode
   * - ``X``
     - Delete character before cursor (in cell)

   * - ``Ctrl+a``
     - Increment number under cursor
   * - ``Ctrl+x``
     - Decrement number under cursor
   * - ``rv``
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
   * - ``hr`` / ``hc``
     - Hide current row / column
   * - ``sr`` / ``sc``
     - Show hidden row / column
   * - ``rl`` / ``ru``
     - Lock / unlock current cell

   * - ``sj`` / ``sk`` / ``sl`` / ``sh``
     - Shift cells down / up / right / left

   * - ``zc`` / ``zo``
     - Close / open fold at cursor
   * - ``za``
     - Toggle fold at cursor
   * - ``zR`` / ``zM``
     - Open all folds / close all folds

   * - ``fb`` / ``fi`` / ``fu`` / ``fl`` / ``fr`` / ``fc``
     - Toggle bold / italic / underline / left-align / right-align / center

   * - ``gt`` / ``gT``
     - Next sheet / previous sheet
   * - ``g{n}``
     - Go to sheet number *n*
   * - ``ZZ``
     - Save and quit
   * - ``ZQ``
     - Quit without saving
   * - ``ge``
     - Open current cell in external editor (``$EDITOR``)

Insert Mode
-----------

.. list-table::
   :header-rows: 1

   * - Key
     - Action
   * - ``Escape``
     - Return to NORMAL mode (confirm cell value)
   * - ``Enter``
     - Confirm cell value, move down
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

Edit Mode
---------

Edit mode has a vi-like sub-mode for navigating within the cell text.

Normal sub-mode (default on entry):

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
   * - ``y``
     - Yank (copy) selection
   * - ``d`` / ``x``
     - Delete / cut selection
   * - ``p`` / ``P``
     - Paste over selection / paste above
   * - ``>`` / ``<``
     - Shift right / shift left
   * - ``:``
     - Execute command on selection (``:fill``, ``:sort``, ``:plot``, etc.)
   * - ``!``
     - Pipe selection through external command
   * - ``Escape``
     - Return to NORMAL mode
