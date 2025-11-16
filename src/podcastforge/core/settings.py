"""
Persistente Einstellungen für PodcastForge

Dieses Modul speichert einfache Key-Value-Settings als JSON in einem
benutzerspezifischen Config-Verzeichnis (XDG on *nix, %APPDATA% on Windows).
"""

from __future__ import annotations

import json
import os
import platform
from pathlib import Path
from typing import Any, Dict, Optional


APP_NAME = "podcastforge"
SETTINGS_FILE = "settings.json"


def get_config_dir() -> Path:
    """Return the user config directory path for the application."""
    system = platform.system()
    if system == "Windows":
        base = os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")
    elif system == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")

    path = Path(base) / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def _settings_path() -> Path:
    return get_config_dir() / SETTINGS_FILE


def load_settings() -> Dict[str, Any]:
    """Load settings from disk. Returns empty dict if none present or on error."""
    p = _settings_path()
    if not p.exists():
        return {}
    try:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_settings(data: Dict[str, Any]) -> bool:
    """Save settings dict to disk. Returns True on success."""
    p = _settings_path()
    try:
        with p.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def get_setting(key: str, default: Optional[Any] = None) -> Any:
    settings = load_settings()
    return settings.get(key, default)


def set_setting(key: str, value: Any) -> bool:
    settings = load_settings()
    settings[key] = value
    return save_settings(settings)
