.. _scripting/user-functions:

User-Defined Functions
======================

Register custom formula functions from Python scripts.

Defining a Function
-------------------

Create a Python file and register functions:

.. code-block:: python

   # my_functions.py
   from vimsheet.formula.functions.registry import register

   @register("DISCOUNT", min_args=2, max_args=2)
   def discount(price: float, rate: float) -> float:
       """Apply a discount rate to a price."""
       return price * (1 - rate)

   @register("GREET", min_args=1, max_args=1)
   def greet(name: str) -> str:
       """Return a greeting string."""
       return f"Hello, {name}!"

Loading Functions
-----------------

Set the path to your custom functions file in the config:

.. code-block:: console

   :set functions_file=~/.config/vimsheet/my_functions.py

Or via the config JSON file at ``~/.config/vimsheet/config.json``:

.. code-block:: json

   {
     "functions_file": "/home/user/.vimsheet/functions.py"
   }

Alternatively, use ``:func`` at runtime to register a script:

.. code-block:: console

   :func /path/to/script.py

Now use them in formulas:

.. code-block:: text

   =DISCOUNT(A1, B1)
   =GREET("World")
