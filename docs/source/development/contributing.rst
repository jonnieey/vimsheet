.. _development/contributing:

Contributing
============

We welcome contributions! Please follow these guidelines.

Development Setup
-----------------

.. code-block:: console

   $ git clone https://github.com/pysheet/pysheet.git
   $ cd pysheet
   $ pip install -e ".[dev]"
   $ pre-commit install

Code Style
----------

We use Ruff for linting and formatting:

.. code-block:: console

   $ ruff check pysheet tests
   $ ruff format pysheet tests

Type checking with MyPy:

.. code-block:: console

   $ mypy pysheet

Running Tests
-------------

.. code-block:: console

   $ pytest tests/unit tests/integration   # Unit + integration tests
   $ pytest tests/e2e                       # End-to-end tests
   $ pytest                                 # All tests

Pull Request Process
--------------------

#. Fork the repository.
#. Create a feature branch.
#. Make your changes with tests.
#. Run the full test suite.
#. Ensure lint and type checks pass.
#. Submit a pull request with a clear description.

Building Documentation
----------------------

.. code-block:: console

   $ cd docs
   $ make html
   $ make linkcheck
   $ make doctest

Pre-commit Hooks
----------------

We use pre-commit hooks to enforce code quality. Install them with:

.. code-block:: console

   $ pre-commit install

The hooks will run Ruff, MyPy, and other checks before each commit.
