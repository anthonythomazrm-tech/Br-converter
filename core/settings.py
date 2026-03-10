from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path


def _default_config_dir() -> Path:
    # Windows: %LOCALAPPDATA%\BRConverter
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "BRConverter"
    # Linux/Mac fallback
    return Path.home() / ".br_converter"


@dataclass
class AppSettings:
    # Se vazio, usa fallback automático (pasta "BR_Converter" no home)
    default_output_dir: str = ""
    name_template: str = "{name}_convertido"  # sem extensão
    default_use_subfolder: bool = False
    default_subfolder_name: str = "Convertidos"

    @staticmethod
    def config_path() -> Path:
        return _default_config_dir() / "config.json"

    @classmethod
    def load(cls) -> "AppSettings":
        path = cls.config_path()
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            s = cls()
            for k, v in data.items():
                if hasattr(s, k):
                    setattr(s, k, v)
            return s
        except Exception:
            # Se quebrar config, não trava o app
            return cls()

    def save(self) -> None:
        path = self.config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(asdict(self), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )


# =========================
# INSTÂNCIA GLOBAL (IMPORTA)
# =========================
settings = AppSettings.load()


def get_default_output_dir_fallback() -> str:
    """
    Fallback caso settings.default_output_dir esteja vazio.
    """
    return str(Path.home() / "BR_Converter")


def get_effective_default_output_dir() -> str:
    """
    Retorna a pasta padrão efetiva:
    - se o usuário configurou, usa ela
    - se não, usa fallback automático
    """
    d = (settings.default_output_dir or "").strip()
    return d if d else get_default_output_dir_fallback()