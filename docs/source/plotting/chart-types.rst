.. _plotting/chart-types:

Chart Types
===========

Supported chart types and how to create them.

Creating Charts
---------------

.. code-block:: console

   :chart bar A1:A10
   :chart line B1:B10 --title "Monthly Sales"
   :chart scatter C1:C100 D1:D100
   :chart pie E1:E5

Chart Types
-----------

.. list-table::
   :header-rows: 1

   * - Type
     - Description
     - Command
   * - Bar
     - Vertical bar chart
     - ``:chart bar <range>``
   * - Line
     - Line chart
     - ``:chart line <range>``
   * - Scatter
     - XY scatter plot
     - ``:chart scatter <x-range> <y-range>``
   * - Pie
     - Pie chart
     - ``:chart pie <range>``
   * - Area
     - Stacked area chart
     - ``:chart area <range>``

Options
-------

.. list-table::
   :header-rows: 1

   * - Option
     - Description
   * - ``--title "Text"``
     - Chart title
   * - ``--xlabel "Text"``
     - X-axis label
   * - ``--ylabel "Text"``
     - Y-axis label
   * - ``--width <n>``
     - Chart width in characters
   * - ``--height <n>``
     - Chart height in rows

Requires the ``plotext`` optional dependency.
