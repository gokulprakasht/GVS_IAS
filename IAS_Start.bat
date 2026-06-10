@echo off
title IAS v9.0 - Smart Launcher
color 0A
cls
echo.
echo  ============================================================
echo   IAS v9.0 - Interview Assessment System
echo   GVS Technologies  .  Gokul Prakash T
echo   Innovate before you automate
echo  ============================================================
echo.

set IAS_DIR=%~dp0
set IAS_DIR=%IAS_DIR:~0,-1%
set ERRORS=0

echo  -- PRE-CHECKS ----------------------------------------------
echo.

:: CHECK 1: Python
echo  [1/7] Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo        FAIL: Python not found
    echo        Install Python 3.11 from python.org
    echo        CHECK "Add Python to PATH" during install
    set /a ERRORS+=1
) else (
    for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo        PASS: %%v found
)

:: CHECK 2: app.py
echo  [2/7] IAS application file...
if not exist "%IAS_DIR%\app.py" (
    echo        FAIL: app.py not found in %IAS_DIR%
    set /a ERRORS+=1
) else (
    for %%A in ("%IAS_DIR%\app.py") do echo        PASS: app.py found ^(%%~zA bytes^)
)

:: CHECK 3: API key [FIXED - uses findstr, no setlocal/endlocal scope issue]
echo  [3/7] Anthropic API key...
if not exist "%IAS_DIR%\api_key.txt" (
    echo        FAIL: api_key.txt missing
    echo        Create api_key.txt in the IAS folder and paste your key
    set /a ERRORS+=1
) else (
    findstr /b "sk-ant-" "%IAS_DIR%\api_key.txt" >nul 2>&1
    if errorlevel 1 (
        echo        FAIL: API key missing or invalid
        echo        Open api_key.txt and paste your Anthropic API key
        echo        Get key from: console.anthropic.com
        set /a ERRORS+=1
    ) else (
        echo        PASS: API key found and valid
    )
)

:: CHECK 4: Core modules
echo  [4/7] Core modules...
set CORE_OK=1
for %%F in (apikey.py config.py reporter.py auto_session.py gmail_monitor.py) do (
    if not exist "%IAS_DIR%\core\%%F" (
        echo        FAIL: core\%%F missing
        set CORE_OK=0
    )
)
if "%CORE_OK%"=="1" (
    echo        PASS: All core modules present
) else (
    set /a ERRORS+=1
)

:: CHECK 5: Streamlit
echo  [5/7] Streamlit framework...
python -m streamlit --version >nul 2>&1
if errorlevel 1 (
    echo        Streamlit not found. Installing now...
    python -m pip install streamlit anthropic python-docx pypdf --quiet
    if errorlevel 1 (
        echo        FAIL: Could not install Streamlit
        set /a ERRORS+=1
    ) else (
        echo        PASS: Streamlit installed successfully
    )
) else (
    for /f "tokens=*" %%v in ('python -m streamlit --version 2^>^&1') do echo        PASS: %%v
)

:: CHECK 6: Folders
echo  [6/7] Required folders...
if not exist "%IAS_DIR%\data" mkdir "%IAS_DIR%\data"
if not exist "%IAS_DIR%\output" mkdir "%IAS_DIR%\output"
if not exist "%IAS_DIR%\output\candidates" mkdir "%IAS_DIR%\output\candidates"
echo        PASS: data\ and output\candidates\ ready

:: CHECK 7: Port
echo  [7/7] Network port...
set PORT=8501
netstat -an 2>nul | find "LISTENING" | find ":8501" >nul 2>&1
if not errorlevel 1 (
    echo        Port 8501 busy. Trying 8502...
    set PORT=8502
    netstat -an 2>nul | find "LISTENING" | find ":8502" >nul 2>&1
    if not errorlevel 1 (
        echo        Port 8502 busy. Trying 8503...
        set PORT=8503
        netstat -an 2>nul | find "LISTENING" | find ":8503" >nul 2>&1
        if not errorlevel 1 set PORT=8504
    )
)
echo        PASS: Using port %PORT%

echo.
echo  ------------------------------------------------------------

if %ERRORS% GTR 0 (
    echo.
    echo  FAILED: %ERRORS% pre-check^(s^) did not pass.
    echo  Fix the issues above and run IAS_Start.bat again.
    echo.
    pause
    exit /b 1
)

echo  ALL PRE-CHECKS PASSED ^(7/7^) - Starting IAS...
echo.

:: CLEANUP
echo  -- CLEANUP -------------------------------------------------
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak >nul
if exist "%APPDATA%\.streamlit\cache" rd /s /q "%APPDATA%\.streamlit\cache" >nul 2>&1
echo  Old processes stopped. Cache cleared.
echo.

:: LAUNCH
echo  -- LAUNCHING IAS v9.0 -------------------------------------
cd /d "%IAS_DIR%"
echo  Opening browser at http://localhost:%PORT%
echo  Keep this window open while using IAS
echo  Press Ctrl+C to stop IAS
echo.
echo  ============================================================
echo   IAS v9.0 is LIVE at http://localhost:%PORT%
echo  ============================================================
echo.

start /b cmd /c "timeout /t 5 /nobreak >nul && start http://localhost:%PORT%"

python -m streamlit run app.py --server.port %PORT% --server.headless true --browser.gatherUsageStats false --server.runOnSave true --server.maxUploadSize 200

:: POST-CHECKS
echo.
echo  -- POST-CHECKS ---------------------------------------------
echo.

if exist "%IAS_DIR%\data\session.json" (
    for %%A in ("%IAS_DIR%\data\session.json") do echo  PASS: Session saved ^(%%~zA bytes^)
) else (
    echo  INFO: No session file ^(no interview conducted this run^)
)

set DOCX_COUNT=0
for /r "%IAS_DIR%\output" %%F in (*.docx) do set /a DOCX_COUNT+=1
echo  PASS: DOCX reports in output\candidates\: %DOCX_COUNT%

set FOLDER_COUNT=0
for /d %%D in ("%IAS_DIR%\output\candidates\*") do set /a FOLDER_COUNT+=1
echo  PASS: Candidate folders stored: %FOLDER_COUNT%

if exist "%IAS_DIR%\data\settings.json" (
    echo  PASS: Settings preserved for next session
) else (
    echo  INFO: No settings saved yet
)

echo.
echo  ------------------------------------------------------------
echo  IAS v9.0 session complete.
echo  GVS Technologies  .  gokul1978@gmail.com
echo  ------------------------------------------------------------
echo.
pause
