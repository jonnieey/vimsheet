.. _user-guide/editing:

Editing
=======

Enter values, formulas, and manipulate cell content.

Entering Data
-------------

#. Navigate to a cell.
#. Press ``\`` to enter INSERT mode for plain values, or ``=`` to
   enter INSERT mode with ``=`` prepended for formulas.
#. Type the value or formula.
#. Press ``Enter`` to confirm, ``Escape`` to cancel.

Editing Existing Cells
----------------------

#. Navigate to a cell you want to edit.
#. Press ``e`` to enter EDIT mode.
#. Formula bar is in visual mode. Press ``i`` to start editing.
#. Modify the content using terminal editing keys.
#. Press ``Enter`` to confirm your changes.

Copy, Cut, and Paste
--------------------

.. list-table::
   :header-rows: 1

   * - Key
     - Action
   * - ``yy``
      - Yank (copy) current cell
   * - ``y`` (visual)
      - Yank selected range
   * - ``p``
      - Paste at cursor with formula adjustment
   * - ``P``
      - Paste at cursor without formula adjustment
   * - ``dd``
      - Delete (cut) current cell
   * - ``d`` (visual)
      - Delete selected range
   * - ``x``
      - Cut current cell content
   * - ``D``
      - Delete cell content (keeps formula)
   * - ``C``
      - Clear cell and enter INSERT mode

Registers
---------

VimSheet supports named registers. Prefix any yank or paste with
``"{reg}`` to use a specific register:

.. code-block:: text

   "ayy        Yank cell into register 'a'
   "aP         Paste from register 'a'
   "bdd        Cut cell into register 'b'

The unnamed register (``""``) stores the last yank or delete.
The numbered registers (``"0`` through ``"9``)

Increment and Decrement
-----------------------

Quickly adjust numeric values using these normal mode keys:

.. list-table::
   :header-rows: 1

   * - Key
     - Action
   * - ``Ctrl+a``
     - Increment the number under the cursor by 1
   * - ``Ctrl+x``
     - Decrement the number under the cursor by 1
   * - ``5 Ctrl+a``
     - Increment the number under the cursor by 5

Valueize
--------

Replace a formula with its current computed value:

.. code-block:: text

   gv   Replace formula in current cell with its current value

Locking Cells
-------------

Prevent a cell from being edited:

.. code-block:: text

   zl   Lock current cell (read-only)
   zL   Unlock current cell

Cell Comments
-------------

Add a note to any cell:

.. code-block:: console

   :comment This is a note about this cell
   :comment        Show the comment on the current cell

Data Validation
---------------

Restrict the type of data that can be entered into a cell:

.. code-block:: console

   :validate list yes,no,maybe
   :validate number gt 0
   :validate integer between 1 100
   :validate clear          Remove validation

Cell History
------------

VimSheet tracks changes to cell values. View the history:

.. code-block:: console

   :history           Show history for current cell
   :history B5        Show history for cell B5

Fill Operations
---------------

Fill a range with sequential data:

.. code-block:: console

   :fill 1 10  A1:A10

This fills A1:A10 with values 1 through 10.
