.. _reference/functions:

Formula Functions
=================

VimSheet includes over 100 built-in functions organized by category.
Functions can be used in formulas: ``=SUM(A1:A10)``, ``=IF(B1>0, "OK", "NOK")``.

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

.. py:function:: AVG(range, ...)
   :noindex:

   Alias for ``AVERAGE``.

.. py:function:: COUNT(range, ...)
   :noindex:

   Count numeric values in the range.

.. py:function:: COUNTA(range, ...)
   :noindex:

   Count non-empty values in the range.

.. py:function:: MIN(range, ...)
   :noindex:

   Return the minimum value.

.. py:function:: MAX(range, ...)
   :noindex:

   Return the maximum value.

.. py:function:: MEDIAN(range, ...)
   :noindex:

   Return the median of values.

.. py:function:: MODE(range, ...)
   :noindex:

   Return the most frequently occurring value.

.. py:function:: STDEV(range, ...)
   :noindex:

   Return the sample standard deviation.

.. py:function:: STDEVS(range, ...)
   :noindex:

   Return the population standard deviation.

.. py:function:: VAR(range, ...)
   :noindex:

   Return the sample variance.

.. py:function:: VARS(range, ...)
   :noindex:

   Return the population variance.

.. py:function:: PERCENTILE(range, p)
   :noindex:

   Return the *p*-th percentile of values (0-100).

.. py:function:: SUMIF(range, condition, [sum_range])
   :noindex:

   Sum values conditionally.

.. py:function:: COUNTIF(range, condition)
   :noindex:

   Count values meeting a condition.

.. py:function:: AVERAGEIF(range, condition, [avg_range])
   :noindex:

   Average values meeting a condition.

.. py:function:: SUBTOTAL(func_num, range, ...)
   :noindex:

   Apply a subtotal function (1=AVERAGE, 9=SUM, etc.).

.. py:function:: PRODUCT(range, ...)
   :noindex:

   Multiply all values together.

.. py:function:: PROD(range, ...)
   :noindex:

   Alias for ``PRODUCT``.

.. py:function:: ROUND(x, digits)
   :noindex:

   Round *x* to *digits* decimal places.

.. py:function:: ROUNDUP(x, digits)
   :noindex:

   Round *x* up (away from zero).

.. py:function:: ROUNDDOWN(x, digits)
   :noindex:

   Round *x* down (toward zero).

.. py:function:: CEILING(x, significance)
   :noindex:

   Round *x* up to the nearest multiple of *significance*.

.. py:function:: FLOOR(x, significance)
   :noindex:

   Round *x* down to the nearest multiple of *significance*.

.. py:function:: CEIL(x, significance)
   :noindex:

   Alias for ``CEILING``.

.. py:function:: INT(x)
   :noindex:

   Truncate *x* to an integer.

.. py:function:: TRUNC(x, [digits])
   :noindex:

   Truncate *x* to *digits* decimal places.

.. py:function:: MOD(x, y)
   :noindex:

   Return the remainder of ``x / y``.

.. py:function:: POWER(x, y)
   :noindex:

   Return *x* raised to the power of *y* (same as ``x ^ y``).

.. py:function:: POW(x, y)
   :noindex:

   Alias for ``POWER``.

.. py:function:: SQRT(x)
   :noindex:

   Return the square root of *x*.

.. py:function:: EXP(x)
   :noindex:

   Return *e* raised to the power of *x*.

.. py:function:: LN(x)
   :noindex:

   Return the natural logarithm of *x*.

.. py:function:: LOG(x, [base])
   :noindex:

   Return the logarithm of *x* with given *base* (default 10).

.. py:function:: LOG10(x)
   :noindex:

   Return the base-10 logarithm of *x*.

.. py:function:: SIN(x)
   :noindex:

   Return the sine of *x* (radians).

.. py:function:: COS(x)
   :noindex:

   Return the cosine of *x* (radians).

.. py:function:: TAN(x)
   :noindex:

   Return the tangent of *x* (radians).

.. py:function:: ASIN(x)
   :noindex:

   Return the arcsine of *x* in radians.

.. py:function:: ACOS(x)
   :noindex:

   Return the arccosine of *x* in radians.

.. py:function:: ATAN(x)
   :noindex:

   Return the arctangent of *x* in radians.

.. py:function:: ATAN2(y, x)
   :noindex:

   Return ``atan2(y, x)`` in radians.

.. py:function:: HYPOT(x, y)
   :noindex:

   Return ``sqrt(x² + y²)``.

.. py:function:: SIGN(x)
   :noindex:

   Return the sign of *x* (-1, 0, or 1).

