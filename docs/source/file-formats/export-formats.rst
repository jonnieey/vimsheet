.. _file-formats/export-formats:

Export Formats
==============

PySheet can export spreadsheets to presentation formats.

HTML
----

Export to HTML table:

.. code-block:: console

   :w output.html

Markdown
--------

Export to Markdown table:

.. code-block:: console

   :w output.md

LaTeX
-----

Export to LaTeX tabular environment:

.. code-block:: console

   :w output.tex

.. code-block:: latex

   \begin{tabular}{lll}
   Name & Age & City \\
   \hline
   Alice & 30 & New York \\
   Bob & 25 & London \\
   \end{tabular}
