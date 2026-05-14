"""Help registry — manages sections, subgroups, and renders help content.

Usage (at module level in any feature file):
    from vimsheet.help_registry import register_section, register_help
    register_section("NAV", "Nav", order=10)
    register_help("NAV", "h / j / k / l", "Move cursor", subgroup="Cursor", order=10)

Formula functions are auto-populated from the formula registry.
"""

from __future__ import annotations

import inspect
from typing import Any

_SECTION_ORDER: list[str] = []  # insertion order of section keys
_SECTIONS: dict[str, str] = {}  # section key → short label
_ENTRIES: dict[
    str, list[tuple[str, str, int, str]]
] = {}  # section → [(binding, desc, order, subgroup)]

# Human-readable category labels for formula function tabs
_CATEGORY_LABELS: dict[str, str] = {
    "math": "Math",
    "text": "Text",
    "logic": "Logic",
    "date": "Date",
    "lookup": "Lookup",
    "web": "Web",
    "other": "Other",
}

# Built-in sections
_BUILTIN_SECTIONS = [
    ("NAV", "Nav", "Navigation"),
    ("EDIT", "Edit", "Editing"),
    ("ROWS", "R/C", "Rows & Columns"),
    ("VIS", "Vis", "Visual Mode"),
    ("MARKS", "Marks", "Marks & Search"),
    ("CMD", "Cmd", "Command Mode"),
    ("MACRO", "Macro", "Macros"),
    ("FUNC", "Func", "Formula Functions"),
]


def register_section(key: str, label: str, order: int = 0) -> None:
    """Register a help section (tab)."""
    if key not in _SECTIONS:
        _SECTIONS[key] = label
        _SECTION_ORDER.append(key)


def register_help(
    section: str,
    binding: str,
    description: str,
    *,
    order: int = 0,
    subgroup: str = "",
) -> None:
    """Register a help entry under *section* with optional *subgroup*."""
    if section not in _SECTIONS:
        register_section(section, section)
    if section not in _ENTRIES:
        _ENTRIES[section] = []
    _ENTRIES[section].append((binding, description, order, subgroup))


# ── Tab & entry accessors ──────────────────────────────────────────────────


def get_tabs() -> list[tuple[str, str]]:
    """Return [(section_key, compact_label)] in registration order + function categories."""
    import vimsheet.help_entries  # noqa: F401 — ensure entries are loaded

    keys = list(dict.fromkeys(_SECTION_ORDER))  # deduplicate, preserve order
    return [(k, _SECTIONS.get(k, k)) for k in keys]


def get_entries(section: str) -> dict[str, list[tuple[str, str]]]:
    """Return {subgroup_name: [(binding, description)]} for a section."""
    groups: dict[str, list[tuple[str, str]]] = {}
    for binding, desc, _, subgroup in _ENTRIES.get(section, []):
        sg = subgroup or "_default"
        if sg not in groups:
            groups[sg] = []
        groups[sg].append((binding, desc))
    return groups


def get_func_categories() -> list[tuple[str, str]]:
    """Return [(category_key, label)] for formula function tabs."""
    from vimsheet.formula.functions.registry import all_functions

    cats: dict[str, str] = {}
    for meta in all_functions().values():
        cats[meta.category] = _CATEGORY_LABELS.get(meta.category, meta.category.title())
    return sorted(cats.items(), key=lambda kv: (kv[0] == "other", kv[0]))


# ── Rendering ──────────────────────────────────────────────────────────────


def build_section(section: str, collapsed_groups: set[str] | None = None) -> str:
    """Build Rich markup for one section with collapsible subgroup headers."""
    rich, _ = section_lines(section, collapsed_groups)
    return rich


