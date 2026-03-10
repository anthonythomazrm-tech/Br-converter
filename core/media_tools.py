import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Literal

AudioFormat = Literal["mp3", "wav", "m4a"]
Quality = Literal["alta", "media", "baixa"]
Resolution = Literal["keep", "1080p", "720p", "480p"]


def _resource_path(rel: str) -> Path:
    """
    Resolve caminho tanto em dev quanto no .exe (PyInstaller).
    Retorna Path absoluto.
    """
    if hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        # media_tools.py está em br_converter/core -> parents[1] = br_converter
        base = Path(__file__).resolve().parents[1]
    return base / rel


def find_ffmpeg() -> str:
    """
    Acha ffmpeg dentro do projeto (br_converter/bin/ffmpeg/ffmpeg.exe) ou no PATH.
    Retorna caminho executável (string) ou levanta erro.
    """
    local_ffmpeg = _resource_path("bin/ffmpeg.exe")
    if local_ffmpeg.exists():
        return str(local_ffmpeg)

    from_path = shutil.which("ffmpeg")
    if from_path:
        return from_path

    raise RuntimeError(
        "FFmpeg não encontrado. Coloque em br_converter/bin/ffmpeg ou instale e adicione no PATH."
    )


def _run(cmd: list[str]):
    # Oculta janela no Windows e captura logs
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
    subprocess.run(cmd, check=True, creationflags=creationflags)


def extract_audio(video_path: str, out_audio_path: str, fmt: AudioFormat):
    ffmpeg = find_ffmpeg()

    out_audio_path = str(Path(out_audio_path))
    Path(out_audio_path).parent.mkdir(parents=True, exist_ok=True)

    # -vn: remove vídeo
    if fmt == "mp3":
        cmd = [ffmpeg, "-y", "-i", video_path, "-vn", "-codec:a", "libmp3lame", "-q:a", "2", out_audio_path]
    elif fmt == "wav":
        cmd = [ffmpeg, "-y", "-i", video_path, "-vn", "-codec:a", "pcm_s16le", out_audio_path]
    elif fmt == "m4a":
        cmd = [ffmpeg, "-y", "-i", video_path, "-vn", "-codec:a", "aac", "-b:a", "192k", out_audio_path]
    else:
        raise ValueError("Formato de áudio inválido.")

    _run(cmd)


def audio_to_video_cover(audio_path: str, image_path: str, out_video_path: str):
    """Cria vídeo MP4 com imagem fixa + áudio (ótimo pra status/reels)."""
    ffmpeg = find_ffmpeg()

    out_video_path = str(Path(out_video_path))
    Path(out_video_path).parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        ffmpeg, "-y",
        "-loop", "1",
        "-i", image_path,
        "-i", audio_path,
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-pix_fmt", "yuv420p",
        out_video_path
    ]
    _run(cmd)


def compress_video(
    input_video: str,
    out_video: str,
    quality: Quality = "media",
    resolution: Resolution = "keep",
):
    ffmpeg = find_ffmpeg()

    Path(out_video).parent.mkdir(parents=True, exist_ok=True)

    # CRF menor = melhor qualidade (e arquivo maior)
    crf_map = {"alta": "22", "media": "26", "baixa": "30"}
    crf = crf_map.get(quality, "26")

    # Escala
    vf: Optional[str] = None
    if resolution == "1080p":
        vf = "scale=-2:1080"
    elif resolution == "720p":
        vf = "scale=-2:720"
    elif resolution == "480p":
        vf = "scale=-2:480"

    cmd = [ffmpeg, "-y", "-i", input_video]
    if vf:
        cmd += ["-vf", vf]

    # Preset: velocidade x compressão
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", crf, "-c:a", "aac", "-b:a", "128k", out_video]
    _run(cmd)