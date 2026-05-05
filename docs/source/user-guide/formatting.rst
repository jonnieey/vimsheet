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

Use the ``:format`` command to set formatting properties on specific cells:

.. code-block:: console

   :format A1 bold
   :format B2 color #ff0000
   :format B2 bg #eeeeee
   :format C5 italic
   :format D10 underline

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
