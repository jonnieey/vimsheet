# VimSheet

A vim-like TUI spreadsheet for the terminal.

**[Full documentation](https://jonnieey.github.io/vimsheet/)**

```
╭─────────────────────────────────────────────────────────╮
│ Vimsheet 0.2.7                                          │
├─────────────────────────────────────────────────────────┤
│ A4  │  =SUM(B4:B12)  │ NORMAL                           │
├────┬──────────────┬──────────┬──────────┬───────────────┤
│    │ A            │    B     │    C     │      D        │
├────┼──────────────┼──────────┼──────────┼───────────────┤
│  1 │ Category     │   Budget │   Actual │     Delta     │
│  2 │ Rent         │  1200.00 │  1200.00 │       0.00    │
│  3 │ Groceries    │   400.00 │   437.50 │     -37.50    │
│  4 │ Transport    │   150.00 │   112.00 │      38.00    │
│  5 │ Utilities    │   200.00 │   183.40 │      16.60    │
│  6 │ Dining       │   250.00 │   318.75 │     -68.75    │
│  7 │ Savings      │   500.00 │   500.00 │       0.00    │
├─────────────────────────────────────────────────────────┤
│Budget│sheet2│sheet3│sheet4│sheet5│sheet6│sheet7│sheet8  │
├─────────────────────────────────────────────────────────┤
│NORMAL│Budget│R4 C1│A4│40 rows│modified│budget.xlsx│time │
╰──────┴──────┴─────┴──┴───────┴────────┴───────────┴─────╯
```
---

## Why VimSheet?

If you live in the terminal and think in vim motions, a GUI spreadsheet is friction.
VimSheet puts a full-featured spreadsheet in your terminal with a keymap you already know.

- **Modal editing** — normal, insert, edit, visual, command modes, just like vim
- **Vim motions everywhere** — `hjkl`, `w/b`, `gg/G`, `0/$`, marks, `/{search}`, macros
- **Real formulas** — `=SUM()`, `=IF()`, `=VLOOKUP()`, `=XLOOKUP()`, cross-sheet refs, live recalculation
- **Visual mode ranges** — select with `v`/`V`/`Ctrl+v`, then yank, delete, sort, format, or run a command
- **Colon commands** — `:sort`, `:filter`, `:format`, `:plot`, `:substitute` and more
- **Multiple sheets & buffers** — `gt`/`gT` to switch tabs, `:sheet add/copy/rename/delete`
- **Undo history** — full per-cell history with `:history`, unlimited undo/redo
- **Macros** — record with `qa`, replay with `@a`, chain with `@@`
- **Charts** — bar, line, scatter, pie, histogram rendered inline via `plotext`
- **Import / Export** — CSV, TSV, XLSX, JSON, ODS, Markdown, LaTeX, HTML
- **Scripting** — non-interactive pipeline mode and `.vsheet` script files
- **Built-in tutorial** — 21 interactive lessons via `vimsheet tutor`

---

## Install

```bash
git clone https://github.com/jonnieey/vimsheet.git
cd vimsheet
`uv tool install . --force --no-cache` or `pip install`  or `pipx https://github.com/jonnieey/vimsheet.git`. 
```

Requires Python 3.11+ and a terminal that supports 256 colours.

---

## Quick start

```bash
vimsheet                        # blank sheet
vimsheet data.csv               # open a file
vimsheet tutor                  # interactive tutorial
```

Basic flow:

| Action | Key |
|--------|-----|
| Move | `h j k l` |
| Enter a string | `\` then type, `Enter` |
| Enter a number | `=100`, `Enter` |
| Enter a formula | `=SUM(A1:A5)`, `Enter` |
| Edit a cell | `e` |
| Yank / paste | `yy` / `p` |
| Undo / redo | `u` / `Ctrl+r` |
| Command | `:` |
| Help | `f1` |
| Quit | `:q` |

---

## Formulas

Formulas start with `=` and recalculate live as you edit:

```
=SUM(B2:B12)
=IF(C4>1000, "Over budget", "OK")
=VLOOKUP(A2, Sheet2!A:C, 2, false)
=FETCH("https://api.example.com/price", "$.usd")
```

Functions cover math, text, date, lookup, logic, and aggregation.
Run `:funcs` to see everything available, or open `f1 > Func` for docs.
Or create your own functions (read docs)

---

## Visual mode & ranges

```
v           cell selection
V           row selection
Ctrl+v      block selection

y           yank selection
d           delete selection
ss / sa / sd  sort rows / ascending / descending
tb / ti / tu  toggle bold / italic / underline
:           run any command on the selected range
```

---

## Scripting

Automate sheet construction with `.vsheet` scripts:

```bash
vimsheet --script setup.vsheet
cat setup.vsheet | vimsheet --nocurses --output result.csv
```

```
# setup.vsheet
set A1 = "Month"
set B1 = "Revenue"
formula C2 = =B2*0.2
sort B desc
save output.xlsx
```

---

## Configuration

Settings live at `~/.config/vimsheet/config.json`.
Change them at runtime with `:set option=value`:

```
:set theme=nord
:set autosave=true
:set enter_moves=right
```

Themes: `dark` `light` `nord` `gruvbox` `dracula` `tokyo` `monokai` `solarized`

---

## Tutorial

The built-in tutorial has 21 interactive lessons covering navigation, editing,
formulas, visual mode, macros, sorting, and more:

```bash
vimsheet tutor           # start from lesson 1
vimsheet tutor -l 5      # jump to a specific lesson
vimsheet tutor -L        # list all lessons
```

---

## License

MIT
