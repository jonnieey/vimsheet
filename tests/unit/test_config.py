"""Unit tests for pysheet.model.config.Config."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pysheet.model.config import Config


class TestConfigDefaults:
    def test_autosave_default(self) -> None:
        cfg = Config()
        assert cfg.autosave is False

    def test_autosave_interval_default(self) -> None:
        assert Config().autosave_interval == 300

    def test_default_col_width(self) -> None:
        assert Config().default_col_width == 10

    def test_theme_default(self) -> None:
        assert Config().theme == "default"

    def test_show_grid_lines_default(self) -> None:
        assert Config().show_grid_lines is True

    def test_max_undo_default(self) -> None:
        assert Config().max_undo == 1000

    def test_enter_moves_default(self) -> None:
        assert Config().enter_moves == "down"

    def test_decimal_separator_default(self) -> None:
        assert Config().decimal_separator == "."

    def test_thousands_separator_default(self) -> None:
        assert Config().thousands_separator == ","


class TestConfigSaveLoad:
    def test_save_creates_file(self, tmp_path: Path) -> None:
        cfg = Config()
        dest = tmp_path / "cfg.json"
        cfg.save(dest)
        assert dest.exists()

    def test_save_creates_parent_dirs(self, tmp_path: Path) -> None:
        cfg = Config()
        dest = tmp_path / "a" / "b" / "config.json"
        cfg.save(dest)
        assert dest.exists()

    def test_round_trip_default(self, tmp_path: Path) -> None:
        cfg = Config()
        dest = tmp_path / "config.json"
        cfg.save(dest)
        loaded = Config.load(dest)
        assert loaded == cfg

    def test_round_trip_modified(self, tmp_path: Path) -> None:
        cfg = Config(autosave=True, theme="dark", max_undo=50, tab_size=4)
        dest = tmp_path / "config.json"
        cfg.save(dest)
        loaded = Config.load(dest)
        assert loaded.autosave is True
        assert loaded.theme == "dark"
        assert loaded.max_undo == 50
        assert loaded.tab_size == 4

    def test_load_missing_file_returns_defaults(self, tmp_path: Path) -> None:
        loaded = Config.load(tmp_path / "nonexistent.json")
        assert loaded == Config()

    def test_load_missing_keys_use_defaults(self, tmp_path: Path) -> None:
        dest = tmp_path / "partial.json"
        dest.write_text(json.dumps({"theme": "light"}), encoding="utf-8")
        loaded = Config.load(dest)
        assert loaded.theme == "light"
        assert loaded.autosave == Config().autosave
        assert loaded.max_undo == Config().max_undo

    def test_load_unknown_keys_ignored(self, tmp_path: Path) -> None:
        dest = tmp_path / "extra.json"
        dest.write_text(
            json.dumps({"theme": "dark", "unknown_key": "ignored"}),
            encoding="utf-8",
        )
        loaded = Config.load(dest)
        assert loaded.theme == "dark"

    def test_load_invalid_json_returns_defaults(self, tmp_path: Path) -> None:
        dest = tmp_path / "bad.json"
        dest.write_text("NOT JSON", encoding="utf-8")
        loaded = Config.load(dest)
        assert loaded == Config()


class TestConfigDefaultPath:
    def test_default_path_returns_path_instance(self) -> None:
        p = Config.default_path()
        assert isinstance(p, Path)

    def test_default_path_ends_with_config_json(self) -> None:
        p = Config.default_path()
        assert p.name == "config.json"

    def test_default_path_under_home(self) -> None:
        p = Config.default_path()
        assert str(p).startswith(str(Path.home()))
