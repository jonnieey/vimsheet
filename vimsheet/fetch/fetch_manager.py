"""FetchManager — coordinates background HTTP fetches per cell."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from vimsheet.fetch.fetch_worker import (
    ARRAY_SPILL_CAP,
    do_fetch,
    extract_json_path,
    parse_response,
)

if TYPE_CHECKING:
    from vimsheet.app import VimSheetApp

FetchKey = tuple[str, int, int]  # (sheet_name, row, col)

SPILL_TAG = "__spill__"


@dataclass
class FetchEntry:
    url: str
    interval: float | None  # None = one-shot
    json_path: str  # "" = whole response
    last_value: Any = "#LOADING"
    status: str = "pending"  # pending | loading | ok | error
    timer: threading.Timer | None = None
    spill_cells: list[tuple[int, int]] = field(default_factory=list)


class FetchManager:
    def __init__(self, app: VimSheetApp) -> None:
        self._app = app
        self._entries: dict[FetchKey, FetchEntry] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ #
    # Public API                                                            #
    # ------------------------------------------------------------------ #

    def get_cached(self, key: FetchKey) -> Any:
        """Return last cached value instantly (never blocks)."""
        with self._lock:
            entry = self._entries.get(key)
            return entry.last_value if entry else "#LOADING"

    def schedule(
        self,
        key: FetchKey,
        url: str,
        interval: float | None,
        json_path: str,
    ) -> None:
        """Register (or re-register) a fetch for *key*.  Idempotent on matching params."""
        with self._lock:
            entry = self._entries.get(key)
            if (
                entry
                and entry.url == url
                and entry.interval == interval
                and entry.json_path == json_path
            ):
                return  # already scheduled with same params — no-op
            # Cancel old timer if params changed
            if entry and entry.timer:
                entry.timer.cancel()
            self._entries[key] = FetchEntry(url=url, interval=interval, json_path=json_path)

        self._launch_thread(key)

    def fetch_now(self, key: FetchKey) -> None:
        """Force an immediate re-fetch regardless of timer."""
        with self._lock:
            entry = self._entries.get(key)
            if entry and entry.timer:
                entry.timer.cancel()
                entry.timer = None
        self._launch_thread(key)

    def cancel(self, key: FetchKey) -> None:
        """Cancel the fetch for *key* and clear its spill cells."""
        with self._lock:
            entry = self._entries.pop(key, None)
        if entry:
            if entry.timer:
                entry.timer.cancel()
            self._clear_spill_cells(entry.spill_cells)

    def cancel_all(self) -> None:
        """Cancel every active fetch — call on app exit."""
        with self._lock:
            entries = list(self._entries.values())
            self._entries.clear()
        for entry in entries:
            if entry.timer:
                entry.timer.cancel()

    def all_entries(self) -> list[tuple[FetchKey, FetchEntry]]:
        """Snapshot for :fetchlist display."""
        with self._lock:
            return list(self._entries.items())

    # ------------------------------------------------------------------ #
    # Private                                                               #
    # ------------------------------------------------------------------ #

    def _launch_thread(self, key: FetchKey) -> None:
        t = threading.Thread(target=self._do_fetch_work, args=(key,), daemon=True)
        with self._lock:
            entry = self._entries.get(key)
            if entry:
                entry.status = "loading"
        t.start()

    def _do_fetch_work(self, key: FetchKey) -> None:
        """Runs in a daemon thread."""
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return
            url = entry.url
            json_path = entry.json_path
            interval = entry.interval

        result = do_fetch(url)

        if not result.ok:
            anchor_val = result.error or "#FETCH"
            spill: list[tuple[int, int, Any]] = []
        else:
            data = parse_response(result)
            if isinstance(data, str) and data.startswith("#"):
                anchor_val = data
                spill = []
            else:
                try:
                    if json_path:
                        data = extract_json_path(data, json_path)
                except (KeyError, IndexError, TypeError):
                    data = "#REF"
                anchor_val, spill = self._build_spill(key, data)

        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return
            entry.last_value = anchor_val
            entry.status = (
                "ok"
                if not (isinstance(anchor_val, str) and anchor_val.startswith("#"))
                else "error"
            )

        self._app.call_from_thread(self._on_result, key, anchor_val, spill)

        # Schedule next refresh
        if interval and interval > 0:
            with self._lock:
                entry = self._entries.get(key)
                if entry is not None:
                    t = threading.Timer(interval, self._launch_thread, args=(key,))
                    t.daemon = True
                    entry.timer = t
                    t.start()

    def _on_result(
        self,
        key: FetchKey,
        anchor_val: Any,
        spill: list[tuple[int, int, Any]],
    ) -> None:
        """Runs on the Textual main thread via call_from_thread."""
        sheet_name, row, col = key
        sheet = next((s for s in self._app.workbook.sheets if s.name == sheet_name), None)
        if sheet is None:
            return

        cell = sheet.get_cell(row, col)
        if cell is None or not (cell.formula and "FETCH" in cell.formula.upper()):
            return  # cell was cleared or overwritten

        # Clear old spill cells
        with self._lock:
            entry = self._entries.get(key)
            old_spill = list(entry.spill_cells) if entry else []
        self._clear_spill_cells(old_spill, sheet)

        # Write anchor value directly (preserve formula)
        cell.value = anchor_val
        cell.display = cell.format_value()

        # Write spill cells
        new_spill_positions: list[tuple[int, int]] = []
        for sr, sc, sv in spill:
            sheet.set_cell_value(sr, sc, sv, record_history=False)
            spill_cell = sheet.get_cell(sr, sc)
            if spill_cell:
                spill_cell.comment = SPILL_TAG
            new_spill_positions.append((sr, sc))

        with self._lock:
            entry = self._entries.get(key)
            if entry:
                entry.spill_cells = new_spill_positions

        # Update dependents of the anchor cell
        sheet._recalculate_dependents(row, col)

        self._app.grid.refresh_grid()
        self._app._sync_formula_bar()

    def _build_spill(self, key: FetchKey, data: Any) -> tuple[Any, list[tuple[int, int, Any]]]:
        """Convert parsed response to (anchor_value, spill_list)."""
        sheet_name, row, col = key
        sheet = next((s for s in self._app.workbook.sheets if s.name == sheet_name), None)

        if isinstance(data, list):
            items = data[:ARRAY_SPILL_CAP]
            for i in range(len(items)):
                candidate = (row + 1 + i, col)
                existing = sheet.get_cell(*candidate) if sheet else None
                if existing and not self._is_empty_or_spill(existing):
                    return ("#SPILL", [])
            spill = [(row + 1 + i, col, v) for i, v in enumerate(items)]
            if len(data) > ARRAY_SPILL_CAP:
                anchor = f"[{ARRAY_SPILL_CAP}/{len(data)} items]"
            else:
                anchor = f"[{len(data)} items]"
            return (anchor, spill)

        if isinstance(data, dict):
            keys = list(data.keys())
            for i in range(len(keys)):
                candidate = (row, col + 1 + i)
                existing = sheet.get_cell(*candidate) if sheet else None
                if existing and not self._is_empty_or_spill(existing):
                    return ("#SPILL", [])
            spill = [(row, col + 1 + i, f"{k}: {v}") for i, (k, v) in enumerate(data.items())]
            anchor = f"[{len(data)} fields]"
            return (anchor, spill)

        # Scalar
        return (data, [])

    def _is_empty_or_spill(self, cell: Any) -> bool:
        return cell is None or cell.value is None or cell.comment == SPILL_TAG

    def _clear_spill_cells(
        self,
        positions: list[tuple[int, int]],
        sheet: Any = None,
    ) -> None:
        if not positions:
            return
        if sheet is None:
            # Attempt to find from active sheet
            try:
                sheet = self._app.workbook.active_sheet
            except Exception:
                return
        for r, c in positions:
            cell = sheet.get_cell(r, c)
            if cell and cell.comment == SPILL_TAG:
                sheet.clear_cell(r, c)


# ------------------------------------------------------------------ #
# Module-level singleton (lets evaluator access manager without       #
# importing the app, avoiding circular imports)                        #
# ------------------------------------------------------------------ #

_global_manager: FetchManager | None = None


def _set_global_manager(mgr: FetchManager) -> None:
    global _global_manager
    _global_manager = mgr


def _get_global_manager() -> FetchManager | None:
    return _global_manager
