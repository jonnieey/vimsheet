.. _user-guide/modes:

Modes
=====

VimSheet uses a modal interface inspired by Vim. Each mode provides a
different set of keybindings for interacting with the spreadsheet.

.. list-table::
   :header-rows: 1

   * - Mode
     - Description
     - Entry Key
   * - NORMAL
     - Navigate, select cells, copy/paste
     - ``Escape`` (from any mode)
    * - INSERT
      - Type values and formulas into cells
      - ``\`` or ``=``
   * - EDIT
     - Edit an existing cell's content
     - ``e``
   * - VISUAL
     - Select ranges with keyboard
     - ``v``
   * - VISUAL LINE
     - Select full rows
     - ``V``
   * - VISUAL BLOCK
     - Select rectangular block
     - ``Ctrl+v``
   * - COMMAND
     - Execute ``:commands``
     - ``:``

Normal Mode
-----------

Default mode on startup. Use Vim-style keys to move the cursor around the
grid. Press ``:`` to enter a command, ``\`` or ``=`` to insert, ``v`` for visual
selection.

Insert Mode
-----------

Type directly into the active cell. Press ``Escape`` to return to NORMAL
mode. Tab moves to the next cell to the right. Press ``Alt+Enter`` to
insert a newline within the cell content — the grid row expands
vertically to show all lines.

Edit Mode
---------

Edit the contents of the current cell without overwriting it. The cursor
appears inside the cell's formula bar at the top. Press ``Escape`` or
 ``Enter`` to confirm changes and return to NORMAL mode.

Visual Modes
------------

Select ranges using keyboard motions:

* ``v`` then ``h`` / ``j`` / ``k`` / ``l`` — expand selection
* ``V`` — select entire rows
* ``Ctrl+v`` — select rectangular block
* ``H`` / ``M`` / ``L`` — jump to top / middle / bottom of viewport
* ``Ctrl+a`` / ``Ctrl+x`` — increment / decrement all numeric cells
* ``go<addr>`` ``Enter`` — extend selection to address
* ``z_`` / ``z+`` — collapse / expand all selected rows
* ``y`` — yank (copy) selection
* ``d`` — delete selection
* ``x`` — cut selection

Command Mode
-----------

Press ``:`` to open the command line and type commands. Tab-completion
is available for commands, file paths, sheet names, and theme names.
See :ref:`reference/commands` for the full command reference.
