.. _plotting/chart-types:

Chart Types
===========

Supported chart types and how to create them.

Creating Charts
---------------

.. code-block:: console

   :plot bar A1:A10
   :plot A1:B10 line "Monthly Sales"
   :plot scatter C1:C100 D1:D100
   :plot pie E1:E5
   :plot histogram F1:F1000
   :A1:B10 plot bar         (range-prefix syntax from visual mode)

Chart Types
-----------

.. list-table::
   :header-rows: 1

   * - Type
     - Description
     - Command
   * - Bar
     - Vertical bar chart
     - ``:plot bar <range>``
   * - Line
     - Line chart
     - ``:plot line <range>``
   * - Scatter
     - XY scatter plot
     - ``:plot scatter <x-range> <y-range>``
   * - Pie
     - Pie chart
     - ``:plot pie <range>``
   * - Histogram
     - Distribution histogram
     - ``:plot hist <range>``

Options
-------

.. list-table::
   :header-rows: 1

   * - Option
     - Description
   * - ``:plot [range] <type> <title>``
     - Chart title as trailing text

Requires the ``plotext`` optional dependency. Falls back to ASCII
block characters if ``plotext`` is not installed.
