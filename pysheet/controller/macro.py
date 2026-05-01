"""Macro recording and replay for vim-style q{reg}/@{reg} macros."""

from __future__ import annotations


class MacroRecorder:
    """Records and replays keystroke sequences into named registers a–z."""

    def __init__(self) -> None:
        self._recording: str | None = None   # register name currently being recorded
        self._buffer: list[str] = []         # keys accumulated during recording
        self._macros: dict[str, list[str]] = {}
        self._last_register: str | None = None  # register used by last @{reg}

    # -----------------------------------------------------------------------
    # Recording
    # -----------------------------------------------------------------------

    def start_recording(self, register: str) -> None:
        """Begin recording into *register* (single lowercase letter)."""
        self._recording = register
        self._buffer = []

    def stop_recording(self) -> None:
        """End recording and save accumulated keys into the register."""
        if self._recording is not None:
            self._macros[self._recording] = list(self._buffer)
            self._recording = None
            self._buffer = []

    def record_key(self, key: str) -> None:
        """Append *key* to the current recording buffer (no-op if not recording)."""
        if self._recording is not None:
            self._buffer.append(key)

    # -----------------------------------------------------------------------
    # Replay
    # -----------------------------------------------------------------------

    def get_macro(self, register: str) -> list[str] | None:
        """Return the key list for *register*, or None if undefined."""
        self._last_register = register
        return self._macros.get(register)

    def replay_last(self) -> list[str] | None:
        """Return keys for the last-used register (@@)."""
        if self._last_register is None:
            return None
        return self._macros.get(self._last_register)

    # -----------------------------------------------------------------------
    # State
    # -----------------------------------------------------------------------

    @property
    def is_recording(self) -> bool:
        return self._recording is not None

    @property
    def recording_register(self) -> str | None:
        return self._recording

    def has_macro(self, register: str) -> bool:
        return register in self._macros
