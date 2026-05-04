.. _advanced/pipeline-mode:

Pipeline Mode
=============

PySheet can operate non-interactively as a UNIX pipeline tool, reading
input from stdin and writing output to stdout.

Basic Usage
-----------

.. code-block:: console

   $ cat data.csv | pysheet --pipeline "=SUM(A:A)" > result.txt
   $ echo "1 2 3" | pysheet --pipeline "=AVERAGE(A1:C1)"
   $ curl -s https://api.example.com/data.json | pysheet --pipeline --format json

Pipeline Commands
-----------------

.. list-table::
   :header-rows: 1

   * - Command
     - Description
   * - ``--pipeline <formula>``
     - Evaluate a formula on the input data
   * - ``--format <csv|json|tsv>``
     - Specify input/output format
   * - ``--output <path>``
     - Write output to file
   * - ``--header``
     - Treat first row as headers

Examples
--------

Compute column statistics:

.. code-block:: console

   $ cat sales.csv | pysheet --pipeline "=SUM(B:B)" --header
   $ cat sales.csv | pysheet --pipeline "=AVERAGE(B:B)" --header
   $ cat sales.csv | pysheet --pipeline "=MAX(B:B)" --header

Transform data with formulas:

.. code-block:: console

   $ cat data.csv | pysheet --pipeline "=UPPER(A1)" > uppercased.csv