.. py:function:: FACT(n)
   :noindex:

   Return the factorial of *n*.

.. py:function:: FACTORIAL(n)
   :noindex:

   Alias for ``FACT``.

.. py:function:: GCD(a, b, ...)
   :noindex:

   Return the greatest common divisor.

.. py:function:: LCM(a, b, ...)
   :noindex:

   Return the least common multiple.

.. py:function:: PI()
   :noindex:

   Return the value of π (3.14159...).

.. py:function:: E()
   :noindex:

   Return the value of *e* (2.71828...).

.. py:function:: RAND()
   :noindex:

   Return a random float between 0 and 1.

.. py:function:: RANDBETWEEN(bottom, top)
   :noindex:

   Return a random integer between *bottom* and *top* (inclusive).

.. py:function:: RADIANS(x)
   :noindex:

   Convert degrees to radians.

.. py:function:: DTR(x)
   :noindex:

   Alias for ``RADIANS``.

.. py:function:: DEGREES(x)
   :noindex:

   Convert radians to degrees.

.. py:function:: RTD(x)
   :noindex:

   Alias for ``DEGREES``.

Logical Functions
-----------------

.. py:function:: IF(condition, true_val, false_val)
   :noindex:

   Return *true_val* if *condition* is truthy, else *false_val*.

.. py:function:: IFS(condition1, value1, [condition2, value2, ...])
   :noindex:

   Evaluate multiple conditions, return value for the first true condition.

.. py:function:: AND(condition, ...)
   :noindex:

   Return ``TRUE`` if all conditions are true.

.. py:function:: OR(condition, ...)
   :noindex:

   Return ``TRUE`` if any condition is true.

.. py:function:: XOR(condition, ...)
   :noindex:

   Return ``TRUE`` if an odd number of conditions are true.

.. py:function:: NOT(condition)
   :noindex:

   Return the logical opposite.

.. py:function:: IFERROR(value, default)
   :noindex:

   Return *default* if *value* evaluates to an error, otherwise *value*.

.. py:function:: IFNA(value, default)
   :noindex:

   Return *default* if *value* is ``#N/A``, otherwise *value*.

.. py:function:: SWITCH(expr, val1, result1, [default])
   :noindex:

   Match *expr* against values and return corresponding result.

.. py:function:: TRUE()
   :noindex:

   Return the boolean ``TRUE``.

.. py:function:: FALSE()
   :noindex:

   Return the boolean ``FALSE``.

.. py:function:: ISBLANK(value)
   :noindex:

   Return ``TRUE`` if *value* is empty or blank.

.. py:function:: ISNUMBER(value)
   :noindex:

   Return ``TRUE`` if *value* is numeric.

.. py:function:: ISTEXT(value)
   :noindex:

   Return ``TRUE`` if *value* is text.

.. py:function:: ISERROR(value)
   :noindex:

   Return ``TRUE`` if *value* is any error value.

Text Functions
--------------

.. py:function:: LEN(text)
   :noindex:

   Return the length (number of characters) of *text*.

.. py:function:: LEFT(text, n)
   :noindex:

   Return the first *n* characters.

.. py:function:: RIGHT(text, n)
   :noindex:

   Return the last *n* characters.

.. py:function:: MID(text, start, n)
   :noindex:

   Return *n* characters starting at position *start* (1-indexed).

.. py:function:: CONCATENATE(text1, text2, ...)
   :noindex:

   Join text strings together (same as ``&`` operator).

.. py:function:: CONCAT(text1, text2, ...)
   :noindex:

   Alias for ``CONCATENATE``.

.. py:function:: UPPER(text)
   :noindex:

   Convert *text* to uppercase.

.. py:function:: LOWER(text)
   :noindex:

   Convert *text* to lowercase.

.. py:function:: PROPER(text)
   :noindex:

   Capitalize the first letter of each word.

.. py:function:: TRIM(text)
   :noindex:

   Remove leading and trailing whitespace.

.. py:function:: FIND(find_text, within_text, [start])
   :noindex:

   Return the position of *find_text* in *within_text* (1-indexed).

.. py:function:: REPLACE(old_text, start, n, new_text)
   :noindex:

   Replace *n* characters starting at *start* with *new_text*.

.. py:function:: SUBSTITUTE(text, old, new, [n])
   :noindex:

   Substitute *old* text with *new* text (optionally only the *n*-th occurrence).

.. py:function:: TEXT(value, format)
   :noindex:

   Format a number as text using a format string.

.. py:function:: VALUE(text)
   :noindex:

   Convert a text string to a number.

