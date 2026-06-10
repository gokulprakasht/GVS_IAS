@echo off
title IAS v9.0 - Streamlit Cloud Deploy Guide
color 0A
cls
echo.
echo  ============================================================
echo   IAS v9.0 - Streamlit Cloud Deployment
echo   GVS Technologies  .  Gokul Prakash T
echo   Innovate before you automate
echo  ============================================================
echo.

set IAS_DIR=C:\IAS\IAS_v9_FINAL\IAS_v9_FINAL
cd /d "%IAS_DIR%"

echo  -- STEP 1: Verify GitHub repo is live ---------------------
echo.
echo  Opening your GitHub repository...
start https://github.com/gokulprakasht/IAS_CLOUD
timeout /t 3 /nobreak >nul

echo  Confirm you can see app.py in the repo.
echo  Press any key when ready to continue...
pause >nul

echo.
echo  -- STEP 2: Open Streamlit Cloud ---------------------------
echo.
echo  Opening Streamlit Cloud...
start https://share.streamlit.io
echo.
echo  Instructions:
echo  1. Sign in with GitHub (gokulprakasht)
echo  2. Click "Create app"
echo  3. Select: gokulprakasht/IAS_CLOUD
echo  4. Branch: main
echo  5. Main file path: app.py
echo  6. App URL: ias-cloud  (gives you ias-cloud.streamlit.app)
echo  7. Click "Deploy!"
echo.
echo  Press any key when app is deploying...
pause >nul

echo.
echo  -- STEP 3: Generate secrets.toml --------------------------
echo.
echo  Collecting your configuration...
echo.

:: Read API key
set /p ANTHRO_KEY="  Paste your Anthropic API key: "
echo.

:: Read Gmail
set /p GMAIL_ADDR="  Your Gmail address [gokul1978@gmail.com]: "
if "%GMAIL_ADDR%"=="" set GMAIL_ADDR=gokul1978@gmail.com
set /p GMAIL_PWD="  Your Gmail App Password (16 chars): "
echo.

:: Write secrets file
set SECRETS_FILE=%IAS_DIR%\streamlit_secrets_PASTE_THIS.toml

echo # Paste this ENTIRE content into Streamlit Cloud > "%SECRETS_FILE%"
echo # App: gokulprakasht/IAS_CLOUD >> "%SECRETS_FILE%"
echo # Settings - Secrets - paste and save >> "%SECRETS_FILE%"
echo. >> "%SECRETS_FILE%"
echo ANTHROPIC_API_KEY = "%ANTHRO_KEY%" >> "%SECRETS_FILE%"
echo. >> "%SECRETS_FILE%"
echo GMAIL_SENDER     = "%GMAIL_ADDR%" >> "%SECRETS_FILE%"
echo GMAIL_APP_PWD    = "%GMAIL_PWD%" >> "%SECRETS_FILE%"
echo RECRUITER_EMAIL  = "interviews@empowerprofessionals.com" >> "%SECRETS_FILE%"
echo INTERVIEWER_NAME = "Gokul Prakash T" >> "%SECRETS_FILE%"
echo. >> "%SECRETS_FILE%"

:: Read Google Calendar JSON
echo  Reading google_credentials.json...
if exist "%IAS_DIR%\google_credentials.json" (
    echo GCAL_CALENDAR_ID = "primary" >> "%SECRETS_FILE%"
    echo. >> "%SECRETS_FILE%"
    :: Write gcal json as multiline
    echo GCAL_CREDS_JSON = ''' >> "%SECRETS_FILE%"
    type "%IAS_DIR%\google_credentials.json" >> "%SECRETS_FILE%"
    echo. >> "%SECRETS_FILE%"
    echo ''' >> "%SECRETS_FILE%"
    echo  Google Calendar credentials added
) else (
    echo GCAL_CREDS_JSON  = "" >> "%SECRETS_FILE%"
    echo GCAL_CALENDAR_ID = "primary" >> "%SECRETS_FILE%"
    echo  WARNING: google_credentials.json not found - add manually
)

echo.
echo  ============================================================
echo   Secrets file created:
echo   %SECRETS_FILE%
echo  ============================================================
echo.
echo  Opening secrets file in Notepad...
notepad "%SECRETS_FILE%"

echo.
echo  -- STEP 4: Add secrets to Streamlit Cloud -----------------
echo.
echo  Instructions:
echo  1. Copy ALL contents of the file that just opened
echo  2. Go to Streamlit Cloud (already open in browser)
echo  3. Click your app - top right "..." menu
echo  4. Click "Settings"
echo  5. Click "Secrets" tab
echo  6. Paste everything and click "Save"
echo  7. App will restart automatically
echo.
echo  Opening Streamlit Cloud app settings...
start https://share.streamlit.io
echo.
echo  -- STEP 5: Verify deployment -------------------------------
echo.
echo  After saving secrets, your app will restart.
echo  Open your live app at:
echo.
echo   https://ias-cloud.streamlit.app
echo.
echo  Opening app now...
timeout /t 5 /nobreak >nul
start https://ias-cloud.streamlit.app

echo.
echo  ============================================================
echo   IAS v9.0 is LIVE on Streamlit Cloud!
echo   URL: https://ias-cloud.streamlit.app
echo   Repo: github.com/gokulprakasht/IAS_CLOUD
echo  ============================================================
echo.

:: Clear sensitive vars
set ANTHRO_KEY=
set GMAIL_PWD=

pause
