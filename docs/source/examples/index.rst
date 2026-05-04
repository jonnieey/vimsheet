.. _examples/index:

Examples
========

Practical examples demonstrating PySheet usage.

Basic Data Entry
----------------

.. code-block:: console

   $ pysheet
   i                    Enter INSERT mode
   Hello<Enter>         Type value, move down
   World<Enter>         Type another value
   <Esc>                Return to NORMAL mode

   gg                   Go to cell A1
   yy                   Yank cell A1
   j                    Move down
   p                    Paste

Financial Calculations
----------------------

Create a simple expense tracker:

.. code-block:: text

   A1: Category    B1: Budget    C1: Actual    D1: Variance
   A2: Rent        B2: 1500       C2: 1500       D2: =C2-B2
   A3: Food        B3: 600        C3: 650        D3: =C3-B3
   A4: Transport   B4: 200        C4: 180        D4: =C4-B4
   A5: Total       B5: =SUM(B2)   C5: =SUM(C2)   D5: =C5-B5

Data Analysis with Pipeline Mode
--------------------------------

.. code-block:: console

   # Generate summary statistics
   $ cat sales.csv | pysheet --pipeline "
       =\"Total: \" & SUM(B:B)
       =\"Avg: \" & AVERAGE(B:B)
       =\"Max: \" & MAX(B:B)
       =\"Count: \" & COUNT(B:B)
   " --header

Batch Processing
----------------

.. code-block:: console

   # Convert all CSV files in a directory to XLSX
   $ for f in *.csv; do
       echo ":w ${f%.csv}.xlsx" | pysheet "$f"
   done

Scripting Integration
---------------------

.. code-block:: python

   """Export selected columns to a new CSV."""
   import sys
   import json

   def req(method, params):
       msg = json.dumps({"type": "request", "id": 1, "method": method, "params": params})
       sys.stdout.write(msg + "\n")
       sys.stdout.flush()
       return json.loads(sys.stdin.readline())["result"]

   # Read the spreadsheet range
   data = req("get_range", {"sheet": 0, "col1": 0, "row1": 0, "col2": 2, "row2": 100})

   # Write CSV to stdout
   import csv
   writer = csv.writer(sys.stdout)
   writer.writerows(data)
