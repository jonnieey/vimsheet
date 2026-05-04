.. _development/testing:

Testing
=======

PySheet has a multi-tier testing strategy.

Test Structure
--------------

.. code-block:: text

   tests/
   ├── unit/           # Unit tests (fast, no external deps)
   ├── integration/    # Integration tests
   ├── e2e/            # End-to-end tests
   ├── property/       # Property-based tests (Hypothesis)
   └── benchmarks/     # Performance benchmarks

Running Tests
-------------

.. code-block:: console

   $ hatch run test        # Unit + integration tests
   $ hatch run test-e2e    # End-to-end tests
   $ hatch run test-all    # All tests
   $ hatch run cov         # Tests with coverage report

Writing Tests
-------------

Unit tests should be self-contained and fast:

.. code-block:: python

   def test_cell_creation():
       cell = Cell(value=42)
       assert cell.value == 42
       assert cell.formula is None

Property-based tests with Hypothesis:

.. code-block:: python

   from hypothesis import given, strategies as st

   @given(st.integers(), st.integers())
   def test_sum_commutative(a, b):
       assert a + b == b + a

Doctests
--------

Documentation examples that double as tests:

.. code-block:: python

   def add(a: int, b: int) -> int:
       """Return the sum of a and b.

       >>> add(2, 3)
       5
       >>> add(-1, 1)
       0
       """
       return a + b

Coverage
--------

.. code-block:: console

   $ coverage run -m pytest tests/unit tests/integration
   $ coverage report
   $ coverage html    # View in browser
