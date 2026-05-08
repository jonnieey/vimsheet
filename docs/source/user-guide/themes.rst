.. _user-guide/themes:

Themes & Color Schemes
======================

VimSheet integrates with Textual's built-in theme system.  When you switch
themes, the spreadsheet grid, sheet tabs, formula bar, and status bar update
automatically — every colour is derived from the theme's CSS variables at
runtime.

Available Themes
----------------

.. code-block:: none

   dark           light          nord           gruvbox
   dracula        tokyo          monokai        solarized
   solarized-light               catppuccin     rose-pine

To apply a theme from the command line:

.. code-block:: console

   :theme nord
   :theme gruvbox
   :theme dracula

The ``:theme`` command accepts short aliases (``dark`` / ``light``) and
theme names interchangeably.

How It Works
------------

The spreadsheet grid is divided into 27 colour **roles** (header background,
cursor cell colour, gridline colour, tab colours, mode indicator colours,
etc.).  Each role is automatically derived from Textual's built-in CSS
variables:

* ``cursor_cell_bg`` → ``$primary``
* ``header_bg`` → ``$surface`` (darkened slightly)
* ``alt_row_bg`` → ``$surface`` (lightened slightly)
* ``visual_sel_bg`` → ``$primary`` blended with ``$surface``
* ``mode_normal`` → ``$success``
* ``mode_insert`` → ``$warning``
* ``mode_edit`` → ``$error``
* ``mode_command`` → ``$primary``
* ``mode_visual`` → ``$accent`` blended with ``$surface``
* … and 18 more roles

This means every built-in Textual theme produces a sensible, matching grid
palette with no manual configuration.

The ``:colorscheme`` Command
----------------------------

You can inspect and tweak individual palette fields at runtime:

List all current colours
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

   :colorscheme

Shows the first few palette field values in the status bar.

Set a single field
~~~~~~~~~~~~~~~~~~

.. code-block:: console

   :colorscheme cursor_cell_bg $primary
   :colorscheme header_bg #2e3440
   :colorscheme gridline red
   :colorscheme alt_row_bg $surface

The value can be:

* A ``$variable`` reference (e.g. ``$primary``, ``$surface``, ``$error``) —
  always resolves to the current theme's value
* A hex colour (e.g. ``#ff0000``, ``#2e3440``)
* A named colour (e.g. ``red``, ``steelblue``, ``ansi_bright_green``)

Reset to theme defaults
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

   :colorscheme reset             # reset all fields
   :colorscheme reset header_bg   # reset a single field

Save overrides
~~~~~~~~~~~~~~

Override changes are temporary until saved.  Once saved they persist across
sessions and re-apply every time you use that theme:

.. code-block:: console

   :colorscheme header_bg #2e3440
   :colorscheme cursor_cell_bg $primary
   :colorscheme save     # writes overrides to config.json

Saved overrides are theme-scoped, so different themes can have different
overrides.

Per-Theme Configuration
-----------------------

You can also define overrides directly in ``~/.config/vimsheet/config.json``.
Every :ref:`palette field <palette-fields>` listed below can be overridden.
For example, to customise the nord theme:

.. code-block:: json

   {
     "theme": "nord",
     "theme_overrides": {
       "nord": {
         "cursor_cell_bg": "#88c0d0",
         "header_bg": "#2e3440",
         "gridline": "#434c5e",
         "tab_active_bg": "#88c0d0",
         "mode_insert": "$warning"
       },
       "gruvbox": {
         "alt_row_bg": "#3c3836"
       }
     }
   }

These overrides are resolved each time the theme is applied, so you can use
Textual ``$variable`` references (e.g. ``$primary``, ``$surface``, ``$warning``)
and they will resolve to the current theme's value at load time:

.. code-block:: json

   {
     "theme_overrides": {
       "nord": {
         "cursor_cell_bg": "$primary",
         "header_bg": "$surface"
       }
     }
   }

.. _palette-fields:

Palette Fields Reference
------------------------

Grid — Headers
~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Field
     - Default derivation
     - Used for
   * - ``header_bg``
     - ``$surface`` (darken 3%)
     - Column & row header background
   * - ``header_fg``
     - ``$text`` (lighten 15%)
     - Column & row header text
   * - ``header_divider``
     - ``$surface`` (darken 8%)
     - Divider characters between headers

Grid — Cursor
~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Field
     - Default derivation
     - Used for
   * - ``cursor_cell_bg``
     - ``$primary``
     - Active cell background
   * - ``cursor_cell_fg``
     - ``$text-primary``
     - Active cell text
   * - ``cursor_header_bg``
     - ``$primary`` (darken 10%)
     - Header at cursor row/column
   * - ``cursor_header_fg``
     - ``$text-primary``
     - Header text at cursor

Grid — Visual Selection
~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Field
     - Default derivation
     - Used for
   * - ``visual_sel_bg``
     - ``$primary`` blended with ``$surface``
     - Visual selection background
   * - ``visual_sel_fg``
     - ``$text``
     - Visual selection text

Grid — Lines & Alternating Rows
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Field
     - Default derivation
     - Used for
   * - ``gridline``
     - ``$surface`` (lighten 12%)
     - Grid line colour
   * - ``alt_row_bg``
     - ``$surface`` (lighten 3%)
     - Alternating row background

Grid — Frozen Panes
~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Field
     - Default derivation
     - Used for
   * - ``frozen_sep``
     - ``$primary`` (lighten 15%)
     - Frozen row/column separator
   * - ``frozen_header_bg``
     - ``$surface`` (lighten 5%)
     - Frozen header background
   * - ``frozen_cell_bg``
     - ``$surface`` (lighten 2%)
     - Frozen cell background

Grid — Error
~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Field
     - Default derivation
     - Used for
   * - ``error_fg``
     - ``$error``
     - Formula error indicator

Sheet Tabs
~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Field
     - Default derivation
     - Used for
   * - ``tab_active_bg``
     - ``$primary``
     - Active tab background
   * - ``tab_active_fg``
     - ``$text-primary``
     - Active tab text
   * - ``tab_inactive_bg``
     - ``$surface``
     - Inactive tab background
   * - ``tab_inactive_fg``
     - ``$text-muted``
     - Inactive tab text
   * - ``tab_add_bg``
     - ``$surface`` (lighten 10%)
     - "+" button background

Formula Bar
~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Field
     - Default derivation
     - Used for
   * - ``formula_cursor_bg``
     - ``$primary``
     - Edit cursor highlight in formula bar

Mode Indicator Colours
~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Field
     - Default derivation
     - Used for
   * - ``mode_normal``
     - ``$success``
     - NORMAL mode label
   * - ``mode_insert``
     - ``$warning``
     - INSERT mode label
   * - ``mode_edit``
     - ``$error``
     - EDIT mode label
   * - ``mode_command``
     - ``$primary``
     - COMMAND mode label
   * - ``mode_visual``
     - ``$accent`` blended with ``$surface``
     - VISUAL mode label
