# Documentation Update Checklist

When making ANY code change that adds/modifies features, commands, or keybindings,
you MUST also update ALL affected documentation files.

## 1. New `:command` (app.py dispatch or `_ALL_COMMANDS`)

- Add `register_help("CMD", "command", "description", subgroup=..., order=...)`
  in `vimsheet/help_entries.py` under the appropriate CMD subgroup
- Add command to `docs/source/reference/commands.rst` under the right category
- If the command has TAB-completion, add it to `_ALL_COMMANDS` in
  `vimsheet/command_completer.py`

## 2. New keybinding (controller handlers)

- Add `register_help("<SECTION>", "<binding>", "<description>")` in
  `vimsheet/help_entries.py` under the right section tab:
  - `NAV` — movement keys (h/j/k/l, G, $, ^, w/b, ctrl+*, etc.)
  - `EDIT` — editing keys (x, D, cw, cc, dd, yy, p, P, u, ., etc.)
  - `ROWS` — row/column ops (dr/dc, ir/ic, hr/hc, z_/z+, zl/zL, etc.)
  - `VIS` — visual mode keys (v/V/Ctrl+v, y, d, >, <, s*, g*, etc.)
  - `MARKS` — marks/find (m, ', /, ?, n, N, *, #)
  - `MACRO` — macro recording (q, @, @@)
- Update `docs/source/reference/keybindings.rst` with the new binding

## 3. New range-prefixed command (`:<range> <cmd>`)

When a command accepts a range prefix (visual mode pre-fills the range),
add a `case _ if` pattern in `app.py` `_dispatch_command()` after the
existing sort range handler (~line 1092), before the `# ---- Cell comment ----`
section.  Pattern:

```python
case _ if len(parts) >= <N> and parts[1].lower() in ("cmd1", "cmd2"):
```

- If the command also has a non-range form, make sure the range-prefixed
  pattern comes FIRST (earlier in the match block) so it catches prefixed input.
- Iterate over the CellRange using `CellRange.from_a1()`, call per-cell
  helpers, and wrap undo ops in `CompositeCommand` or `FillRangeCommand`.

## 4. Range + function apply

- `:<range> <FUNCNAME> [args]` applies scalar functions element-wise
- Aggregate functions (SUM, AVG, etc.) listed in `_AGGREGATE_FUNCS` on
  the `VimSheetApp` class yank total to register instead
- Scalar functions are applied via `_apply_func_to_range()` which
  evaluates `=FUNCNAME(value, *extra_args)` per cell
- Add new aggregate functions to `_AGGREGATE_FUNCS` if needed

## 5. Formula functions

- Update relevant user-guide RST in `docs/source/user-guide/`
  (e.g., `editing.rst`, `navigation.rst`, `modes.rst`, `sort-filter.rst`, etc.)
- Always update `docs/source/changelog.rst` with a changelog entry

## 4. Formula functions

- FUNC tab is auto-populated from the formula registry at runtime —
  no `register_help()` entry needed
- But do add docs to `docs/source/reference/functions.rst` if adding a new function

## 6. Section mapping cheat sheet

| Help Section | Code Location | RST File |
|---|---|---|
| NAV | `normal_handler.py` (h/j/k/l, G, 0, $, ^, ctrl+*, etc.) | `keybindings.rst` |
| EDIT | `normal_handler.py` (x, D, cw, cc, p, P, u, ctrl+r, ., etc.), `insert_handler.py`, `edit_handler.py` | `keybindings.rst`, `editing.rst` |
| ROWS | `normal_handler.py` (dr, dc, ir, ic, hr, hc, sr, sc, z_, z+, zl, zL, zc/zo, etc.) | `keybindings.rst` |
| VIS | `visual_handler.py` (all visual mode keys) | `keybindings.rst` |
| MARKS | `normal_handler.py` (m, ', /, ?, n, N, *, #) | `keybindings.rst`, `navigation.rst` |
| MACRO | `normal_handler.py` (q, @, @@) | `keybindings.rst` |
| CMD | `app.py` `_dispatch_command()` + `_ALL_COMMANDS` | `commands.rst` |

## 7. New CLI subcommand `vimsheet tutor`

When adding a new CLI subcommand (like `vimsheet tutor`):

- Add interception in `vimsheet/__main__.py` `main()` **before** `_build_parser()`
  with a `sys.argv[1] == "<cmd>"` check
- Create a separate `_run_<cmd>()` function with its own `ArgumentParser`
- The subcommand handler launches via `VimSheetApp(workbook=..., config=...).run()`
- Tutorial originals live in `vimsheet/tutorials/originals/` (package data)
- Working copies live in `XDG_DATA_HOME/vimsheet/tutorials/`
- Register package data in `pyproject.toml` under `[tool.hatch.build.targets.wheel] include`
- Update `vimsheet/tutorial_manager.py` with lesson metadata if modifying lessons

## 8. Verification

Before declaring work complete, run `python -m pytest tests/ -x -q` and ensure
all tests pass (known pre-existing failures: test_P_keeps_exact_formula,
test_range_yank_paste_adjusts, and all test_insert_* tests).
