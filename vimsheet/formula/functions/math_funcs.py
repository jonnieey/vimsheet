"""Math and aggregation built-in functions."""

from __future__ import annotations

import math
import random
import statistics
from typing import Any

from vimsheet.formula.functions.registry import register

# Error sentinel
ERR = "#ERR"
DIV0 = "#DIV/0"
NA = "#N/A"
TYPE_ERR = "#TYPE"


def _nums(values: list[Any]) -> list[float]:
    """Extract numeric values from a flat list, skipping None/errors/strings."""
    result = []
    for v in values:
        if v is None:
            continue
        if isinstance(v, bool):
            result.append(1.0 if v else 0.0)
        elif isinstance(v, int | float):
            result.append(float(v))
    return result


def _flat(args: list[Any]) -> list[Any]:
    """Flatten nested lists (ranges expand to flat lists of values)."""
    out: list[Any] = []
    for a in args:
        if isinstance(a, list):
            for row in a:
                if isinstance(row, list):
                    out.extend(row)
                else:
                    out.append(row)
        else:
            out.append(a)
    return out


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


@register("SUM", desc="Sum of values. =SUM(1,2,3)→6")
def fn_sum(*args: Any) -> Any:
    nums = _nums(_flat(list(args)))
    return sum(nums)


@register("AVG", "AVERAGE", desc="Average of values")
def fn_avg(*args: Any) -> Any:
    nums = _nums(_flat(list(args)))
    if not nums:
        return DIV0
    return sum(nums) / len(nums)


@register("COUNT", desc="Count of numeric values")
def fn_count(*args: Any) -> Any:
    return len(_nums(_flat(list(args))))


@register("COUNTA", desc="Count of non-empty cells")
def fn_counta(*args: Any) -> Any:
    return sum(1 for v in _flat(list(args)) if v is not None and v != "")


@register("MIN", desc="Minimum value")
def fn_min(*args: Any) -> Any:
    nums = _nums(_flat(list(args)))
    return min(nums) if nums else NA


@register("MAX", desc="Maximum value")
def fn_max(*args: Any) -> Any:
    nums = _nums(_flat(list(args)))
    return max(nums) if nums else NA


@register("PROD", "PRODUCT", desc="Product of values")
def fn_prod(*args: Any) -> Any:
    nums = _nums(_flat(list(args)))
    result = 1.0
    for n in nums:
        result *= n
    return result


@register("STDDEV", "STDEV", desc="Sample standard deviation")
def fn_stddev(*args: Any) -> Any:
    nums = _nums(_flat(list(args)))
    if len(nums) < 2:
        return DIV0
    return statistics.pstdev(nums)


@register("STDEVS", desc="Population std deviation")
def fn_stdevs(*args: Any) -> Any:
    nums = _nums(_flat(list(args)))
    if len(nums) < 2:
        return DIV0
    return statistics.stdev(nums)


@register("VAR", desc="Sample variance")
def fn_var(*args: Any) -> Any:
    nums = _nums(_flat(list(args)))
    if len(nums) < 2:
        return DIV0
    return statistics.pvariance(nums)


@register("VARS", desc="Population variance")
def fn_vars(*args: Any) -> Any:
    nums = _nums(_flat(list(args)))
    if len(nums) < 2:
        return DIV0
    return statistics.variance(nums)


@register("MEDIAN", desc="Median value")
def fn_median(*args: Any) -> Any:
    nums = sorted(_nums(_flat(list(args))))
    if not nums:
        return NA
    return statistics.median(nums)


@register("MODE", desc="Most frequent value")
def fn_mode(*args: Any) -> Any:
    nums = _nums(_flat(list(args)))
    if not nums:
        return NA
    try:
        return statistics.mode(nums)
    except statistics.StatisticsError:
        return NA


@register("PERCENTILE", desc="Value at percentile")
def fn_percentile(range_val: Any, n: Any) -> Any:
    nums = sorted(_nums(_flat([range_val])))
    if not nums:
        return NA
    try:
        pct = float(n)
        if not 0 <= pct <= 100:
            return ERR
        idx = (pct / 100) * (len(nums) - 1)
        lo = int(idx)
        hi = min(lo + 1, len(nums) - 1)
        return nums[lo] + (nums[hi] - nums[lo]) * (idx - lo)
    except (TypeError, ValueError):
        return TYPE_ERR


@register("SUMIF", desc="Sum values matching condition")
def fn_sumif(range_val: Any, criteria: Any, sum_range: Any = None) -> Any:
    flat = _flat([range_val])
    sums = _flat([sum_range]) if sum_range is not None else flat
    total = 0.0
    for i, v in enumerate(flat):
        if _criteria_match(v, criteria):
            sv = sums[i] if i < len(sums) else None
            if isinstance(sv, int | float):
                total += float(sv)
    return total


@register("COUNTIF", desc="Count values matching condition")
def fn_countif(range_val: Any, criteria: Any) -> Any:
    return sum(1 for v in _flat([range_val]) if _criteria_match(v, criteria))


