import os
from typing import List
from PyPDF2 import PdfMerger

def merge_pdfs(pdf_paths: List[str], out_pdf: str):
    merger = PdfMerger()
    for p in pdf_paths:
        merger.append(p)
    os.makedirs(os.path.dirname(out_pdf), exist_ok=True)
    merger.write(out_pdf)
    merger.close()
