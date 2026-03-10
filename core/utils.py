import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

def safe_mkdir(path: str):
    Path(path).mkdir(parents=True, exist_ok=True)

def open_folder(path: str):
    try:
        if os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
        elif os.name == "posix":
            subprocess.Popen(["xdg-open", path])
        else:
            subprocess.Popen(["open", path])
    except Exception:
        pass

def temp_dir(prefix: str = "brc_") -> str:
    return tempfile.mkdtemp(prefix=prefix)

def which(exe_name: str) -> Optional[str]:
    return shutil.which(exe_name)
