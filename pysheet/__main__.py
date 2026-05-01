"""Entry point for ``python -m pysheet`` and the ``pysheet`` CLI command."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any


def _setup_logging() -> None:
    """Configure logging to write to the user config directory."""
    log_dir = Path.home() / ".config" / "pysheet"
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=str(log_dir / "pysheet.log"),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="pysheet",
        description="A vim-like TUI spreadsheet for the terminal",
    )
    parser.add_argument(
        "file",
        nargs="?",
        metavar="FILE",
        help="File to open (CSV, XLSX, JSON, …). Opens blank sheet if omitted.",
    )
    parser.add_argument(
        "--script",
        metavar="SCRIPT",
        help="Run a PySheet script file non-interactively and exit.",
    )
    parser.add_argument(
        "--nocurses",
        action="store_true",
        help="Non-interactive pipeline mode: read commands from stdin.",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        help="Output file for pipeline / script mode.",
    )
    parser.add_argument(
        "--diff",
        nargs=2,
        metavar=("FILE_A", "FILE_B"),
        help="Diff two spreadsheet files side-by-side.",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Auto-reload mode: watch FILE for changes.",
    )
    parser.add_argument(
        "--set",
        action="append",
        metavar="KEY=VALUE",
        dest="set_values",
        help="Override a config value (may be repeated).",
    )
    parser.add_argument(
        "--theme",
        metavar="THEME",
        default=None,
        help=(
            "Start with a colour theme (dark, light, nord, gruvbox, dracula, "
            "tokyo, monokai, solarized, catppuccin, rose-pine)."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )
    return parser


def main() -> None:
    """CLI entry point."""
    _setup_logging()
    parser = _build_parser()
    args = parser.parse_args()

    # --- Parse --set overrides ---
    config_overrides: dict[str, str] = {}
    for item in args.set_values or []:
        if "=" not in item:
            parser.error(f"--set requires KEY=VALUE format, got: {item!r}")
        k, _, v = item.partition("=")
        config_overrides[k.strip()] = v.strip()

    # --- Non-interactive / pipeline modes ---
    if args.nocurses or args.script:
        _run_pipeline(args, config_overrides)
        return

    if args.diff:
        _run_diff(args.diff[0], args.diff[1])
        return

    # --- Interactive TUI ---
    _run_tui(args, config_overrides)


def _run_tui(args: argparse.Namespace, config_overrides: dict[str, str]) -> None:
    """Launch the interactive Textual application."""
    from pysheet.app import PySheetApp
    from pysheet.model.config import Config
    from pysheet.model.workbook import Workbook

    # Load config and apply --set overrides
    config = Config.load(Config.default_path())
    for key, val in config_overrides.items():
        if hasattr(config, key):
            field_type = type(getattr(config, key))
            try:
                if field_type is bool:
                    setattr(config, key, val.lower() in ("true", "1", "yes"))
                else:
                    setattr(config, key, field_type(val))
            except (ValueError, TypeError):
                pass

    workbook = Workbook.blank()

    if args.file:
        filepath = Path(args.file)
        if filepath.exists():
            workbook = _load_file(filepath)
        else:
            # New file — blank workbook, will save to this path on :w
            workbook.filepath = filepath

    app = PySheetApp(workbook=workbook)
    if args.theme:
        app._startup_theme = args.theme

    if args.watch and args.file:
        _start_watch_mode(Path(args.file), app)

    app.run()


def _load_file(filepath: Path) -> "Workbook":
    """Load a workbook from *filepath* using the appropriate I/O adapter."""
    from pysheet.model.workbook import Workbook
    from pysheet.io.registry import get_adapter

    try:
        adapter = get_adapter(filepath)
        wb = adapter.read(filepath)
        wb._bind_sheets()
        return wb
    except Exception as exc:
        logging.getLogger(__name__).error("Failed to load %s: %s", filepath, exc)
        wb = Workbook.blank()
        wb.filepath = filepath
        return wb


def _run_pipeline(args: argparse.Namespace, config_overrides: dict[str, str]) -> None:
    """Non-interactive mode: execute commands from stdin or a script file."""
    from pysheet.scripting.engine import ScriptEngine

    workbook = None
    if args.file:
        filepath = Path(args.file)
        if filepath.exists():
            workbook = _load_file(filepath)
    engine = ScriptEngine(workbook=workbook)

    if args.script:
        script_path = Path(args.script)
        if not script_path.exists():
            print(f"Script not found: {script_path}", file=sys.stderr)
            sys.exit(1)
        result = engine.run_file(script_path)
    else:
        # Read commands from stdin
        lines = sys.stdin.read().splitlines()
        result = engine.run_lines(lines)

    for err in result.errors:
        print(f"ERROR: {err}", file=sys.stderr)

    # Save output if requested
    if args.output:
        out_path = Path(args.output)
        from pysheet.io.registry import get_adapter
        try:
            adapter = get_adapter(out_path)
            adapter.write(engine.workbook, out_path)
        except Exception as exc:
            print(f"Save error: {exc}", file=sys.stderr)
            sys.exit(1)

    if result.errors:
        sys.exit(1)


def _run_diff(file_a: str, file_b: str) -> None:
    """Print a side-by-side diff of two spreadsheet files to stdout."""
    pa, pb = Path(file_a), Path(file_b)
    for p in (pa, pb):
        if not p.exists():
            print(f"File not found: {p}", file=sys.stderr)
            sys.exit(1)

    wb_a = _load_file(pa)
    wb_b = _load_file(pb)
    sa = wb_a.active_sheet
    sb = wb_b.active_sheet

    max_r = max(sa.max_row, sb.max_row)
    max_c = max(sa.max_col, sb.max_col)

    col_w = 12
    header = f"{'ROW':>4}  {'FILE A':<{col_w}}  {'FILE B':<{col_w}}  STATUS"
    print(header)
    print("-" * len(header))

    diffs = 0
    for r in range(max_r + 1):
        for c in range(max_c + 1):
            ca = sa.get_cell(r, c)
            cb = sb.get_cell(r, c)
            va = ca.display if ca else ""
            vb = cb.display if cb else ""
            if va != vb:
                from pysheet.model.range import rowcol_to_a1
                addr = rowcol_to_a1(r, c)
                status = "CHANGED" if va and vb else ("ADDED" if not va else "REMOVED")
                print(f"{addr:>4}  {va:<{col_w}}  {vb:<{col_w}}  {status}")
                diffs += 1

    print(f"\n{diffs} difference(s) found.")
    if diffs:
        sys.exit(1)


def _start_watch_mode(filepath: Path, app: Any) -> None:
    """Start file-watch mode using watchdog if available."""
    log = logging.getLogger(__name__)
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler

        class _Reload(FileSystemEventHandler):
            def __init__(self, path: Path) -> None:
                self._path = path
                self._last_mtime: float = 0.0

            def on_modified(self, event: Any) -> None:
                if Path(event.src_path).resolve() != self._path.resolve():
                    return
                import time
                mtime = self._path.stat().st_mtime
                if mtime == self._last_mtime:
                    return
                self._last_mtime = mtime
                log.info("File changed: %s — reloading", self._path)
                # Schedule reload on Textual's event loop thread
                app.call_from_thread(app._open_file, self._path)

        observer = Observer()
        observer.schedule(_Reload(filepath), str(filepath.parent), recursive=False)
        observer.daemon = True
        observer.start()
        log.info("Watching %s for changes", filepath)
    except ImportError:
        log.info("watchdog not installed — watch mode disabled")


if __name__ == "__main__":
    main()
