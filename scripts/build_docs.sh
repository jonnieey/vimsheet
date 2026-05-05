#!/usr/bin/env bash
# build_docs.sh — build VimSheet Sphinx documentation
# Usage:
#   ./scripts/build_docs.sh           # build only
#   ./scripts/build_docs.sh --open    # build and open in browser

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DOCS_DIR="$PROJECT_ROOT/docs"
BUILD_OUTPUT="$DOCS_DIR/build/html/index.html"

# ------------------------------------------------------------------
# 1. Install doc requirements
# ------------------------------------------------------------------
echo "Installing documentation requirements..."
pip install sphinx furo

# ------------------------------------------------------------------
# 2. Build the docs
# ------------------------------------------------------------------
echo "Building docs..."
cd "$DOCS_DIR"
make clean html

# ------------------------------------------------------------------
# 3. Report success
# ------------------------------------------------------------------
echo ""
echo "Docs built at $BUILD_OUTPUT"

# ------------------------------------------------------------------
# 4. Optionally open in the default browser
# ------------------------------------------------------------------
if [[ "${1:-}" == "--open" ]]; then
    echo "Opening in browser..."
    if command -v xdg-open &>/dev/null; then
        xdg-open "$BUILD_OUTPUT"
    elif command -v open &>/dev/null; then
        open "$BUILD_OUTPUT"
    elif command -v start &>/dev/null; then
        start "$BUILD_OUTPUT"
    else
        echo "Could not detect a browser opener. Open manually: $BUILD_OUTPUT"
    fi
fi
