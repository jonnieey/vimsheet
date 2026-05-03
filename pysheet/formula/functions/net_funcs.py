"""Network formula functions — @FETCH."""

from __future__ import annotations

from typing import Any

from pysheet.formula.functions.registry import register

# Injected by the evaluator before calling FETCH so the function knows
# which cell it is being evaluated for.  Formula evaluation is single-
# threaded (Textual event loop), so a plain module-level variable is safe.
_fetch_context: tuple[Any, int, int] | None = None  # (FetchManager, row, col)


@register("FETCH")
def fn_fetch(url: Any, refresh_seconds: Any = None, json_path: Any = "") -> Any:
    """=@FETCH(url, [refresh_seconds], [json_path])

    Fetches *url* in a background thread and returns the result.
    Returns #LOADING while the first request is in flight.
    Subsequent formula re-evals return the last cached value immediately.

    url            — HTTP/HTTPS URL string
    refresh_seconds — optional float; re-fetches every N seconds (0 or omitted = one-shot)
    json_path       — optional dot-notation path to extract from a JSON response
                      e.g. "data.price" or "items[0].name"
    """
    if _fetch_context is None or _fetch_context[0] is None:
        return "#LOADING"

    fetch_manager, row, col = _fetch_context

    url_str = str(url).strip() if url is not None else ""
    if not url_str:
        return "#FETCH"

    try:
        interval: float | None = float(refresh_seconds) if refresh_seconds is not None else None
        if interval is not None and interval <= 0:
            interval = None
    except (TypeError, ValueError):
        interval = None

    path_str = str(json_path).strip() if json_path else ""
    sheet_name: str = fetch_manager._app.workbook.active_sheet.name
    key = (sheet_name, row, col)

    fetch_manager.schedule(key, url_str, interval, path_str)
    return fetch_manager.get_cached(key)
