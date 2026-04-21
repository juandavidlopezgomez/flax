"""
Cliente de TikTok via navegador automatizado (no requiere API oficial).
Sube videos automatizando Chrome con tu sesion logueada (cookies).

IMPORTANTE: Debes exportar las cookies de tu navegador logueado en tiktok.com
Instrucciones en COOKIES.md
"""
import os
from tiktok_uploader.upload import upload_video

COOKIES_FILE = "tiktok_cookies.txt"


def upload_to_tiktok(video_path, description=""):
    """Sube un video a TikTok usando cookies de tu sesion.

    description: texto del post (incluye hashtags si quieres)
    """
    if not os.path.exists(COOKIES_FILE):
        raise FileNotFoundError(
            f"No hay cookies. Exporta las cookies de tiktok.com a {COOKIES_FILE}. "
            "Ver COOKIES.md para instrucciones."
        )

    print(f"[TikTok-Uploader] Subiendo: {os.path.basename(video_path)}")
    print(f"[TikTok-Uploader] Descripcion: {description[:80]}")

    try:
        result = upload_video(
            filename=video_path,
            description=description[:2200],  # limite de TikTok
            cookies=COOKIES_FILE,
            headless=True,  # navegador invisible
        )
        # result es una lista de fallos; vacia = exito
        if result:
            print(f"[TikTok-Uploader] Fallos reportados: {result}")
            return False
        print(f"[TikTok-Uploader] Video subido correctamente.")
        return True
    except Exception as e:
        print(f"[TikTok-Uploader] Error: {e}")
        return False
