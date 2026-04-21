"""
Uploader de TikTok 100% automatico usando Playwright.
Maneja los modales nuevos de TikTok (unoriginal content, etc.) automaticamente.
"""
import os
import re
import time
import json
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

COOKIES_FILE = "tiktok_cookies.txt"
UPLOAD_URL = "https://www.tiktok.com/tiktokstudio/upload?from=upload"


def parse_netscape_cookies(path):
    """Convierte un cookies.txt (formato Netscape) a formato Playwright."""
    cookies = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 7:
                continue
            domain, _flag, path_, secure, expires, name, value = parts[:7]
            try:
                expires = int(expires)
            except ValueError:
                expires = -1
            cookie = {
                "name": name,
                "value": value,
                "domain": domain,
                "path": path_,
                "secure": secure.upper() == "TRUE",
                "httpOnly": False,
                "sameSite": "Lax",
            }
            if expires > 0:
                cookie["expires"] = expires
            cookies.append(cookie)
    return cookies


def dismiss_modals(page):
    """Cierra/remueve cualquier modal, overlay o tutorial que TikTok muestre."""
    # 1. Remover overlays de react-joyride (tutorial guiado)
    try:
        page.evaluate("""
            () => {
                document.querySelectorAll('#react-joyride-portal, [data-test-id="overlay"], .react-joyride__overlay, .react-joyride__spotlight, .react-joyride__tooltip').forEach(el => el.remove());
                document.body.style.overflow = 'auto';
            }
        """)
    except Exception:
        pass

    # 2. Intentar cerrar con botones de texto
    selectors = [
        'button:has-text("Continue")',
        'button:has-text("Continuar")',
        'button:has-text("Got it")',
        'button:has-text("Entendido")',
        'button:has-text("OK")',
        'button:has-text("Allow")',
        'button:has-text("Permitir")',
        'button:has-text("Skip")',
        'button:has-text("Omitir")',
        'button:has-text("Saltar")',
        'button:has-text("Cancel")',
        'button[aria-label="Close"]',
        'button[aria-label="Cerrar"]',
        'button[aria-label="Skip"]',
        'button.react-joyride__button',
    ]
    for sel in selectors:
        try:
            for btn in page.locator(sel).all():
                try:
                    if btn.is_visible(timeout=500):
                        btn.click(timeout=1000)
                        time.sleep(0.3)
                except Exception:
                    pass
        except Exception:
            pass

    # 3. Remover modales genericos por CSS
    try:
        page.evaluate("""
            () => {
                document.querySelectorAll('[class*="TUXModal-overlay"], [role="presentation"][data-test-id="overlay"]').forEach(el => el.remove());
            }
        """)
    except Exception:
        pass


def upload_to_tiktok(video_path, description=""):
    """Sube un video a TikTok de forma 100% automatica."""
    if not os.path.exists(COOKIES_FILE):
        raise FileNotFoundError(f"Falta {COOKIES_FILE}")

    abs_video = os.path.abspath(video_path)
    print(f"[TikTok] Subiendo: {os.path.basename(abs_video)}")
    print(f"[TikTok] Descripcion: {description[:80]}")

    cookies = parse_netscape_cookies(COOKIES_FILE)
    tiktok_cookies = [c for c in cookies if "tiktok.com" in c["domain"]]

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 900},
            locale="es-ES",
        )
        context.add_cookies(tiktok_cookies)
        page = context.new_page()

        try:
            page.goto(UPLOAD_URL, wait_until="domcontentloaded", timeout=60000)
            time.sleep(5)

            # Cerrar modales iniciales
            dismiss_modals(page)

            # 1. Subir archivo - el input esta oculto detras del boton "Seleccionar videos"
            print("[TikTok] Cargando video en el input...")
            # Esperamos que el DOM tenga el input (aunque este oculto)
            page.wait_for_selector('input[type="file"]', state="attached", timeout=30000)
            file_input = page.locator('input[type="file"]').first
            file_input.set_input_files(abs_video)
            print("[TikTok] Archivo cargado, esperando procesamiento...")
            time.sleep(5)

            # 2. Esperar a que aparezca el editor de descripcion
            #    Hay varias formas en que TikTok lo renderiza; usamos multiples selectores
            caption_sel = 'div[contenteditable="true"]'
            page.wait_for_selector(caption_sel, timeout=120000)
            time.sleep(3)

            # Cerrar posibles modales
            dismiss_modals(page)

            # 3. Escribir descripcion (limpiamos primero)
            print("[TikTok] Escribiendo descripcion...")
            caption = page.locator(caption_sel).first
            caption.click()
            # Seleccionar todo y borrar
            page.keyboard.press("Control+A")
            page.keyboard.press("Delete")
            time.sleep(0.5)

            # Escribir char por char para que TikTok procese hashtags
            for ch in description:
                page.keyboard.type(ch)
                time.sleep(0.02)
            time.sleep(2)

            # Cerrar sugerencia de menciones/hashtags si aparece
            page.keyboard.press("Escape")
            time.sleep(1)

            # 4. Esperar a que termine de subir el video (barra de progreso)
            print("[TikTok] Esperando a que termine la subida del video...")
            for _ in range(60):  # hasta 5 minutos
                time.sleep(5)
                dismiss_modals(page)
                # Si vemos el boton Post habilitado, ya esta
                try:
                    post_btn = page.locator(
                        'button:has-text("Post"), button:has-text("Publicar")'
                    ).first
                    if post_btn.is_visible() and post_btn.is_enabled():
                        break
                except Exception:
                    continue

            # 5. Cerrar modales ANTES de click Post
            dismiss_modals(page)
            time.sleep(1)

            # 6. Click en Post con multiples estrategias
            print("[TikTok] Publicando...")
            clicked = False
            for attempt in range(5):
                dismiss_modals(page)
                try:
                    post_btn = page.locator(
                        'button:has-text("Post"), button:has-text("Publicar")'
                    ).first
                    post_btn.wait_for(state="visible", timeout=10000)
                    # Intentar click normal
                    try:
                        post_btn.click(timeout=5000)
                        clicked = True
                        break
                    except Exception:
                        # Forzar click por JS si algo intercepta
                        post_btn.evaluate("el => el.click()")
                        clicked = True
                        break
                except Exception as e:
                    print(f"[TikTok] Intento {attempt+1} fallo: {e}")
                    time.sleep(2)

            if not clicked:
                print("[TikTok] No se pudo hacer click en Post")
                page.screenshot(path="tiktok_error.png", full_page=True)
                return False

            # 7. Esperar confirmacion
            print("[TikTok] Esperando confirmacion...")
            time.sleep(8)

            # Buscar indicadores de exito
            success_indicators = [
                'text=Your video is being uploaded',
                'text=uploaded successfully',
                'text=exito',
                'text=subido',
                'text=Manage posts',
            ]
            for ind in success_indicators:
                try:
                    if page.locator(ind).first.is_visible(timeout=2000):
                        print(f"[TikTok] Exito detectado: {ind}")
                        return True
                except Exception:
                    continue

            # Si la URL cambio a /manage o similar, probablemente exito
            if "upload" not in page.url:
                print(f"[TikTok] URL cambio a {page.url}, asumiendo exito")
                return True

            print("[TikTok] Publicacion enviada (no se detecto confirmacion explicita)")
            return True

        except Exception as e:
            print(f"[TikTok] Error: {e}")
            try:
                page.screenshot(path="tiktok_error.png", full_page=True)
                print("[TikTok] Screenshot guardado en tiktok_error.png")
            except Exception:
                pass
            return False
        finally:
            try:
                browser.close()
            except Exception:
                pass
