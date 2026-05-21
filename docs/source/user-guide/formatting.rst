.. _user-guide/formatting:

Formatting
=========

Control how cell content is displayed.

Cell Format Properties
----------------------

.. list-table::
   :header-rows: 1

   * - Key
     - Action
   * - ``fb``
     - Toggle bold on current cell
   * - ``fi``
     - Toggle italic on current cell
   * - ``fu``
     - Toggle underline on current cell
   * - ``fl``
     - Left-align cell content
   * - ``fr``
     - Right-align cell content
   * - ``fc``
     - Center cell content

Cell Format Commands
--------------------

Use the ``:format`` command to set formatting properties on specific cells.
Multiple properties can be combined using ``prop=val`` syntax:

.. code-block:: console

   # Single property (legacy syntax still works)
   :format A1 bold
   :format C5 italic

   # Multi-property prop=val syntax
   :format B1:B5 bold=1 italic=1
   :format D3 align=center num_decimals=2
   :format A1 fg=#ff0000 bg=#eeeeee
   :format E1:E10 bold=1 align=right num_decimals=0

Number Formatting
-----------------

.. code-block:: console

   :format A1: number 2
   :format B1: percent 0
   :format C1: currency 2
   :format D1: date "%Y-%m-%d"

Conditional Formatting
----------------------

Apply formatting that depends on cell values:

.. code-block:: console

   :cond A1:A10 gt 50 color #ff0000
   :cond A1:A10 lt 0 bg #ffcccc bold
   :cond B1:B10 eq "Done" bg #00ff00
   :cond clear

See :ref:`advanced/conditional-fmt` for full details.
