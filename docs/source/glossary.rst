.. _glossary:

Glossary
========

.. glossary::

   Cell
      The intersection of a row and column in a spreadsheet. Identified
      by its column letter and row number (e.g., ``A1``).

   Command Mode
      A mode entered by pressing ``:``, allowing the user to type
      commands such as ``:w`` to save or ``:q`` to quit.

   Dependency Graph
      A directed acyclic graph (DAG) tracking which cells depend on
      which other cells. Used for efficient recalculation when values
      change.

   Edit Mode
      A mode for editing existing cell content with vi-style line-editing
      keybindings (``h``/``l``/``w``/``b``, ``x``, ``u``, etc.).

   Formula
      An expression starting with ``=`` that computes a value from
      other cells, functions, and operators.

   Insert Mode
      A mode where typed characters are entered directly into the active
      cell.

   Macro
      A recorded sequence of keystrokes that can be replayed to automate
      repetitive tasks.

   Named Range
      A symbolic name assigned to a cell or range (e.g., ``SalesData``
      for ``A1:B100``). Usable in formulas like ``=SUM(SalesData)``.

   NORMAL Mode
      The default mode for navigating the spreadsheet and performing
      operations like yank, paste, and delete.

   Pipeline Mode
      A non-interactive mode where VimSheet reads from stdin, processes
      a script or formula, and writes to stdout.

   Range
      A rectangular selection of cells, specified as ``TopLeft:BottomRight``
      (e.g., ``A1:C10``).

   Register
      A named storage location for yanked or deleted content. VimSheet
      supports named registers (``"a``-``"z``), the unnamed register (``""``),
      and numbered registers (``"0``-``"9``).

   Sheet
      An individual grid of cells within a workbook. A workbook can
      have multiple sheets.

   Valueize
      The act of replacing a formula with its current computed value
      (key: ``rv``).

   VISUAL Mode
      A mode for selecting ranges of cells using keyboard motions.

   Workbook
      The top-level document containing one or more sheets. VimSheet
      can have multiple workbooks open as buffers.

   Yank
      The Vim term for copying content to a register.
