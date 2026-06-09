#!/usr/bin/env python3
"""Generate all 21 tutorial .vimsheet files for development / packaging.

This is a thin CLI wrapper around :mod:`vimsheet.tutorial_data`.
Run directly to write files to the ``originals`` output directory,
or import the module from Python code to generate on demand.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from vimsheet.tutorial_data import LESSONS, generate_lesson

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "examples" / "tutorial" / "originals"
VSCRIPT_DIR = Path(__file__).resolve().parent.parent / "examples" / "tutorial" / "_scripts"


def _save_vsheet(fname: str, title: str, sheet: dict) -> None:
    """Write a minimal .vsheet regeneration script."""
    lines = [
        f"# Regeneration script for {fname}.vimsheet",
        "# Full formatting is applied by: python scripts/generate_tutorials.py",
        "",
        f"# --- {title} ---",
        "",
        'renamesheet "Sheet1" "Tutorial"',
        "",
    ]
    cw = sheet.get("col_widths", {})
    for col_idx_str, width in sorted(cw.items(), key=lambda x: int(x[0])):
        col_letter = chr(65 + int(col_idx_str))
        lines.append(f"colwidth {col_letter} {width}")
    fr = sheet.get("freeze_rows", 0)
    if fr:
        lines.append(f"freeze {fr}")
    lines.append("")
    for cell in sheet.get("cells", []):
        v = cell.get("value", "")
        if isinstance(v, str) and v.startswith("VIMSHEET TUTORIAL"):
            lines.append(f'set A1 = "{v}"')
            break
    lines.append("")
    lines.append(f"save ../{fname}.vimsheet")
    lines.append("")
    (VSCRIPT_DIR / f"{fname}.vsheet").write_text("\n".join(lines), encoding="utf-8")
    print(f"  → .vsheet  {fname}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="generate_tutorials")
    parser.add_argument("--vsheet", action="store_true", help="Also generate .vsheet scripts")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if args.vsheet:
        VSCRIPT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Generating {len(LESSONS)} tutorial files → {OUTPUT_DIR}")
    # all_wb = generate_all()
    for num, fname, title in LESSONS:
        wb = generate_lesson(num)
        path = OUTPUT_DIR / f"{fname}.vimsheet"
        path.write_text(json.dumps(wb, indent=2), encoding="utf-8")
        print(f"  ✓ {num:2d}  {fname}")
        if args.vsheet:
            _save_vsheet(fname, title, wb["sheets"][0])
    print("\nDone.")


if __name__ == "__main__":
    main()
