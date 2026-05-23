@echo off
chcp 65001 >nul
title Compilation MailCentPro.exe

echo.
echo ╔══════════════════════════════════════════════╗
echo ║   Compilation de MailCentPro.exe           ║
echo ╚══════════════════════════════════════════════╝
echo.

REM ── Vérifier que Python est installé ──────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python n'est pas installé ou pas dans le PATH.
    echo.
    echo Téléchargez Python sur https://www.python.org/downloads/
    echo Cochez bien "Add Python to PATH" lors de l'installation.
    echo.
    pause
    exit /b 1
)

echo ✅ Python détecté :
python --version
echo.

REM ── Installer PyInstaller ──────────────────────────────────────────────────
echo 📦 Installation de PyInstaller...
pip install pyinstaller --quiet
if errorlevel 1 (
    echo ❌ Échec installation PyInstaller.
    pause
    exit /b 1
)
echo ✅ PyInstaller prêt.
echo.

REM ── Compiler ──────────────────────────────────────────────────────────────
echo 🔨 Compilation en cours, merci de patienter...
echo.

pyinstaller --onefile --windowed --name "MailCentPro" --clean mailcentpro.py

if errorlevel 1 (
    echo.
    echo ❌ La compilation a échoué. Consultez les messages ci-dessus.
    pause
    exit /b 1
)

REM ── Copier le .exe à la racine ─────────────────────────────────────────────
copy /Y "dist\MailCentPro.exe" "MailCentPro.exe" >nul

REM ── Nettoyage ──────────────────────────────────────────────────────────────
rmdir /S /Q build >nul 2>&1
rmdir /S /Q dist  >nul 2>&1
del /Q *.spec     >nul 2>&1

echo.
echo ╔══════════════════════════════════════════════╗
echo ║   ✅ Compilation réussie !                   ║
echo ║                                              ║
echo ║   → MailCentPro.exe créé                  ║
echo ║                                              ║
echo ║   Placez le .exe à côté du dossier data/    ║
echo ║   et double-cliquez pour lancer.             ║
echo ╚══════════════════════════════════════════════╝
echo.
pause
