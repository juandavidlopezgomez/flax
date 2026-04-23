"""
Uploader de TikTok 100% automatico usando undetected-chromedriver.
Abre una ventana de Chrome real (minimizable) para evadir la deteccion anti-bot
de TikTok en modo headless.

Ejecutar DESDE POWERSHELL/CMD de Windows, no desde otros entornos.
"""
import os
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

COOKIES_FILE = "tiktok_cookies.txt"
UPLOAD_URL = "https://www.tiktok.com/tiktokstudio/upload?from=upload"


def parse_netscape_cookies(path):
    """Convierte cookies.txt (Netscape) a formato Selenium."""
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
            cookie = {
                "name": name,
                "value": value,
                "domain": domain.lstrip("."),
                "path": path_,
                "secure": secure.upper() == "TRUE",
            }
            try:
                exp = int(expires)
                if exp > 0:
                    cookie["expiry"] = exp
            except ValueError:
                pass
            cookies.append(cookie)
    return cookies


def dismiss_overlays(driver):
    """Remueve tutoriales y modales que bloquean interaccion."""
    try:
        driver.execute_script("""
            document.querySelectorAll(
                '#react-joyride-portal, [data-test-id="overlay"], .react-joyride__overlay, ' +
                '.react-joyride__spotlight, .react-joyride__tooltip, [class*="TUXModal-overlay"]'
            ).forEach(el => el.remove());
        """)
    except Exception:
        pass


def upload_to_tiktok(video_path, description="", headless=False):
    """Sube un video a TikTok de forma 100% automatica.

    headless=False (default) abre ventana visible de Chrome - TikTok NO bloquea.
    headless=True abre sin ventana - TikTok puede throttlear la subida.
    """
    if not os.path.exists(COOKIES_FILE):
        raise FileNotFoundError(f"Falta {COOKIES_FILE}")

    abs_video = os.path.abspath(video_path)
    print(f"[TikTok] Subiendo: {os.path.basename(abs_video)}")
    print(f"[TikTok] Descripcion: {description[:80]}")

    cookies = parse_netscape_cookies(COOKIES_FILE)
    tiktok_cookies = [c for c in cookies if "tiktok.com" in c["domain"]]

    options = uc.ChromeOptions()
    options.add_argument("--lang=es-ES")
    options.add_argument("--window-size=1366,900")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-first-run")
    options.add_argument("--disable-extensions")
    # Perfil dedicado estable
    profile_dir = os.path.abspath("chrome_profile")
    os.makedirs(profile_dir, exist_ok=True)
    options.add_argument(f"--user-data-dir={profile_dir}")
    if headless:
        options.add_argument("--headless=new")

    driver = None
    try:
        driver = uc.Chrome(options=options)
        driver.set_page_load_timeout(60)

        print("[TikTok] Cargando tiktok.com para setear cookies...")
        driver.get("https://www.tiktok.com/")
        time.sleep(3)

        for c in tiktok_cookies:
            try:
                driver.add_cookie(c)
            except Exception:
                pass

        print("[TikTok] Navegando a upload...")
        driver.get(UPLOAD_URL)
        time.sleep(8)
        dismiss_overlays(driver)

        print("[TikTok] Cargando video...")
        file_input = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="file"]'))
        )
        file_input.send_keys(abs_video)
        print("[TikTok] Video cargado.")
        time.sleep(5)
        dismiss_overlays(driver)

        print("[TikTok] Buscando campo de descripcion...")
        caption_el = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[contenteditable="true"]'))
        )
        time.sleep(2)
        dismiss_overlays(driver)

        driver.execute_script("arguments[0].click();", caption_el)
        time.sleep(1)
        caption_el.send_keys(Keys.CONTROL + "a")
        caption_el.send_keys(Keys.DELETE)
        time.sleep(0.5)

        print("[TikTok] Escribiendo descripcion...")
        for ch in description:
            caption_el.send_keys(ch)
            time.sleep(0.03)
        time.sleep(2)
        caption_el.send_keys(Keys.ESCAPE)
        time.sleep(1)

        print("[TikTok] Esperando a que termine la subida...")
        last_progress = -1
        stuck_count = 0
        finished = False
        for i in range(240):
            time.sleep(5)
            dismiss_overlays(driver)

            try:
                progress = driver.execute_script("""
                    const text = document.body.innerText;
                    const m = text.match(/(\\d+(?:\\.\\d+)?)\\s*%/);
                    return m ? parseFloat(m[1]) : null;
                """)
                if progress is not None:
                    if progress != last_progress:
                        print(f"[TikTok] Progreso: {progress}%")
                        last_progress = progress
                        stuck_count = 0
                    else:
                        stuck_count += 1

                    if progress >= 100:
                        print("[TikTok] 100% completado")
                        time.sleep(8)
                        finished = True
                        break
                else:
                    if i > 5:
                        print("[TikTok] Procesamiento finalizado")
                        finished = True
                        break
            except Exception:
                pass

            if stuck_count > 96:
                print(f"[TikTok] Atascado en {last_progress}%")
                driver.save_screenshot("tiktok_stuck.png")
                return False

        if not finished:
            print("[TikTok] Timeout esperando subida")
            return False

        dismiss_overlays(driver)
        print("[TikTok] Publicando...")
        for attempt in range(5):
            dismiss_overlays(driver)
            try:
                buttons = driver.find_elements(By.TAG_NAME, "button")
                post_btn = None
                for btn in buttons:
                    try:
                        text = btn.text.strip().lower()
                        if text in ("post", "publicar") and btn.is_enabled() and btn.is_displayed():
                            post_btn = btn
                            break
                    except Exception:
                        continue

                if post_btn:
                    driver.execute_script("arguments[0].click();", post_btn)
                    print("[TikTok] Click en Post enviado")
                    break
            except Exception as e:
                print(f"[TikTok] Intento {attempt+1}: {e}")
            time.sleep(2)

        time.sleep(15)
        driver.save_screenshot("tiktok_after_post.png")
        current_url = driver.current_url
        print(f"[TikTok] URL final: {current_url}")

        if "upload" not in current_url:
            print("[TikTok] Publicacion confirmada")
            return True

        body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        for kw in ["uploaded", "subido", "publicado", "manage posts", "administrar"]:
            if kw in body_text:
                print(f"[TikTok] Detectado: {kw}")
                return True

        print("[TikTok] Sin confirmacion clara. Revisa tiktok_after_post.png")
        return False

    except Exception as e:
        print(f"[TikTok] Error: {e}")
        if driver:
            try:
                driver.save_screenshot("tiktok_error.png")
            except Exception:
                pass
        return False
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
