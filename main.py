import os
import ttkbootstrap as tb

from core.config import ConfigStore
from ui.welcome import WelcomeScreen
from ui.app import MainApp
from ui.theme import theme_for_config, set_theme_in_config


APP_TITLE = "BR Converter"


def main():
    cfg = ConfigStore(app_name="BR Converter")

    # cria a janela já com o tema salvo
    win = tb.Window(themename=theme_for_config(cfg))
    win.title(APP_TITLE)
    win.minsize(980, 640)

    # ÍCONE (se tiver)
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")
    try:
        if os.path.exists(icon_path):
            img = tb.PhotoImage(file=icon_path)
            win.iconphoto(True, img)
            win._app_icon = img  # manter referência
    except Exception:
        pass

    def go_main():
        for w in win.winfo_children():
            w.destroy()
        MainApp(win, cfg).mount()

    if cfg.get("first_run", True):
        WelcomeScreen(win, cfg, on_start=go_main).mount()
    else:
        go_main()

    win.mainloop()


if __name__ == "__main__":
    main()