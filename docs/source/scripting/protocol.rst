.. _scripting/protocol:

Scripting Protocol
==================

VimSheet exposes a JSON-based protocol for external scripts to
interact with a running instance.

Communication
-------------

Scripts communicate with VimSheet via stdin/stdout using newline-delimited
JSON messages.

Communication
-------------

Scripts communicate with VimSheet via stdin/stdout using newline-delimited
JSON messages (one JSON object per line).

Message format:

.. code-block:: json

   {"type": "request", "id": 1, "method": "get_cell", "params": {"sheet": 0, "col": 0, "row": 0}}

Response format:

.. code-block:: json

   {"type": "response", "id": 1, "result": {"value": "Hello"}}

Available Methods
-----------------

.. list-table::
   :header-rows: 1

   * - Method
     - Params
     - Description
   * - ``get_cell``
     - ``sheet``, ``col``, ``row``
     - Get cell value
   * - ``set_cell``
     - ``sheet``, ``col``, ``row``, ``value``
     - Set cell value
   * - ``get_range``
     - ``sheet``, ``col1``, ``row1``, ``col2``, ``row2``
     - Get range as 2D array
   * - ``set_range``
     - ``sheet``, ``col1``, ``row1``, ``col2``, ``row2``, ``values``
     - Set range from 2D array
   * - ``evaluate``
     - ``formula``
     - Evaluate a formula string
   * - ``exec_command``
     - ``command``
     - Execute a ``:command``

Using External Scripts
----------------------

In visual mode, press ``!`` or use the range-prefix syntax to pipe a
selection through an external script:

.. code-block:: console

   :A1:B10!/path/to/script.py

Protocol version 1. Newline-delimited JSON on stdin/stdout.

Example
-------

.. code-block:: python

   import sys
   import json

   def request(method, params):
       msg = json.dumps({"type": "request", "id": 1, "method": method, "params": params})
       sys.stdout.write(msg + "\n")
       sys.stdout.flush()
       return json.loads(sys.stdin.readline())["result"]

   # Get cell A1
   value = request("get_cell", {"sheet": 0, "col": 0, "row": 0})
   print(f"A1 = {value}")

   # Set cell B1 to 42
   request("set_cell", {"sheet": 0, "col": 1, "row": 0, "value": 42})
