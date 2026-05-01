"""Date/Time built-in functions."""

from __future__ import annotations

import datetime
from typing import Any

from pysheet.formula.functions.registry import register

ERR = "#ERR"
TYPE_ERR = "#TYPE"


def _to_date(v: Any) -> datetime.date | None:
    if isinstance(v, datetime.datetime):
        return v.date()
    if isinstance(v, datetime.date):
        return v
    if isinstance(v, str):
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
            try:
                return datetime.datetime.strptime(v, fmt).date()
            except ValueError:
                continue
    return None


@register("TODAY")
def fn_today() -> Any:
    return datetime.date.today()


@register("NOW")
def fn_now() -> Any:
    return datetime.datetime.now()


@register("DATE")
def fn_date(y: Any, m: Any, d: Any) -> Any:
    try:
        return datetime.date(int(y), int(m), int(d))
    except (TypeError, ValueError):
        return ERR


@register("TIME")
def fn_time(h: Any, m: Any, s: Any) -> Any:
    try:
        return datetime.time(int(h), int(m), int(s))
    except (TypeError, ValueError):
        return ERR


@register("YEAR")
def fn_year(date: Any) -> Any:
    d = _to_date(date)
    return d.year if d else TYPE_ERR


@register("MONTH")
def fn_month(date: Any) -> Any:
    d = _to_date(date)
    return d.month if d else TYPE_ERR


@register("DAY")
def fn_day(date: Any) -> Any:
    d = _to_date(date)
    return d.day if d else TYPE_ERR


@register("HOUR")
def fn_hour(dt: Any) -> Any:
    if isinstance(dt, (datetime.datetime, datetime.time)):
        return dt.hour
    return TYPE_ERR


@register("MINUTE")
def fn_minute(dt: Any) -> Any:
    if isinstance(dt, (datetime.datetime, datetime.time)):
        return dt.minute
    return TYPE_ERR


@register("SECOND")
def fn_second(dt: Any) -> Any:
    if isinstance(dt, (datetime.datetime, datetime.time)):
        return dt.second
    return TYPE_ERR


@register("DATEDIF")
def fn_datedif(d1: Any, d2: Any, unit: Any) -> Any:
    date1, date2 = _to_date(d1), _to_date(d2)
    if not date1 or not date2:
        return TYPE_ERR
    match str(unit).upper():
        case "D":
            return (date2 - date1).days
        case "M":
            return (date2.year - date1.year) * 12 + (date2.month - date1.month)
        case "Y":
            return date2.year - date1.year
        case _:
            return ERR


@register("EDATE")
def fn_edate(date: Any, months: Any) -> Any:
    d = _to_date(date)
    if not d:
        return TYPE_ERR
    try:
        m = d.month + int(months)
        y = d.year + (m - 1) // 12
        m = (m - 1) % 12 + 1
        import calendar
        day = min(d.day, calendar.monthrange(y, m)[1])
        return datetime.date(y, m, day)
    except (TypeError, ValueError):
        return ERR


@register("EOMONTH")
def fn_eomonth(date: Any, months: Any) -> Any:
    result = fn_edate(date, months)
    if isinstance(result, str):
        return result
    import calendar
    return datetime.date(result.year, result.month,
                         calendar.monthrange(result.year, result.month)[1])


@register("WEEKDAY")
def fn_weekday(date: Any) -> Any:
    d = _to_date(date)
    if not d:
        return TYPE_ERR
    return d.isoweekday()  # 1=Monday … 7=Sunday


@register("WEEKNUM")
def fn_weeknum(date: Any) -> Any:
    d = _to_date(date)
    if not d:
        return TYPE_ERR
    return d.isocalendar()[1]


@register("NETWORKDAYS")
def fn_networkdays(d1: Any, d2: Any) -> Any:
    date1, date2 = _to_date(d1), _to_date(d2)
    if not date1 or not date2:
        return TYPE_ERR
    count = 0
    cur = date1
    while cur <= date2:
        if cur.weekday() < 5:
            count += 1
        cur += datetime.timedelta(days=1)
    return count
