"""
Persistent user configuration management for ollama-web.
Stores defaults in ~/.config/ollama-web/config.json (or %APPDATA%/ollama-web/config.json on Windows).
"""

import os
import sys
import json
from pathlib import Path

def get_config_dir() -> Path:
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    cfg_dir = base / "ollama-web"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    return cfg_dir

def get_config_file() -> Path:
    return get_config_dir() / "config.json"

DEFAULT_CONFIG = {
    "default_model": None,
    "search_mode": "auto",
    "num_ctx": 16384,
    "max_search_results": 5,
    "voice_enabled": True,
    "voice_engine": "edge",
    "first_run_completed": False,
    "api_keys": {}
}

def load_config() -> dict:
    cfg_file = get_config_file()
    if not cfg_file.exists():
        return dict(DEFAULT_CONFIG)
    try:
        with open(cfg_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            merged = dict(DEFAULT_CONFIG)
            merged.update(data)
            return merged
    except Exception:
        return dict(DEFAULT_CONFIG)

def save_config(cfg: dict) -> None:
    cfg_file = get_config_file()
    try:
        with open(cfg_file, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print(f"[!] Warning: Could not save config to {cfg_file}: {e}", file=sys.stderr)
