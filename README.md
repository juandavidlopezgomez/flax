# flax

Agente que descarga clips nuevos de un canal de Kick y los sube automaticamente a TikTok.

## Requisitos

- Python 3.10+
- Cuenta en [Kick Developer](https://kick.com/settings/developer)
- Cuenta en [TikTok for Developers](https://developers.tiktok.com/)

## Instalacion

```bash
pip install -r requirements.txt
```

## Configuracion

1. Copia `config.example.py` como `config.py` y llena tus credenciales.
2. Autoriza TikTok:
   ```bash
   python tiktok_auth.py
   ```

## Uso

Ejecutar una vez:
```bash
python main.py
```

Modo automatico (cada hora):
```bash
python main.py --loop
```

## Estructura

```
flax/
├── config.py          # Credenciales (no subir a git)
├── kick_client.py     # Descarga de clips
├── tiktok_auth.py     # Autorizacion OAuth
├── tiktok_client.py   # Subida a TikTok
├── main.py            # Agente principal
└── docs/              # Paginas legales (GitHub Pages)
```

## Legal

- [Terminos de Servicio](https://juandavidlopezgomez.github.io/flax/terms.html)
- [Politica de Privacidad](https://juandavidlopezgomez.github.io/flax/privacy.html)
