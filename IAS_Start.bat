@echo off
title IAS v9 — GVS Technologies
color 0A
echo.
echo  =============================================
echo   IAS v9 — Interview Assessment System
echo   GVS Technologies / Digitaliotai
echo  =============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (echo ERROR: Python not found. Install from python.org & pause & exit)

:: Check API key
if not exist api_key.txt (
    set /p KEY="Enter Anthropic API key (sk-ant-...): "
    echo !KEY!> api_key.txt
)

:: Install dependencies
echo Installing dependencies...
pip install -r requirements.txt -q

:: Launch
echo.
echo  Starting IAS v9...
echo  Open browser at: http://localhost:8501
echo.
streamlit run app.py --server.port=8501
pause
