.. _advanced/performance:

Performance
===========

Tips for working with large spreadsheets efficiently.

Large Datasets
--------------

VimSheet is optimized for responsive editing. For best performance:

* Use CSV format for large datasets (faster than XLSX).
* Avoid excessive conditional formatting rules.
* Limit the number of volatile functions (``RAND``, ``NOW``, ``TODAY``).

Configuration
-------------

Adjust these settings to improve performance:

Configuration values (set via ``:set`` or ``~/.config/vimsheet/config.json``):

.. code-block:: json

   {
     "max_undo": 100,
     "autocalc": true,
     "scroll_speed": 3
   }

Cache Settings
--------------

The formula engine caches computed values and only recalculates
dependent cells when a source cell changes. This makes editing large
dependency chains efficient.

Memory Usage
------------

* Cell data is stored efficiently with a sparse structure.
* Only cells with content consume memory.
* Large text values are stored as strings.
* The undo stack stores deltas, not full snapshots.
