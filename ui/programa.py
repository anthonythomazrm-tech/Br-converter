import os
import threading
import shutil
from pathlib import Path
from typing import List

import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from tkinter import filedialog

from core.config import ConfigStore
from core.rules import merge_option_allowed, is_supported_combo
from core.utils import open_folder, safe_mkdir
from core.converters import (
    images_to_single_pdf, images_to_pdfs,
    pdfs_to_docx,
    docxs_to_pdfs, docxs_to_single_pdf,
    merge_pdfs_direct,
    xlsx_to_pdf_via_excel, xlsx_to_pdf_via_libreoffice
)
from core.image_tools import image_to_ico, image_resize_png
from core.media_tools import extract_audio, audio_to_video_cover, compress_video

from ui.theme import toggle_theme_window

VERSION_TEXT = "v1.0 • Developed by Anthony"


class MainApp:
    def __init__(self, window: tb.Window, cfg: ConfigStore):
        self.window = window
        self.cfg = cfg

        self.files: List[str] = []
        self.is_working = False

        # Documentos
        self.target_var = tb.StringVar(value=cfg.get("last_target", "PDF"))
        self.merge_var = tb.BooleanVar(value=bool(cfg.get("last_merge", False)))
        self.output_dir_var = tb.StringVar(value=cfg.get("last_output_dir", ""))

        # Imagens -> Ícone
        self.icon_image_var = tb.StringVar(value="")
        self.icon_outname_var = tb.StringVar(value="app_icon")
        self.icon_make_png512_var = tb.BooleanVar(value=True)

        # Mídia
        self.video_in_var = tb.StringVar(value="")
        self.audio_out_fmt_var = tb.StringVar(value="mp3")

        self.audio_in_var = tb.StringVar(value="")
        self.cover_img_var = tb.StringVar(value="")

        self.compress_in_var = tb.StringVar(value="")
        self.compress_quality_var = tb.StringVar(value="media")
        self.compress_res_var = tb.StringVar(value="720p")

        # Status
        self.status_var = tb.StringVar(value="Pronto.")
        self.progress_var = tb.IntVar(value=0)

        # widgets
        self.listbox_docs = None
        self.merge_check = None
        self.btn_convert = None
        self.progress = None
        self.log_text = None

    def mount(self):
        root = tb.Frame(self.window, padding=18)
        root.pack(fill=BOTH, expand=YES)

        # HEADER
        header = tb.Frame(root)
        header.pack(fill=X)

        left = tb.Frame(header)
        left.pack(side=LEFT, anchor=W)

        tb.Label(left, text="BR Converter", font=("Segoe UI", 18, "bold")).pack(anchor=W)
        tb.Label(left, text="Documentos • Imagens • Mídia", font=("Segoe UI", 10)).pack(anchor=W)

        tb.Button(
            header,
            text="🌙/☀️ Tema",
            bootstyle=SECONDARY,
            command=lambda: toggle_theme_window(self.window, self.cfg),
        ).pack(side=RIGHT)

        # NOTEBOOK (abas)
        nb = tb.Notebook(root, bootstyle=SECONDARY)
        nb.pack(fill=BOTH, expand=YES, pady=(14, 0))

        tab_docs = tb.Frame(nb, padding=12)
        tab_imgs = tb.Frame(nb, padding=12)
        tab_media = tb.Frame(nb, padding=12)

        nb.add(tab_docs, text="📄 Documentos")
        nb.add(tab_imgs, text="🖼 Imagens")
        nb.add(tab_media, text="🎬 Mídia")

        # Build tabs
        self._build_docs_tab(tab_docs)
        self._build_images_tab(tab_imgs)
        self._build_media_tab(tab_media)

        # FOOTER (status + logs)
        footer = tb.Labelframe(root, text="Status", padding=12, bootstyle=SECONDARY)
        footer.pack(fill=BOTH, expand=YES, pady=(12, 0))

        self.progress = tb.Progressbar(footer, maximum=100, variable=self.progress_var, bootstyle=INFO)
        self.progress.pack(fill=X)

        tb.Label(footer, textvariable=self.status_var).pack(anchor=W, pady=(6, 0))

        self.log_text = tk.Text(footer, height=10, wrap="word", bd=0, highlightthickness=0)
        self.log_text.pack(fill=BOTH, expand=YES, pady=(10, 0))
        self.log_text.configure(state="disabled")

        foot2 = tb.Frame(root)
        foot2.pack(fill=X, pady=(8, 0))
        tb.Label(foot2, text=VERSION_TEXT).pack(side=LEFT)

        # defaults
        if not self.output_dir_var.get():
            default = str(Path.home() / "Documents" / "BR Converter")
            safe_mkdir(default)
            self.output_dir_var.set(default)
            self.cfg.set("last_output_dir", default)

        self._refresh_merge_visibility()

    # ---------------------- TAB: DOCUMENTOS ----------------------
    def _build_docs_tab(self, parent: tb.Frame):
        row = tb.Frame(parent)
        row.pack(fill=BOTH, expand=YES)

        col_left = tb.Frame(row)
        col_right = tb.Frame(row)
        col_left.pack(side=LEFT, fill=BOTH, expand=YES, padx=(0, 10))
        col_right.pack(side=RIGHT, fill=BOTH, expand=YES)

        card_files = tb.Labelframe(col_left, text="Arquivos", padding=12, bootstyle=SECONDARY)
        card_files.pack(fill=BOTH, expand=YES)

        actions = tb.Frame(card_files)
        actions.pack(fill=X, pady=(0, 10))

        tb.Button(actions, text="Selecionar arquivos", bootstyle=PRIMARY, command=self.pick_files).pack(side=LEFT)
        tb.Button(actions, text="Remover selecionado", bootstyle=WARNING, command=self.remove_selected).pack(side=LEFT, padx=8)
        tb.Button(actions, text="Limpar lista", bootstyle=SECONDARY, command=self.clear_files).pack(side=LEFT)

        self.listbox_docs = tk.Listbox(card_files, height=14, bd=0, highlightthickness=0)
        self.listbox_docs.pack(fill=BOTH, expand=YES)

        # CONFIG
        card_cfg = tb.Labelframe(col_right, text="Configurações", padding=12, bootstyle=SECONDARY)
        card_cfg.pack(fill=X)

        row1 = tb.Frame(card_cfg)
        row1.pack(fill=X, pady=(0, 10))

        tb.Label(row1, text="Converter para:").pack(side=LEFT)
        cb = tb.Combobox(row1, textvariable=self.target_var, values=["PDF", "DOCX", "XLSX"], state="readonly", width=10)
        cb.pack(side=LEFT, padx=10)
        cb.bind("<<ComboboxSelected>>", lambda e: self._on_target_change())

        self.merge_check = tb.Checkbutton(
            card_cfg,
            text="Converter em um arquivo único (merge)",
            variable=self.merge_var,
            bootstyle="round-toggle",
            command=self._on_merge_change
        )
        self.merge_check.pack(anchor=W, pady=(0, 10))

        row2 = tb.Frame(card_cfg)
        row2.pack(fill=X)

        tb.Label(row2, text="Salvar no:").pack(side=LEFT)
        tb.Entry(row2, textvariable=self.output_dir_var).pack(side=LEFT, fill=X, expand=YES, padx=8)
        tb.Button(row2, text="Procurar", bootstyle=SECONDARY, command=self.pick_dir).pack(side=LEFT)

        # ACTIONS
        card_run = tb.Labelframe(col_right, text="Ações", padding=12, bootstyle=SECONDARY)
        card_run.pack(fill=BOTH, expand=YES, pady=(12, 0))

        run_row = tb.Frame(card_run)
        run_row.pack(fill=X)

        self.btn_convert = tb.Button(run_row, text="Converter", bootstyle=SUCCESS, command=self.run_convert)
        self.btn_convert.pack(side=LEFT)

        tb.Button(run_row, text="Abrir pasta de destino", bootstyle=SECONDARY, command=self.open_dest).pack(side=LEFT, padx=10)

        hint = tb.Label(
            card_run,
            text="Dica: para DOCX→PDF no Windows, geralmente precisa do Microsoft Word instalado.",
            bootstyle="secondary"
        )
        hint.pack(anchor=W, pady=(12, 0))

    # ---------------------- TAB: IMAGENS ----------------------
    def _build_images_tab(self, parent: tb.Frame):
        card = tb.Labelframe(parent, text="Imagem → Ícone / PNG", padding=12, bootstyle=SECONDARY)
        card.pack(fill=BOTH, expand=YES)

        row1 = tb.Frame(card)
        row1.pack(fill=X, pady=(0, 10))

        tb.Label(row1, text="Imagem (PNG/JPG):").pack(side=LEFT)
        tb.Entry(row1, textvariable=self.icon_image_var).pack(side=LEFT, fill=X, expand=YES, padx=8)
        tb.Button(row1, text="Procurar", bootstyle=SECONDARY, command=self.pick_icon_image).pack(side=LEFT)

        row2 = tb.Frame(card)
        row2.pack(fill=X, pady=(0, 10))

        tb.Label(row2, text="Nome do arquivo (sem extensão):").pack(side=LEFT)
        tb.Entry(row2, textvariable=self.icon_outname_var, width=20).pack(side=LEFT, padx=8)

        tb.Checkbutton(
            row2,
            text="Gerar PNG 512x512 também",
            variable=self.icon_make_png512_var,
            bootstyle="round-toggle"
        ).pack(side=LEFT, padx=8)

        row3 = tb.Frame(card)
        row3.pack(fill=X)

        tb.Button(row3, text="Criar Ícone (.ico)", bootstyle=SUCCESS, command=self.run_image_to_ico).pack(side=LEFT)
        tb.Button(row3, text="Abrir pasta de destino", bootstyle=SECONDARY, command=self.open_dest).pack(side=LEFT, padx=10)

        tb.Label(
            card,
            text="Gera um .ico com múltiplos tamanhos (16–256). Ideal pra .exe e atalhos.",
            bootstyle="secondary"
        ).pack(anchor=W, pady=(12, 0))

    # ---------------------- TAB: MÍDIA ----------------------
    def _build_media_tab(self, parent: tb.Frame):
        # Extrair áudio
        card1 = tb.Labelframe(parent, text="Vídeo → Música (Extrair áudio)", padding=12, bootstyle=SECONDARY)
        card1.pack(fill=X)

        r1 = tb.Frame(card1)
        r1.pack(fill=X, pady=(0, 10))
        tb.Label(r1, text="Vídeo:").pack(side=LEFT)
        tb.Entry(r1, textvariable=self.video_in_var).pack(side=LEFT, fill=X, expand=YES, padx=8)
        tb.Button(r1, text="Procurar", bootstyle=SECONDARY, command=self.pick_video).pack(side=LEFT)

        r2 = tb.Frame(card1)
        r2.pack(fill=X)
        tb.Label(r2, text="Formato:").pack(side=LEFT)
        tb.Combobox(r2, textvariable=self.audio_out_fmt_var, values=["mp3", "wav", "m4a"], state="readonly", width=8).pack(side=LEFT, padx=8)
        tb.Button(r2, text="Extrair", bootstyle=SUCCESS, command=self.run_extract_audio).pack(side=LEFT)
        tb.Button(r2, text="Abrir pasta", bootstyle=SECONDARY, command=self.open_dest).pack(side=LEFT, padx=10)

        # Música -> vídeo (capa)
        card2 = tb.Labelframe(parent, text="Música → Vídeo (capa + áudio)", padding=12, bootstyle=SECONDARY)
        card2.pack(fill=X, pady=(12, 0))

        a1 = tb.Frame(card2)
        a1.pack(fill=X, pady=(0, 10))
        tb.Label(a1, text="Áudio (mp3/wav/m4a):").pack(side=LEFT)
        tb.Entry(a1, textvariable=self.audio_in_var).pack(side=LEFT, fill=X, expand=YES, padx=8)
        tb.Button(a1, text="Procurar", bootstyle=SECONDARY, command=self.pick_audio).pack(side=LEFT)

        a2 = tb.Frame(card2)
        a2.pack(fill=X, pady=(0, 10))
        tb.Label(a2, text="Imagem (capa):").pack(side=LEFT)
        tb.Entry(a2, textvariable=self.cover_img_var).pack(side=LEFT, fill=X, expand=YES, padx=8)
        tb.Button(a2, text="Procurar", bootstyle=SECONDARY, command=self.pick_cover).pack(side=LEFT)

        a3 = tb.Frame(card2)
        a3.pack(fill=X)
        tb.Button(a3, text="Criar vídeo (.mp4)", bootstyle=SUCCESS, command=self.run_audio_to_video).pack(side=LEFT)
        tb.Button(a3, text="Abrir pasta", bootstyle=SECONDARY, command=self.open_dest).pack(side=LEFT, padx=10)

        # Comprimir vídeo
        card3 = tb.Labelframe(parent, text="Comprimir vídeo (reduzir tamanho)", padding=12, bootstyle=SECONDARY)
        card3.pack(fill=X, pady=(12, 0))

        c1 = tb.Frame(card3)
        c1.pack(fill=X, pady=(0, 10))
        tb.Label(c1, text="Vídeo:").pack(side=LEFT)
        tb.Entry(c1, textvariable=self.compress_in_var).pack(side=LEFT, fill=X, expand=YES, padx=8)
        tb.Button(c1, text="Procurar", bootstyle=SECONDARY, command=self.pick_compress_video).pack(side=LEFT)

        c2 = tb.Frame(card3)
        c2.pack(fill=X)
        tb.Label(c2, text="Qualidade:").pack(side=LEFT)
        tb.Combobox(c2, textvariable=self.compress_quality_var, values=["alta", "media", "baixa"], state="readonly", width=8).pack(side=LEFT, padx=8)
        tb.Label(c2, text="Resolução:").pack(side=LEFT, padx=(18, 0))
        tb.Combobox(c2, textvariable=self.compress_res_var, values=["keep", "1080p", "720p", "480p"], state="readonly", width=8).pack(side=LEFT, padx=8)

        tb.Button(c2, text="Comprimir", bootstyle=SUCCESS, command=self.run_compress_video).pack(side=LEFT, padx=(12, 0))
        tb.Button(c2, text="Abrir pasta", bootstyle=SECONDARY, command=self.open_dest).pack(side=LEFT, padx=10)

        tb.Label(
            parent,
            text="Obs: Para ferramentas de mídia, o FFmpeg precisa estar instalado (ou embutido no app).",
            bootstyle="secondary"
        ).pack(anchor=W, pady=(10, 0))

    # ---------------------- LOG / STATUS ----------------------
    def _log(self, msg: str):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _set_status(self, msg: str):
        self.status_var.set(msg)

    def _progress_cb(self, cur: int, total: int, msg: str):
        pct = 0 if total <= 0 else int((cur / total) * 100)
        self.progress_var.set(pct)
        self._set_status(f"{msg} ({cur}/{total})")

    def _run_on_ui(self, fn):
        self.window.after(0, fn)

    def _ui_log(self, msg: str):
        self._run_on_ui(lambda: self._log(msg))

    def _ui_progress(self, cur: int, total: int, msg: str):
        self._run_on_ui(lambda: self._progress_cb(cur, total, msg))

    def _unlock_ui(self):
        self.is_working = False
        if self.btn_convert:
            self.btn_convert.configure(state="normal")
        self.progress_var.set(0)
        self._set_status("Pronto.")

    # ---------------------- DOCUMENTOS actions ----------------------
    def pick_files(self):
        if self.is_working:
            return
        paths = filedialog.askopenfilenames(title="Selecione arquivos")
        if not paths:
            return
        self.files = list(paths)
        self._render_files()
        self._refresh_merge_visibility()

    def _render_files(self):
        self.listbox_docs.delete(0, "end")
        for p in self.files:
            self.listbox_docs.insert("end", p)

    def remove_selected(self):
        if self.is_working:
            return
        sel = list(self.listbox_docs.curselection())
        if not sel:
            return
        for idx in reversed(sel):
            self.files.pop(idx)
        self._render_files()
        self._refresh_merge_visibility()

    def clear_files(self):
        if self.is_working:
            return
        self.files = []
        self._render_files()
        self._refresh_merge_visibility()

    def pick_dir(self):
        if self.is_working:
            return
        d = filedialog.askdirectory(title="Escolha a pasta de destino")
        if not d:
            return
        self.output_dir_var.set(d)
        self.cfg.set("last_output_dir", d)

    def open_dest(self):
        d = self.output_dir_var.get().strip()
        if d:
            open_folder(d)

    def _on_target_change(self):
        self.cfg.set("last_target", self.target_var.get())
        self._refresh_merge_visibility()

    def _on_merge_change(self):
        self.cfg.set("last_merge", bool(self.merge_var.get()))

    def _refresh_merge_visibility(self):
        allowed = merge_option_allowed(self.files, self.target_var.get())
        if allowed:
            self.merge_check.pack(anchor=W, pady=(0, 10))
        else:
            self.merge_var.set(False)
            try:
                self.merge_check.pack_forget()
            except Exception:
                pass

    def run_convert(self):
        if self.is_working:
            return

        ok, reason = is_supported_combo(self.files, self.target_var.get())
        if not ok:
            Messagebox.show_warning(reason, "Não suportado")
            return

        out_dir = self.output_dir_var.get().strip()
        if not out_dir:
            out_dir = str(Path.home() / "Documents" / "BR Converter")
            safe_mkdir(out_dir)
            self.output_dir_var.set(out_dir)

        safe_mkdir(out_dir)
        self.cfg.set("last_output_dir", out_dir)
        self.cfg.set("last_target", self.target_var.get())
        self.cfg.set("last_merge", bool(self.merge_var.get()))

        self.is_working = True
        self.btn_convert.configure(state="disabled")
        self.progress_var.set(0)
        self._set_status("Iniciando...")
        self._log("🚀 Iniciando conversão...")

        th = threading.Thread(
            target=self._convert_worker,
            args=(self.files[:], self.target_var.get(), bool(self.merge_var.get()), out_dir),
            daemon=True
        )
        th.start()

    def _convert_worker(self, files: List[str], target: str, do_merge: bool, out_dir: str):
        try:
            target_u = target.upper()
            ext = Path(files[0]).suffix.lower()

            if target_u == "DOCX":
                self._ui_log("🔁 PDF → DOCX")
                pdfs_to_docx(files, out_dir, progress_cb=self._ui_progress, log_cb=self._ui_log)

            elif target_u == "PDF":
                if ext == ".pdf":
                    if do_merge and len(files) >= 2:
                        out_pdf = os.path.join(out_dir, "BR_Converter_merged.pdf")
                        self._ui_log("🔗 Unindo PDFs em um único arquivo...")
                        merge_pdfs_direct(files, out_pdf, progress_cb=self._ui_progress, log_cb=self._ui_log)
                    else:
                        self._ui_log("ℹ️ PDFs selecionados (sem merge). Copiando para a pasta...")
                        total = len(files)
                        for i, p in enumerate(files, 1):
                            name = Path(p).name
                            dst = os.path.join(out_dir, name)
                            self._ui_progress(i, total, f"Copiando: {name}")
                            shutil.copy2(p, dst)
                        self._ui_log("✅ Copiados com sucesso.")

                elif ext == ".docx":
                    if do_merge and len(files) >= 2:
                        out_pdf = os.path.join(out_dir, "BR_Converter_merged.pdf")
                        self._ui_log("🔁 DOCX → PDF (merge em 1 arquivo)")
                        docxs_to_single_pdf(files, out_pdf, progress_cb=self._ui_progress, log_cb=self._ui_log)
                    else:
                        self._ui_log("🔁 DOCX → PDF")
                        docxs_to_pdfs(files, out_dir, progress_cb=self._ui_progress, log_cb=self._ui_log)

                elif ext in (".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff"):
                    if do_merge and len(files) >= 2:
                        out_pdf = os.path.join(out_dir, "BR_Converter_images.pdf")
                        self._ui_log("🖼️ Imagens → PDF único")
                        self._ui_progress(1, 1, "Gerando PDF único...")
                        images_to_single_pdf(files, out_pdf, log_cb=self._ui_log)
                        self._ui_progress(1, 1, "Concluído")
                    else:
                        self._ui_log("🖼️ Imagens → PDFs")
                        images_to_pdfs(files, out_dir, progress_cb=self._ui_progress, log_cb=self._ui_log)

                elif ext == ".xlsx":
                    self._ui_log("📊 XLSX → PDF (opcional)")
                    total = len(files)
                    for i, p in enumerate(files, 1):
                        name = Path(p).stem
                        out_pdf = os.path.join(out_dir, f"{name}.pdf")
                        self._ui_progress(i, total, f"XLSX→PDF: {name}")
                        try:
                            xlsx_to_pdf_via_excel(p, out_pdf, log_cb=self._ui_log)
                        except Exception:
                            xlsx_to_pdf_via_libreoffice(p, out_dir, log_cb=self._ui_log)
                    self._ui_log("✅ XLSX→PDF concluído.")

            self._ui_log("🎉 Conversão concluída!")
            self._run_on_ui(lambda: Messagebox.show_info("Conversão concluída!", "Sucesso"))

        except Exception as e:
            self._ui_log(f"❌ Erro: {e}")
            self._run_on_ui(lambda: Messagebox.show_error(str(e), "Erro"))
        finally:
            self._run_on_ui(self._unlock_ui)

    # ---------------------- IMAGENS: ÍCONE ----------------------
    def pick_icon_image(self):
        p = filedialog.askopenfilename(
            title="Selecione uma imagem",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.webp *.bmp *.tiff")]
        )
        if p:
            self.icon_image_var.set(p)

    def run_image_to_ico(self):
        if self.is_working:
            return
        img = self.icon_image_var.get().strip()
        if not img or not os.path.exists(img):
            Messagebox.show_warning("Selecione uma imagem válida.", "Imagem → Ícone")
            return

        out_dir = self.output_dir_var.get().strip()
        if not out_dir:
            out_dir = str(Path.home() / "Documents" / "BR Converter")
            safe_mkdir(out_dir)
            self.output_dir_var.set(out_dir)

        name = (self.icon_outname_var.get().strip() or "app_icon")
        out_ico = os.path.join(out_dir, f"{name}.ico")
        out_png = os.path.join(out_dir, f"{name}_512.png")

        def worker():
            try:
                self._ui_log("🖼️ Criando ícone .ico...")
                self._ui_progress(1, 2, "Gerando ICO...")
                image_to_ico(img, out_ico)

                if self.icon_make_png512_var.get():
                    self._ui_progress(2, 2, "Gerando PNG 512...")
                    image_resize_png(img, out_png, 512)

                self._ui_log(f"✅ Ícone criado: {out_ico}")
                if self.icon_make_png512_var.get():
                    self._ui_log(f"✅ PNG criado: {out_png}")

                self._run_on_ui(lambda: Messagebox.show_info("Ícone gerado com sucesso!", "Imagem → Ícone"))
            except Exception as e:
                self._ui_log(f"❌ Erro: {e}")
                self._run_on_ui(lambda: Messagebox.show_error(str(e), "Erro"))
            finally:
                self._run_on_ui(self._unlock_ui)

        self.is_working = True
        if self.btn_convert:
            self.btn_convert.configure(state="disabled")
        self.progress_var.set(0)
        self._set_status("Iniciando...")
        threading.Thread(target=worker, daemon=True).start()

    # ---------------------- MÍDIA ----------------------
    def pick_video(self):
        p = filedialog.askopenfilename(
            title="Selecione um vídeo",
            filetypes=[("Vídeos", "*.mp4 *.mkv *.mov *.webm *.avi")]
        )
        if p:
            self.video_in_var.set(p)

    def run_extract_audio(self):
        if self.is_working:
            return
        video = self.video_in_var.get().strip()
        if not video or not os.path.exists(video):
            Messagebox.show_warning("Selecione um vídeo válido.", "Vídeo → Música")
            return

        out_dir = self.output_dir_var.get().strip()
        safe_mkdir(out_dir)
        fmt = self.audio_out_fmt_var.get().strip().lower()
        base = Path(video).stem
        out_audio = os.path.join(out_dir, f"{base}.{fmt}")

        def worker():
            try:
                self._ui_log("🎬 Extraindo áudio do vídeo...")
                self._ui_progress(1, 1, "Extraindo áudio...")
                extract_audio(video, out_audio, fmt)  # type: ignore
                self._ui_log(f"✅ Áudio criado: {out_audio}")
                self._run_on_ui(lambda: Messagebox.show_info("Áudio extraído com sucesso!", "Vídeo → Música"))
            except Exception as e:
                self._ui_log(f"❌ Erro: {e}")
                msg = str(e)
                self._run_on_ui(lambda m=msg: Messagebox.show_error(m, "Erro"))
            finally:
                self._run_on_ui(self._unlock_ui)

        self.is_working = True
        self.progress_var.set(0)
        self._set_status("Iniciando...")
        threading.Thread(target=worker, daemon=True).start()

    def pick_audio(self):
        p = filedialog.askopenfilename(
            title="Selecione um áudio",
            filetypes=[("Áudios", "*.mp3 *.wav *.m4a")]
        )
        if p:
            self.audio_in_var.set(p)

    def pick_cover(self):
        p = filedialog.askopenfilename(
            title="Selecione uma imagem de capa",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.webp *.bmp *.tiff")]
        )
        if p:
            self.cover_img_var.set(p)

    def run_audio_to_video(self):
        if self.is_working:
            return
        audio = self.audio_in_var.get().strip()
        cover = self.cover_img_var.get().strip()
        if not audio or not os.path.exists(audio):
            Messagebox.show_warning("Selecione um áudio válido.", "Música → Vídeo")
            return
        if not cover or not os.path.exists(cover):
            Messagebox.show_warning("Selecione uma imagem de capa válida.", "Música → Vídeo")
            return

        out_dir = self.output_dir_var.get().strip()
        safe_mkdir(out_dir)
        out_video = os.path.join(out_dir, f"{Path(audio).stem}_video.mp4")

        def worker():
            try:
                self._ui_log("🎵 Criando vídeo com capa + áudio...")
                self._ui_progress(1, 1, "Renderizando vídeo...")
                audio_to_video_cover(audio, cover, out_video)
                self._ui_log(f"✅ Vídeo criado: {out_video}")
                self._run_on_ui(lambda: Messagebox.show_info("Vídeo criado com sucesso!", "Música → Vídeo"))
            except Exception as e:
                self._ui_log(f"❌ Erro: {e}")
                self._run_on_ui(lambda: Messagebox.show_error(str(e), "Erro"))
            finally:
                self._run_on_ui(self._unlock_ui)

        self.is_working = True
        self.progress_var.set(0)
        self._set_status("Iniciando...")
        threading.Thread(target=worker, daemon=True).start()

    def pick_compress_video(self):
        p = filedialog.askopenfilename(
            title="Selecione um vídeo",
            filetypes=[("Vídeos", "*.mp4 *.mkv *.mov *.webm *.avi")]
        )
        if p:
            self.compress_in_var.set(p)

    def run_compress_video(self):
        if self.is_working:
            return
        vid = self.compress_in_var.get().strip()
        if not vid or not os.path.exists(vid):
            Messagebox.show_warning("Selecione um vídeo válido.", "Comprimir vídeo")
            return

        out_dir = self.output_dir_var.get().strip()
        safe_mkdir(out_dir)

        q = self.compress_quality_var.get().strip().lower()
        r = self.compress_res_var.get().strip().lower()

        out_video = os.path.join(out_dir, f"{Path(vid).stem}_compressed.mp4")

        def worker():
            try:
                self._ui_log("📦 Comprimindo vídeo...")
                self._ui_progress(1, 1, "Comprimindo...")
                compress_video(vid, out_video, quality=q, resolution=r)  # type: ignore
                self._ui_log(f"✅ Vídeo comprimido: {out_video}")
                self._run_on_ui(lambda: Messagebox.show_info("Vídeo comprimido com sucesso!", "Comprimir vídeo"))
            except Exception as e:
                self._ui_log(f"❌ Erro: {e}")
                self._run_on_ui(lambda: Messagebox.show_error(str(e), "Erro"))
            finally:
                self._run_on_ui(self._unlock_ui)

        self.is_working = True
        self.progress_var.set(0)
        self._set_status("Iniciando...")
        threading.Thread(target=worker, daemon=True).start()