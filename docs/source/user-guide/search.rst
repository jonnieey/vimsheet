.. _user-guide/search:

Search and Replace
==================

PySheet includes a powerful regex-based search and replace engine.

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

The ``:s`` command supports capture groups and backreferences:

.. code-block:: console

   :%s/(\w+)-(\w+)/$2_$1/g
