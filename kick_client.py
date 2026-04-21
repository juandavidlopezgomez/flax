"""
Cliente de Kick: descarga clips del canal configurado.
Usa curl_cffi para saltarse Cloudflare y ffmpeg para convertir HLS a MP4.
"""
import os
import json
import subprocess
from curl_cffi import requests as creq
import imageio_ffmpeg
from config import KICK_CHANNEL, DOWNLOAD_FOLDER

UPLOADED_LOG = "uploaded.json"
IMPERSONATE = "chrome120"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def load_uploaded():
    if os.path.exists(UPLOADED_LOG):
        with open(UPLOADED_LOG, "r") as f:
            return json.load(f)
    return []


def save_uploaded(uploaded):
    with open(UPLOADED_LOG, "w") as f:
        json.dump(uploaded, f, indent=2)


def get_new_clips():
    """Obtiene clips nuevos del canal de Kick que aun no se subieron a TikTok."""
    uploaded = load_uploaded()
    url = f"https://kick.com/api/v2/channels/{KICK_CHANNEL}/clips"

    try:
        resp = creq.get(url, impersonate=IMPERSONATE, timeout=20)
        if resp.status_code != 200:
            print(f"[Kick] Error HTTP {resp.status_code}")
            return []
        data = resp.json()
        raw_clips = data.get("clips", []) if isinstance(data, dict) else data
    except Exception as e:
        print(f"[Kick] Error obteniendo clips: {e}")
        return []

    new_clips = []
    for c in raw_clips:
        clip_id = c.get("id")
        if not clip_id or clip_id in uploaded:
            continue
        video_url = (
            c.get("video_url")
            or c.get("clip_url")
            or (c.get("video") or {}).get("s3")
        )
        if not video_url:
            continue
        new_clips.append({
            "id": clip_id,
            "title": c.get("title", "Clip"),
            "video_url": video_url,
            "view_count": c.get("view_count", 0),
            "duration": c.get("duration", 0),
        })

    print(f"[Kick] {len(new_clips)} clips nuevos encontrados.")
    return new_clips


def download_clip(clip):
    """Descarga un clip HLS y lo convierte a MP4 con ffmpeg."""
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    clip_id = clip["id"]
    output_path = os.path.join(DOWNLOAD_FOLDER, f"{clip_id}.mp4")

    if os.path.exists(output_path):
        print(f"[Kick] Ya descargado: {clip_id}")
        return output_path

    video_url = clip.get("video_url")
    if not video_url:
        print(f"[Kick] Clip {clip_id} sin URL de video")
        return None

    print(f"[Kick] Descargando {clip_id}: {clip.get('title', '')[:50]}")

    # ffmpeg descarga el HLS y convierte a MP4
    cmd = [
        FFMPEG,
        "-y",
        "-loglevel", "error",
        "-i", video_url,
        "-c", "copy",
        "-bsf:a", "aac_adtstoasc",
        output_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            print(f"[Kick] ffmpeg error: {result.stderr[:300]}")
            if os.path.exists(output_path):
                os.remove(output_path)
            return None

        size_mb = os.path.getsize(output_path) / 1024 / 1024
        print(f"[Kick] Descargado: {output_path} ({size_mb:.1f} MB)")
        return output_path
    except subprocess.TimeoutExpired:
        print(f"[Kick] Timeout descargando {clip_id}")
        return None
    except Exception as e:
        print(f"[Kick] Error: {e}")
        return None
