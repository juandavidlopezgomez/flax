import requests
import yt_dlp
import os
import json
from config import KICK_CHANNEL, DOWNLOAD_FOLDER

UPLOADED_LOG = "uploaded.json"

def load_uploaded():
    if os.path.exists(UPLOADED_LOG):
        with open(UPLOADED_LOG, "r") as f:
            return json.load(f)
    return []

def save_uploaded(uploaded):
    with open(UPLOADED_LOG, "w") as f:
        json.dump(uploaded, f, indent=2)

def get_new_clips():
    """Obtiene clips nuevos del canal de Kick que aún no fueron subidos."""
    uploaded = load_uploaded()
    url = f"https://kick.com/api/v2/channels/{KICK_CHANNEL}/clips"
    headers = {"Accept": "application/json"}

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        clips = data.get("clips", data) if isinstance(data, dict) else data
    except Exception as e:
        print(f"[Kick] Error obteniendo clips: {e}")
        return []

    new_clips = [c for c in clips if c["id"] not in uploaded]
    print(f"[Kick] {len(new_clips)} clips nuevos encontrados.")
    return new_clips

def download_clip(clip):
    """Descarga un clip y retorna la ruta del archivo."""
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    clip_id = clip["id"]
    video_url = clip.get("clip_url") or clip.get("url")
    output_path = os.path.join(DOWNLOAD_FOLDER, f"{clip_id}.mp4")

    if os.path.exists(output_path):
        print(f"[Kick] Ya descargado: {clip_id}")
        return output_path

    print(f"[Kick] Descargando clip {clip_id}...")
    ydl_opts = {
        "outtmpl": output_path,
        "format": "mp4/best",
        "quiet": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        print(f"[Kick] Descargado: {output_path}")
        return output_path
    except Exception as e:
        print(f"[Kick] Error descargando {clip_id}: {e}")
        return None
