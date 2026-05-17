"""Entry point for ``python -m vimsheet`` and the ``vimsheet`` CLI command."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

from vimsheet.model.workbook import Workbook


def _setup_logging() -> None:
    """Configure logging to write to the user config directory."""
    log_dir = Path.home() / ".config" / "vimsheet"
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=str(log_dir / "vimsheet.log"),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="vimsheet",
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
        help="Run a VimSheet script file non-interactively and exit.",
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

    # --- tutor subcommand (intercepted before argparse to avoid refactoring) ---
    if len(sys.argv) >= 2 and sys.argv[1] == "tutor":
        _run_tutor(sys.argv[2:])
        return

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
    from vimsheet.app import VimSheetApp
    from vimsheet.model.config import Config

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

    app = VimSheetApp(workbook=workbook, config=config)
    if args.theme:
        app._startup_theme = args.theme

    if args.watch and args.file:
        _start_watch_mode(Path(args.file), app)

    app.run()


def _load_file(filepath: Path) -> Workbook:
    """Load a workbook from *filepath* using the appropriate I/O adapter."""
    from vimsheet.io.registry import get_adapter
    from vimsheet.model.workbook import Workbook

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
    from vimsheet.scripting.engine import ScriptEngine

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
        from vimsheet.io.registry import get_adapter

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
                from vimsheet.model.range import rowcol_to_a1

                addr = rowcol_to_a1(r, c)
                status = "CHANGED" if va and vb else ("ADDED" if not va else "REMOVED")
                print(f"{addr:>4}  {va:<{col_w}}  {vb:<{col_w}}  {status}")
                diffs += 1

    print(f"\n{diffs} difference(s) found.")
    if diffs:
        sys.exit(1)


def _run_tutor(argv: list[str]) -> None:
    """Handle the ``vimsheet tutor`` subcommand."""
    tutor_parser = argparse.ArgumentParser(
        prog="vimsheet tutor",
        description="Interactive tutorial for VimSheet",
    )
    tutor_parser.add_argument(
        "-l",
        "--lesson",
        type=int,
        default=None,
        help="Launch a single lesson N (0–20) and exit. No auto-advance.",
    )
    tutor_parser.add_argument(
        "-s",
        "--start",
        type=int,
        default=None,
        help="Start sequential mode from lesson N (0–20).",
    )
    tutor_parser.add_argument(
        "-c",
        "--resume",
        action="store_true",
        help="Resume sequential mode from the last visited lesson.",
    )
    tutor_parser.add_argument(
        "-r",
        "--reset",
        type=int,
        default=None,
        help="Reset lesson N to its original state.",
    )
    tutor_parser.add_argument(
        "--reset-progress",
        action="store_true",
        help="Clear saved progress without resetting any lesson.",
    )
    tutor_parser.add_argument(
        "-L",
        "--list",
        action="store_true",
        help="List all available lessons and exit.",
    )
    args = tutor_parser.parse_args(argv)

    from vimsheet.tutorial_manager import TutorialError, TutorialManager

    tm = TutorialManager()

    # --- List ---
    if args.list:
        lessons = tm.list_lessons()
        print(f"{'Num':>4}  {'Lesson':<30}  {'Description'}")
        print(f"{'─' * 4}  {'─' * 30}  {'─' * 50}")
        for le in lessons:
            print(f"  {le['num']:2d}   {le['file']:<30}  {le['title']}")
        return

    # --- Reset progress ---
    if args.reset_progress:
        tm.reset_progress()
        print("Progress cleared.")
        return

    # --- Reset lesson ---
    if args.reset is not None:
        try:
            tm.reset_lesson(args.reset)
            print(f"Lesson {args.reset} reset to original.")
        except TutorialError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        return

    # --- Single lesson mode (-l) ---
    if args.lesson is not None:
        _launch_single_lesson(tm, args.lesson)
        return

    # --- Sequential mode ---
    start: int | None = args.start
    if args.resume:
        resumed = tm.load_progress()
        if resumed is None:
            print("No progress found. Starting from lesson 0.")
            start = 0
        else:
            next_num = resumed + 1
            if next_num > tm.max_lesson:
                print("All lessons already complete. Starting from lesson 0.")
                start = 0
            else:
                start = next_num
                print(f"Resuming at lesson {start}.")
    if start is None:
        start = 0

    _run_sequential(tm, start)


def _launch_single_lesson(tm: Any, lesson_num: int) -> None:
    """Open a single lesson and exit after the user quits."""
    _launch_lesson(tm, lesson_num)


def _launch_lesson(tm: Any, lesson_num: int) -> None:
    """Open *lesson_num* in the TUI and block until the user exits."""
    from vimsheet.app import VimSheetApp
    from vimsheet.io.registry import get_adapter
    from vimsheet.model.config import Config
    from vimsheet.tutorial_manager import TutorialError

    try:
        path = tm.get_lesson(lesson_num)
    except TutorialError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    config = Config.load(Config.default_path())
    workbook = get_adapter(path).read(path)
    workbook._bind_sheets()
    app = VimSheetApp(workbook=workbook, config=config)
    app.run()


def _run_sequential(tm: Any, start: int) -> None:
    """Run lessons from *start* through the end, prompting to continue."""
    n = start
    while n <= tm.max_lesson:
        print(f"\n── Lesson {n} of {tm.max_lesson} ──")
        _launch_lesson(tm, n)
        tm.save_progress(n)

        if n >= tm.max_lesson:
            print("\nAll lessons complete! 🎉")
            tm.reset_progress()
            break

        answer = input(f"\nContinue to lesson {n + 1}? [Y/n/q]: ").strip().lower()
        if answer in ("n", "q", "no", "quit"):
            if answer != "q" and answer != "quit":
                print("Resume later with:  vimsheet tutor -c")
            break
        n += 1


def _start_watch_mode(filepath: Path, app: Any) -> None:
    """Start file-watch mode using watchdog if available."""
    log = logging.getLogger(__name__)
    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer

        class _Reload(FileSystemEventHandler):
            def __init__(self, path: Path) -> None:
                self._path = path
                self._last_mtime: float = 0.0

            def on_modified(self, event: Any) -> None:
                if Path(event.src_path).resolve() != self._path.resolve():
                    return
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
