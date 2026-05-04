.. _reference/functions:

Formula Functions
=================

PySheet includes over 80 built-in functions organized by category.

Mathematical Functions
----------------------

.. py:function:: ABS(x)
   :noindex:

   Return the absolute value of *x*.

.. py:function:: SUM(range, ...)
   :noindex:

   Sum all values in the given ranges or numbers.

.. py:function:: AVERAGE(range, ...)
   :noindex:

   Return the arithmetic mean of values.

.. py:function:: MIN(range, ...)
   :noindex:

   Return the minimum value.

.. py:function:: MAX(range, ...)
   :noindex:

   Return the maximum value.

.. py:function:: COUNT(range, ...)
   :noindex:

   Count numeric values.

.. py:function:: COUNTA(range, ...)
   :noindex:

   Count non-empty values.

.. py:function:: ROUND(x, digits)
   :noindex:

   Round *x* to *digits* decimal places.

.. py:function:: CEILING(x, significance)
   :noindex:

   Round *x* up to nearest multiple of *significance*.

.. py:function:: FLOOR(x, significance)
   :noindex:

   Round *x* down to nearest multiple of *significance*.

.. py:function:: MOD(x, y)
   :noindex:

   Return remainder of ``x / y``.

.. py:function:: POWER(x, y)
   :noindex:

   Return ``x`` raised to the power of ``y`` (same as ``x ^ y``).

.. py:function:: SQRT(x)
   :noindex:

   Return the square root of *x*.

.. py:function:: PI()
   :noindex:

   Return the value of π.

.. py:function:: RAND()
   :noindex:

   Return a random float between 0 and 1.

.. py:function:: RANDBETWEEN(bottom, top)
   :noindex:

   Return a random integer between *bottom* and *top*.

Logical Functions
-----------------

.. py:function:: IF(condition, true_val, false_val)
   :noindex:

   Return *true_val* if *condition* is truthy, else *false_val*.

.. py:function:: AND(condition, ...)
   :noindex:

   Return ``TRUE`` if all conditions are true.

.. py:function:: OR(condition, ...)
   :noindex:

   Return ``TRUE`` if any condition is true.

.. py:function:: NOT(condition)
   :noindex:

   Return the logical opposite.

.. py:function:: IFERROR(value, default)
   :noindex:

   Return *default* if *value* is an error, otherwise *value*.

.. py:function:: ISBLANK(value)
   :noindex:

   Return ``TRUE`` if *value* is empty.

Text Functions
--------------

.. py:function:: LEN(text)
   :noindex:

   Return the length of *text*.

.. py:function:: LEFT(text, n)
   :noindex:

   Return the first *n* characters.

.. py:function:: RIGHT(text, n)
   :noindex:

   Return the last *n* characters.

.. py:function:: MID(text, start, n)
   :noindex:

   Return *n* characters starting at position *start*.

.. py:function:: CONCATENATE(text1, text2, ...)
   :noindex:

   Join text strings together (same as ``&`` operator).

.. py:function:: UPPER(text)
   :noindex:

   Convert to uppercase.

.. py:function:: LOWER(text)
   :noindex:

   Convert to lowercase.

.. py:function:: TRIM(text)
   :noindex:

   Remove leading and trailing whitespace.

.. py:function:: FIND(find_text, within_text)
   :noindex:

   Return the position of *find_text* in *within_text*.

.. py:function:: REPLACE(old_text, start, n, new_text)
   :noindex:

   Replace *n* characters starting at *start* with *new_text*.

Lookup and Reference
--------------------

.. py:function:: VLOOKUP(lookup_value, table_array, col_index, [range_lookup])
   :noindex:

   Vertical lookup. Search the first column of *table_array* for
   *lookup_value* and return the value at *col_index*.

.. py:function:: HLOOKUP(lookup_value, table_array, row_index, [range_lookup])
   :noindex:

   Horizontal lookup. Search the first row of *table_array*.

.. py:function:: INDEX(range, row, [column])
   :noindex:

   Return the value at the specified position within a range.

.. py:function:: MATCH(lookup_value, lookup_array, [match_type])
   :noindex:

   Return the relative position of *lookup_value* in *lookup_array*.

Date Functions
--------------

.. py:function:: TODAY()
   :noindex:

   Return today's date.

.. py:function:: NOW()
   :noindex:

   Return current date and time.

.. py:function:: DATE(year, month, day)
   :noindex:

   Create a date from year, month, day components.

.. py:function:: YEAR(date)
   :noindex:

   Extract the year from a date.

.. py:function:: MONTH(date)
   :noindex:

   Extract the month (1–12) from a date.

.. py:function:: DAY(date)
   :noindex:

   Extract the day of the month from a date.
