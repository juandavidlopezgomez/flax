@echo off
REM Prueba: descarga y sube solo 1 clip.
cd /d "%~dp0"
echo.
echo ============================================
echo   FLAX - PRUEBA (1 clip)
echo ============================================
echo.
python main.py --mode unofficial --limit 1
pause
