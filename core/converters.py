import os
from typing import List, Callable, Optional
from pathlib import Path

from PIL import Image
from pdf2docx import Converter as Pdf2DocxConverter
from docx2pdf import convert as docx2pdf_convert

from core.merge import merge_pdfs
from core.utils import safe_mkdir, temp_dir, which

# ✅ Novos imports
from core.output_paths import resolve_output_dir, build_out_path
from core.docx_cleanup import cleanup_docx_paragraphs
from core.docx_formlines import fix_form_lines_in_docx, looks_like_form_docx

ProgressCb = Callable[[int, int, str], None]  # current, total, message
LogCb = Callable[[str], None]


def _log(log_cb: Optional[LogCb], msg: str):
    if log_cb:
        log_cb(msg)


def _progress(progress_cb: Optional[ProgressCb], cur: int, total: int, msg: str):
    if progress_cb:
        progress_cb(cur, total, msg)


def images_to_single_pdf(images: List[str], out_pdf: str, log_cb=None):
    safe_mkdir(os.path.dirname(out_pdf))
    pil_images = []
    for p in images:
        img = Image.open(p).convert("RGB")
        pil_images.append(img)
    first, rest = pil_images[0], pil_images[1:]
    first.save(out_pdf, save_all=True, append_images=rest)
    _log(log_cb, f"✅ PDF criado: {out_pdf}")


def images_to_pdfs(
    images: List[str],
    out_dir: str,
    same_folder: bool = False,
    progress_cb=None,
    log_cb=None,
):
    # out_dir só é obrigatório se same_folder=False (o UI deve garantir)
    if not same_folder:
        safe_mkdir(out_dir)

    total = len(images)
    for i, p in enumerate(images, 1):
        name = Path(p).stem
        dest_dir = resolve_output_dir(p, out_dir, same_folder)
        safe_mkdir(dest_dir)

        out_pdf = os.path.join(dest_dir, f"{name}.pdf")
        _progress(progress_cb, i, total, f"Imagem→PDF: {name}")
        images_to_single_pdf([p], out_pdf, log_cb=log_cb)


def pdf_to_docx(pdf_path: str, out_docx: str, log_cb=None):
    safe_mkdir(os.path.dirname(out_docx))
    cv = Pdf2DocxConverter(pdf_path)
    try:
        cv.convert(out_docx)
    finally:
        cv.close()

    # ✅ Premium texto (sempre): corrige quebra de linhas/parágrafos
    cleanup_docx_paragraphs(out_docx)

    # ✅ Auto-detect formulário: só aplica se tiver cara de ficha
    # threshold=6 é um bom padrão pra não "inventar" em PDFs normais
    if looks_like_form_docx(out_docx, threshold=6):
        # default_answer_lines é fallback; no seu docx_formlines você pode recriar pelo "removed"
        fix_form_lines_in_docx(out_docx, default_answer_lines=6, aggressive=True)
        _log(log_cb, "🧠 Formulário detectado: linhas recriadas automaticamente.")

    _log(log_cb, f"✅ DOCX criado: {out_docx}")


def pdfs_to_docx(
    pdfs: List[str],
    out_dir: str,
    same_folder: bool = False,
    progress_cb=None,
    log_cb=None,
):
    if not same_folder:
        safe_mkdir(out_dir)

    total = len(pdfs)
    for i, p in enumerate(pdfs, 1):
        name = Path(p).stem
        dest_dir = resolve_output_dir(p, out_dir, same_folder)
        safe_mkdir(dest_dir)

        out_docx = os.path.join(dest_dir, f"{name}.docx")
        _progress(progress_cb, i, total, f"PDF→DOCX: {name}")
        pdf_to_docx(p, out_docx, log_cb=log_cb)


def docx_to_pdf(docx_path: str, out_pdf: str, log_cb=None):
    safe_mkdir(os.path.dirname(out_pdf))
    docx2pdf_convert(docx_path, out_pdf)
    _log(log_cb, f"✅ PDF criado: {out_pdf}")


def docxs_to_pdfs(
    docxs: List[str],
    out_dir: str,
    same_folder: bool = False,
    progress_cb=None,
    log_cb=None,
):
    if not same_folder:
        safe_mkdir(out_dir)

    total = len(docxs)
    for i, p in enumerate(docxs, 1):
        name = Path(p).stem
        dest_dir = resolve_output_dir(p, out_dir, same_folder)
        safe_mkdir(dest_dir)

        out_pdf = os.path.join(dest_dir, f"{name}.pdf")
        _progress(progress_cb, i, total, f"DOCX→PDF: {name}")
        docx_to_pdf(p, out_pdf, log_cb=log_cb)


def docxs_to_single_pdf(docxs: List[str], out_pdf: str, progress_cb=None, log_cb=None):
    work = temp_dir("brc_docx_merge_")
    tmp_pdfs = []
    total = len(docxs)

    for i, p in enumerate(docxs, 1):
        name = Path(p).stem
        tmp = os.path.join(work, f"{name}.pdf")
        _progress(progress_cb, i, total, f"DOCX→PDF (temp): {name}")
        docx_to_pdf(p, tmp, log_cb=log_cb)
        tmp_pdfs.append(tmp)

    _log(log_cb, "🔗 Unindo PDFs temporários...")
    safe_mkdir(os.path.dirname(out_pdf))
    merge_pdfs(tmp_pdfs, out_pdf)
    _log(log_cb, f"✅ PDF único criado: {out_pdf}")


def merge_pdfs_direct(pdfs: List[str], out_pdf: str, progress_cb=None, log_cb=None):
    _progress(progress_cb, 1, 1, "Unindo PDFs...")
    safe_mkdir(os.path.dirname(out_pdf))
    merge_pdfs(pdfs, out_pdf)
    _log(log_cb, f"✅ PDF único criado: {out_pdf}")


def xlsx_to_pdf_via_excel(xlsx_path: str, out_pdf: str, log_cb=None):
    safe_mkdir(os.path.dirname(out_pdf))
    try:
        import win32com.client  # type: ignore
    except Exception as e:
        raise RuntimeError("Para XLSX→PDF via Excel, instale: pip install pywin32") from e

    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    wb = None
    try:
        wb = excel.Workbooks.Open(os.path.abspath(xlsx_path))
        wb.ExportAsFixedFormat(0, os.path.abspath(out_pdf))  # 0 = PDF
    finally:
        if wb is not None:
            wb.Close(False)
        excel.Quit()
    _log(log_cb, f"✅ PDF criado: {out_pdf}")


def xlsx_to_pdf_via_libreoffice(xlsx_path: str, out_dir: str, log_cb=None):
    soffice = which("soffice") or which("libreoffice")
    if not soffice:
        raise RuntimeError("LibreOffice não encontrado. Instale LibreOffice ou use Excel+pywin32.")
    safe_mkdir(out_dir)
    import subprocess
    subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", out_dir, xlsx_path], check=True)
    _log(log_cb, f"✅ PDF criado via LibreOffice em: {out_dir}")