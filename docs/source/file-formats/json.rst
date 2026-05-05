.. _file-formats/json:

JSON
====

JSON format for interoperability with web services and scripting.
VimSheet supports two JSON formats.

Loading JSON
------------

.. code-block:: console

   :e data.json

**Plain JSON** (``.json``) — a 2D array of rows:

.. code-block:: json

   [
     ["Name", "Age", "City"],
     ["Alice", 30, "New York"],
     ["Bob", 25, "London"]
   ]

Or as an array of objects (headers inferred from keys):

.. code-block:: json

   [
     {"Name": "Alice", "Age": 30, "City": "New York"},
     {"Name": "Bob", "Age": 25, "City": "London"}
   ]

**Native VimSheet format** (``.vimsheet``) — preserves formulas, formatting,
multiple sheets, and all workbook state:

.. code-block:: json

   {
     "sheets": [
       {
         "name": "Sheet1",
         "cells": {
           "A1": {"value": "Hello", "formula": null, "fmt": {"bold": true}}
         }
       }
     ]
   }

Saving JSON
-----------

.. code-block:: console

   :w output.json          Plain JSON (values only)
   :w output.vimsheet      Native format (formulas + formatting)
