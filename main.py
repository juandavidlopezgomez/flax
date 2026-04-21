"""
Agente principal: descarga clips nuevos de Westcol en Kick y los sube a TikTok.
Uso:
    python main.py          # Ejecuta una vez
    python main.py --loop   # Ejecuta cada hora automaticamente
"""
import os
import sys
import time
import argparse
from kick_client import get_new_clips, download_clip, load_uploaded, save_uploaded
from tiktok_client import upload_video
from config import CHECK_INTERVAL_MINUTES

def run_once():
    print("\n========== FLAX - Kick → TikTok ==========")
    clips = get_new_clips()

    if not clips:
        print("[Main] No hay clips nuevos. Nada que hacer.")
        return

    uploaded = load_uploaded()

    for clip in clips:
        clip_id = clip["id"]
        title = clip.get("title", "Clip de Westcol")
        print(f"\n[Main] Procesando: {title} ({clip_id})")

        # Descargar
        video_path = download_clip(clip)
        if not video_path:
            print(f"[Main] Saltando {clip_id} (error de descarga)")
            continue

        # Subir a TikTok
        result = upload_video(video_path, title=title)
        if result:
            uploaded.append(clip_id)
            save_uploaded(uploaded)
            print(f"[Main] Clip {clip_id} subido y registrado.")

            # Borrar el archivo local para ahorrar espacio
            os.remove(video_path)
            print(f"[Main] Archivo local eliminado.")
        else:
            print(f"[Main] Error subiendo {clip_id} a TikTok.")

    print("\n[Main] Ciclo completado.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--loop", action="store_true", help="Ejecutar en bucle cada hora")
    args = parser.parse_args()

    if args.loop:
        print(f"[Main] Modo automatico: revisando cada {CHECK_INTERVAL_MINUTES} minutos.")
        while True:
            run_once()
            print(f"[Main] Esperando {CHECK_INTERVAL_MINUTES} minutos...")
            time.sleep(CHECK_INTERVAL_MINUTES * 60)
    else:
        run_once()

if __name__ == "__main__":
    main()
