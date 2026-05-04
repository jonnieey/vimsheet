.. _scripting/user-functions:

User-Defined Functions
======================

Register custom formula functions from Python scripts.

Defining a Function
-------------------

Create a Python file and register functions:

.. code-block:: python

   # my_functions.py
   from pysheet.formula.functions.registry import registry

   @registry.register("DISCOUNT", min_args=2, max_args=2)
   def discount(price: float, rate: float) -> float:
       """Apply a discount rate to a price."""
       return price * (1 - rate)

   @registry.register("GREET", min_args=1, max_args=1)
   def greet(name: str) -> str:
       """Return a greeting string."""
       return f"Hello, {name}!"

Loading Functions
-----------------

Load your functions at startup via the config file:

.. code-block:: toml

   [scripting]
   init_scripts = ["~/.pysheet/my_functions.py"]

Now use them in formulas:

.. code-block:: text

   =DISCOUNT(A1, B1)
   =GREET("World")
