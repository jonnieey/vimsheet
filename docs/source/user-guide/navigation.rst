.. _user-guide/navigation:

Navigation
==========

Move around the spreadsheet efficiently using keyboard shortcuts.

Cell Movement
-------------

.. list-table::
   :header-rows: 1

   * - Key
     - Action
   * - ``h``
     - Move left
   * - ``j``
     - Move down
   * - ``k``
     - Move up
   * - ``l``
     - Move right
   * - ``w``
     - Jump to next edge of data
   * - ``b``
     - Jump to previous edge of data
   * - ``e``
     - Jump to end of current word/data block
   * - ``gg``
     - Go to first cell in column
   * - ``G``
     - Go to last non-empty cell in the column
   * - ``0``
     - First column of row
   * - ``$``
     - Last column non-empty cell in the row
   * - ``^``
     - First non-empty cell in row
   * - ``H``
     - Top of visible viewport
   * - ``M``
     - Middle of visible viewport
   * - ``L``
     - Bottom of visible viewport

Scrolling
---------

.. list-table::
   :header-rows: 1

   * - Key
     - Action
   * - ``Ctrl+f``
     - Page down
   * - ``Ctrl+b``
     - Page up
   * - ``Ctrl+d``
     - Half page down
   * - ``Ctrl+u``
     - Half page up
   * - ``z`` + ``Enter``
     - Scroll current cell to top
   * - ``z.``
     - Scroll current cell to center
   * - ``z-``
     - Scroll current cell to bottom

Named Markers
-------------

Press ``m`` followed by a letter to set a marker at the current cell.
Press ``'`` followed by the same letter to jump back.

.. code-block:: text

   ma    Set marker 'a' at current cell
   'a    Jump to marker 'a'

Goto Address
------------

Press ``go`` followed by a cell address and ``Enter`` to jump directly:

.. code-block:: text

   goZ100<Enter>    Go to cell Z100
   goB5<Enter>      Go to cell B5

Use ``:{n}`` as a command to jump to row *n*:

.. code-block:: text

   :42    Go to row 42
   :1     Go to row 1 (top of sheet)
