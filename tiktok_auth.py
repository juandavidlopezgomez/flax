"""
Ejecuta este archivo UNA SOLA VEZ para autorizarte con TikTok.
Abre el navegador, inicia sesión y copia el código que aparece.
Guarda el access_token en tiktok_token.json.
"""
import requests
import json
import time
import webbrowser
from urllib.parse import urlencode, urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
from config import TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET, TIKTOK_REDIRECT_URI

TOKEN_FILE = "tiktok_token.json"
auth_code_received = None

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code_received
        params = parse_qs(urlparse(self.path).query)
        if "code" in params:
            auth_code_received = params["code"][0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"<h1>Autorizado! Puedes cerrar esta ventana.</h1>")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"<h1>Error: no se recibio el codigo.</h1>")

    def log_message(self, format, *args):
        pass  # Silencia logs del servidor

def get_auth_url():
    params = {
        "client_key": TIKTOK_CLIENT_KEY,
        "response_type": "code",
        "scope": "user.info.basic,video.upload",
        "redirect_uri": TIKTOK_REDIRECT_URI,
    }
    return "https://www.tiktok.com/v2/auth/authorize/?" + urlencode(params)

def exchange_code_for_token(code):
    resp = requests.post("https://open.tiktokapis.com/v2/oauth/token/", data={
        "client_key": TIKTOK_CLIENT_KEY,
        "client_secret": TIKTOK_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": TIKTOK_REDIRECT_URI,
    })
    return resp.json()

def main():
    auth_url = get_auth_url()
    print(f"\n[TikTok Auth] Abriendo navegador para autorizar la app...")
    print(f"URL: {auth_url}\n")
    webbrowser.open(auth_url)

    print("[TikTok Auth] Esperando callback en http://localhost:8080...")
    server = HTTPServer(("localhost", 8080), CallbackHandler)
    server.handle_request()

    if not auth_code_received:
        print("[TikTok Auth] No se recibio el codigo. Intenta de nuevo.")
        return

    print(f"[TikTok Auth] Codigo recibido. Obteniendo token...")
    token_data = exchange_code_for_token(auth_code_received)

    if "access_token" not in token_data:
        print(f"[TikTok Auth] Error: {token_data}")
        return

    token_data["saved_at"] = int(time.time())
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)

    print(f"[TikTok Auth] Token guardado en {TOKEN_FILE}")
    print(f"Access token: {token_data['access_token'][:20]}...")
    print(f"Expira en: {token_data.get('expires_in', '?')} segundos")

if __name__ == "__main__":
    main()
