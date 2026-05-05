.. _user-guide/formatting:

Formatting
==========

Control how cell content is displayed.

Cell Format Options
-------------------

.. list-table::
   :header-rows: 1

   * - Property
     - Values
     - Description
   * - ``align``
     - ``left``, ``center``, ``right``
     - Text alignment
   * - ``bold``
     - ``true``, ``false``
     - Bold text
   * - ``italic``
     - ``true``, ``false``
     - Italic text
   * - ``fg``
     - Color name or hex
     - Foreground (text) color
   * - ``bg``
     - Color name or hex
     - Background color
   * - ``format``
     - ``general``, ``number``, ``percent``, ``date``, ``currency``
     - Display format

Number Formatting
-----------------

.. code-block:: console

   :format number A1:A10 2
   :format percent B1:B10 0
   :format currency C1:C10 2
   :format date D1:D10 "%Y-%m-%d"

Conditional Formatting
----------------------

See :ref:`advanced/conditional-fmt` for conditional formatting rules,
color scales, and data bars.
