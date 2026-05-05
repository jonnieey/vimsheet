.. _reference/errors:

Error Reference
===============

Understanding VimSheet error messages.

Cell Errors
-----------

When a formula cannot be evaluated, the cell displays an error value:

.. list-table::
   :header-rows: 1

   * - Error
     - Meaning
   * - ``#ERR``
     - General evaluation error (e.g., invalid operation)
   * - ``#DIV/0``
     - Division by zero
   * - ``#REF``
     - Invalid cell reference (cell was deleted or out of bounds)
   * - ``#NAME``
     - Unknown function or named range
   * - ``#CIRC``
     - Circular reference detected (formula depends on itself)
   * - ``#TYPE``
     - Wrong value type for an operation (e.g., text in a math formula)
   * - ``#N/A``
     - Value not available (lookup function found no match)

Application Errors
------------------

.. list-table::
   :header-rows: 1

   * - Error
     - Cause
   * - ``File not found: <path>``
     - Specified file does not exist
   * - ``Unsupported format: <ext>``
     - No adapter registered for the file extension
   * - ``Read error: <details>``
     - File could not be read
   * - ``Write error: <details>``
     - File could not be written
   * - ``Invalid range: <range>``
     - Range syntax is invalid
   * - ``Command not found: <cmd>``
     - Unknown command entered
   * - ``Circular dependency``
     - Formula creates a cycle in the dependency graph
   * - ``Tokenize error``
     - Formula contains unexpected or illegal characters
