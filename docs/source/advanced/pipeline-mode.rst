.. _advanced/pipeline-mode:

Pipeline Mode
=============

VimSheet can operate non-interactively as a UNIX pipeline tool, reading
input from stdin and writing output to stdout.

Basic Usage
-----------

.. code-block:: console

   $ cat data.csv | vimsheet --nocurses "=SUM(A:A)" > result.txt
   $ echo "1 2 3" | vimsheet --nocurses "=AVERAGE(A1:C1)"
   $ vimsheet --nocurses --script transform.vsheet --output result.xlsx

Pipeline Commands
-----------------

.. list-table::
   :header-rows: 1

   * - Command
     - Description
   * - ``--nocurses``
     - Enable non-interactive pipeline mode
   * - ``--script <file>``
     - Run a ``.vsheet`` script file
   * - ``--output <path>``
     - Write output to file (detects format from extension)
   * - ``<formula>``
     - Evaluate a single formula and print the result (positional arg)

Script File Format (``.vsheet``)
------------------------------

Script files use a simple DSL:

.. code-block:: text

   open data.csv
   addsheet Summary
   set A1 "Total"
   formula B1 =SUM(Sheet1!B:B)
   save result.xlsx

Available script commands:

.. list-table::
   :header-rows: 1

   * - Command
     - Description
   * - ``set <addr> <value>``
     - Set a cell value
   * - ``formula <addr> =<expr>``
     - Set a cell formula
   * - ``clear <addr>``
     - Clear a cell
   * - ``open <file>``
     - Open a workbook file
   * - ``save [<file>]``
     - Save the workbook
   * - ``addsheet [<name>]``
     - Add a new sheet
   * - ``delsheet [<name>]``
     - Delete a sheet
   * - ``renamesheet <name>``
     - Rename the current sheet
   * - ``sheet <name>``
     - Switch to a named sheet
   * - ``sort <col> [asc|desc] [<col> [asc|desc] ...]``
      - Sort by one or more columns
   * - ``colwidth <n>``
     - Set column width
   * - ``autofit``
     - Auto-fit current column
   * - ``freeze <rows> [<cols>]``
     - Freeze panes
   * - ``unfreeze``
     - Unfreeze panes
   * - ``hiderow <n>`` / ``showrow <n>``
     - Hide or show a row
   * - ``hidecol <col>`` / ``showcol <col>``
     - Hide or show a column
   * - ``comment <addr> <text>``
     - Add a comment to a cell
   * - ``name <NAME> <range>``
     - Define a named range
   * - ``print``
     - Print current sheet info

Examples
--------

Compute column statistics:

.. code-block:: console

   $ cat sales.csv | vimsheet --nocurses "=SUM(B:B)"
   $ cat sales.csv | vimsheet --nocurses "=AVERAGE(B:B)"
   $ cat sales.csv | vimsheet --nocurses "=MAX(B:B)"

Transform data with formulas:

.. code-block:: console

   $ cat data.csv | vimsheet --nocurses "=UPPER(A1)" > uppercased.csv

Batch convert files:

.. code-block:: console

   $ for f in *.csv; do
       echo "open $f" > /tmp/convert.vsheet
       echo "save ${f%.csv}.xlsx" >> /tmp/convert.vsheet
       vimsheet --nocurses --script /tmp/convert.vsheet
     done
