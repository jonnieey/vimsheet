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
   * - ``:sdup`` / ``:sc`` / ``:sheet copy``
     - Duplicate the current sheet (appends " (copy)")
   * - ``:sdup <newname>`` / ``:sc <newname>`` / ``:sheet copy <newname>``
     - Rename the current sheet
   * - ``:sdup <src> <newname>`` / ``:sc <src> <newname>`` / ``:sheet copy <src> <newname>``
     - Duplicate sheet ``src`` as a new sheet named ``newname``
   * - ``:sl`` / ``:sheet list``
     - List all sheets (modal screen)

Sheet names may contain spaces if quoted, e.g. ``:sr "Q1 Sales"``,
``:sa "Q1 Sales"`` or ``:sc "Q1 Sales" Q1_2024``.

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
