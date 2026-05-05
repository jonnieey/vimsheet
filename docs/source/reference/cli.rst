.. _reference/cli:

Command-Line Interface
======================

.. code-block:: console

   $ pysheet [OPTIONS] [FILE]

Options
-------

.. list-table::
   :header-rows: 1

   * - Option
     - Description
   * - ``FILE``
     - Optional file to open on startup
   * - ``--version``
     - Show version and exit
   * - ``--help``
     - Show help message and exit
   * - ``--config PATH``
     - Path to config file (default: ``~/.config/pysheet/config.toml``)

Environment Variables
---------------------

.. list-table::
   :header-rows: 1

   * - Variable
     - Description
   * - ``PYSHOOK_CONFIG``
     - Path to configuration file
   * - ``TERM``
     - Terminal type (for color support)
   * - ``COLORTERM``
     - Color capability hint

Exit Codes
----------

.. list-table::
   :header-rows: 1

   * - Code
     - Meaning
   * - ``0``
     - Success
   * - ``1``
     - General error
   * - ``2``
     - Invalid arguments
