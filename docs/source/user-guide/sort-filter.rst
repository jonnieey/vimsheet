.. _user-guide/sort-filter:

Sort and Filter
===============

Organize your spreadsheet data.

Sorting
-------

Sort all rows in the sheet by one or more columns using the command:

.. code-block:: console

   :sort B desc              Sort column B descending
   :sort A                   Sort column A ascending (default)
   :sort B desc C asc        Sort by B desc, then C asc
   :sort 1                   Sort column 1 (A), ascending
   :sort A:D desc            Sort columns A through D descending
   :sort A,C desc            Sort columns A and C descending
   :sort A:D,C asc           Sort columns A-D and C ascending (mixed range + comma)
   :A1:B10 sort              Sort all columns in A1:B10 ascending
   :A1:B10 sort desc         Sort all columns in A1:B10 descending
   :A1:B10 sort A asc B desc Sort column A asc, column B desc within range
   :A1:B10 sort A:D desc     Sort columns A-D within range descending

The first argument is the column letter (``A``, ``B``, ...) or 1-based
column number (``1``, ``2``, ...). Follow it with ``asc`` (default) or
``desc``. Add more columns for multi-key sorting — each successive
column is used as a tiebreaker when the previous columns have equal
values.

If no column is given, the current cursor column is used (ascending).

**Visual mode sort** — select a range in VISUAL mode and press ``ss`` to
sort the selection ascending by the first column of the selection.

.. note::
   ``:sort`` and ``:sort <col> ...`` are undoable and update the sheet's
   sort state.  Visual mode ``ss`` is not undoable and sorts the
   selection in place.

**How sorting works:**

#. For each row, the value in the primary sort column is extracted.
   Ties are resolved by the next sort column, and so on.
#. Numeric values are sorted numerically; text is sorted
   lexicographically.
#. Rows with no value in any sort column are pushed to the bottom.
#. All rows are rewritten in the new order, preserving formulas,
   formatting, comments, and locked state.
#. **Frozen rows and columns are excluded** — rows above the freeze
   line and columns left of the freeze line are never reordered.

Filtering
---------

Apply filters to hide rows that don't match criteria:

.. code-block:: console

   :filter A1:C100 column=2 pattern=">100"
   :filter A1:C100 column=1 pattern="John"
   :filter clear

Filter Rules
------------

Each filter rule specifies a column and a condition:

.. list-table::
   :header-rows: 1

   * - Pattern
     - Description
     - Example
   * - ``>value``
     - Greater than
     - ``>100``
   * - ``<value``
     - Less than
     - ``<50``
   * - ``=value``
     - Equal to
     - ``=Active``
   * - ``!=value``
     - Not equal
     - ``!=Pending``
   * - ``>=value``
     - Greater or equal
     - ``>=0``
   * - ``<=value``
     - Less or equal
     - ``<=100``
   * - ``regex``
     - Regex match
     - ``^2024-``
