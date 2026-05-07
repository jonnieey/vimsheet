"""Full-screen help overlay with tabs, collapsible subgroups, and vim search."""

from __future__ import annotations

import contextlib

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Static, Tab, Tabs

from vimsheet.help_registry import (
    build_func_category,
    build_search_index,
    get_func_categories,
    get_tabs,
    search_matches,
    section_lines,
)
from vimsheet.ui.vim_modal import VimModalScreen


class HelpScreen(VimModalScreen):
    """Modal overlay displaying help with tabbed sections and search."""

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
    }
    HelpScreen > #help-container {
        width: 88%;
        height: 92%;
        background: $surface;
        border: round $primary;
        padding: 0;
    }
    HelpScreen > #help-container > Tabs {
        dock: top;
        height: 3;
    }
    HelpScreen > #help-container > VerticalScroll {
        height: 1fr;
        padding: 0 2 1 2;
    }
    HelpScreen > #help-container > VerticalScroll > Static {
        width: auto;
    }
    HelpScreen > #search-line {
        dock: bottom;
        height: 1;
        padding: 0 2;
        background: $primary-background;
        display: none;
    }
    HelpScreen > #help-bar {
        dock: bottom;
        height: 1;
        padding: 0 2;
        background: $primary-background;
        color: $text-disabled;
    }
    """

    # Content cache: only rebuilt when structure changes (tab switch, collapse toggle)
    _section_rich: dict[str, str] = {}
    _section_positions: dict[str, list[tuple[int, str]]] = {}

    def __init__(self) -> None:
        super().__init__()
        self._tabs_data: list[tuple[str, str]] = []
        self._current_tab: str = ""
        self._collapsed: set[str] = set()
        self._search_query: str = ""
        self._search_typing: bool = False
        self._matches: list[tuple[str, str, str, int]] = []
        self._match_idx: int = 0
        self._func_categories: list[tuple[str, str]] = []

    def compose(self) -> ComposeResult:
        self._tabs_data = get_tabs()
        self._func_categories = get_func_categories()
        tab_widgets = [Tab(label, id=key) for key, label in self._tabs_data if key != "FUNC"]
        if self._func_categories:
            tab_widgets.append(Tab("Func", id="FUNC"))

        with Vertical(id="help-container"):
            yield Tabs(*tab_widgets, id="help-tabs")
            with VerticalScroll(id="help-scroll"):
                yield Static(id="help-content", markup=True)
        yield Static(id="search-line", markup=True)
        yield Static(id="help-bar", markup=True)

    def on_mount(self) -> None:
        self._current_tab = self._tabs_data[0][0] if self._tabs_data else ""
        self._build_cache_for(self._current_tab)
        self._render_current()
        bar = self.query_one("#help-bar", Static)
        bar.update("[dim]/? Search   n/N next   h/l tab   j/k scroll   q close[/dim]")

    # ── Content cache ─────────────────────────────────────────────────────

    def _build_cache_for(self, section: str) -> None:
        """Build rich markup and position index for *section*."""
        if section == "FUNC":
            rich = self._render_func_tab()
            positions: list[tuple[int, str]] = []
            for cat_key, _ in self._func_categories:
                from vimsheet.formula.functions.registry import all_functions

                for name, meta in sorted(all_functions().items()):
                    if meta.category == cat_key and not meta._is_script_func:
                        positions.append((0, name))
            self._section_rich["FUNC"] = rich
            self._section_positions["FUNC"] = positions
        else:
            rich, positions = section_lines(section, self._collapsed)
            self._section_rich[section] = rich
            self._section_positions[section] = positions

    def _invalidate_cache(self, section: str) -> None:
        self._section_rich.pop(section, None)
        self._section_positions.pop(section, None)

    # ── Key handling ─────────────────────────────────────────────────────

    def on_key(self, event) -> None:
        key = event.key
        char = event.character

        if self._search_typing:
            self._handle_typing_key(key, char, event)
        else:
            self._handle_normal_key(key, char, event)

    def _handle_typing_key(self, key: str, char: str | None, event) -> None:
        if key == "escape":
            event.stop()
            self._cancel_search()
        elif key == "enter":
            event.stop()
            self._confirm_search()
        elif key == "backspace":
            event.stop()
            self._search_query = self._search_query[:-1]
            self._update_typing_prompt()
        elif char is not None and char.isprintable():
            event.stop()
            self._search_query += char
            self._update_typing_prompt()

    def _handle_normal_key(self, key: str, char: str | None, event) -> None:
        if key == "slash":
            event.stop()
            self._start_typing()
        elif key in ("h", "left"):
            event.stop()
            self.action_prev_tab()
        elif key in ("l", "right"):
            event.stop()
            self.action_next_tab()
        elif key in ("n", "N"):
            event.stop()
            if self._matches:
                if key == "n":
                    self.action_next_match()
                else:
                    self.action_prev_match()
        elif key == "enter":
            event.stop()
            if self._matches:
                self._scroll_to_match(self._match_idx)
        elif key == "escape":
            event.stop()
            if self._search_query:
                self._clear_results()
            else:
                self.dismiss()
        elif key == "q":
            event.stop()
            self.dismiss()
        elif key == "tab":
            event.stop()
            self.action_next_tab()

    # ── Tab management ───────────────────────────────────────────────────

    def action_next_tab(self) -> None:
        self._cycle_tab(1)

    def action_prev_tab(self) -> None:
        self._cycle_tab(-1)

    def _cycle_tab(self, delta: int) -> None:
        keys = [k for k, _ in self._tabs_data]
        if not keys:
            return
        idx = keys.index(self._current_tab) if self._current_tab in keys else 0
        idx = (idx + delta) % len(keys)
        self._switch_tab(keys[idx])

    def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        tab_id = event.tab.id or ""
        if tab_id and tab_id in dict(self._tabs_data):
            self._switch_tab(tab_id)

    def _switch_tab(self, key: str) -> None:
        if key == self._current_tab:
            return
        self._current_tab = key
        tabs = self.query_one("#help-tabs", Tabs)
        with contextlib.suppress(Exception):
            tabs.active = key
        self._build_cache_for(key)
        self._render_current()

    # ── Rendering ────────────────────────────────────────────────────────

    def _render_current(self) -> None:
        static = self.query_one("#help-content", Static)
        key = self._current_tab

        if key not in self._section_rich:
            self._build_cache_for(key)

        content = self._section_rich.get(key, "")

        if self._search_typing or self._search_query:
            q = self._search_query or ""
            if self._search_typing:
                header = f"[bold]/[reverse]{q}[/reverse]▌[/bold]"
                content = f"{header}\n\n{content}"
            elif q:
                counts = build_search_index(q) if q else {}
                total = sum(counts.values())
                idx_display = self._match_idx + 1 if self._matches else 0
                header = f"[bold]/{q}  ({idx_display}/{total})[/bold]"
                content = f"{header}\n\n{content}"
                active_binding = self._matches[self._match_idx][2] if self._matches else ""
                content = self._highlight_matches(content, q, active_binding, key)

        static.update(content)
        self._update_search_line()

    def _render_func_tab(self) -> str:
        lines: list[str] = []
        for cat_key, cat_label in self._func_categories:
            toggle = "▼" if cat_key not in self._collapsed else "▶"
            lines.append(f"\n[green]{toggle}[/green] [bold]{cat_label}[/bold]")
            if cat_key not in self._collapsed:
                content = build_func_category(cat_key)
                if content:
                    lines.append(content)
        return "\n".join(lines)

    def _highlight_matches(
        self, text: str, query: str, active_binding: str = "", section: str = ""
    ) -> str:
        """Apply [reverse] to all matches, [reverse bold] to the active match line."""
        import re as _re

        q = _re.escape(query)
        positions = self._section_positions.get(section, [])
        active_indices = (
            {li for li, b in positions if b == active_binding} if active_binding else set()
        )

        lines = text.split("\n")
        for li in range(len(lines)):
            plain = _re.sub(r"\[/?\w+(?:=[^\]]*)?\]", "", lines[li])
            if _re.search(q, plain, _re.IGNORECASE):
                style = "[reverse bold]" if li in active_indices else "[reverse]"
                parts = _re.split(r"(\[[^\]]*\])", lines[li])
                for i in range(len(parts)):
                    if i % 2 == 0:
                        parts[i] = _re.sub(
                            f"({q})", rf"{style}\1[/reverse]", parts[i], flags=_re.IGNORECASE
                        )
                lines[li] = "".join(parts)
        return "\n".join(lines)

    # ── Search ───────────────────────────────────────────────────────────

    def _start_typing(self) -> None:
        self._search_typing = True
        self._search_query = ""
        self._matches = []
        self._match_idx = 0
        self._update_typing_prompt()

    def _cancel_search(self) -> None:
        self._search_typing = False
        self._search_query = ""
        self._matches = []
        self._match_idx = 0
        self._update_tab_badges("")
        self._render_current()

    def _confirm_search(self) -> None:
        q = self._search_query
        self._search_typing = False
        if q:
            self._matches = search_matches(q)
            self._match_idx = 0
            self._update_tab_badges(q)
            self._render_current()
            if self._matches:
                self._scroll_to_match(0)
        else:
            self._render_current()

    def _clear_results(self) -> None:
        self._search_query = ""
        self._matches = []
        self._match_idx = 0
        self._update_tab_badges("")
        self._render_current()

    def _update_typing_prompt(self) -> None:
        self._update_search_line()

    def action_next_match(self) -> None:
        if not self._matches:
            return
        self._match_idx = (self._match_idx + 1) % len(self._matches)
        self._jump_to_match()

    def action_prev_match(self) -> None:
        if not self._matches:
            return
        self._match_idx = (self._match_idx - 1) % len(self._matches)
        self._jump_to_match()

    def _jump_to_match(self) -> None:
        """Switch to the match's tab, ensure it's expanded, then scroll."""
        section, subgroup, _, _ = self._matches[self._match_idx]
        if section != self._current_tab:
            self._switch_tab(section)
        if subgroup and (subgroup in self._collapsed):
            self._collapsed.discard(subgroup)
            self._invalidate_cache(section)
        self._render_current()
        self._scroll_to_match(self._match_idx)

    def _scroll_to_match(self, match_idx: int) -> None:
        """Scroll viewport to center the match line."""
        section, _, binding, _ = self._matches[match_idx]
        vs = self.query_one("#help-scroll", VerticalScroll)
        positions = self._section_positions.get(section, [])
        for li, b in positions:
            if b == binding:
                view_h = vs.scrollable_content_region.height
                scroll_y = max(0, li * 1.2 - view_h / 2.5)
                vs.scroll_to(y=scroll_y, animate=False)
                return

    # ── UI helpers ───────────────────────────────────────────────────────

    def _update_search_line(self) -> None:
        sl = self.query_one("#search-line", Static)
        bar = self.query_one("#help-bar", Static)
        if self._search_typing:
            display = f"[bold]/[reverse]{self._search_query}[/reverse]▌[/bold]"
            sl.update(display)
            sl.styles.display = "block"
            bar.styles.display = "none"
        else:
            sl.styles.display = "none"
            bar.styles.display = "block"

    def _update_tab_badges(self, query: str) -> None:
        tabs = self.query_one("#help-tabs", Tabs)
        counts = build_search_index(query) if query else {}
        for key, label in self._tabs_data:
            try:
                tab = tabs._tab_id_map.get(key)
                if tab:
                    cnt = counts.get(key, 0)
                    new_label = f"{label}({cnt})" if cnt else label
                    if tab.label != new_label:
                        tab.label = new_label
            except Exception:
                pass
