.. _advanced/named-ranges:

Named Ranges
============

Assign symbolic names to cell ranges for more readable formulas.

Defining Named Ranges
---------------------

.. code-block:: console

   :range define SalesData A1:B100
   :range define TaxRate C1
   :range list

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
   * - ``:range define <name> <range>``
     - Create or update a named range
   * - ``:range delete <name>``
     - Delete a named range
   * - ``:range list``
     - List all named ranges
   * - ``:range jump <name>``
     - Jump to a named range

Scope
-----

Named ranges are scoped to the workbook. You can reference them from any
sheet within the same workbook.

.. code-block:: text

   =SUM(SalesData)          Works from any sheet
   =SalesData               Returns the first cell of the named range
