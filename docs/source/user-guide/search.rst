.. _user-guide/search:

Search and Replace
==================

VimSheet includes a powerful regex-based search and replace engine.

Searching
---------

Press ``/`` in NORMAL mode to start a forward search:

.. code-block:: text

   /search_term
   /^2024-.*\d{3}

Press ``n`` to jump to the next match, ``N`` to the previous match.

Search Options
--------------

.. list-table::
   :header-rows: 1

   * - Option
     - Default
     - Description
   * - ``ignorecase``
     - ``true``
     - Case-insensitive matching
   * - ``smartcase``
     - ``true``
     - Case-sensitive if uppercase in query
   * - ``wrapscan``
     - ``true``
     - Wrap around at sheet edges
   * - ``hlsearch``
     - ``true``
     - Highlight all matches

Replace
-------

.. code-block:: console

   :%s/old/new/g
   :%s/\d+/[&]/g

Column and Row Substitution
----------------------------

Search and replace within a single column or row:

.. code-block:: console

   :cs/old/new/g       Replace in current column
   :rs/old/new/g       Replace in current row
   :5,10rs/old/new/g   Replace in rows 5 through 10

The replace commands support capture groups and backreferences:

.. code-block:: console

   :%s/(\w+)-(\w+)/$2_$1/g
   :rs/^(\d{4})-(\d{2})/$2\/$1/g

Search Modes
------------

.. code-block:: text

   /pattern         Forward search (from cursor)
   ?pattern         Backward search (from cursor)
   *                Search forward for word under cursor
   #                Search backward for word under cursor
   n                Next match
   N                Previous match
