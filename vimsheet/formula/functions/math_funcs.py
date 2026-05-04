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


@register("SUM")
def fn_sum(*args: Any) -> Any:
    nums = _nums(_flat(list(args)))
    return sum(nums)


@register("AVG", "AVERAGE")
def fn_avg(*args: Any) -> Any:
    nums = _nums(_flat(list(args)))
    if not nums:
        return DIV0
    return sum(nums) / len(nums)


@register("COUNT")
def fn_count(*args: Any) -> Any:
    return len(_nums(_flat(list(args))))


@register("COUNTA")
def fn_counta(*args: Any) -> Any:
    return sum(1 for v in _flat(list(args)) if v is not None and v != "")


@register("MIN")
def fn_min(*args: Any) -> Any:
    nums = _nums(_flat(list(args)))
    return min(nums) if nums else NA


@register("MAX")
def fn_max(*args: Any) -> Any:
    nums = _nums(_flat(list(args)))
    return max(nums) if nums else NA


@register("PROD", "PRODUCT")
def fn_prod(*args: Any) -> Any:
    nums = _nums(_flat(list(args)))
    result = 1.0
    for n in nums:
        result *= n
    return result


@register("STDDEV", "STDEV")
def fn_stddev(*args: Any) -> Any:
    nums = _nums(_flat(list(args)))
    if len(nums) < 2:
        return DIV0
    return statistics.pstdev(nums)


@register("STDEVS")
def fn_stdevs(*args: Any) -> Any:
    nums = _nums(_flat(list(args)))
    if len(nums) < 2:
        return DIV0
    return statistics.stdev(nums)


@register("VAR")
def fn_var(*args: Any) -> Any:
    nums = _nums(_flat(list(args)))
    if len(nums) < 2:
        return DIV0
    return statistics.pvariance(nums)


@register("VARS")
def fn_vars(*args: Any) -> Any:
    nums = _nums(_flat(list(args)))
    if len(nums) < 2:
        return DIV0
    return statistics.variance(nums)


@register("MEDIAN")
def fn_median(*args: Any) -> Any:
    nums = sorted(_nums(_flat(list(args))))
    if not nums:
        return NA
    return statistics.median(nums)


@register("MODE")
def fn_mode(*args: Any) -> Any:
    nums = _nums(_flat(list(args)))
    if not nums:
        return NA
    try:
        return statistics.mode(nums)
    except statistics.StatisticsError:
        return NA


@register("PERCENTILE")
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


@register("SUMIF")
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


@register("COUNTIF")
def fn_countif(range_val: Any, criteria: Any) -> Any:
    return sum(1 for v in _flat([range_val]) if _criteria_match(v, criteria))


@register("AVERAGEIF")
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


@register("SUBTOTAL")
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


@register("ABS")
def fn_abs(n: Any) -> Any:
    try:
        return abs(float(n))
    except (TypeError, ValueError):
        return TYPE_ERR


@register("CEIL", "CEILING")
def fn_ceil(n: Any, sig: Any = 1) -> Any:
    try:
        s = float(sig) if sig != 1 else 1.0
        return math.ceil(float(n) / s) * s
    except (TypeError, ValueError):
        return TYPE_ERR


@register("FLOOR")
def fn_floor(n: Any, sig: Any = 1) -> Any:
    try:
        s = float(sig) if sig != 1 else 1.0
        return math.floor(float(n) / s) * s
    except (TypeError, ValueError):
        return TYPE_ERR


@register("ROUND")
def fn_round(n: Any, d: Any) -> Any:
    try:
        return round(float(n), int(d))
    except (TypeError, ValueError):
        return TYPE_ERR


@register("ROUNDUP")
def fn_roundup(n: Any, d: Any) -> Any:
    try:
        factor = 10 ** int(d)
        return math.ceil(float(n) * factor) / factor
    except (TypeError, ValueError):
        return TYPE_ERR


@register("ROUNDDOWN")
def fn_rounddown(n: Any, d: Any) -> Any:
    try:
        factor = 10 ** int(d)
        return math.floor(float(n) * factor) / factor
    except (TypeError, ValueError):
        return TYPE_ERR


@register("SQRT")
def fn_sqrt(n: Any) -> Any:
    try:
        v = float(n)
        if v < 0:
            return ERR
        return math.sqrt(v)
    except (TypeError, ValueError):
        return TYPE_ERR


@register("POW", "POWER")
def fn_pow(base: Any, exp: Any) -> Any:
    try:
        return float(base) ** float(exp)
    except (TypeError, ValueError, ZeroDivisionError):
        return TYPE_ERR


