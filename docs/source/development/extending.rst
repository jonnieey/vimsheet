.. _development/extending:

Extending PySheet
=================

Guide for creating extensions and plugins.

Adding File Format Support
--------------------------

Implement the :py:class:`pysheet.io.base.SheetAdapter` interface:

.. code-block:: python

   from pysheet.io.base import SheetAdapter
   from pysheet.model.workbook import Workbook

   class MyFormatAdapter(SheetAdapter):
       extensions = {".myfmt"}

       def read(self, path: str) -> Workbook:
           ...

       def write(self, path: str, workbook: Workbook) -> None:
           ...

Then register it:

.. code-block:: python

   from pysheet.io.registry import register_adapter
   register_adapter(MyFormatAdapter)

Custom Formula Functions
------------------------

Define and register a function:

.. code-block:: python

   from pysheet.formula.functions.registry import registry

   @registry.register("DOUBLE", min_args=1, max_args=1)
   def double(value: float) -> float:
       return value * 2

External Scripting
------------------

PySheet supports a JSON-based protocol for external scripts. See
:ref:`scripting/protocol` for details.
