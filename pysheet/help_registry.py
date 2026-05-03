"""Help registry — collects key-binding and command entries for the help screen.

Usage (at module level in any feature file):
    from pysheet.help_registry import register_help
    register_help("SECTION NAME", "key or :cmd", "what it does")

Formula functions are auto-populated from the formula registry at render time.
"""

from __future__ import annotations

import inspect

_SECTION_KEYS: list[str] = []  # insertion-order section names
_ENTRIES: dict[str, list[tuple[str, str, int]]] = {}  # section → [(binding, desc, order)]


def register_help(section: str, binding: str, description: str, *, order: int = 0) -> None:
    """Register a single help entry under *section*."""
    if section not in _ENTRIES:
        _SECTION_KEYS.append(section)
        _ENTRIES[section] = []
    _ENTRIES[section].append((binding, description, order))


def _formula_section() -> str:
    """Build the FORMULA FUNCTIONS section from the live registry."""
    from rich.markup import escape

    from pysheet.formula.functions.registry import all_functions

    # Pass 1 — collect (sig_plain, desc) for every function
    entries: list[tuple[str, str]] = []
    for name, fn in sorted(all_functions().items()):
        if getattr(fn, "_is_script_func", False):
            continue
        sig = inspect.signature(fn)
        parts: list[str] = []
        for pname, p in sig.parameters.items():
            if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
                parts.append("...")
            elif p.default is inspect.Parameter.empty:
                parts.append(pname)
            else:
                # Angle brackets — square brackets clash with Rich markup
                parts.append(f"<{pname}>")
        sig_plain = f"=@{name}({','.join(parts)})"

        desc = ""
        if fn.__doc__:
            for line in fn.__doc__.strip().splitlines():
                line = line.strip()
                if line and not line.startswith("=@"):
                    desc = escape(line[:48])
                    break
        entries.append((sig_plain, desc))

    # Pass 2 — determine column width and render two-per-row with uniform padding
    col_w = max((len(s) for s, _ in entries), default=20) + 2
    lines: list[str] = ["\n[bold cyan]FORMULA FUNCTIONS[/bold cyan]"]
    row: list[str] = []

    for sig_plain, desc in entries:
        padded = sig_plain.ljust(col_w)
        cell = f"[chartreuse]{escape(padded)}[/chartreuse]"
        if desc:
            cell += f" [dim]{desc}[/dim]"
        row.append(cell)
        if len(row) == 2:
            lines.append("  " + "  ".join(row))
            row = []
    if row:
        lines.append("  " + row[0])
    return "\n".join(lines)


def build_help_text() -> str:
    """Render the full help text with Rich markup."""
    from rich.markup import escape

    # Ensure entries file is loaded (idempotent — Python caches the import)
    import pysheet.help_entries  # noqa: F401

    # Global binding column width so descriptions align across all sections
    bind_w = (
        max(
            (len(b) for section_entries in _ENTRIES.values() for b, _, _ in section_entries),
            default=0,
        )
        + 2
    )

    lines: list[str] = []
    for section in _SECTION_KEYS:
        lines.append(f"[bold cyan]{section}[/bold cyan]")
        entries = sorted(_ENTRIES[section], key=lambda t: t[2])
        for binding, desc, _ in entries:
            padded = escape(binding).ljust(bind_w)
            lines.append(f"  [white]{padded}[/white] {desc}")
        lines.append("")

    lines.append(_formula_section())
    lines.append("\n[dim]Press q, Escape, or Space to close[/dim]")
    return "\n".join(lines)
