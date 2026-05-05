.. _advanced/macros:

Macros
======

Record and replay keystroke sequences to automate repetitive tasks.

Recording
---------

Start recording by pressing ``q`` followed by a register name:

.. code-block:: text

   qa     Start recording to register 'a'
   q0     Start recording to register '0'

All subsequent keystrokes are recorded until you stop.

Stop recording by pressing ``q`` while not in a recording context:

.. code-block:: text

   q      Stop recording

Playback
--------

Execute a recorded macro:

.. code-block:: text

   @[a-z]     Play macro from register 'a'

Repeat the last played macro:

.. code-block:: text

   @@         Repeat last macro

Compound repeats:

.. code-block:: text

   5@a        Play macro 'a' five times

Workflow Example
----------------

Record a macro to format a column as currency:

#. Move to first cell in column.
#. Press ``qa`` to start recording to register ``a``.
#. Press ``:`` then type ``format currency <Enter>``.
#. Press ``j`` to move down.
#. Press ``q`` to stop recording.
#. Press ``10@a`` to apply to the next 10 cells.
