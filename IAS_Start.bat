@echo off
setlocal enabledelayedexpansion
title IAS v9 - GVS Technologies
color 0A

:: ============================================================
:: IAS v9 - SMART LAUNCHER
:: Self-healing: installs missing packages, fixes PATH issues
:: Only requirement from user: Anthropic API key
:: ============================================================

echo.
echo  ============================================================
echo   IAS v9 -- Interview Assessment System
echo   GVS Technologies / Digitaliotai
echo  ============================================================
echo.

:: ── Q-GATE 1: Python ────────────────────────────────────────
echo [Q1] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo  Python not found. Downloading installer...
    powershell -Command "Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe -OutFile python_installer.exe"
    echo  Installing Python silently...
    python_installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1
    del python_installer.exe
    echo  Python installed. Please restart this bat file.
    pause & exit
)
for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo  %PYVER% found. OK

:: ── Q-GATE 2: pip ───────────────────────────────────────────
echo [Q2] Checking pip...
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo  pip not found. Installing...
    python -m ensurepip --upgrade
)
echo  pip OK

:: ── Q-GATE 3: Install all packages ──────────────────────────
echo [Q3] Installing required packages...
python -m pip install streamlit anthropic python-docx pypdf pandas pillow requests openpyxl google-auth google-auth-oauthlib google-api-python-client -q --disable-pip-version-check
echo  All packages installed. OK

:: ── Q-GATE 4: Verify streamlit ──────────────────────────────
echo [Q4] Verifying streamlit...
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo  Streamlit missing. Force installing...
    python -m pip install streamlit --force-reinstall -q
)
echo  Streamlit OK

:: ── Q-GATE 5: app.py exists ─────────────────────────────────
echo [Q5] Checking app.py...
if not exist app.py (
    echo.
    echo  ERROR: app.py not found in this folder.
    echo  Make sure you are running IAS_Start.bat from inside
    echo  the GVS_IAS-main folder where app.py is located.
    echo.
    pause & exit
)
echo  app.py found. OK

:: ── Q-GATE 6: API Key ───────────────────────────────────────
echo [Q6] Checking API key...
if exist api_key.txt (
    set /p STORED_KEY=<api_key.txt
    if "!STORED_KEY:~0,7!"=="sk-ant-" (
        echo  API key found. OK
        goto LAUNCH
    )
)
echo.
echo  No valid API key found.
set /p API_KEY="  Paste your Anthropic API key (sk-ant-...): "
if "!API_KEY:~0,7!" NEQ "sk-ant-" (
    echo  Invalid key format. Must start with sk-ant-
    pause & exit
)
echo !API_KEY!> api_key.txt
echo  API key saved. OK

:: ── Q-GATE 7: Port 8501 free ────────────────────────────────
:LAUNCH
echo [Q7] Checking port 8501...
netstat -ano | findstr ":8501" >nul 2>&1
if not errorlevel 1 (
    echo  Port 8501 in use. Killing old process...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8501"') do (
        taskkill /PID %%a /F >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
)
echo  Port 8501 ready. OK

:: ── ALL GATES PASSED ────────────────────────────────────────
echo.
echo  ============================================================
echo   ALL Q-GATES PASSED -- Launching IAS v9
echo  ============================================================
echo.
echo  App will open at: http://localhost:8501
echo  Press Ctrl+C to stop IAS
echo.
timeout /t 2 /nobreak >nul
start "" http://localhost:8501
python -m streamlit run app.py --server.port=8501 --server.address=localhost --server.headless=false --browser.gatherUsageStats=false
pause
