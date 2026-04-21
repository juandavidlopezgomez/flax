import requests
import json
import os

TOKEN_FILE = "tiktok_token.json"
CHUNK_SIZE = 10 * 1024 * 1024  # 10MB por chunk

def load_token():
    if not os.path.exists(TOKEN_FILE):
        raise FileNotFoundError("No hay token de TikTok. Ejecuta primero: python tiktok_auth.py")
    with open(TOKEN_FILE, "r") as f:
        return json.load(f)

def upload_video(video_path, title=""):
    """Sube un video a TikTok y lo publica."""
    token_data = load_token()
    access_token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    file_size = os.path.getsize(video_path)
    chunk_count = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE

    print(f"[TikTok] Iniciando subida: {os.path.basename(video_path)} ({file_size // 1024 // 1024}MB)")

    # 1. Inicializar la subida
    init_resp = requests.post(
        "https://open.tiktokapis.com/v2/post/publish/video/init/",
        headers={**headers, "Content-Type": "application/json; charset=UTF-8"},
        json={
            "post_info": {
                "title": title[:150] if title else "Clip de Westcol",
                "privacy_level": "PUBLIC_TO_EVERYONE",
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": file_size,
                "chunk_size": CHUNK_SIZE,
                "total_chunk_count": chunk_count,
            },
        },
    )

    init_data = init_resp.json()
    if "error" in init_data and init_data["error"]["code"] != "ok":
        print(f"[TikTok] Error iniciando subida: {init_data}")
        return False

    publish_id = init_data["data"]["publish_id"]
    upload_url = init_data["data"]["upload_url"]
    print(f"[TikTok] Subida iniciada. publish_id: {publish_id}")

    # 2. Subir chunks
    with open(video_path, "rb") as f:
        for i in range(chunk_count):
            chunk = f.read(CHUNK_SIZE)
            start = i * CHUNK_SIZE
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
            print(f"[TikTok] Chunk {i+1}/{chunk_count} subido ({chunk_resp.status_code})")

    print(f"[TikTok] Video subido exitosamente. publish_id: {publish_id}")
    return publish_id
