"""Function registry — maps uppercase names to callable implementations."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

# Module-name fragment → category mapping (auto-detected from __module__)
_CATEGORY_MODULES: dict[str, list[str]] = {
    "math": ["math_funcs"],
    "text": ["text_funcs"],
    "logic": ["logic_funcs"],
    "date": ["date_funcs"],
    "lookup": ["lookup_funcs"],
    "web": ["net_funcs"],
}


class FunctionMeta:
    """Metadata wrapper for a registered formula function."""

    __slots__ = ("fn", "names", "category", "_is_script_func", "desc")

    def __init__(
        self,
        fn: Callable,
        names: tuple[str, ...],
        category: str = "other",
        _is_script_func: bool = False,
        desc: str = "",
    ):
        self.fn = fn
        self.names = names
        self.category = category
        self._is_script_func = _is_script_func
        self.desc = desc

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the wrapped function."""
        if name == "__wrapped__":
            return self.fn
        return getattr(self.fn, name)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.fn(*args, **kwargs)


def _detect_category(fn: Callable) -> str:
    """Auto-detect category from the function's module name."""
    module = getattr(fn, "__module__", "")
    for cat, patterns in _CATEGORY_MODULES.items():
        if any(p in module for p in patterns):
            return cat
    return "other"


_REGISTRY: dict[str, FunctionMeta] = {}


def register(
    *names: str, category: str | None = None, desc: str = ""
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator: register a function under one or more uppercase names.

    If *category* is None, it is auto-detected from the function's module name.
    *desc* is a brief one-line description shown in the help screen.
    """

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        cat = category if category is not None else _detect_category(fn)
        meta = FunctionMeta(fn=fn, names=names, category=cat, desc=desc)
        for name in names:
            _REGISTRY[name.upper()] = meta
        return fn

    return decorator


def get(name: str) -> FunctionMeta | None:
    """Return the FunctionMeta registered under *name* (case-insensitive), or None."""
    return _REGISTRY.get(name.upper())


def all_names() -> list[str]:
    """Return sorted list of all registered function names."""
    return sorted(_REGISTRY.keys())


def all_functions() -> dict[str, FunctionMeta]:
    """Return a copy of the registry mapping name → FunctionMeta."""
    return dict(_REGISTRY)


def register_script_function(name: str, script_path: str) -> None:
    """Register an external Python script as a callable formula function."""
    import json
    import subprocess

    def _coerce(v: Any) -> Any:
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                try:
                    return float(v)
                except ValueError:
                    pass
        return v

    def _script_fn(*args: Any, _source_ranges: list | None = None, _sheet: Any = None) -> Any:
        import sys as _sys

        from vimsheet.model.range import CellRange, a1_to_rowcol

        # Build flat list of (address, value) pairs preserving source cell addresses
        cell_pairs: list[tuple[str, Any]] = []
        if _source_ranges and _sheet:
            for ref in _source_ranges:
                try:
                    cr = CellRange.from_a1(ref) if ":" in ref else None
                    if cr:
                        for r in range(cr.start_row, cr.end_row + 1):
                            for c in range(cr.start_col, cr.end_col + 1):
                                col_letter = chr(65 + c) if c < 26 else ref[0]
                                addr = f"{col_letter}{r + 1}"
                                cell = _sheet.get_cell(r, c)
                                val = _coerce(cell.value if cell else None)
                                cell_pairs.append((addr, val))
                    else:
                        r2, c2 = a1_to_rowcol(ref)
                        col_letter = chr(65 + c2) if c2 < 26 else ref[0]
                        addr = f"{col_letter}{r2 + 1}"
                        cell = _sheet.get_cell(r2, c2)
                        cell_pairs.append((addr, _coerce(cell.value if cell else None)))
                except Exception:
                    pass

        if not cell_pairs:
            # Fallback: use evaluated args without address info
            flat = []
            for a in args:
                if isinstance(a, list):
                    for row in a:
                        flat.extend(row if isinstance(row, list) else [row])
                else:
                    flat.append(a)
            cell_pairs = [(f"A{i + 1}", _coerce(v)) for i, v in enumerate(flat)]

        rows_data = [{"_row": i + 1, k[0]: v} for i, (k, v) in enumerate(cell_pairs)]
        # Use actual column from address
        rows_data = []
        for _, (addr, val) in enumerate(cell_pairs):
            col_letter = "".join(c for c in addr if c.isalpha())
            row_num = int("".join(c for c in addr if c.isdigit()))
            rows_data.append({"_row": row_num, col_letter: val})

        payload = json.dumps({"rows": rows_data})
        try:
            proc = subprocess.run(
                [_sys.executable, script_path],
                input=payload + "\n",
                capture_output=True,
                text=True,
                timeout=10,
            )
            if proc.returncode != 0:
                return f"#SCRIPT:{proc.stderr.strip()[:40]}"

            # Parse outputs and write back to source cells if sheet available
            written = 0
            for line in proc.stdout.splitlines():
                try:
                    obj = json.loads(line)
                    if obj.get("type") == "cell" and _sheet:
                        addr = obj.get("address", "").upper()
                        val = obj.get("value")
                        r2, c2 = a1_to_rowcol(addr)
                        _sheet.set_cell_value(r2, c2, val, record_history=True)
                        written += 1
                    elif obj.get("type") == "done":
                        break
                except Exception:
                    pass
            return written  # return count of cells updated to formula cell
        except Exception as exc:
            return f"#SCRIPT:{exc}"

    meta = FunctionMeta(
        fn=_script_fn, names=(name.upper(),), category="other", _is_script_func=True
    )
    _REGISTRY[name.upper()] = meta
