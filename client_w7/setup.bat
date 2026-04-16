@echo off
setlocal EnableDelayedExpansion

set "DIR=%~dp0"
set "VENV=%DIR%.venv"

echo ============================================
echo    QuizSolver Client W7 - Setup
echo ============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [!] Python topilmadi.
    echo     https://www.python.org/downloads/release/python-3810/
    echo     Urnatishda "Add Python to PATH" ni belgilang.
    pause & exit /b 1
)
echo [+] Python topildi.

if exist "%VENV%" (
    echo [*] Eski .venv uchirilmoqda...
    rmdir /s /q "%VENV%"
)
echo [*] Virtual environment yaratilmoqda...
python -m venv "%VENV%"
if errorlevel 1 ( echo [!] Xato. & pause & exit /b 1 )

echo [*] Paketlar o'rnatilmoqda...
"%VENV%\Scripts\python.exe" -m pip install --quiet --upgrade pip
"%VENV%\Scripts\python.exe" -m pip install --quiet pynput Pillow requests
if errorlevel 1 ( echo [!] Paket xatosi. & pause & exit /b 1 )
echo [+] Paketlar tayyor.

echo [*] Desktop shortcut yaratilmoqda...
powershell -NoProfile -ExecutionPolicy Bypass -File "%DIR%make_shortcut.ps1" "%DIR%"

echo.
echo ============================================
echo   Setup tayyor!
echo   Ishga tushirish: Desktop - QuizSolver W7
echo   Ishlatish: chap tugmani 3x bosing
echo ============================================
echo.
pause