@register("AVERAGEIF", desc="Average values matching condition")
def fn_averageif(range_val: Any, criteria: Any, avg_range: Any = None) -> Any:
    flat = _flat([range_val])
    avgs = _flat([avg_range]) if avg_range is not None else flat
    nums = []
    for i, v in enumerate(flat):
        if _criteria_match(v, criteria):
            sv = avgs[i] if i < len(avgs) else None
            if isinstance(sv, int | float):
                nums.append(float(sv))
    if not nums:
        return DIV0
    return sum(nums) / len(nums)


@register("SUBTOTAL", desc="Aggregate with filter support")
def fn_subtotal(func_num: Any, range_val: Any) -> Any:
    nums = _nums(_flat([range_val]))
    try:
        fn = int(func_num)
    except (TypeError, ValueError):
        return TYPE_ERR
    match fn:
        case 1:
            return sum(nums) / len(nums) if nums else DIV0
        case 2:
            return len(nums)
        case 3:
            return len(nums)
        case 4:
            return max(nums) if nums else NA
        case 5:
            return min(nums) if nums else NA
        case 9:
            return sum(nums)
        case _:
            return ERR


# ---------------------------------------------------------------------------
# Math
# ---------------------------------------------------------------------------


@register("ABS", desc="Absolute value")
def fn_abs(n: Any) -> Any:
    try:
        return abs(float(n))
    except (TypeError, ValueError):
        return TYPE_ERR


@register("CEIL", "CEILING", desc="Round up to multiple")
def fn_ceil(n: Any, sig: Any = 1) -> Any:
    try:
        s = float(sig) if sig != 1 else 1.0
        return math.ceil(float(n) / s) * s
    except (TypeError, ValueError):
        return TYPE_ERR


@register("FLOOR", desc="Round down to multiple")
def fn_floor(n: Any, sig: Any = 1) -> Any:
    try:
        s = float(sig) if sig != 1 else 1.0
        return math.floor(float(n) / s) * s
    except (TypeError, ValueError):
        return TYPE_ERR


@register("ROUND", desc="Round to N digits")
def fn_round(n: Any, d: Any) -> Any:
    try:
        return round(float(n), int(d))
    except (TypeError, ValueError):
        return TYPE_ERR


@register("ROUNDUP", desc="Round up away from zero")
def fn_roundup(n: Any, d: Any) -> Any:
    try:
        factor = 10 ** int(d)
        return math.ceil(float(n) * factor) / factor
    except (TypeError, ValueError):
        return TYPE_ERR


@register("ROUNDDOWN", desc="Round down toward zero")
def fn_rounddown(n: Any, d: Any) -> Any:
    try:
        factor = 10 ** int(d)
        return math.floor(float(n) * factor) / factor
    except (TypeError, ValueError):
        return TYPE_ERR


@register("SQRT", desc="Square root")
def fn_sqrt(n: Any) -> Any:
    try:
        v = float(n)
        if v < 0:
            return ERR
        return math.sqrt(v)
    except (TypeError, ValueError):
        return TYPE_ERR


@register("POW", "POWER", desc="Number raised to power")
def fn_pow(base: Any, exp: Any) -> Any:
    try:
        return float(base) ** float(exp)
    except (TypeError, ValueError, ZeroDivisionError):
        return TYPE_ERR


@register("EXP", desc="e raised to the power")
def fn_exp(n: Any) -> Any:
    try:
        return math.exp(float(n))
    except (TypeError, ValueError, OverflowError):
        return TYPE_ERR


@register("LOG", desc="Logarithm (base N)")
def fn_log(n: Any, base: Any = math.e) -> Any:
    try:
        b = float(base) if base != math.e else math.e
        v = float(n)
        if v <= 0:
            return ERR
        return math.log(v, b)
    except (TypeError, ValueError):
        return TYPE_ERR


@register("LOG10", desc="Base-10 logarithm")
def fn_log10(n: Any) -> Any:
    try:
        v = float(n)
        if v <= 0:
            return ERR
        return math.log10(v)
    except (TypeError, ValueError):
        return TYPE_ERR


@register("LN", desc="Natural logarithm")
def fn_ln(n: Any) -> Any:
    try:
        v = float(n)
        if v <= 0:
            return ERR
        return math.log(v)
    except (TypeError, ValueError):
        return TYPE_ERR


@register("SIN", desc="Sine (radians)")
def fn_sin(n: Any) -> Any:
    try:
        return math.sin(float(n))
    except (TypeError, ValueError):
        return TYPE_ERR


@register("COS", desc="Cosine (radians)")
def fn_cos(n: Any) -> Any:
    try:
        return math.cos(float(n))
    except (TypeError, ValueError):
        return TYPE_ERR


@register("TAN", desc="Tangent (radians)")
def fn_tan(n: Any) -> Any:
    try:
        return math.tan(float(n))
    except (TypeError, ValueError):
        return TYPE_ERR


