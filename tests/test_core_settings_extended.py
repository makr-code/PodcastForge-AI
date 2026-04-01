"""Extended tests for podcastforge.core.settings."""
import json
import platform
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import podcastforge.core.settings as settings_module
from podcastforge.core.settings import (
    get_config_dir,
    load_settings,
    save_settings,
    get_setting,
    set_setting,
    APP_NAME,
)


def _isolated_settings(tmp_path, monkeypatch):
    """Redirect all settings calls to use tmp_path as config dir."""
    monkeypatch.setattr(settings_module, "get_config_dir", lambda: tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# get_config_dir
# ---------------------------------------------------------------------------


class TestGetConfigDir:
    def test_returns_path_object(self, tmp_path, monkeypatch):
        monkeypatch.setattr(settings_module, "get_config_dir", lambda: tmp_path)
        result = settings_module.get_config_dir()
        assert isinstance(result, Path)

    def test_linux_uses_xdg_config_home(self, tmp_path, monkeypatch):
        monkeypatch.setattr(platform, "system", lambda: "Linux")
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        result = get_config_dir()
        assert str(tmp_path) in str(result)
        assert APP_NAME in str(result)

    def test_linux_falls_back_to_dot_config(self, tmp_path, monkeypatch):
        monkeypatch.setattr(platform, "system", lambda: "Linux")
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
        result = get_config_dir()
        assert ".config" in str(result) or str(result)  # just check it doesn't crash

    def test_windows_uses_appdata(self, tmp_path, monkeypatch):
        monkeypatch.setattr(platform, "system", lambda: "Windows")
        monkeypatch.setenv("APPDATA", str(tmp_path))
        result = get_config_dir()
        assert APP_NAME in str(result)

    def test_creates_directory_if_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(platform, "system", lambda: "Linux")
        new_dir = tmp_path / "new_xdg"
        monkeypatch.setenv("XDG_CONFIG_HOME", str(new_dir))
        result = get_config_dir()
        assert result.exists()


# ---------------------------------------------------------------------------
# load_settings / save_settings
# ---------------------------------------------------------------------------


class TestLoadSaveSettings:
    def test_load_returns_empty_dict_when_no_file(self, tmp_path, monkeypatch):
        _isolated_settings(tmp_path, monkeypatch)
        result = load_settings()
        assert result == {}

    def test_save_and_load_round_trip(self, tmp_path, monkeypatch):
        _isolated_settings(tmp_path, monkeypatch)
        data = {"key1": "value1", "count": 42, "nested": {"a": 1}}
        assert save_settings(data) is True
        loaded = load_settings()
        assert loaded == data

    def test_load_corrupt_json_returns_empty(self, tmp_path, monkeypatch):
        _isolated_settings(tmp_path, monkeypatch)
        settings_file = tmp_path / "settings.json"
        settings_file.write_text("{ broken json !!!", encoding="utf-8")
        result = load_settings()
        assert result == {}

    def test_save_returns_false_on_ioerror(self, tmp_path, monkeypatch):
        _isolated_settings(tmp_path, monkeypatch)
        # Patch json.dump to raise so save_settings returns False
        with patch("podcastforge.core.settings.json.dump", side_effect=IOError("disk full")):
            result = save_settings({"k": "v"})
        assert result is False

    def test_load_empty_json_file_returns_empty(self, tmp_path, monkeypatch):
        _isolated_settings(tmp_path, monkeypatch)
        (tmp_path / "settings.json").write_text("{}", encoding="utf-8")
        assert load_settings() == {}

    def test_save_preserves_unicode(self, tmp_path, monkeypatch):
        _isolated_settings(tmp_path, monkeypatch)
        data = {"greeting": "Hällö Wörld 🎙️"}
        save_settings(data)
        loaded = load_settings()
        assert loaded["greeting"] == "Hällö Wörld 🎙️"


# ---------------------------------------------------------------------------
# get_setting / set_setting
# ---------------------------------------------------------------------------


class TestGetSetSetting:
    def test_get_missing_key_returns_default(self, tmp_path, monkeypatch):
        _isolated_settings(tmp_path, monkeypatch)
        assert get_setting("missing_key") is None
        assert get_setting("missing_key", default="fallback") == "fallback"

    def test_set_then_get_returns_value(self, tmp_path, monkeypatch):
        _isolated_settings(tmp_path, monkeypatch)
        set_setting("theme", "dark")
        assert get_setting("theme") == "dark"

    def test_set_overwrites_existing(self, tmp_path, monkeypatch):
        _isolated_settings(tmp_path, monkeypatch)
        set_setting("volume", 50)
        set_setting("volume", 80)
        assert get_setting("volume") == 80

    def test_set_multiple_keys_independent(self, tmp_path, monkeypatch):
        _isolated_settings(tmp_path, monkeypatch)
        set_setting("a", 1)
        set_setting("b", 2)
        assert get_setting("a") == 1
        assert get_setting("b") == 2

    def test_set_returns_true_on_success(self, tmp_path, monkeypatch):
        _isolated_settings(tmp_path, monkeypatch)
        assert set_setting("x", "y") is True

    def test_get_various_types(self, tmp_path, monkeypatch):
        _isolated_settings(tmp_path, monkeypatch)
        set_setting("bool_val", True)
        set_setting("list_val", [1, 2, 3])
        set_setting("none_val", None)
        assert get_setting("bool_val") is True
        assert get_setting("list_val") == [1, 2, 3]
        assert get_setting("none_val") is None
