"""Mode enum and state-machine transitions."""

from __future__ import annotations

from enum import Enum, auto


class Mode(Enum):
    """Application editing modes, mirroring vim modal behaviour."""

    NORMAL = auto()
    INSERT = auto()
    EDIT = auto()
    COMMAND = auto()
    VISUAL = auto()
    VISUAL_LINE = auto()
    VISUAL_BLOCK = auto()

    def label(self) -> str:
        """Return the display label shown in the formula bar / status bar."""
        match self:
            case Mode.NORMAL:
                return "NORMAL"
            case Mode.INSERT:
                return "INSERT"
            case Mode.EDIT:
                return "EDIT"
            case Mode.COMMAND:
                return "COMMAND"
            case Mode.VISUAL:
                return "VISUAL"
            case Mode.VISUAL_LINE:
                return "VISUAL LINE"
            case Mode.VISUAL_BLOCK:
                return "VISUAL BLOCK"

    def css_class(self) -> str:
        """Return a CSS class name for theme-dependent mode colour."""
        match self:
            case Mode.NORMAL:
                return "mode-normal"
            case Mode.INSERT:
                return "mode-insert"
            case Mode.EDIT:
                return "mode-edit"
            case Mode.COMMAND:
                return "mode-command"
            case Mode.VISUAL | Mode.VISUAL_LINE | Mode.VISUAL_BLOCK:
                return "mode-visual"

    def is_visual(self) -> bool:
        """Return True for any Visual sub-mode."""
        return self in (Mode.VISUAL, Mode.VISUAL_LINE, Mode.VISUAL_BLOCK)


# ---------------------------------------------------------------------------
# Valid transitions (for documentation / assertion purposes)
# ---------------------------------------------------------------------------

VALID_TRANSITIONS: dict[Mode, set[Mode]] = {
    Mode.NORMAL: {
        Mode.INSERT,
        Mode.EDIT,
        Mode.COMMAND,
        Mode.VISUAL,
        Mode.VISUAL_LINE,
        Mode.VISUAL_BLOCK,
    },
    Mode.INSERT: {Mode.NORMAL, Mode.EDIT},
    Mode.EDIT: {Mode.NORMAL, Mode.INSERT},
    Mode.COMMAND: {Mode.NORMAL},
    Mode.VISUAL: {Mode.NORMAL, Mode.COMMAND},
    Mode.VISUAL_LINE: {Mode.NORMAL, Mode.COMMAND},
    Mode.VISUAL_BLOCK: {Mode.NORMAL, Mode.COMMAND},
}


def can_transition(from_mode: Mode, to_mode: Mode) -> bool:
    """Return True if a direct mode transition is valid."""
    return to_mode in VALID_TRANSITIONS.get(from_mode, set())
