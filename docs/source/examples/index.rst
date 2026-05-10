.. _examples/index:

Examples
========

Practical, self-contained examples demonstrating real-world usage of
VimSheet.

Expense Tracker
---------------

Create a monthly expense tracker with conditional formatting:

.. code-block:: text

   # Enter headers
   A1: Category    B1: Budget    C1: Actual    D1: Variance

   # Enter data
   A2: Rent        B2: 1500       C2: 1500
   A3: Food        B3: 600        C3: 650
   A4: Transport   B4: 200        C4: 180
   A5: Utilities   B5: 300        C5: 320
   A6: Total       B6: =SUM(B2:B5) C6: =SUM(C2:C5)

   # Variance column
   D2: =C2-B2
   D3: =C3-B3
   D4: =C4-B4
   D5: =C5-B5
   D6: =C6-B6

   # Conditional formatting: highlight overspend in red
   :cond D2:D6 gt 0 color #ff0000 bold

   # Format as currency
   :format B2 bold
   :format C2 bold

   # Save
   :w expenses.vimsheet

Grade Calculator
----------------

Calculate student grades with letter assignment:

.. code-block:: text

   A1: Student  B1: Score   C1: Grade

   A2: Alice    B2: 92
   A3: Bob      B3: 78
   A4: Carol    B4: 85
   A5: Dave     B5: 63
   A6: Eve      B6: 95

   C2: =IF(B2>=90, "A", IF(B2>=80, "B", IF(B2>=70, "C", IF(B2>=60, "D", "F"))))

Fill the grade formula down:

.. code-block:: text

   # Yank C2, select C3:C6, paste
   yy (on C2)
   j  (move to C3)
   v  (enter visual mode)
   jjj (select down to C6)
   p  (paste formula)

Or use the fill command after selecting the range in visual mode:

.. code-block:: console

   :C3:C6 fill =IF(B3>=90,"A",IF(B3>=80,"B",IF(B3>=70,"C",IF(B3>=60,"D","F"))))

   # Show summary
   A8: Average   B8: =AVERAGE(B2:B6)
   A9: Max       B9: =MAX(B2:B6)
   A10: Min      B10: =MIN(B2:B6)
   A11: Count    B11: =COUNT(B2:B6)

   :sort C            Sort by grade ascending
   :sort B desc       Sort by score descending

Sales Data Analysis with VLOOKUP
--------------------------------

Analyze sales data with product lookup:

.. code-block:: text

   # Sheet1: Sales Transactions
   A1: Date       B1: Product   C1: Qty   D1: Price
   A2: 2026-01-05 B2: P001      C2: 10
   A3: 2026-01-06 B3: P003      C3: 5
   A4: 2026-01-07 B4: P002      C4: 8

   # Sheet2: Product Catalog
   :addsheet Catalog
   A1: Code    B1: Name       C1: Unit Price
   A2: P001    B2: Widget A   C2: 19.99
   A3: P002    B3: Widget B   C3: 29.99
   A4: P003    B4: Widget C   C4: 14.99

   # Sheet1: Lookup prices and compute total
   :sheet Sheet1
   D2: =VLOOKUP(B2, Catalog!A1:C4, 3, FALSE)
   D3: =VLOOKUP(B3, Catalog!A1:C4, 3, FALSE)
   D4: =VLOOKUP(B4, Catalog!A1:C4, 3, FALSE)

   E1: Total
   E2: =C2*D2      E3: =C3*D3      E4: =C4*D4
   E6: =SUM(E2:E4)

Budget vs Actual Dashboard
--------------------------

Multi-sheet workbook for monthly budget tracking:

