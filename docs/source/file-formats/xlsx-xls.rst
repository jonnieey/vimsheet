.. _file-formats/xlsx-xls:

Excel Files
===========

Read and write Microsoft Excel files.

XLSX (Excel 2007+)
------------------

.. code-block:: console

   :e workbook.xlsx
   :w output.xlsx

Supports:
* Multiple sheets
* Cell values and formulas
* Number formatting
* Conditional formatting (limited)
* Named ranges

XLS (Excel 97–2003)
-------------------

Read-only support via ``xlrd``:

.. code-block:: console

   :e legacy.xls

Requires the ``xlrd`` optional dependency:

.. code-block:: console

   $ pip install pysheet[full]

Limitations
-----------

* XLSX macros are not executed.
* Some advanced Excel formatting may not be preserved.
* PivotTables and charts are not imported.
