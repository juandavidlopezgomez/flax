"""
Cliente de TikTok: sube videos usando la Content Posting API.
Maneja refresh automatico del access_token.
"""
import requests
import json
import os
import time
from config import TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET

TOKEN_FILE = "tiktok_token.json"
CHUNK_SIZE = 10 * 1024 * 1024  # 10 MB por chunk
MIN_CHUNK = 5 * 1024 * 1024    # 5 MB minimo por chunk (requisito TikTok)


def load_token():
    if not os.path.exists(TOKEN_FILE):
        raise FileNotFoundError("No hay token de TikTok. Ejecuta: python tiktok_auth.py")
    with open(TOKEN_FILE, "r") as f:
        return json.load(f)


def save_token(token_data):
    # Guarda con el timestamp de cuando fue obtenido
    token_data["saved_at"] = int(time.time())
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)


def refresh_access_token(refresh_token):
    """Renueva el access_token usando el refresh_token."""
    resp = requests.post(
        "https://open.tiktokapis.com/v2/oauth/token/",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_key": TIKTOK_CLIENT_KEY,
            "client_secret": TIKTOK_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
    )
    return resp.json()


def get_valid_access_token():
    """Retorna un access_token vigente, refrescandolo si expiro."""
    token = load_token()
    saved_at = token.get("saved_at", 0)
    expires_in = token.get("expires_in", 86400)

    # Renovar 5 minutos antes de que expire
    if time.time() >= (saved_at + expires_in - 300):
        print("[TikTok] Access token expirado, renovando...")
        refresh = token.get("refresh_token")
        if not refresh:
            raise Exception("No hay refresh_token, autoriza de nuevo con tiktok_auth.py")
        new_token = refresh_access_token(refresh)
        if "access_token" not in new_token:
            raise Exception(f"Error refrescando token: {new_token}")
        save_token(new_token)
        token = new_token

    return token["access_token"]


def upload_video(video_path, title=""):
    """Sube un video a TikTok como borrador (el usuario lo publica manualmente).

    En modo Sandbox y sin dominio verificado solo se puede subir como borrador.
    """
    access_token = get_valid_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    file_size = os.path.getsize(video_path)

    # Calcular chunks
    if file_size <= CHUNK_SIZE:
        chunk_size = file_size
        chunk_count = 1
    else:
        chunk_size = CHUNK_SIZE
        chunk_count = (file_size + chunk_size - 1) // chunk_size

    print(f"[TikTok] Iniciando subida: {os.path.basename(video_path)} ({file_size/1024/1024:.1f} MB, {chunk_count} chunks)")

    # 1. Inicializar upload (endpoint "inbox" = borrador)
    init_resp = requests.post(
        "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/",
        headers={**headers, "Content-Type": "application/json; charset=UTF-8"},
        json={
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": file_size,
                "chunk_size": chunk_size,
                "total_chunk_count": chunk_count,
            },
        },
    )

    init_data = init_resp.json()
    if init_resp.status_code != 200 or init_data.get("error", {}).get("code") != "ok":
        print(f"[TikTok] Error iniciando: {init_data}")
        return None

    publish_id = init_data["data"]["publish_id"]
    upload_url = init_data["data"]["upload_url"]
    print(f"[TikTok] publish_id: {publish_id}")

    # 2. Subir chunks
    with open(video_path, "rb") as f:
        for i in range(chunk_count):
            chunk = f.read(chunk_size)
            start = i * chunk_size
            end = start + len(chunk) - 1

            chunk_resp = requests.put(
                upload_url,
                headers={
                    "Content-Range": f"bytes {start}-{end}/{file_size}",
                    "Content-Length": str(len(chunk)),
                    "Content-Type": "video/mp4",
                },
                data=chunk,
            )
            if chunk_resp.status_code not in (200, 201, 206):
                print(f"[TikTok] Error chunk {i+1}: {chunk_resp.status_code} {chunk_resp.text[:200]}")
                return None
            print(f"[TikTok] Chunk {i+1}/{chunk_count} OK ({chunk_resp.status_code})")

    print(f"[TikTok] Video subido como borrador. publish_id: {publish_id}")
    print(f"[TikTok] Ve a tu app de TikTok -> Notificaciones -> Revisa el borrador para publicar.")
    return publish_id


def check_upload_status(publish_id):
    """Consulta el estado de un upload."""
    access_token = get_valid_access_token()
    resp = requests.post(
        "https://open.tiktokapis.com/v2/post/publish/status/fetch/",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        },
        json={"publish_id": publish_id},
    )
    return resp.json()