@register("EXP")
def fn_exp(n: Any) -> Any:
    try:
        return math.exp(float(n))
    except (TypeError, ValueError, OverflowError):
        return TYPE_ERR


@register("LOG")
def fn_log(n: Any, base: Any = math.e) -> Any:
    try:
        b = float(base) if base != math.e else math.e
        v = float(n)
        if v <= 0:
            return ERR
        return math.log(v, b)
    except (TypeError, ValueError):
        return TYPE_ERR


@register("LOG10")
def fn_log10(n: Any) -> Any:
    try:
        v = float(n)
        if v <= 0:
            return ERR
        return math.log10(v)
    except (TypeError, ValueError):
        return TYPE_ERR


@register("LN")
def fn_ln(n: Any) -> Any:
    try:
        v = float(n)
        if v <= 0:
            return ERR
        return math.log(v)
    except (TypeError, ValueError):
        return TYPE_ERR


@register("SIN")
def fn_sin(n: Any) -> Any:
    try:
        return math.sin(float(n))
    except (TypeError, ValueError):
        return TYPE_ERR


@register("COS")
def fn_cos(n: Any) -> Any:
    try:
        return math.cos(float(n))
    except (TypeError, ValueError):
        return TYPE_ERR


@register("TAN")
def fn_tan(n: Any) -> Any:
    try:
        return math.tan(float(n))
    except (TypeError, ValueError):
        return TYPE_ERR


@register("ASIN")
def fn_asin(n: Any) -> Any:
    try:
        return math.asin(float(n))
    except (TypeError, ValueError):
        return TYPE_ERR


@register("ACOS")
def fn_acos(n: Any) -> Any:
    try:
        return math.acos(float(n))
    except (TypeError, ValueError):
        return TYPE_ERR


@register("ATAN")
def fn_atan(n: Any) -> Any:
    try:
        return math.atan(float(n))
    except (TypeError, ValueError):
        return TYPE_ERR


@register("ATAN2")
def fn_atan2(y: Any, x: Any) -> Any:
    try:
        return math.atan2(float(y), float(x))
    except (TypeError, ValueError):
        return TYPE_ERR


@register("HYPOT")
def fn_hypot(x: Any, y: Any) -> Any:
    try:
        return math.hypot(float(x), float(y))
    except (TypeError, ValueError):
        return TYPE_ERR


@register("MOD")
def fn_mod(n: Any, d: Any) -> Any:
    try:
        dv = float(d)
        if dv == 0:
            return DIV0
        return float(n) % dv
    except (TypeError, ValueError):
        return TYPE_ERR


@register("RAND")
def fn_rand() -> Any:
    return random.random()


@register("RANDBETWEEN")
def fn_randbetween(lo: Any, hi: Any) -> Any:
    try:
        return random.randint(int(lo), int(hi))
    except (TypeError, ValueError):
        return TYPE_ERR


@register("SIGN")
def fn_sign(n: Any) -> Any:
    try:
        v = float(n)
        return 0 if v == 0 else (1 if v > 0 else -1)
    except (TypeError, ValueError):
        return TYPE_ERR


@register("INT")
def fn_int(n: Any) -> Any:
    try:
        return int(float(n))
    except (TypeError, ValueError):
        return TYPE_ERR


@register("TRUNC")
def fn_trunc(n: Any, m: Any = 0) -> Any:
    try:
        factor = 10 ** int(m)
        v = float(n)
        return math.trunc(v * factor) / factor
    except (TypeError, ValueError):
        return TYPE_ERR


@register("FACT", "FACTORIAL")
def fn_fact(n: Any) -> Any:
    try:
        return math.factorial(int(n))
    except (TypeError, ValueError, OverflowError):
        return TYPE_ERR


@register("GCD")
def fn_gcd(a: Any, b: Any) -> Any:
    try:
        return math.gcd(int(a), int(b))
    except (TypeError, ValueError):
        return TYPE_ERR


@register("LCM")
def fn_lcm(a: Any, b: Any) -> Any:
    try:
        return math.lcm(int(a), int(b))
    except (TypeError, ValueError):
        return TYPE_ERR


@register("PI")
def fn_pi() -> Any:
    return math.pi


@register("E")
def fn_e() -> Any:
    return math.e


@register("DTR", "RADIANS")
def fn_dtr(deg: Any) -> Any:
    try:
        return math.radians(float(deg))
    except (TypeError, ValueError):
        return TYPE_ERR


@register("RTD", "DEGREES")
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
