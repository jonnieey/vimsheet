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

Configure CSV behavior in your config file:

.. code-block:: toml

   [csv]
   delimiter = ","
   quotechar = "\""
   encoding = "utf-8"
   has_header = true
