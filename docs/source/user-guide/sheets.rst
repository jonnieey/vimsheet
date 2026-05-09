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
   * - ``:sa Name`` / ``:sheet add Name``
     - Add a new sheet
   * - ``:sr <newname>`` / ``:sheet rename <newname>``
     - Rename the current sheet
   * - ``:sr <old> <new>`` / ``:sheet rename <old> <new>``
     - Rename a sheet by name
   * - ``:sd Name`` / ``:sheet delete Name``
     - Delete a sheet
   * - ``:sdup Name`` / ``:sc Name`` / ``:sheet copy Name``
     - Duplicate a sheet (appends " (copy)" suffix)
   * - ``:sl`` / ``:sheet list``
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
