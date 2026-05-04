.. _user-guide/undo-redo:

Undo and Redo
=============

PySheet maintains a full history of changes to your spreadsheet.

Undo Operations
---------------

.. list-table::
   :header-rows: 1

   * - Key / Command
     - Description
   * - ``u``
     - Undo last change
   * - ``Ctrl+r``
     - Redo last undone change
   * - ``:undo``
     - Undo last change
   * - ``:redo``
     - Redo last undone change

The undo stack tracks all types of modifications:

* Cell value changes
* Cell format changes
* Row/column insertions and deletions
* Paste operations
* Fill range operations
* Sort operations
* Clear operations

Undo Branches
-------------

If you make a change after undoing, the redo history is cleared and a new
branch starts.

.. code-block:: text

   A1 = 10      (state 1)
   A1 = 20      (state 2)
   A1 = 30      (state 3)
   u            back to state 2
   A1 = 25      (state 4 — redo branch discarded)
