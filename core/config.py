import json
import os
from pathlib import Path

def _default_config_dir(app_name: str) -> Path:
    # Windows: %APPDATA%\AppName
    # Outros: ~/.config/AppName
    appdata = os.getenv("APPDATA")
    if appdata:
        return Path(appdata) / app_name
    return Path.home() / ".config" / app_name

def _default_documents_dir(app_name: str) -> Path:
    docs = Path.home() / "Documents"
    out = docs / app_name
    out.mkdir(parents=True, exist_ok=True)
    return out

class ConfigStore:
    def __init__(self, app_name: str):
        self.app_name = app_name
        self.dir = _default_config_dir(app_name)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.path = self.dir / "config.json"
        self.data = {}
        self._load_or_init()

    def _load_or_init(self):
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text(encoding="utf-8"))
                if not isinstance(self.data, dict):
                    self.data = {}
            except Exception:
                self.data = {}

        self.data.setdefault("theme", "dark")  # "dark" / "light"
        self.data.setdefault("first_run", True)
        self.data.setdefault("last_output_dir", str(_default_documents_dir(self.app_name)))
        self.data.setdefault("last_target", "PDF")  # PDF/DOCX/XLSX
        self.data.setdefault("last_merge", False)
        self.save()

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()

    def save(self):
        try:
            self.path.write_text(
                json.dumps(self.data, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
        except Exception:
            pass

