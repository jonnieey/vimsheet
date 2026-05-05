.. _user-guide/sort-filter:

Sort and Filter
===============

Organize your spreadsheet data.

Sorting
-------

.. code-block:: console

   :sort A1:C100 column=1 order=asc
   :sort A1:C100 column=3 order=desc
   :sort A1:C100 column=1 order=asc column=2 order=desc

Sort by multiple columns:

.. code-block:: console

   :sort A1:C100 column=1 order=asc column=2 order=asc

Filtering
---------

Apply filters to hide rows that don't match criteria:

.. code-block:: console

   :filter A1:C100 column=2 pattern=">100"
   :filter A1:C100 column=1 pattern="John"
   :filter clear

Filter Rules
------------

Each filter rule specifies a column and a condition:

.. list-table::
   :header-rows: 1

   * - Pattern
     - Description
     - Example
   * - ``>value``
     - Greater than
     - ``>100``
   * - ``<value``
     - Less than
     - ``<50``
   * - ``=value``
     - Equal to
     - ``=Active``
   * - ``!=value``
     - Not equal
     - ``!=Pending``
   * - ``>=value``
     - Greater or equal
     - ``>=0``
   * - ``<=value``
     - Less or equal
     - ``<=100``
   * - ``regex``
     - Regex match
     - ``^2024-``
