# Como obtener las cookies de TikTok

El uploader no oficial necesita tu sesion de TikTok para subir videos.
Debes exportar las cookies del navegador donde estas logueado.

## Paso 1: Instalar extension

Instala una de estas extensiones en Chrome (o tu navegador):
- **Get cookies.txt LOCALLY** (recomendada, no envia datos a servidores)
- **EditThisCookie**
- **Cookie-Editor**

Link directo (Chrome Web Store):
https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc

## Paso 2: Loguearte en TikTok

1. Ve a https://www.tiktok.com
2. Inicia sesion con la cuenta donde quieres subir los videos
3. Asegurate de que funciona (puedes ver tu perfil)

## Paso 3: Exportar cookies

Con la extension "Get cookies.txt LOCALLY":
1. Abre tiktok.com
2. Click en el icono de la extension
3. Click en "Export As" -> "Netscape HTTP Cookie File"
4. Guarda el archivo como `tiktok_cookies.txt`

## Paso 4: Colocar el archivo

Pon `tiktok_cookies.txt` en la carpeta del proyecto flax:
```
C:\Users\juand\Documents\flax\tiktok_cookies.txt
```

## IMPORTANTE

- Las cookies caducan cada 30-60 dias, tendras que renovarlas
- NO compartas este archivo con nadie (da acceso a tu cuenta)
- El archivo ya esta en .gitignore, no se sube a GitHub

## Formato esperado

El archivo debe verse asi (formato Netscape):
```
# Netscape HTTP Cookie File
.tiktok.com    TRUE    /    TRUE    1234567890    sessionid    abc123...
.tiktok.com    TRUE    /    TRUE    1234567890    tt_csrf_token    xyz...
...
```
