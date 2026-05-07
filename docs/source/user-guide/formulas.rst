.. _user-guide/formulas:

Formulas
========

VimSheet supports a full-featured formula engine with over 100 built-in
functions and dependency tracking.

Entering Formulas
-----------------

Start a cell with ``=`` followed by the formula expression:

.. code-block:: text

   =SUM(A1:A10)
   =AVERAGE(B1:B20)
   =IF(A1 > 10, "High", "Low")
   =VLOOKUP(D5, A1:B100, 2, FALSE)

Cell References
---------------

.. list-table::
   :header-rows: 1

   * - Reference
     - Description
   * - ``A1``
     - Relative reference
   * - ``$A$1``
     - Absolute reference
   * - ``$A1``
     - Mixed (column absolute, row relative)
   * - ``A$1``
     - Mixed (column relative, row absolute)
   * - ``A1:B10``
     - Range reference
   * - ``Sheet2!A1``
     - Cross-sheet reference

Paste Behavior
--------------

When you yank a formula cell and paste with ``p``, cell references are
adjusted relative to the destination cell:

* **Relative row** (e.g. ``A1``) — row number is set to the
  destination cell's row: yanking ``=B2`` from D1 and pasting to D3
  produces ``=B3``.
* **Relative column** (e.g. ``A1``) — column letter is shifted by the
  column offset between source and destination: yanking ``=B2`` from D1
  and pasting to E1 produces ``=C2``.
* **Absolute** (e.g. ``$A$1``) — never changed.
* **Mixed** — the locked part is preserved, the unlocked part is
  adjusted: ``$A1`` keeps column ``A`` but the row is set to the
  destination row; ``A$1`` keeps row ``1`` but the column shifts.

Pasting with ``P`` pastes the formula exactly as yanked — no adjustment
is applied.

Operators
---------

.. list-table::
   :header-rows: 1

   * - Operator
     - Description
   * - ``+``, ``-``, ``*``, ``/``
     - Arithmetic
   * - ``^``
     - Exponentiation
   * - ``&``
     - String concatenation
   * - ``=``, ``<>``, ``<``, ``>``, ``<=``, ``>=``
     - Comparison
   * - ``:``
     - Range operator
   * - ``,``
     - Union operator

Dependency Tracking
-------------------

VimSheet automatically builds a dependency graph when you enter formulas.
When a cell's value changes, all dependent cells are recalculated in
topological order. This ensures correct results even with complex chains
of dependencies.

.. code-block:: text

   A1 = 10
   A2 = A1 * 2         → 20
   A3 = A2 + A1        → 30
   Changing A1 to 20 → A2=40, A3=60

Circular references are detected and reported as ``#CIRC`` errors.

HTTP Data Fetching
------------------

Fetch live data from the web with the ``@FETCH`` function:

.. code-block:: text

   =FETCH("https://api.example.com/data")
   =FETCH("https://api.example.com/data", 60, "$.temperature")
   =FETCH("https://api.example.com/data", 300, "results[0].value")

The function takes:
- **url** — the URL to fetch
- **refresh_seconds** (optional) — how often to refresh in the background
- **json_path** (optional) — dot/bracket notation to extract a specific value

Array and object responses automatically spill into adjacent cells.
Use ``:fetchlist`` to see all active fetches, ``:fetchnow`` to
immediately refresh, and ``:fetchstop`` to stop all background fetches.

See :ref:`reference/functions` for the complete function reference.
