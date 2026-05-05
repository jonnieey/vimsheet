.. _development/extending:

Extending VimSheet
==================

Guide for creating extensions and plugins.

Adding File Format Support
--------------------------

Implement the :py:class:`vimsheet.io.base.FormatAdapter` interface:

.. code-block:: python

   from vimsheet.io.base import FormatAdapter
   from vimsheet.model.workbook import Workbook

   class MyFormatAdapter(FormatAdapter):
       extensions = {".myfmt"}

       def read(self, path: str) -> Workbook:
           ...

       def write(self, path: str, workbook: Workbook) -> None:
           ...

Then register it:

.. code-block:: python

   from vimsheet.io.registry import register_adapter
   register_adapter(MyFormatAdapter)

Custom Formula Functions
------------------------

Define and register a function:

.. code-block:: python

   from vimsheet.formula.functions.registry import register

   @register("DOUBLE", min_args=1, max_args=1)
   def double(value: float) -> float:
       return value * 2

External Scripting
------------------

VimSheet supports a JSON-based protocol for external scripts. See
:ref:`scripting/protocol` for details.
