@echo off
chcp 65001 >nul
title UNO - Pixel Retro

echo ========================================
echo    UNO - Pixel Retro
echo ========================================
echo.

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python no esta instalado.
    echo.
    echo Abriendo pagina de descarga...
    start https://python.org/downloads/
    echo.
    echo 1. Descarga Python (marcar "Add Python to PATH")
    echo 2. Abre el instalador, click INSTALL NOW
    echo 3. Cierra esta ventana y ejecuta "jugar.bat" de nuevo
    echo.
    pause
    exit /b
)

echo [OK] Python encontrado
echo.

echo Instalando dependencias...
pip install pygame -q
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] No se pudo instalar pygame
    pause
    exit /b
)

echo [OK] Dependencias listas
echo.
echo Iniciando juego...
python cliente.py

echo.
pause
