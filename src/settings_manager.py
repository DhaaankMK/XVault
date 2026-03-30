"""
X-Vault :: settings_manager.py
Gerencia configurações persistentes do aplicativo.
"""

import json
import os
from pathlib import Path

_CONFIG_DIR  = Path(os.getenv("APPDATA", "")) / "XVault"
_CONFIG_FILE = _CONFIG_DIR / "settings.json"

_DEFAULTS = {
    "theme": "dark",
    "language": "pt_BR",
    "auto_lock_minutes": 5,
    "panic_on_wrong_attempts": True,
    "show_tray_icon": True,
    "last_vault_label": "Meu Cofre",
    "first_run": True,
}


class SettingsManager:
    def __init__(self):
        _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    def _load(self) -> dict:
        if _CONFIG_FILE.exists():
            try:
                with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    return {**_DEFAULTS, **loaded}
            except Exception:
                pass
        return dict(_DEFAULTS)

    def save(self):
        with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value):
        self._data[key] = value
        self.save()

    def get_all(self) -> dict:
        return dict(self._data)
