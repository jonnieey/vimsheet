.. _reference/errors:

Error Reference
===============

Understanding PySheet error messages.

Cell Errors
-----------

.. list-table::
   :header-rows: 1

   * - Error
     - Meaning
   * - ``#DIV/0!``
     - Division by zero
   * - ``#VALUE!``
     - Wrong value type
   * - ``#REF!``
     - Invalid cell reference
   * - ``#NAME?``
     - Unknown function name
   * - ``#N/A``
     - Value not available (lookup failed)
   * - ``#NUM!``
     - Invalid numeric value
   * - ``#NULL!``
     - Intersection of ranges is empty
   * - ``#CIRC!``
     - Circular reference detected
   * - ``#PARSE!``
     - Formula parse error

Application Errors
------------------

.. list-table::
   :header-rows: 1

   * - Error
     - Cause
   * - ``File not found: <path>``
     - Specified file does not exist
   * - ``Unsupported format: <ext>``
     - No adapter for file extension
   * - ``Read error: <details>``
     - File could not be read
   * - ``Write error: <details>``
     - File could not be written
   * - ``Invalid range: <range>``
     - Range syntax is invalid
   * - ``Command not found: <cmd>``
     - Unknown command entered
   * - ``Circular dependency``
     - Formula creates a cycle
