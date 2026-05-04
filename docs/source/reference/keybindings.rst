.. _reference/keybindings:

Keybindings
===========

Complete keybinding reference organized by mode.

Normal Mode
-----------

.. list-table::
   :header-rows: 1

   * - Key
     - Action
   * - ``h`` / ``j`` / ``k`` / ``l``
     - Move cursor
   * - ``w`` / ``b``
     - Word forward/backward
   * - ``e``
     - Word end forward
   * - ``gg`` / ``G``
     - Go to first/last cell
   * - ``0`` / ``$`` / ``^``
     - First/last/first-nonempty column
   * - ``Ctrl+f`` / ``Ctrl+b``
     - Page down / page up
   * - ``Ctrl+d`` / ``Ctrl+u``
     - Half page down / up
   * - ``H`` / ``M`` / ``L``
     - Top/middle/bottom of screen
   * - ``i``
     - Enter INSERT mode
   * - ``e``
     - Enter EDIT mode
   * - ``v`` / ``V`` / ``Ctrl+v``
     - Enter VISUAL / VISUAL LINE / VISUAL BLOCK
   * - ``:``
     - Enter COMMAND mode
   * - ``/``
     - Enter search
   * - ``u``
     - Undo
   * - ``Ctrl+r``
     - Redo
   * - ``yy``
     - Yank cell
   * - ``dd``
     - Delete cell
   * - ``p`` / ``P``
     - Paste below / above
   * - ``x``
     - Cut cell
   * - ``.``
     - Repeat last change
   * - ``m[a-z]``
     - Set marker
   * - ``'`` + ``[a-z]``
     - Jump to marker
   * - ``z`` + ``Enter``
     - Scroll cell to top
   * - ``z.``
     - Scroll cell to center
   * - ``z-``
     - Scroll cell to bottom

Insert Mode
-----------

.. list-table::
   :header-rows: 1

   * - Key
     - Action
   * - ``Escape``
     - Return to NORMAL mode
   * - ``Enter``
     - Confirm cell value, move down
   * - ``Tab``
     - Confirm cell value, move right

Edit Mode
---------

.. list-table::
   :header-rows: 1

   * - Key
     - Action
   * - ``Escape``
     - Confirm changes, return to NORMAL
   * - ``Enter``
     - Confirm changes

Visual Modes
------------

.. list-table::
   :header-rows: 1

   * - Key
     - Action
   * - ``h`` / ``j`` / ``k`` / ``l``
     - Extend selection
   * - ``y``
     - Yank (copy) selection
   * - ``d``
     - Delete selection
   * - ``x``
     - Cut selection
   * - ``>``
     - Indent / shift right
   * - ``<``
     - Outdent / shift left
   * - ``Escape``
     - Return to NORMAL mode
