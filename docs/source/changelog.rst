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
