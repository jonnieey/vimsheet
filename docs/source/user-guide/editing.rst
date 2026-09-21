.. _user-guide/editing:

Editing
=======

Enter values, formulas, and manipulate cell content.

Entering Data
-------------

VimSheet distinguishes **strings** from **numbers and formulas** at entry time:

* ``\`` — open the cell editor for a **string** (stored as text, left-aligned by
  default).  Use ``<``, ``>``, or ``|`` for left-, right-, or center-aligned
  string insert.
* ``=`` — open the cell editor for a **number or formula**.
  Typing ``=100`` stores the number 100; ``=SUM(A1:A5)`` stores a live formula.
  Content after ``=`` is evaluated — pure literals are stored as values,
  expressions as formulas.

To confirm, press ``Enter``.  ``Escape`` leaves the insert sub-mode for the
normal sub-mode (your text is preserved); press ``Enter`` (or ``Escape`` again)
to commit, or use vi motions to fix the entry first.

Multi-line Cell Content
-----------------------

Cells can hold multiple lines of text. While in the cell editor:

* Press ``Alt+Enter`` to insert a newline at the cursor position.
* The grid row automatically expands to show all lines.
* The formula bar shows the current line (the line after the last
  newline) for focused editing.

Collapse and expand row height with normal mode keys:

.. list-table::
   :header-rows: 1

   * - Key
     - Action
   * - ``z_``
     - Collapse current row to height 1
   * - ``z+``
     - Expand current row to full content height

In visual mode, ``z_`` and ``z+`` collapse or expand all rows in the
selection.

Editing Existing Cells
----------------------

#. Navigate to a cell you want to edit.
#. Press ``e`` to open the editor at the end of the content (``E`` for the
   start).  The editor opens in normal sub-mode.
#. Use vi motions (``h``, ``w``, ``dw`` …) or press ``i`` / ``a`` to type.
#. Press ``Enter`` to confirm your changes.

``A`` and ``I`` open the editor in insert sub-mode at the end / start of the
content, pre-filled with the existing value.  All of these keys share the same
editor, so ``Escape`` always drops you into normal sub-mode to fix the entry
with vi motions before committing.

Copy, Cut, and Paste
--------------------

.. list-table::
   :header-rows: 1

   * - Key
     - Action
   * - ``yy``
      - Yank (copy) current cell
   * - ``yr``
      - Yank entire current row
   * - ``yc``
      - Yank entire current column
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
      - Clear cell and enter the editor (insert sub-mode)

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

Increment, decrement, ``dd``, ``dr``, and ``dc`` are all repeatable with ``.``.

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
-----------

VimSheet tracks changes to cell values. View the history:

.. code-block:: console

   :history           Show history for current cell
   :history B5        Show history for cell B5

Restore a previous cell value from history:

.. code-block:: text

   U   Restore current cell to previous value

Fill Operations
---------------

Fill a range with sequential data:

.. code-block:: console

   :fill 1 10  A1:A10

This fills A1:A10 with values 1 through 10.

Message History
---------------

VimSheet keeps a history of status messages, errors, and notifications.
View them with:

.. code-block:: console

   :messages      Open the message history panel

Messages are color-coded: red for errors, green for success, yellow
for informational messages. The panel shows timestamps and scrolls
chronologically (newest at the top).
