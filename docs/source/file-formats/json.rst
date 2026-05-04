.. _file-formats/json:

JSON
====

JSON format for interoperability with web services and scripting.

Loading JSON
------------

.. code-block:: console

   :e data.json

JSON is expected as a 2D array of rows:

.. code-block:: json

   [
     ["Name", "Age", "City"],
     ["Alice", 30, "New York"],
     ["Bob", 25, "London"]
   ]

Or as an array of objects (with headers from keys):

.. code-block:: json

   [
     {"Name": "Alice", "Age": 30, "City": "New York"},
     {"Name": "Bob", "Age": 25, "City": "London"}
   ]

Saving JSON
-----------

.. code-block:: console

   :w output.json
