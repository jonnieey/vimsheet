.. _advanced/conditional-fmt:

Conditional Formatting
======================

Apply formatting rules that depend on cell values.

Operators
---------

.. list-table::
   :header-rows: 1

   * - Operator
     - Description
     - Example
   * - ``gt``
     - Greater than
     - ``gt 50``
   * - ``lt``
     - Less than
     - ``lt 0``
   * - ``eq``
     - Equal to
     - ``eq "Done"``
   * - ``ne``
     - Not equal
     - ``ne "Pending"``
   * - ``ge``
     - Greater or equal
     - ``ge 100``
   * - ``le``
     - Less or equal
     - ``le 50``

Defining Rules
--------------

.. code-block:: console

   :cond A1:A10 gt 50 color #ff0000 bg #ffcccc
   :cond B1:B10 le 100 bold
   :cond C1:C10 eq "Complete" bg #00ff00
   :cond clear

Managing Rules
--------------

.. list-table::
   :header-rows: 1

   * - Command
     - Description
   * - ``:cond <range> <op> <value> [options]``
     - Add conditional formatting rule
   * - ``:cond clear``
     - Clear all conditional formatting rules