.. code-block:: text

   # --- Sheet: Budget ---
   :renamesheet Budget
   A1: Item       B1: Jan    C1: Feb    D1: Mar
   A2: Rent       B2: 1500   C2: 1500   D2: 1500
   A3: Food       B3: 600    C3: 600    C3: 600
   A4: Transport  B4: 200    B4: 200    B4: 200

   # --- Sheet: Actuals ---
   :addsheet Actuals
   A1: Item       B1: Jan    C1: Feb    D1: Mar
   A2: Rent       B2: 1500   C2: 1500   D2: 1550
   A3: Food       B3: 580    C3: 620    C3: 590
   A4: Transport  B4: 180    B4: 210    B4: 195

   # --- Sheet: Dashboard ---
   :addsheet Dashboard
   A1: Item       B1: Jan    C1: Feb    D1: Mar
   A2: Rent       B2: =Actuals!B2-Budget!B2
   A3: Food       B3: =Actuals!B3-Budget!B3
   A4: Transport  B4: =Actuals!B4-Budget!B4

   A6: Surplus    B6: =SUM(B2:B4)

   # Highlight negative variances
   :cond B2:D4 lt 0 color #ff0000 bg #ffcccc

   # Save as native format to preserve formulas
   :w budget.vimsheet

Data Cleaning with Text Functions
----------------------------------

Clean and standardize messy data:

.. code-block:: text

   A1: Raw Data     B1: Cleaned
   A2: "  john   "  B2: =TRIM(PROPER(A2))
   A3: "ALICE"      B3: =TRIM(PROPER(A3))
   A4: "  bob  "    B4: =TRIM(PROPER(A4))
   A5: "CAROL  "    B5: =TRIM(PROPER(A5))

   # Extract parts from formatted strings
   D1: Full Name    E1: First     F1: Last
   D2: "Smith, John"
   E2: =TRIM(MID(D2, FIND(",", D2)+1, 99))   → "John"
   F2: =LEFT(D2, FIND(",", D2)-1)             → "Smith"

External Scripting with Python
-------------------------------

Process spreadsheet data with an external Python script:

.. code-block:: python

   #!/usr/bin/env python3
   """double.py — doubles all numeric values in a selected range.
   Usage: Select a range in VimSheet, press :!./double.py"""
   import sys, json

   for line in sys.stdin:
       msg = json.loads(line.strip())
       if msg.get("type") == "request":
           method = msg["method"]
           params = msg.get("params", {})
           if method == "get_range":
               data = json.loads(sys.stdin.readline())
               doubled = [[c * 2 if isinstance(c, (int, float)) else c for c in row] for row in data]
               response = {"type": "response", "id": msg["id"], "result": doubled}
               sys.stdout.write(json.dumps(response) + "\n")
               sys.stdout.flush()

Run it from VimSheet:

.. code-block:: text

   # Select a range in visual mode, then:
   :!./double.py

Fetch Live API Data
-------------------

Use ``@FETCH`` to pull live data into your spreadsheet:

.. code-block:: text

   # Weather data (refreshed every 5 minutes)
   A1: =FETCH("https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&current_weather=true", 300, "$.current_weather.temperature")
   B1: =FETCH("https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&current_weather=true", 300, "$.current_weather.windspeed")
   C1: =FETCH("https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&current_weather=true", 300, "$.current_weather.weathercode")

   # View all active fetches
   :fetchlist

   # Force immediate refresh
   :fetchnow

Recording and Playing Macros
-----------------------------

Automate repetitive formatting:

.. code-block:: text

   # Goal: Bold the first column and italicize the second
   # Record macro to register 'a':
   qa       Start recording
   fb       Toggle bold
   l        Move right
   fi       Toggle italic
   j        Move down
   0        Move to start of row
   q        Stop recording

   # Play it 10 times:
   10@a

   # Or repeat last macro:
   @@

Pipeline Batch Conversion
--------------------------

Convert all CSV files in a directory to XLSX:

.. code-block:: console

   $ for f in *.csv; do
       cat > /tmp/convert.vsheet << EOF
   open $f
   save ${f%.csv}.xlsx
   EOF
       vimsheet --nocurses --script /tmp/convert.vsheet
     done

Or use a single formula pipeline to compute statistics:

.. code-block:: console

   $ cat sales.csv | vimsheet --nocurses "=SUM(B:B)"
   $ cat sales.csv | vimsheet --nocurses "=AVERAGE(B:B)"
   $ cat sales.csv | vimsheet --nocurses "=MAX(B:B) & \", \" & MIN(B:B)"

Diff Two Spreadsheets
----------------------

Side-by-side comparison of two workbooks:

.. code-block:: console

   $ vimsheet --diff original.xlsx updated.xlsx

   # Cells with differences are highlighted with their old and new values
