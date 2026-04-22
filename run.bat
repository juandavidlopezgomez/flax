@echo off
REM Ejecuta el agente flax en modo automatico (loop).
REM Doble click en este archivo para iniciar.
cd /d "%~dp0"
echo.
echo ============================================
echo   FLAX - Kick westcol -^> TikTok
echo ============================================
echo.
python main.py --loop --mode unofficial
pause