.. py:function:: REPT(text, n)
   :noindex:

   Repeat *text* *n* times.

.. py:function:: REPEAT(text, n)
   :noindex:

   Alias for ``REPT``.

.. py:function:: EXACT(text1, text2)
   :noindex:

   Return ``TRUE`` if two strings are exactly equal (case-sensitive).

.. py:function:: CHAR(code)
   :noindex:

   Return the character for the given ASCII/Unicode code.

.. py:function:: CODE(text)
   :noindex:

   Return the ASCII/Unicode code of the first character of *text*.

Lookup and Reference
--------------------

.. py:function:: VLOOKUP(lookup_value, table_array, col_index, [range_lookup])
   :noindex:

   Vertical lookup. Search the first column of *table_array* for
   *lookup_value* and return the value at *col_index*. Set *range_lookup*
   to ``FALSE`` for exact match.

.. py:function:: HLOOKUP(lookup_value, table_array, row_index, [range_lookup])
   :noindex:

   Horizontal lookup. Search the first row of *table_array* for
   *lookup_value* and return the value at *row_index*.

.. py:function:: XLOOKUP(lookup_value, lookup_array, return_array, [if_not_found])
   :noindex:

   Modern lookup that searches *lookup_array* and returns the
   corresponding value from *return_array*.

.. py:function:: INDEX(range, row, [column])
   :noindex:

   Return the value at the specified position within a range.

.. py:function:: MATCH(lookup_value, lookup_array, [match_type])
   :noindex:

   Return the relative position of *lookup_value* in *lookup_array*.
   ``match_type``: 0=exact, 1=ascending, -1=descending.

.. py:function:: CHOOSE(index, value1, value2, ...)
   :noindex:

   Return the *index*-th value from the argument list (1-indexed).

.. py:function:: ROW([cell])
   :noindex:

   Return the row number of *cell* (or current cell). 1-indexed.

.. py:function:: COL([cell])
   :noindex:

   Return the column number of *cell* (or current cell). 1-indexed.

.. py:function:: ROWS(range)
   :noindex:

   Return the number of rows in *range*.

.. py:function:: COLS(range)
   :noindex:

   Return the number of columns in *range*.

.. py:function:: OFFSET(cell, rows, cols, [height], [width])
   :noindex:

   Return a reference offset from *cell* by *rows* and *cols*.

.. py:function:: INDIRECT(ref_text)
   :noindex:

   Return the reference specified by a text string.

Date Functions
--------------

.. py:function:: TODAY()
   :noindex:

   Return today's date.

.. py:function:: NOW()
   :noindex:

   Return the current date and time.

.. py:function:: DATE(year, month, day)
   :noindex:

   Create a date from year, month, and day components.

.. py:function:: TIME(hour, minute, second)
   :noindex:

   Create a time from hour, minute, and second components.

.. py:function:: YEAR(date)
   :noindex:

   Extract the year from a date.

.. py:function:: MONTH(date)
   :noindex:

   Extract the month (1-12) from a date.

.. py:function:: DAY(date)
   :noindex:

   Extract the day of the month from a date.

.. py:function:: HOUR(time)
   :noindex:

   Extract the hour (0-23) from a time.

.. py:function:: MINUTE(time)
   :noindex:

   Extract the minute (0-59) from a time.

.. py:function:: SECOND(time)
   :noindex:

   Extract the second (0-59) from a time.

.. py:function:: DATEDIF(start_date, end_date, unit)
   :noindex:

   Return the difference between dates. *unit*: ``"Y"`` (years),
   ``"M"`` (months), ``"D"`` (days), ``"MD"``, ``"YM"``, ``"YD"``.

.. py:function:: EDATE(start_date, months)
   :noindex:

   Return the date *months* away from *start_date*.

.. py:function:: EOMONTH(start_date, months)
   :noindex:

   Return the last day of the month *months* away from *start_date*.

.. py:function:: WEEKDAY(date, [return_type])
   :noindex:

   Return the day of the week (1=Sunday by default).

.. py:function:: WEEKNUM(date)
   :noindex:

   Return the week number of the year.

.. py:function:: NETWORKDAYS(start_date, end_date)
   :noindex:

   Return the number of working days between two dates.

Data Fetching
-------------

.. py:function:: FETCH(url, [refresh_seconds], [json_path])
   :noindex:

   Fetch data from a URL asynchronously. Data is refreshed in the
   background. Use *json_path* (dot/bracket notation) to extract a
   specific value, e.g., ``FETCH("https://api.example.com/data", 60, "$.results[0].value")``.
