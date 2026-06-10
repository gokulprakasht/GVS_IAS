@echo off
title IAS v9.0 — Installation Wizard
color 0B
cls
echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║        IAS v9.0 — Installation Wizard                    ║
echo  ║        GVS Technologies  ·  Gokul Prakash T              ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.
echo  This will install IAS v9.0 on your computer.
echo  Estimated time: 5-10 minutes
echo.
pause

set IAS_DIR=%~dp0
set IAS_DIR=%IAS_DIR:~0,-1%
set ERRORS=0

:: STEP 1: Python
echo.
echo  [STEP 1/6] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo  ❌ Python not found.
    echo.
    echo  Please install Python 3.11:
    echo  1. Go to: https://www.python.org/downloads/
    echo  2. Download Python 3.11
    echo  3. During install: CHECK "Add Python to PATH"
    echo  4. Run INSTALL.bat again
    echo.
    start https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo  ✅ %%v

:: STEP 2: pip upgrade
echo.
echo  [STEP 2/6] Upgrading pip...
python -m pip install --upgrade pip --quiet
echo  ✅ pip updated

:: STEP 3: Install dependencies
echo.
echo  [STEP 3/6] Installing IAS dependencies...
echo  (This may take 3-7 minutes — please wait)
echo.
python -m pip install streamlit>=1.35.0 anthropic>=0.25.0 python-docx>=1.1.0 pypdf>=4.0.0 pandas>=2.0.0 pillow>=10.0.0 --quiet
if errorlevel 1 (
    echo  Retrying with --user flag...
    python -m pip install streamlit anthropic python-docx pypdf pandas pillow --user --quiet
)
echo  ✅ All dependencies installed

:: STEP 4: Folders
echo.
echo  [STEP 4/6] Creating folders...
if not exist "%IAS_DIR%\data" mkdir "%IAS_DIR%\data"
if not exist "%IAS_DIR%\output" mkdir "%IAS_DIR%\output"
if not exist "%IAS_DIR%\output\candidates" mkdir "%IAS_DIR%\output\candidates"
echo  ✅ Folders created

:: STEP 5: Desktop shortcut
echo.
echo  [STEP 5/6] Creating Desktop shortcut...
set SHORTCUT="%USERPROFILE%\Desktop\IAS v9.0.lnk"
set SCRIPT="%TEMP%\create_ias_shortcut.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > %SCRIPT%
echo Set oLink = oWS.CreateShortcut(%SHORTCUT%) >> %SCRIPT%
echo oLink.TargetPath = "%IAS_DIR%\IAS_Start.bat" >> %SCRIPT%
echo oLink.WorkingDirectory = "%IAS_DIR%" >> %SCRIPT%
echo oLink.Description = "IAS v9.0 - AI Interview Assessment System" >> %SCRIPT%
echo oLink.IconLocation = "%SystemRoot%\System32\SHELL32.dll,25" >> %SCRIPT%
echo oLink.Save >> %SCRIPT%
cscript /nologo %SCRIPT%
del %SCRIPT% >nul 2>&1
echo  ✅ Desktop shortcut "IAS v9.0" created

:: STEP 6: API Key setup
echo.
echo  [STEP 6/6] API Key configuration...
if exist "%IAS_DIR%\api_key.txt" (
    for %%A in ("%IAS_DIR%\api_key.txt") do set KSIZE=%%~zA
    if %KSIZE% LSS 40 (
        echo  ⚠️  API key not configured.
        echo.
        echo  You need an Anthropic API key to use IAS:
        echo  1. Go to: https://console.anthropic.com
        echo  2. Create account and generate API key
        echo  3. Paste the key in IAS Settings → API Key
        echo     OR open api_key.txt and paste it there
        echo.
        start https://console.anthropic.com
    ) else (
        echo  ✅ API key configured
    )
) else (
    echo  ⚠️  api_key.txt not found. Configure API key after launch.
)

:: DONE
echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║   ✅ IAS v9.0 INSTALLATION COMPLETE                      ║
echo  ╠══════════════════════════════════════════════════════════╣
echo  ║                                                          ║
echo  ║   To start IAS:                                          ║
echo  ║   • Double-click "IAS v9.0" on your Desktop             ║
echo  ║   • OR double-click IAS_Start.bat in this folder        ║
echo  ║                                                          ║
echo  ║   IAS opens at: http://localhost:8501                    ║
echo  ║                                                          ║
echo  ║   Support: gokul1978@gmail.com                           ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.
set /p LAUNCH="Launch IAS now? (Y/N): "
if /i "%LAUNCH%"=="Y" call "%IAS_DIR%\IAS_Start.bat"
pause
