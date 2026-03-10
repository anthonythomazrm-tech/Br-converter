import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox

from core.config import ConfigStore
from ui.theme import toggle_theme_window

VERSION_TEXT = "v1.0 • Developed by Anthony"


class WelcomeScreen:
    def __init__(self, window: tb.Window, cfg: ConfigStore, on_start):
        self.window = window
        self.cfg = cfg
        self.on_start = on_start

    def mount(self):
        root = tb.Frame(self.window, padding=24)
        root.pack(fill=BOTH, expand=YES)

        card = tb.Frame(root, padding=24, bootstyle="secondary")
        card.pack(fill=BOTH, expand=YES)

        tb.Label(
            card,
            text="Bem-vindo ao melhor conversor de arquivos do Brasil 🇧🇷",
            font=("Segoe UI", 18, "bold"),
        ).pack(pady=(18, 8))

        tb.Label(
            card,
            text="Converta DOCX, PDF, XLSX e imagens em segundos.",
            font=("Segoe UI", 11),
        ).pack(pady=(0, 24))

        btns = tb.Frame(card)
        btns.pack(pady=10)

        tb.Button(
            btns,
            text="Quero experimentar",
            bootstyle=PRIMARY,
            width=22,
            command=self._start,
        ).grid(row=0, column=0, padx=8, pady=6)

        tb.Button(
            btns,
            text="Versão para Android (em breve)",
            bootstyle=SECONDARY,
            width=26,
            command=self._android,
        ).grid(row=0, column=1, padx=8, pady=6)

        bottom = tb.Frame(card)
        bottom.pack(side=BOTTOM, fill=X, pady=(18, 0))

        tb.Label(bottom, text=VERSION_TEXT, font=("Segoe UI", 9)).pack(side=LEFT)

        tb.Button(
            bottom,
            text="🌙/☀️",
            bootstyle=OUTLINE,
            width=6,
            command=lambda: toggle_theme_window(self.window, self.cfg),
        ).pack(side=RIGHT)

    def _android(self):
        Messagebox.show_info("Ainda não disponível. Em breve!", "Android")

    def _start(self):
        self.cfg.set("first_run", False)
        self.on_start()