@register("ASIN", desc="Arc sine (radians)")
def fn_asin(n: Any) -> Any:
    try:
        return math.asin(float(n))
    except (TypeError, ValueError):
        return TYPE_ERR


@register("ACOS", desc="Arc cosine (radians)")
def fn_acos(n: Any) -> Any:
    try:
        return math.acos(float(n))
    except (TypeError, ValueError):
        return TYPE_ERR


@register("ATAN", desc="Arc tangent (radians)")
def fn_atan(n: Any) -> Any:
    try:
        return math.atan(float(n))
    except (TypeError, ValueError):
        return TYPE_ERR


@register("ATAN2", desc="Angle from x,y coordinates")
def fn_atan2(y: Any, x: Any) -> Any:
    try:
        return math.atan2(float(y), float(x))
    except (TypeError, ValueError):
        return TYPE_ERR


@register("HYPOT", desc="Hypotenuse of triangle")
def fn_hypot(x: Any, y: Any) -> Any:
    try:
        return math.hypot(float(x), float(y))
    except (TypeError, ValueError):
        return TYPE_ERR


@register("MOD", desc="Remainder after division")
def fn_mod(n: Any, d: Any) -> Any:
    try:
        dv = float(d)
        if dv == 0:
            return DIV0
        return float(n) % dv
    except (TypeError, ValueError):
        return TYPE_ERR


@register("RAND", desc="Random number 0-1")
def fn_rand() -> Any:
    return random.random()


@register("RANDBETWEEN", desc="Random int between bounds")
def fn_randbetween(lo: Any, hi: Any) -> Any:
    try:
        return random.randint(int(lo), int(hi))
    except (TypeError, ValueError):
        return TYPE_ERR


@register("SIGN", desc="Sign (-1, 0, 1)")
def fn_sign(n: Any) -> Any:
    try:
        v = float(n)
        return 0 if v == 0 else (1 if v > 0 else -1)
    except (TypeError, ValueError):
        return TYPE_ERR


@register("INT", desc="Integer part (floor)")
def fn_int(n: Any) -> Any:
    try:
        return int(float(n))
    except (TypeError, ValueError):
        return TYPE_ERR


@register("TRUNC", desc="Truncate decimal places")
def fn_trunc(n: Any, m: Any = 0) -> Any:
    try:
        factor = 10 ** int(m)
        v = float(n)
        return math.trunc(v * factor) / factor
    except (TypeError, ValueError):
        return TYPE_ERR


@register("FACT", "FACTORIAL", desc="Factorial of N")
def fn_fact(n: Any) -> Any:
    try:
        return math.factorial(int(n))
    except (TypeError, ValueError, OverflowError):
        return TYPE_ERR


@register("GCD", desc="Greatest common divisor")
def fn_gcd(a: Any, b: Any) -> Any:
    try:
        return math.gcd(int(a), int(b))
    except (TypeError, ValueError):
        return TYPE_ERR


@register("LCM", desc="Least common multiple")
def fn_lcm(a: Any, b: Any) -> Any:
    try:
        return math.lcm(int(a), int(b))
    except (TypeError, ValueError):
        return TYPE_ERR


@register("PI", desc="Value of pi")
def fn_pi() -> Any:
    return math.pi


@register("E", desc="Euler's number")
def fn_e() -> Any:
    return math.e


@register("DTR", "RADIANS", desc="Degrees to radians")
def fn_dtr(deg: Any) -> Any:
    try:
        return math.radians(float(deg))
    except (TypeError, ValueError):
        return TYPE_ERR


@register("RTD", "DEGREES", desc="Radians to degrees")
def fn_rtd(rad: Any) -> Any:
    try:
        return math.degrees(float(rad))
    except (TypeError, ValueError):
        return TYPE_ERR


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------


def _criteria_match(value: Any, criteria: Any) -> bool:
    """Return True if *value* satisfies *criteria* (Excel-style)."""
    if isinstance(criteria, str):
        import re

        for prefix, op in (
            (">=", "ge"),
            ("<=", "le"),
            ("<>", "ne"),
            (">", "gt"),
            ("<", "lt"),
            ("=", "eq"),
        ):
            if criteria.startswith(prefix):
                rhs = criteria[len(prefix) :]
                try:
                    fv, frhs = float(value), float(rhs)  # type: ignore[arg-type]
                    match op:
                        case "ge":
                            return fv >= frhs
                        case "le":
                            return fv <= frhs
                        case "ne":
                            return fv != frhs
                        case "gt":
                            return fv > frhs
                        case "lt":
                            return fv < frhs
                        case "eq":
                            return fv == frhs
                except (TypeError, ValueError):
                    sv = str(value).lower()
                    match op:
                        case "ne":
                            return sv != rhs.lower()
                        case "eq":
                            return sv == rhs.lower()
                        case _:
                            return False
        # Wildcard / plain text match
        pattern = re.escape(criteria).replace(r"\*", ".*").replace(r"\?", ".")
        return bool(re.fullmatch(pattern, str(value), re.IGNORECASE))
    return value == criteria
