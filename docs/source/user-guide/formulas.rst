.. _user-guide/formulas:

Formulas
========

PySheet supports a full-featured formula engine with over 80 built-in
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

PySheet automatically builds a dependency graph when you enter formulas.
When a cell's value changes, all dependent cells are recalculated in
topological order. This ensures correct results even with complex chains
of dependencies.

.. code-block:: text

   A1 = 10
   A2 = A1 * 2         → 20
   A3 = A2 + A1        → 30
   Changing A1 to 20 → A2=40, A3=60

Circular references are detected and reported as errors.

See :ref:`reference/functions` for the complete function reference.
