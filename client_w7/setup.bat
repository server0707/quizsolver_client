@echo off
setlocal

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

:: ── Tesseract OCR ──────────────────────────────────────────────
tesseract --version >nul 2>&1
if not errorlevel 1 goto tesseract_ok

echo [*] Tesseract OCR yuklab olinmoqda...
set "TESS_FILE=tesseract-ocr-w64-setup-5.3.3.20231005.exe"
if not "%PROCESSOR_ARCHITECTURE%"=="AMD64" set "TESS_FILE=tesseract-ocr-w32-setup-5.3.3.20231005.exe"
set "TESS_URL=https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.3.20231005/%TESS_FILE%"
set "TESS_TMP=%TEMP%\tesseract_setup.exe"
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object Net.WebClient).DownloadFile('%TESS_URL%', '%TESS_TMP%')"
if not exist "%TESS_TMP%" (
    echo [!] Tesseract yuklanmadi. Internetni tekshiring.
    pause & exit /b 1
)
echo [*] Tesseract o'rnatilmoqda (bir oz kuting)...
"%TESS_TMP%" /S
del "%TESS_TMP%"
echo [+] Tesseract o'rnatildi.
goto tesseract_done

:tesseract_ok
echo [+] Tesseract allaqachon mavjud.

:tesseract_done

:: ── Virtual environment ────────────────────────────────────────
if exist "%VENV%" (
    echo [*] Eski .venv uchirilmoqda...
    rmdir /s /q "%VENV%"
)
echo [*] Virtual environment yaratilmoqda...
python -m venv "%VENV%"
if errorlevel 1 ( echo [!] Xato. & pause & exit /b 1 )

echo [*] Paketlar o'rnatilmoqda...
"%VENV%\Scripts\python.exe" -m pip install --quiet --upgrade pip
"%VENV%\Scripts\python.exe" -m pip install --quiet pynput Pillow requests pytesseract
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
