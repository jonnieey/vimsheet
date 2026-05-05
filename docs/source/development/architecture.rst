.. _development/architecture:

Architecture
============

High-level overview of the VimSheet codebase.

Component Overview
------------------

.. code-block:: text

   ┌─────────────────────────────────────────┐
   │             VimSheetApp                  │
   │  (textual.app.App - main application)   │
   ├─────────┬─────────┬──────────┬──────────┤
   │  Model   │  UI     │Controller│  I/O     │
   ├─────────┼─────────┼──────────┼──────────┤
   │Workbook │ Grid    │ Normal   │ CSV      │
   │Sheet    │ Formula │ Insert   │ XLSX     │
   │Cell     │ Status  │ Edit     │ JSON     │
   │Range    │ Tabs    │ Visual   │ HTML     │
   │Undo     │ Help    │ Command  │ Markdown │
   │Config   │ Chart   │ Search   │ LaTeX    │
   │Validation│ Tabs   │ Macro    │ XLS      │
   └─────────┴─────────┴──────────┴──────────┘
         │         │          │          │
         └─────────┴──────────┴──────────┘
                     │
            Formula Engine          Fetch
         (Tokenizer → Parser →   (HTTP Data
          AST → Evaluator)        Fetcher)

Key Design Decisions
--------------------

* **Modal architecture**: Borrowed from Vim, modes reduce keybinding
  conflicts and enable efficient editing.
* **Dependency graph**: Formulas build a DAG for topological
  recalculation — only changed cells and their dependents update.
* **Adapter pattern**: File I/O uses a pluggable adapter system. Adding
  a new format means implementing a single class.
* **Textual framework**: The UI is built on Textual, a Python TUI
  framework with async event loop and reactive widgets.
* **Adapter pattern**: File I/O uses a pluggable ``FormatAdapter`` system.
  Adding a new format means implementing a single class that extends
  :py:class:`vimsheet.io.base.FormatAdapter`.
* **Macro system**: Keystroke macros recorded with ``q{a-z}`` are stored
  in named registers and replayed with ``@{a-z}``.
* **Background HTTP fetch**: ``@FETCH()`` runs in a background thread
  with configurable refresh intervals. Results are cached and pushed
  to cells when updated.

Data Flow
---------

#. User presses a key.
#. ``VimSheetApp`` routes the key to the current mode handler.
#. The handler performs operations on the model (workbook/sheet/cell).
#. The model emits change events.
#. UI widgets reactively update to reflect the new state.
