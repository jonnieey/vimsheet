"""Functions reference modal — lists all formula functions with signatures."""

from __future__ import annotations

import inspect

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from pysheet.ui.vim_modal import VimModalScreen


def _build_funcs_text(filter_term: str = "") -> str:
    from pysheet.formula.functions.registry import all_functions

    fns = all_functions()
    term = filter_term.strip().upper()

    # Group by source module
    _CATEGORY_ORDER = ["math_funcs", "text_funcs", "logic_funcs", "date_funcs", "lookup_funcs"]
    _CATEGORY_LABELS = {
        "math_funcs": "Math & Statistics",
        "text_funcs": "Text",
        "logic_funcs": "Logic",
        "date_funcs": "Date & Time",
        "lookup_funcs": "Lookup",
    }

    # Build name → (category, signature_str) mapping
    # Multiple names may map to the same fn (aliases); track by fn id to show aliases together
    seen_fn_ids: dict[int, list[str]] = {}
    for name, fn in sorted(fns.items()):
        seen_fn_ids.setdefault(id(fn), []).append(name)

    # Build entries: (category, primary_name, aliases, sig_str)
    entries: list[tuple[str, str, list[str], str]] = []
    processed: set[int] = set()
    for _, fn in sorted(fns.items()):
        fn_id = id(fn)
        if fn_id in processed:
            continue
        processed.add(fn_id)
        names = sorted(seen_fn_ids[fn_id])
        primary = names[0]
        aliases = names[1:]
        module = getattr(fn, "__module__", "")
        category = next((k for k in _CATEGORY_ORDER if k in module), "other")

        try:
            sig = inspect.signature(fn)
            params = []
            for pname, p in sig.parameters.items():
                if pname.startswith("_"):
                    continue
                if p.kind == inspect.Parameter.VAR_POSITIONAL:
                    params.append(f"{pname}...")
                elif p.default is inspect.Parameter.empty:
                    params.append(pname)
                else:
                    params.append(f"[{pname}]")
            sig_str = ", ".join(params) if params else ""
        except (ValueError, TypeError):
            sig_str = "..."

        entries.append((category, primary, aliases, sig_str))

    # Filter
    if term:
        entries = [e for e in entries if term in e[1] or any(term in a for a in e[2])]

    if not entries:
        return f"No functions matching '{filter_term}'."

    # Group and render
    by_cat: dict[str, list[tuple[str, list[str], str]]] = {}
    for cat, primary, aliases, sig_str in entries:
        by_cat.setdefault(cat, []).append((primary, aliases, sig_str))

    lines: list[str] = []
    col_w = 14

    for cat_key in _CATEGORY_ORDER + ["other"]:
        group = by_cat.get(cat_key)
        if not group:
            continue
        label = _CATEGORY_LABELS.get(cat_key, cat_key.replace("_", " ").title())
        lines.append(f"[bold cyan]── {label} {'─' * (40 - len(label))}[/bold cyan]")
        for primary, aliases, sig_str in sorted(group):
            name_col = primary.ljust(col_w)
            sig_col = f"({sig_str})" if sig_str else "()"
            alias_col = f"  [dim]aka {', '.join(aliases)}[/dim]" if aliases else ""
            row_str = (
                f"  [bold chartreuse]{name_col}[/bold chartreuse]"
                f" [yellow]{sig_col}[/yellow]{alias_col}"
            )
            lines.append(row_str)
        lines.append("")

    total = len(entries)
    plural = "s" if total != 1 else ""
    header = f"[bold]{total} function{plural} available[/bold]  [dim](q/Esc to close)[/dim]\n"
    return header + "\n".join(lines)


class FuncsScreen(VimModalScreen):
    """Scrollable modal listing all formula functions with signatures."""

    DEFAULT_CSS = """
    FuncsScreen {
        align: center middle;
    }
    FuncsScreen > VerticalScroll {
        width: 84%;
        height: 92%;
        background: $surface;
        border: round $primary;
        padding: 1 2;
    }
    FuncsScreen > VerticalScroll > Static {
        width: auto;
    }
    """

    def __init__(self, filter_term: str = "") -> None:
        super().__init__()
        self._filter = filter_term

    def compose(self) -> ComposeResult:
        text = _build_funcs_text(self._filter)
        with VerticalScroll():
            yield Static(text, markup=True)
