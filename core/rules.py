import os
from typing import List, Tuple, Set

IMG_EXTS: Set[str] = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff"}

def ext_lower(path: str) -> str:
    return os.path.splitext(path)[1].lower()

def classify_inputs(files: List[str]) -> Tuple[Set[str], int]:
    exts = {ext_lower(f) for f in files}
    return exts, len(files)

def merge_option_allowed(files: List[str], target: str) -> bool:
    """Regras do 'arquivo único' (merge) — aparece só quando faz sentido."""
    if len(files) < 2:
        return False

    exts, _ = classify_inputs(files)
    target = target.upper()

    if target != "PDF":
        return False

    if exts == {".pdf"}:
        return True

    if exts.issubset(IMG_EXTS) and len(exts) >= 1:
        return True

    if exts == {".docx"}:
        return True

    return False

def is_supported_combo(files: List[str], target: str) -> Tuple[bool, str]:
    if not files:
        return False, "Nenhum arquivo selecionado."

    exts, _ = classify_inputs(files)
    target = target.upper()

    if target == "DOCX":
        if exts == {".pdf"}:
            return True, ""
        return False, "Para DOCX, selecione apenas PDFs."

    if target == "PDF":
        if exts == {".docx"}:
            return True, ""
        if exts == {".pdf"}:
            return True, ""
        if exts.issubset(IMG_EXTS):
            return True, ""
        if exts == {".xlsx"}:
            return True, ""
        return False, "Para PDF, use apenas DOCX ou PDF ou imagens ou XLSX (um tipo por vez)."

    if target == "XLSX":
        return False, "XLSX ainda não está disponível nesta versão (evitar conversão ruim)."

    return False, "Formato de saída não reconhecido."

