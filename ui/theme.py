from core.config import ConfigStore

# Temas modernos e consistentes:
# darkly = dark bonito
# flatly = light clean
THEME_MAP = {
    "dark": "darkly",
    "light": "flatly",
}

REVERSE_THEME_MAP = {
    "darkly": "dark",
    "flatly": "light",
}

def theme_for_config(cfg: ConfigStore) -> str:
    mode = (cfg.get("theme", "dark") or "dark").lower()
    return THEME_MAP.get(mode, "darkly")

def set_theme_in_config(cfg: ConfigStore, theme_mode: str):
    # theme_mode: "dark" ou "light"
    theme_mode = (theme_mode or "dark").lower()
    if theme_mode not in ("dark", "light"):
        theme_mode = "dark"
    cfg.set("theme", theme_mode)

def toggle_theme_window(window, cfg: ConfigStore):
    """
    Alterna tema no ttkbootstrap e salva no config.
    """
    current_theme = window.style.theme.name  # ex: "darkly" / "flatly"
    if current_theme == "darkly":
        window.style.theme_use("flatly")
        cfg.set("theme", "light")
    else:
        window.style.theme_use("darkly")
        cfg.set("theme", "dark")