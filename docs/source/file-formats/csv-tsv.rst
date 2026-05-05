.. _file-formats/csv-tsv:

CSV and TSV
===========

Comma-separated and tab-separated values.

Opening
-------

.. code-block:: console

   :e data.csv
   :e data.tsv

Saving
------

.. code-block:: console

   :w output.csv
   :w output.tsv

Options
-------

Configure CSV behavior in your config file (``~/.config/vimsheet/config.json``):

.. code-block:: json

   {
     "csv_delimiter": ",",
     "csv_quotechar": "\"",
     "csv_encoding": "utf-8",
     "csv_has_header": true
   }
