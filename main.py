"""
Agente principal: descarga clips nuevos de Westcol en Kick y los sube a TikTok.

Uso:
    python main.py              # Ejecuta una vez
    python main.py --loop       # Ejecuta cada hora automaticamente
    python main.py --limit 1    # Solo procesa 1 clip (para pruebas)
    python main.py --dry-run    # Descarga pero NO sube (para pruebas)
"""
import os
import sys
import time
import argparse
from kick_client import get_new_clips, download_clip, load_uploaded, save_uploaded
from tiktok_client import upload_video
from config import CHECK_INTERVAL_MINUTES


def run_once(limit=None, dry_run=False, keep_files=False):
    print("\n========== FLAX - Kick -> TikTok ==========")
    clips = get_new_clips()

    if not clips:
        print("[Main] No hay clips nuevos.")
        return

    # Procesar los mas viejos primero para no saltarnos ninguno
    clips = list(reversed(clips))
    if limit:
        clips = clips[:limit]

    uploaded = load_uploaded()
    success = 0
    errors = 0

    for clip in clips:
        clip_id = clip["id"]
        title = clip.get("title", "Clip de Westcol")
        print(f"\n[Main] Procesando: {title[:60]} ({clip_id})")

        # 1. Descargar
        video_path = download_clip(clip)
        if not video_path:
            print(f"[Main] Saltando (error de descarga)")
            errors += 1
            continue

        # 2. Subir a TikTok (si no es dry-run)
        if dry_run:
            print(f"[Main] DRY RUN: no se sube a TikTok")
            success += 1
            continue

        try:
            publish_id = upload_video(video_path, title=title)
            if publish_id:
                uploaded.append(clip_id)
                save_uploaded(uploaded)
                print(f"[Main] OK. Borrador creado en TikTok (publish_id: {publish_id})")
                success += 1

                if not keep_files:
                    os.remove(video_path)
                    print(f"[Main] Archivo local eliminado")
            else:
                print(f"[Main] Error subiendo a TikTok")
                errors += 1
        except Exception as e:
            print(f"[Main] Excepcion subiendo: {e}")
            errors += 1

    print(f"\n[Main] Resumen: {success} exitosos, {errors} errores.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--loop", action="store_true", help="Ejecutar en bucle cada hora")
    parser.add_argument("--limit", type=int, default=None, help="Limitar numero de clips a procesar")
    parser.add_argument("--dry-run", action="store_true", help="Solo descarga, no sube a TikTok")
    parser.add_argument("--keep-files", action="store_true", help="No borrar archivos locales")
    args = parser.parse_args()

    if args.loop:
        print(f"[Main] Modo automatico: cada {CHECK_INTERVAL_MINUTES} min.")
        while True:
            try:
                run_once(limit=args.limit, dry_run=args.dry_run, keep_files=args.keep_files)
            except Exception as e:
                print(f"[Main] Error en ciclo: {e}")
            print(f"[Main] Esperando {CHECK_INTERVAL_MINUTES} min...")
            time.sleep(CHECK_INTERVAL_MINUTES * 60)
    else:
        run_once(limit=args.limit, dry_run=args.dry_run, keep_files=args.keep_files)


if __name__ == "__main__":
    main()
