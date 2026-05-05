.. _installation:

Installation
============

VimSheet requires **Python 3.11 or later**.

Stable Release
--------------

Install from PyPI:

.. code-block:: console

   $ pip install vimsheet

With full optional dependencies (plotting, HTTP fetch, Excel .xls support):

.. code-block:: console

   $ pip install vimsheet[full]

Development Version
-------------------

Clone and install from source:

.. code-block:: console

   $ git clone https://github.com/vimsheet/vimsheet.git
   $ cd vimsheet
   $ pip install -e ".[dev]"

Verify Installation
-------------------

.. code-block:: console

   $ vimsheet --version
   VimSheet 0.1.0

   $ vimsheet --help

Dependencies
------------

.. list-table::
   :header-rows: 1

   * - Package
     - Minimum Version
     - Purpose
   * - ``textual``
     - 0.60.0
     - Terminal UI framework
   * - ``openpyxl``
     - 3.1.0
     - Excel .xlsx read/write
   * - ``xlrd`` (optional)
     - 2.0.0
     - Excel .xls read
   * - ``odfpy`` (optional)
     - 1.4.0
     - OpenDocument format
   * - ``plotext`` (optional)
     - 5.2.0
     - Terminal charting
   * - ``requests`` (optional)
     - 2.31.0
     - HTTP data fetching
   * - ``watchdog`` (optional)
     - 4.0.0
     - File system watching
