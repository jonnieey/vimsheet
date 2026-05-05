#!/usr/bin/env python3
"""
Build vimsheet Sphinx docs and serve them over HTTP.
Usage:
    python scripts/serve_sphinx_docs.py
"""

from __future__ import annotations

import http.server
import mimetypes
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_SOURCE = PROJECT_ROOT / "docs" / "source"
DOCS_BUILD = PROJECT_ROOT / "docs" / "build" / "html"
PORT = 8000

# Register the .inv MIME type so it doesn't trigger a download
mimetypes.add_type("application/x-sphinx-inventory", ".inv")


class SphinxDocsHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DOCS_BUILD), **kwargs)

    def log_message(self, format: str, *args):
        sys.stderr.write(f"[docs] {args[0]} {args[1]} {args[2]}\n")


def build_docs() -> bool:
    print("Building Sphinx documentation...")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "sphinx",
            "-b",
            "html",
            str(DOCS_SOURCE),
            str(DOCS_BUILD),
        ],
        cwd=str(PROJECT_ROOT),
    )
    return result.returncode == 0


def serve() -> None:
    os.chdir(str(PROJECT_ROOT))
    server = http.server.HTTPServer(("0.0.0.0", PORT), SphinxDocsHandler)
    url = f"http://localhost:{PORT}"
    print(f"Serving vimsheet docs at {url}")
    print(f"  Source: {DOCS_SOURCE}")
    print(f"  Build:  {DOCS_BUILD}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


def main() -> None:
    if not build_docs():
        print("ERROR: Documentation build failed.", file=sys.stderr)
        sys.exit(1)
    serve()


if __name__ == "__main__":
    main()
