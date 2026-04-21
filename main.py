"""
Agente principal: descarga clips nuevos de Westcol en Kick y los sube a TikTok.

Modos de subida:
  --mode unofficial  Usa tiktok-uploader (Chrome con cookies) - 100% automatico
  --mode official    Usa la API oficial (borrador, requiere tiktok_auth.py)

Uso:
    python main.py --mode unofficial              # subida directa publicada
    python main.py --mode official                # borrador en la API
    python main.py --loop --mode unofficial       # automatico cada hora
    python main.py --limit 1 --mode unofficial    # solo 1 clip (prueba)
    python main.py --dry-run --limit 1            # solo descarga, no sube
"""
import os
import time
import argparse
from kick_client import get_new_clips, download_clip, load_uploaded, save_uploaded
from config import CHECK_INTERVAL_MINUTES, KICK_CHANNEL


def build_description(clip):
    title = clip.get("title", "Clip")
    return f"{title} #westcol #kick #clips #viral #foryou #fyp"


def upload(video_path, clip, mode):
    if mode == "official":
        from tiktok_client import upload_video
        return bool(upload_video(video_path, title=clip.get("title", "Clip")))
    else:
        from tiktok_uploader_client import upload_to_tiktok
        return upload_to_tiktok(video_path, description=build_description(clip))


def run_once(limit=None, dry_run=False, keep_files=False, mode="unofficial"):
    print(f"\n========== FLAX - Kick({KICK_CHANNEL}) -> TikTok ({mode}) ==========")
    clips = get_new_clips()

    if not clips:
        print("[Main] No hay clips nuevos.")
        return

    # Procesar del mas viejo al mas nuevo (orden cronologico)
    clips = list(reversed(clips))
    if limit:
        clips = clips[:limit]

    uploaded = load_uploaded()
    success = 0
    errors = 0

    for clip in clips:
        clip_id = clip["id"]
        title = clip.get("title", "Clip")
        print(f"\n[Main] Procesando: {title[:60]} ({clip_id})")

        video_path = download_clip(clip)
        if not video_path:
            errors += 1
            continue

        if dry_run:
            print(f"[Main] DRY RUN: saltando subida")
            success += 1
            continue

        try:
            ok = upload(video_path, clip, mode)
            if ok:
                uploaded.append(clip_id)
                save_uploaded(uploaded)
                print(f"[Main] OK. Subido a TikTok")
                success += 1
                if not keep_files:
                    os.remove(video_path)
            else:
                errors += 1
        except Exception as e:
            print(f"[Main] Excepcion: {e}")
            errors += 1

        # Espera entre subidas para no parecer bot
        if not dry_run and len(clips) > 1:
            print(f"[Main] Esperando 30s antes del siguiente...")
            time.sleep(30)

    print(f"\n[Main] Resumen: {success} OK, {errors} errores.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["unofficial", "official"], default="unofficial",
                        help="Metodo de subida: unofficial (Chrome+cookies) o official (API TikTok)")
    parser.add_argument("--loop", action="store_true", help="Ejecutar en bucle")
    parser.add_argument("--limit", type=int, default=None, help="Limitar numero de clips")
    parser.add_argument("--dry-run", action="store_true", help="Solo descarga, no sube")
    parser.add_argument("--keep-files", action="store_true", help="No borrar archivos locales")
    args = parser.parse_args()

    if args.loop:
        print(f"[Main] Modo automatico: cada {CHECK_INTERVAL_MINUTES} min.")
        while True:
            try:
                run_once(limit=args.limit, dry_run=args.dry_run,
                         keep_files=args.keep_files, mode=args.mode)
            except Exception as e:
                print(f"[Main] Error en ciclo: {e}")
            print(f"[Main] Esperando {CHECK_INTERVAL_MINUTES} min...")
            time.sleep(CHECK_INTERVAL_MINUTES * 60)
    else:
        run_once(limit=args.limit, dry_run=args.dry_run,
                 keep_files=args.keep_files, mode=args.mode)


if __name__ == "__main__":
    main()
