@echo off
echo ==========================================
echo  FLAX - Instalando dependencias...
echo ==========================================
pip install -r requirements.txt
echo.
echo ==========================================
echo  Instalacion completada.
echo.
echo  PASOS PARA USAR:
echo  1. Ejecuta: python tiktok_auth.py
echo     (Autoriza la app en el navegador)
echo.
echo  2. Ejecuta una vez:
echo     python main.py
echo.
echo  3. Ejecuta en modo automatico (cada hora):
echo     python main.py --loop
echo ==========================================
pause
