.. _user-guide/sheets:

Sheets
======

Workbooks contain multiple sheets. Each sheet is an independent grid of
cells.

Sheet Management
----------------

.. list-table::
   :header-rows: 1

   * - Command
     - Description
   * - ``:sheet add Name``
     - Add a new sheet
   * - ``:sheet rename Old New``
     - Rename a sheet
   * - ``:sheet delete Name``
     - Delete a sheet
   * - ``:sheet list``
     - List all sheets

Tab Navigation
--------------

Use the ``j``/``k`` keys on the sheet tab bar (above the grid) to switch
between sheets, or use these commands:

.. list-table::
   :header-rows: 1

   * - Key/Command
     - Action
   * - ``g`` + ``t``
     - Next sheet
   * - ``g`` + ``T``
     - Previous sheet
   * - ``:sheet Name``
     - Switch to named sheet

Cross-Sheet References
----------------------

Reference cells on other sheets using the ``SheetName!Cell`` syntax:

.. code-block:: text

   =Sheet2!A1
   =SUM(Sheet2!A1:A10)
   =Expenses!B5 - Income!C5

Moving and Copying Sheets
-------------------------

.. code-block:: console

   :sheet move Name 1
   :sheet copy Name NameCopy
