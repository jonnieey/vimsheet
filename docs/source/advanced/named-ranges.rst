.. _advanced/named-ranges:

Named Ranges
============

Assign symbolic names to cell ranges for more readable formulas.

Defining Named Ranges
---------------------

.. code-block:: console

   :name SalesData A1:B100
   :name TaxRate C1
   :name

Using Named Ranges
------------------

Once defined, use the name directly in formulas:

.. code-block:: text

   =SUM(SalesData)
   =AVERAGE(SalesData)
   =C5 * TaxRate

Managing Named Ranges
---------------------

.. list-table::
   :header-rows: 1

   * - Command
     - Description
   * - ``:name <NAME> <range>``
     - Create or update a named range
   * - ``:name <NAME>``
     - Show the range or value of a named range
   * - ``:name``
     - List all named ranges (use ``:name`` with no arguments as a command to show current usage)

Scope
-----

Named ranges are scoped to the workbook. You can reference them from any
sheet within the same workbook.

.. code-block:: text

   =SUM(SalesData)          Works from any sheet
   =SalesData               Returns the first cell of the named range
