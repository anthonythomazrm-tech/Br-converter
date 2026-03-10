from pathlib import Path
from typing import Iterable
from PIL import Image


def image_to_ico(image_path: str, out_ico_path: str, sizes: Iterable[int] = (16, 32, 48, 64, 128, 256)):
    """
    Converte PNG/JPG em ICO multi-tamanhos (bem profissional).
    """
    out = Path(out_ico_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    img = Image.open(image_path).convert("RGBA")
    ico_sizes = [(s, s) for s in sizes]

    # Pillow gera ICO com múltiplos tamanhos
    img.save(str(out), format="ICO", sizes=ico_sizes)


def image_resize_png(image_path: str, out_png_path: str, size: int = 512):
    """
    Gera PNG quadrado (útil pra capa/loja/app).
    """
    out = Path(out_png_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    img = Image.open(image_path).convert("RGBA")
    img = img.resize((size, size))
    img.save(str(out), format="PNG")