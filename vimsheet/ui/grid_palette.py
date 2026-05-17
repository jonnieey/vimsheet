"""GridPalette — theme-aware color palette for the spreadsheet grid.

Colors are auto-derived from Textual's built-in CSS variables
(``App.theme_variables``) at runtime.  Users can override individual
fields per theme in their config file, or interactively via
``:colorscheme``.
"""

from __future__ import annotations

from dataclasses import dataclass, fields

from textual.color import Color


@dataclass
class GridPalette:
    """All colour-role slots used by the grid, sheet tabs, and formula bar.

    Every field defaults to a sensible fallback string.  Call
    ``from_theme_variables()`` to derive real values from Textual's
    built-in CSS variables.
    """

    # ── Grid — header row ──────────────────────────────────────────────
    header_bg: str = "#1a1a2e"
    header_fg: str = "#b0b0b0"
    header_divider: str = "#111118"

    # ── Grid — cursor ──────────────────────────────────────────────────
    cursor_cell_bg: str = "#0066cc"
    cursor_cell_fg: str = "#ffffff"
    cursor_header_bg: str = "#0055aa"
    cursor_header_fg: str = "#ffffff"

    # ── Grid — visual selection ────────────────────────────────────────
    visual_sel_bg: str = "#1a1a3e"
    visual_sel_fg: str = "#ffffff"

    # ── Grid — lines & alternating rows ────────────────────────────────
    gridline: str = "#2a2a3e"
    alt_row_bg: str = "#1d1d32"

    # ── Grid — frozen rows/cols ────────────────────────────────────────
    frozen_sep: str = "#4488ff"
    frozen_header_bg: str = "#222238"
    frozen_cell_bg: str = "#111122"
    frozen_cell_fg: str = "#e0e0e0"

    # ── Grid — collapsed-row indicator ─────────────────────────────────
    collapsed_fg: str = "#888888"

    # ── Grid — error indicator ─────────────────────────────────────────
    error_fg: str = "#ff4444"

    # ── Sheet tabs ─────────────────────────────────────────────────────
    tab_active_bg: str = "#4488ff"
    tab_active_fg: str = "#ffffff"
    tab_inactive_bg: str = "#555555"
    tab_inactive_fg: str = "#cccccc"
    tab_add_bg: str = "#777777"
    tab_add_fg: str = "#ffffff"

    # ── Formula bar ────────────────────────────────────────────────────
    formula_cursor_bg: str = "steel_blue1"

    # ── Mode indicator colours ─────────────────────────────────────────
    mode_normal: str = "bright_green"
    mode_insert: str = "yellow"
    mode_edit: str = "red"
    mode_command: str = "cyan"
    mode_visual: str = "magenta"

    # ── Public helpers ─────────────────────────────────────────────────

    @classmethod
    def from_theme_variables(cls, variables: dict[str, str]) -> GridPalette:
        """Derive a palette from Textual's resolved CSS variables dict."""
        p = cls()

        def _var(key: str, fallback: str) -> str:
            return variables.get(key, fallback)

        def _safe_hex(raw: str, fallback: str) -> str:
            """Return a resolved hex colour, falling back for ``auto`` values."""
            if raw.startswith("auto"):
                return fallback
            try:
                return Color.parse(raw).hex
            except Exception:
                return fallback

        def _darken(hex_color: str, amount: float) -> str:
            try:
                return Color.parse(hex_color).darken(amount).hex
            except Exception:
                return hex_color

        def _lighten(hex_color: str, amount: float) -> str:
            try:
                return Color.parse(hex_color).lighten(amount).hex
            except Exception:
                return hex_color

        def _blend(fg_hex: str, bg_hex: str, alpha: float) -> str:
            try:
                fg = Color.parse(fg_hex)
                bg = Color.parse(bg_hex)
                return fg.blend(bg, alpha).hex
            except Exception:
                return fg_hex

        def _contrast_text(bg_hex: str, light: str = "#ffffff", dark: str = "#000000") -> str:
            """Return *light* or *dark* text based on background luminance."""
            try:
                return light if Color.parse(bg_hex).luminance < 0.5 else dark
            except Exception:
                return light

        surface = _var("surface", "#0f0f14")
        primary = _var("primary", "#0066cc")
        error = _var("error", "#ff4444")
        success = _var("success", "#44cc44")
        warning = _var("warning", "#ccaa00")
        accent = _var("accent", "#cc44cc")

        # text / text-muted may be "auto XX%" — always resolve to hex
        text = _safe_hex(_var("text", "#e0e0e0"), "#e0e0e0")
        text_muted = _safe_hex(_var("text-muted", "#808080"), "#808080")

        p.header_bg = _darken(surface, 0.03)
        p.header_fg = _lighten(text, 0.15)
        p.header_divider = _darken(surface, 0.08)

        p.cursor_cell_bg = primary
        p.cursor_cell_fg = _contrast_text(primary)
        p.cursor_header_bg = _darken(primary, 0.10)
        p.cursor_header_fg = _contrast_text(p.cursor_header_bg)

        p.visual_sel_bg = _blend(primary, surface, 0.40)
        p.visual_sel_fg = text

        p.gridline = _lighten(surface, 0.12)
        p.alt_row_bg = _lighten(surface, 0.03)

        p.frozen_sep = _lighten(primary, 0.15)
        p.frozen_header_bg = _darken(primary, 0.08)
        p.frozen_cell_bg = _lighten(surface, 0.02)
        p.frozen_cell_fg = text

        p.collapsed_fg = text_muted
        p.error_fg = error

        p.tab_active_bg = primary
        p.tab_active_fg = _contrast_text(primary)
        p.tab_inactive_bg = surface
        p.tab_inactive_fg = _contrast_text(surface, "#cccccc", "#555555")
        p.tab_add_bg = _lighten(surface, 0.10)
        p.tab_add_fg = text

        p.formula_cursor_bg = primary

        p.mode_normal = success
        p.mode_insert = warning
        p.mode_edit = error
        p.mode_command = primary
        p.mode_visual = _blend(accent, surface, 0.40)

        return p

    @classmethod
    def from_config(
        cls,
        variables: dict[str, str],
        theme_name: str,
        theme_overrides: dict[str, dict[str, str]] | None,
    ) -> GridPalette:
        """Derive palette from theme variables, then apply user overrides."""
        p = cls.from_theme_variables(variables)
        if theme_overrides and theme_name in theme_overrides:
            overrides = theme_overrides[theme_name]
            for field_name, raw_value in overrides.items():
                if hasattr(p, field_name):
                    resolved = _resolve_color_value(raw_value, variables)
                    if resolved is not None:
                        setattr(p, field_name, resolved)
        return p

    def apply_override(self, key: str, raw_value: str, variables: dict[str, str]) -> bool:
        """Set a single palette field from a user-entered value (hex, name, or ``$var``).

        Returns True on success, False if the key is unknown or value unparseable.
        """
        if not hasattr(self, key):
            return False
        resolved = _resolve_color_value(raw_value, variables)
        if resolved is None:
            return False
        setattr(self, key, resolved)
        return True

    def as_dict(self) -> dict[str, str]:
        return {f.name: getattr(self, f.name) for f in fields(self)}


# ── Internal helpers ──────────────────────────────────────────────────────


def _resolve_color_value(raw: str, variables: dict[str, str]) -> str | None:
    """Resolve a user-entered ``:colorscheme`` value to a hex string.

    Accepts:
    - ``$variable`` references (e.g. ``$primary``, ``$surface``)
    - named/hex colors understood by ``Color.parse()`` (``red``, ``#ff0000``, …)
    """
    if raw.startswith("$"):
        key = raw[1:]
        resolved = variables.get(key)
        if resolved:
            return resolved
        return None
    try:
        return Color.parse(raw).hex
    except Exception:
        return None
