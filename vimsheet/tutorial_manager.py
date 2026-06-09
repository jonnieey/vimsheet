"""Manage the interactive tutorial system — generate, reset, and launch lessons.

Lessons are generated on demand from Python code (``vimsheet.tutorial_data``)
and cached in ``XDG_DATA_HOME/vimsheet/tutorials/``.  User modifications to
working copies persist between sessions.
"""

from __future__ import annotations

import json
from pathlib import Path

from vimsheet.model.config import _user_data_dir

_XDG_TUTORIALS = _user_data_dir() / "vimsheet" / "tutorials"

_LESSONS: list[tuple[int, str, str]] = [
    (0, "00_General", "Overview, Help, and General Commands"),
    (1, "01_Navigation", "Movement Basics (hjkl, 0/$, gg/G, Ctrl+f/b)"),
    (2, "02_CellEditing", "Entering and Editing Cell Contents"),
    (3, "03_CopyPaste", "Yank, Paste, Cut, and Registers"),
    (4, "04_UndoRedo", "Undo, Redo, and Repeat"),
    (5, "05_Marks", "Marks and Search (/ ? n N * #)"),
    (6, "06_Modes", "VimSheet Modes Overview"),
    (7, "07_InsertEdit", "Insert and Edit Mode Deep-Dive"),
    (8, "08_VisualMode", "Visual Mode (v V Ctrl+v)"),
    (9, "09_RowColOps", "Row and Column Operations"),
    (10, "10_Formulas", "Formulas and Basic Functions"),
    (11, "11_AdvancedFormulas", "Advanced Formulas (IF, VLOOKUP, etc.)"),
    (12, "12_SortFilter", "Sort and Filter Commands"),
    (13, "13_Formatting", "Cell Formatting and Themes"),
    (14, "14_Macros", "Macro Recording and Replay"),
    (15, "15_Substitute", "Find, Replace, and Substitute"),
    (16, "16_FreezeGroups", "Freeze Panes and Row/Column Groups"),
    (17, "17_CommandMode", "Command-Mode Operations"),
    (18, "18_SheetsBuffers", "Sheets and Buffers"),
    (19, "19_Plotting", "Plotting Charts"),
    (20, "20_FileOps", "File I/O (save, open, export)"),
]


class TutorialError(Exception):
    """Raised when a tutorial operation fails."""


class TutorialManager:
    """Generate, list, load, and reset interactive tutorial lessons.

    Working copies live in ``XDG_DATA_HOME/vimsheet/tutorials/`` so that
    user modifications persist between sessions.  Lessons are re-generated
    from Python code only when missing or explicitly reset.
    """

    def __init__(self) -> None:
        self._tutorials_dir = _XDG_TUTORIALS

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def tutorials_dir(self) -> Path:
        """Return the path to the working-copy tutorial directory."""
        return self._tutorials_dir

    def ensure_installed(self) -> None:
        """Generate any missing lesson files in the XDG data directory."""
        from vimsheet.tutorial_data import generate_lesson

        self._tutorials_dir.mkdir(parents=True, exist_ok=True)
        for num, fname, _ in _LESSONS:
            dest = self._tutorials_dir / f"{fname}.vimsheet"
            if not dest.exists():
                wb = generate_lesson(num)
                import json as _json

                dest.write_text(_json.dumps(wb, indent=2), encoding="utf-8")

    def get_lesson(self, num: int) -> Path:
        """Return the path to lesson *num*, generating it if missing."""
        self.ensure_installed()
        try:
            fname = _LESSONS[num][1]
        except IndexError as err:
            raise TutorialError(f"Lesson {num} does not exist (0–{self.max_lesson})") from err
        path = self._tutorials_dir / f"{fname}.vimsheet"
        if not path.exists():
            raise TutorialError(f"Lesson {num} file not found: {path}")
        return path

    def reset_lesson(self, num: int) -> None:
        """Regenerate lesson *num* from Python code, overwriting any changes."""
        from vimsheet.tutorial_data import generate_lesson

        try:
            fname = _LESSONS[num][1]
        except IndexError as err:
            raise TutorialError(f"Lesson {num} does not exist (0–{self.max_lesson})") from err
        wb = generate_lesson(num)
        self._tutorials_dir.mkdir(parents=True, exist_ok=True)
        dest = self._tutorials_dir / f"{fname}.vimsheet"
        dest.write_text(json.dumps(wb, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------
    # Progress tracking
    # ------------------------------------------------------------------

    @property
    def _progress_path(self) -> Path:
        return self._tutorials_dir / ".progress.json"

    def save_progress(self, lesson_num: int) -> None:
        """Record *lesson_num* as the last-visited lesson."""
        self._tutorials_dir.mkdir(parents=True, exist_ok=True)
        self._progress_path.write_text(
            json.dumps({"last_lesson": lesson_num}, indent=2),
            encoding="utf-8",
        )

    def load_progress(self) -> int | None:
        """Return the last-visited lesson number, or ``None``."""
        path = self._progress_path
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return int(data["last_lesson"])
        except (ValueError, KeyError, json.JSONDecodeError):
            return None

    def reset_progress(self) -> None:
        """Delete the progress file."""
        self._progress_path.unlink(missing_ok=True)

    def list_lessons(self) -> list[dict]:
        """Return metadata for every lesson (no file I/O)."""
        return [{"num": num, "file": fname, "title": title} for num, fname, title in _LESSONS]

    @property
    def max_lesson(self) -> int:
        """Highest lesson number (inclusive)."""
        return _LESSONS[-1][0]

    def lesson_exists(self, num: int) -> bool:
        """Return whether lesson *num* is a valid lesson number."""
        return 0 <= num <= self.max_lesson
