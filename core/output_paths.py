import os
from pathlib import Path
from typing import Optional

from .settings import get_effective_default_output_dir


def resolve_output_dir(
    input_path: str,
    chosen_out_dir: Optional[str],
    same_folder: bool,
    create_subfolder: bool = False,
    subfolder_name: str = "convertidos",
) -> str:
    """
    Decide o diretório final de saída.

    - same_folder=True  => pasta do arquivo original
    - same_folder=False => pasta escolhida OU pasta padrão (fallback)
    - create_subfolder  => cria subpasta dentro do diretório base
    """

    if same_folder:
        base_dir = Path(input_path).parent
    else:
        if chosen_out_dir and chosen_out_dir.strip():
            base_dir = Path(chosen_out_dir.strip())
        else:
            base_dir = Path(get_effective_default_output_dir())

    if create_subfolder:
        name = (subfolder_name or "").strip() or "convertidos"
        base_dir = base_dir / name

    base_dir.mkdir(parents=True, exist_ok=True)
    return str(base_dir)


def build_out_path(
    input_path: str,
    out_dir: str,
    new_ext: str,
    new_name: Optional[str] = None,
) -> str:
    """
    Monta caminho de saída trocando extensão e (opcionalmente) o nome.
    """
    ext = new_ext.lstrip(".")
    name = (new_name or "").strip() or Path(input_path).stem
    return os.path.join(out_dir, f"{name}.{ext}")


def ensure_dir(path: str) -> None:
    """
    Garante que o diretório exista. (compat)
    """
    Path(path).mkdir(parents=True, exist_ok=True)