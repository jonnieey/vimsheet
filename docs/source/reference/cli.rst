.. _reference/cli:

Command-Line Interface
======================

.. code-block:: console

   $ vimsheet [OPTIONS] [FILE]

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
   * - ``--script SCRIPT``
     - Run a script file non-interactively
   * - ``--nocurses``
     - Pipeline mode — read from stdin, write to stdout
   * - ``--output FILE``
     - Output file for pipeline or script mode
   * - ``--diff FILE_A FILE_B``
     - Side-by-side cell diff of two spreadsheet files
   * - ``--watch``
     - Auto-reload the file on change
   * - ``--set KEY=VALUE``
     - Override a configuration option (repeatable)
   * - ``--theme THEME``
     - Startup theme (e.g., ``dark``, ``nord``, ``gruvbox``)

Pipeline Mode
-------------

Non-interactive mode reads data from stdin and writes results to stdout:

.. code-block:: console

   $ cat data.csv | vimsheet --nocurses --script transform.vsheet
   $ cat data.csv | vimsheet --nocurses "=SUM(A:A)" > result.txt
   $ vimsheet --nocurses --script my_script.vsheet --output result.xlsx

Diff Mode
---------

Compare two spreadsheet files cell by cell:

.. code-block:: console

   $ vimsheet --diff original.xlsx modified.xlsx

Environment Variables
---------------------

.. list-table::
   :header-rows: 1

   * - Variable
     - Description
   * - ``TERM``
     - Terminal type (for color support)
   * - ``COLORTERM``
     - Color capability hint

Configuration
-------------

VimSheet stores its configuration at ``~/.config/vimsheet/config.json``.
Override with ``--set key=value`` at runtime:

.. code-block:: console

   $ vimsheet --set theme=nord --set autocalc=false

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
