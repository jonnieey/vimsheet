.. _reference/commands:

Commands
========

PySheet commands are entered after pressing ``:`` in NORMAL mode.

File Operations
---------------

.. list-table::
   :header-rows: 1

   * - Command
     - Description
   * - ``:e <path>``
     - Open a file
   * - ``:w``
     - Save current sheet
   * - ``:w <path>``
     - Save to specific path
   * - ``:wq``
     - Save and quit
   * - ``:q``
     - Quit (fails if unsaved)
   * - ``:q!``
     - Force quit without saving

Cell Operations
---------------

.. list-table::
   :header-rows: 1

   * - Command
     - Description
   * - ``:clear <range>``
     - Clear cell values
   * - ``:fill <start> <end> <range>``
     - Fill range with sequence
   * - ``:sort <range> column=N order=asc|desc``
     - Sort range

Sheet Operations
----------------

.. list-table::
   :header-rows: 1

   * - Command
     - Description
   * - ``:sheet add <name>``
     - Add sheet
   * - ``:sheet rename <old> <new>``
     - Rename sheet
   * - ``:sheet delete <name>``
     - Delete sheet
   * - ``:sheet <name>``
     - Switch to sheet

Format Commands
---------------

.. list-table::
   :header-rows: 1

   * - Command
     - Description
   * - ``:format <type> <range> [<args>]``
     - Set number format
   * - ``:align <left|center|right> <range>``
     - Set alignment

Configuration
-------------

.. list-table::
   :header-rows: 1

   * - Command
     - Description
   * - ``:set <option>=<value>``
     - Set configuration option
   * - ``:set``
     - Show current settings

Miscellaneous
-------------

.. list-table::
   :header-rows: 1

   * - Command
     - Description
   * - ``:help [topic]``
     - Show help
   * - ``:version``
     - Show version information
   * - ``:echo <message>``
     - Print a message
   * - ``:!<shell-command>``
     - Execute shell command
