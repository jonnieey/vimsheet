.. _advanced/conditional-fmt:

Conditional Formatting
======================

Apply formatting rules that depend on cell values.

Rule Types
----------

.. list-table::
   :header-rows: 1

   * - Rule Type
     - Description
     - Example
   * - ``highlight``
     - Highlight cells matching criteria
     - ``>100`` → green bg
   * - ``color_scale``
     - Gradient scale across range
     - Low→high → red→yellow→green
   * - ``data_bar``
     - Bar chart within cells
     - Length proportional to value

Defining Rules
--------------

.. code-block:: console

   :cf add A1:A10 highlight ">100" bg=green fg=white
   :cf add B1:B10 color_scale min_color=red max_color=green
   :cf add C1:C10 data_bar color=blue

Managing Rules
--------------

.. list-table::
   :header-rows: 1

   * - Command
     - Description
   * - ``:cf add <range> <type> <args>``
     - Add conditional formatting rule
   * - ``:cf list``
     - List all rules
   * - ``:cf remove <index>``
     - Remove a rule by index
   * - ``:cf clear [range]``
     - Clear rules
