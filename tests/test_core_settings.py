"""Unit tests for podcastforge.core.settings."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from podcastforge.core import settings as s_module
from podcastforge.core.settings import (
    load_settings,
    save_settings,
    get_setting,
    set_setting,
    get_config_dir,
)


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path, monkeypatch):
    """Redirect settings path to a temp directory so tests don't touch user config."""
    settings_file = tmp_path / "settings.json"
    monkeypatch.setattr(s_module, "_settings_path", lambda: settings_file)
    yield settings_file


class TestLoadSettings:
    def test_returns_empty_dict_when_no_file(self):
        result = load_settings()
        assert result == {}

    def test_loads_existing_json(self, isolated_settings):
        isolated_settings.write_text(json.dumps({"key": "value"}), encoding="utf-8")
        result = load_settings()
        assert result == {"key": "value"}

    def test_returns_empty_dict_on_corrupt_json(self, isolated_settings):
        isolated_settings.write_text("not valid json", encoding="utf-8")
        result = load_settings()
        assert result == {}


class TestSaveSettings:
    def test_saves_and_reloads(self):
        data = {"theme": "dark", "volume": 80}
        ok = save_settings(data)
        assert ok is True
        assert load_settings() == data

    def test_returns_false_on_write_error(self, monkeypatch):
        def bad_path():
            return Path("/nonexistent_dir/settings.json")
        monkeypatch.setattr(s_module, "_settings_path", bad_path)
        ok = save_settings({"x": 1})
        assert ok is False


class TestGetSetSetting:
    def test_get_nonexistent_returns_default(self):
        val = get_setting("no_such_key", default="fallback")
        assert val == "fallback"

    def test_get_nonexistent_returns_none_by_default(self):
        val = get_setting("no_such_key")
        assert val is None

    def test_set_and_get(self):
        set_setting("my_key", "my_value")
        assert get_setting("my_key") == "my_value"

    def test_set_overwrites(self):
        set_setting("key", "old")
        set_setting("key", "new")
        assert get_setting("key") == "new"

    def test_set_various_types(self):
        set_setting("int_val", 42)
        set_setting("list_val", [1, 2, 3])
        set_setting("dict_val", {"nested": True})
        assert get_setting("int_val") == 42
        assert get_setting("list_val") == [1, 2, 3]
        assert get_setting("dict_val") == {"nested": True}
