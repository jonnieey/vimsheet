.. _user-guide/editing:

Editing
=======

Enter values, formulas, and manipulate cell content.

Entering Data
-------------

#. Navigate to a cell.
#. Press ``i`` to enter INSERT mode.
#. Type the value or formula (prefix with ``=`` for formulas).
#. Press ``Enter`` to confirm, ``Escape`` to cancel.

Editing Existing Cells
----------------------

#. Navigate to a cell you want to edit.
#. Press ``e`` to enter EDIT mode.
#. Modify the content using terminal editing keys.
#. Press ``Enter`` to confirm your changes.

Copy and Paste
--------------

.. list-table::
   :header-rows: 1

   * - Key
     - Action
   * - ``yy``
     - Yank (copy) current cell
   * - ``y`` (visual)
     - Yank selected range
   * - ``p``
     - Paste below/right
   * - ``P``
     - Paste above/left
   * - ``dd``
     - Delete (cut) current cell
   * - ``d`` (visual)
     - Delete selected range
   * - ``x``
     - Cut current cell
   * - ``u``
     - Undo
   * - ``Ctrl+r``
     - Redo

Fill Operations
---------------

Fill a range with sequential data:

.. code-block:: console

   :fill 1 10  A1:A10

This fills A1:A10 with values 1 through 10.

Clear Cells
-----------

.. code-block:: console

   :clear A1:C10

Or in NORMAL mode, select a range in VISUAL mode and press ``d``.
