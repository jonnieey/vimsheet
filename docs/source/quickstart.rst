.. _quickstart:

Quickstart
==========

Launch VimSheet from your terminal:

.. code-block:: console

   $ vimsheet

You will see an empty spreadsheet grid with a status bar at the bottom.

.. note::

   VimSheet starts in **NORMAL** mode (like Vim). Press ``i`` to enter
   **INSERT** mode and start typing into cells.

Your First Spreadsheet
----------------------

1. Press ``i`` to enter INSERT mode.
2. Type ``Hello`` in cell A1 and press ``Enter``.
3. Press ``j`` to move down to A2.
4. Press ``i``, type ``World``, and press ``Enter``.
5. Move to cell A3 and enter the formula ``=SUM(A1:A2)``.
6. Press ``Enter`` — the cell shows the sum.

Basic Navigation
----------------

.. list-table::
   :header-rows: 1

   * - Key
     - Action
   * - ``h`` / ``j`` / ``k`` / ``l``
     - Move left / down / up / right
   * - ``gg``
     - Go to top of sheet
   * - ``G``
     - Go to bottom of sheet
   * - ``0`` / ``$``
     - Start / end of row
   * - ``Ctrl+f`` / ``Ctrl+b``
     - Page down / page up

Saving and Loading
------------------

.. code-block:: console

   :w filename.csv     Save as CSV
   :e filename.csv     Open CSV file
   :wq                 Save and quit
   :q!                 Quit without saving

Next Steps
----------

* :ref:`user-guide/index` — learn all features in depth
* :ref:`reference/keybindings` — complete keybinding reference
* :ref:`reference/functions` — formula function reference