def section_lines(
    section: str, collapsed_groups: set[str] | None = None
) -> tuple[str, list[tuple[int, str]]]:
    """Return (rich_markup, [(line_index, binding), ...]) for a section.

    line_index is the 0-based line number in rich_markup.
    """
    from rich.markup import escape

    import vimsheet.help_entries  # noqa: F401

    groups = get_entries(section)
    collapsed = collapsed_groups or set()
    buf: list[str] = []
    positions: list[tuple[int, str]] = []
    bind_w = max((len(b) for grp in groups.values() for b, _ in grp), default=0) + 2

    for sg_name in sorted(groups.keys(), key=lambda k: (k == "_default", k)):
        sg_label = sg_name if sg_name != "_default" else ""
        items = groups[sg_name]
        is_collapsed = sg_name in collapsed
        if sg_label:
            toggle = "[green]▼[/green]" if not is_collapsed else "[green]▶[/green]"
            buf.append(f"\n{toggle} [bold]{escape(sg_label)}[/bold]")
        if not is_collapsed:
            for binding, desc in items:
                buf.append(f"\n  [white]{escape(binding).ljust(bind_w)}[/white] {desc}")
                line_count = "".join(buf).count("\n")
                positions.append((line_count, binding))
    return "".join(buf), positions


def build_func_category(category: str, collapsed: bool = False) -> str:
    """Build Rich markup for one formula function category."""
    from rich.markup import escape

    from vimsheet.formula.functions.registry import all_functions

    fns = sorted(
        (name, meta) for name, meta in all_functions().items() if meta.category == category
    )
    if not fns:
        return ""

    lines: list[str] = []
    col_w = max((len(name) + 2 for name, _ in fns), default=20)

    for name, meta in fns:
        sig = _format_func_sig(name, meta)
        desc = _func_desc(meta)
        padded = f"[chartreuse]{escape(sig.ljust(col_w))}[/chartreuse]"
        if desc:
            padded += f" [dim]{desc}[/dim]"
        lines.append(f"  {padded}")
    return "\n".join(lines)


def _format_func_sig(name: str, meta: Any) -> str:
    """Format a function signature like =@SUM(a,b,...)."""
    try:
        sig = inspect.signature(meta)
        parts: list[str] = []
        for pname, p in sig.parameters.items():
            if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
                parts.append("...")
            elif p.default is inspect.Parameter.empty:
                parts.append(pname)
            else:
                parts.append(f"<{pname}>")
        return f"=@{name}({','.join(parts)})"
    except Exception:
        return f"=@{name}()"


def _func_desc(meta: Any) -> str:
    """Extract first line of docstring from the wrapped function, or use meta.desc."""
    # Prefer meta.desc (from @register(desc="..."))
    if hasattr(meta, "desc") and meta.desc:
        return meta.desc
    # Fallback to wrapped function's docstring
    source = meta.fn if hasattr(meta, "fn") else meta
    doc = source.__doc__ if hasattr(source, "__doc__") else None
    if doc:
        for line in doc.strip().splitlines():
            line = line.strip()
            if line and not line.startswith("=@"):
                from rich.markup import escape

                return escape(line[:60])
    return ""


# ── Search ─────────────────────────────────────────────────────────────────


def build_search_index(query: str) -> dict[str, int]:
    """Return {section_key: match_count} for all tabs.

    Matches against both binding and description text (case-insensitive).
    """
    import vimsheet.help_entries  # noqa: F401

    q = query.lower()
    counts: dict[str, int] = {}
    for section, entries in _ENTRIES.items():
        total = 0
        for binding, desc, _, _ in entries:
            if q in binding.lower() or q in desc.lower():
                total += 1
        if total:
            counts[section] = total

    # Search formula function names and descriptions
    from vimsheet.formula.functions.registry import all_functions

    func_count = 0
    for name, meta in all_functions().items():
        desc = (meta.desc or "").lower()
        if q in name.lower() or q in desc:
            func_count += 1
    if func_count:
        counts["FUNC"] = counts.get("FUNC", 0) + func_count

    return counts


def search_matches(query: str) -> list[tuple[str, str, str, int]]:
    """Return [(section_key, subgroup, binding, order_index)] for all matches.

    order_index is the registration order for stable sorting.
    """
    import vimsheet.help_entries  # noqa: F401

    q = query.lower()
    results: list[tuple[str, str, str, int]] = []
    for section, entries in _ENTRIES.items():
        for binding, desc, order, subgroup in entries:
            line = f"{binding}  {desc}"
            if q in line.lower():
                results.append((section, subgroup, binding, order))

    # Search formula function names and descriptions
    from vimsheet.formula.functions.registry import all_functions

    for name, meta in sorted(all_functions().items()):
        desc = (meta.desc or "").lower()
        if q in name.lower() or q in desc:
            results.append(("FUNC", "Formula", name, 0))

    return results
