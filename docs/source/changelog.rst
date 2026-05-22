.. _changelog:

Changelog
=========

Release notes for VimSheet.

0.2.0 — 2026-05-14
------------------

Features
~~~~~~~~

* Multi-line cell content: ``Alt+Enter`` inserts newlines, grid rows
  expand vertically to show all lines
* Row collapse/expand: ``z_`` collapses current row, ``z+`` expands it
* Visual mode row collapse: ``z_`` / ``z+`` collapses/expands all
  selected rows
* Live cell preview: uncommitted content shown in grid during
  insert/edit mode
* Message history: ``:messages`` opens a colored, timestamped log of
  status messages
* Help screen now covers all commands, keybindings, and built-in
  functions
* Range-prefix support for ``:format``, ``:condformat``, ``:comment``,
  ``:hide``, and ``:show`` commands
* Element-wise function apply via ``:<range> <FUNC> [args]``
  (e.g., ``:A1:B10 UPPER`` uppercases every cell).  Aggregate functions
  (SUM, AVG, etc.) continue to yank total to register.
* Bold/normal/italic/underline formatting visual feedback in grid
* Range-prefix support for ``:colwidth``, ``:autofit``, ``:validate``,
  ``:history``, and ``:clearfilter`` commands
* ``ValidationCommand`` undo class for per-cell validation undo
* ``HistoryScreen`` modal for browsing cell change history by range
* ``:colfit`` / ``:colf`` and ``:rowfit`` / ``:rowf`` commands for
  column-only or row-only fit
* ``:<range> autofit`` now accepts ``col`` / ``row`` / ``both``
  argument (default ``both``) to fit columns and/or rows in range
* ``:format`` now supports ``prop=val`` syntax to set multiple properties (e.g. ``bg=red fg=white bold``) and exposes ``align``, ``num_decimals``, ``num_format``, and ``thousands_sep``
* XLSX: import now restores cell font, alignment, fill colors (ARGB→RGB) and defaults to left-align on import. Invalid ``#00000000`` colors no longer crash the grid rendering.
* CSV/TSV: imported cells now default to left alignment
* Plain JSON: imported cells now default to left alignment

0.1.0 — 2026-01-15
------------------

Initial release.

Features
~~~~~~~~

* Modal spreadsheet editing (NORMAL, INSERT, EDIT, VISUAL, COMMAND modes)
* Formula engine with 80+ built-in functions
* Multi-sheet workbook support
* File I/O: CSV, TSV, XLSX, XLS, JSON, HTML, Markdown, LaTeX
* Terminal charting (bar, line, scatter, pie, area)
* Dependency graph with topological recalculation
* Undo/redo stack
* Named ranges
* Conditional formatting
* Data validation
* Search and replace with regex
* Sort and filter
* Macro recording and playback
* Pipeline (non-interactive) mode
* HTTP data fetching
* JSON scripting protocol
* Configurable keybindings and themes
* Frozen panes
