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
    * - EDIT
      - Enter and edit cell content (insert / normal sub-modes)
      - ``\``, ``=``, ``e``, ``E``, ``A``, ``I``, ``S``
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

Cell Editor (EDIT)
------------------

The unified editor handles every kind of cell entry — new values, formulas,
and edits to existing content. It has two sub-modes:

* **insert** — type directly into the cell. The formula bar shows ``INSERT``.
  Tab moves to the next cell to the right. Press ``Alt+Enter`` to insert a
  newline within the cell content; the grid row expands vertically to show
  all lines.
* **normal** — vi motions and operators over the cell text (``h``/``l``,
  ``w``/``b``, ``dw``, ``cw``, ``x``, ``r`` …). The formula bar shows
  ``EDIT``.

Entry keys such as ``\`` and ``=`` open the editor in insert sub-mode so you
can type immediately. From insert sub-mode, ``Escape`` drops to normal
sub-mode (keeping your text) so you can fix a typo with vi motions; ``Enter``
commits from either sub-mode. ``e`` / ``E`` open the editor directly in
normal sub-mode.

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
