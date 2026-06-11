@echo off
setlocal enabledelayedexpansion
title IAS v9 - GVS Technologies
color 0A
echo.
echo  =============================================
echo   IAS v9 - Interview Assessment System
echo   GVS Technologies / Digitaliotai
echo  =============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found.
    echo Download from https://www.python.org/downloads/
    echo Make sure to tick "Add Python to PATH" during install.
    pause & exit
)

:: Save API key
if not exist api_key.txt (
    set /p KEY="Enter Anthropic API key (sk-ant-...): "
    echo !KEY!> api_key.txt
    echo  API key saved.
)

:: Install dependencies
echo Installing dependencies...
python -m pip install -r requirements.txt -q --disable-pip-version-check

:: Launch using python -m streamlit (works even if streamlit not in PATH)
echo.
echo  Starting IAS v9...
echo  Open browser at: http://localhost:8501
echo.
python -m streamlit run app.py --server.port=8501 --server.address=localhost
pause
