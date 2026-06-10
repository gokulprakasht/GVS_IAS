@echo off
title IAS v9.0 - GitHub Push Automation
color 0A
cls
echo.
echo  ============================================================
echo   IAS v9.0 - GitHub Push Automation
echo   GVS Technologies  .  Gokul Prakash T
echo   Innovate before you automate
echo  ============================================================
echo.

:: -- CONFIGURATION ---------------------------------------------
set IAS_DIR=C:\IAS\IAS_v9_FINAL\IAS_v9_FINAL
set GITHUB_USER=gokulprakasht
set GITHUB_REPO=IAS_CLOUD
set COMMIT_MSG=IAS v9.0 - Production ready - GVS Technologies

:: -- TOKEN INPUT -----------------------------------------------
echo  Enter your GitHub Personal Access Token
echo  (Get from: github.com/settings/tokens)
echo  Token will NOT be displayed as you type
echo.
set /p GITHUB_TOKEN="  Token: "
echo.

if "%GITHUB_TOKEN%"=="" (
    echo  ERROR: No token entered. Exiting.
    pause
    exit /b 1
)

:: -- NAVIGATE TO IAS FOLDER ------------------------------------
echo  -- SETUP ---------------------------------------------------
cd /d "%IAS_DIR%"
if errorlevel 1 (
    echo  ERROR: Could not navigate to %IAS_DIR%
    pause
    exit /b 1
)
echo  Working directory: %IAS_DIR%

:: -- CREATE .streamlit FOLDER AND CONFIG -----------------------
if not exist ".streamlit" mkdir ".streamlit"
if exist "config.toml" (
    copy /y config.toml .streamlit\config.toml >nul 2>&1
    echo  Copied config.toml to .streamlit\
)

:: -- GIT INIT --------------------------------------------------
echo.
echo  -- GIT SETUP -----------------------------------------------
git --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Git not installed.
    echo  Download from: https://git-scm.com/download/win
    pause
    exit /b 1
)

:: Init if not already a repo
if not exist ".git" (
    git init
    echo  Git repository initialized
) else (
    echo  Git repository already exists
)

:: Set remote
git remote remove origin >nul 2>&1
git remote add origin https://%GITHUB_USER%:%GITHUB_TOKEN%@github.com/%GITHUB_USER%/%GITHUB_REPO%.git
echo  Remote set: github.com/%GITHUB_USER%/%GITHUB_REPO%

:: -- CONFIGURE GIT USER ----------------------------------------
git config user.email "gokul1978@gmail.com"
git config user.name "Gokul Prakash T"

:: -- CREATE .gitignore IF MISSING ------------------------------
if not exist ".gitignore" (
    echo api_key.txt > .gitignore
    echo google_credentials.json >> .gitignore
    echo .streamlit/secrets.toml >> .gitignore
    echo secrets.toml >> .gitignore
    echo data/ >> .gitignore
    echo output/ >> .gitignore
    echo __pycache__/ >> .gitignore
    echo *.pyc >> .gitignore
    echo fix_gcal.* >> .gitignore
    echo check_gcal.* >> .gitignore
    echo  Created .gitignore
)

:: -- STAGE FILES -----------------------------------------------
echo.
echo  -- STAGING FILES -------------------------------------------
git add app.py
echo  Staged: app.py

if exist "requirements.txt" (
    git add requirements.txt
    echo  Staged: requirements.txt
)

if exist "gcal_integration.py" (
    git add gcal_integration.py
    echo  Staged: gcal_integration.py
)

git add .gitignore
echo  Staged: .gitignore

if exist ".streamlit\config.toml" (
    git add .streamlit\config.toml
    echo  Staged: .streamlit\config.toml
)

:: Stage core modules
if exist "core\apikey.py"        git add core\apikey.py
if exist "core\config.py"        git add core\config.py
if exist "core\reporter.py"      git add core\reporter.py
if exist "core\auto_session.py"  git add core\auto_session.py
if exist "core\gmail_monitor.py" git add core\gmail_monitor.py
echo  Staged: core\ modules

:: -- COMMIT ----------------------------------------------------
echo.
echo  -- COMMITTING ----------------------------------------------
git commit -m "%COMMIT_MSG%"
if errorlevel 1 (
    echo  Nothing new to commit - files may already be up to date
)

:: -- PUSH ------------------------------------------------------
echo.
echo  -- PUSHING TO GITHUB ---------------------------------------
git branch -M main
git push -u origin main --force
if errorlevel 1 (
    echo.
    echo  Push failed. Possible reasons:
    echo  1. Token expired or invalid
    echo  2. Repository does not exist
    echo  3. Network issue
    echo.
    echo  Check: github.com/settings/tokens
) else (
    echo.
    echo  ============================================================
    echo   SUCCESS! IAS v9.0 pushed to GitHub
    echo   Repository: github.com/%GITHUB_USER%/%GITHUB_REPO%
    echo  ============================================================
    echo.
    echo  NEXT STEP - Deploy on Streamlit Cloud:
    echo  1. Go to: https://share.streamlit.io
    echo  2. Sign in with GitHub
    echo  3. New app - Repo: %GITHUB_USER%/%GITHUB_REPO%
    echo  4. Branch: main - File: app.py - Deploy
    echo  5. Settings - Secrets - paste your secrets.toml contents
    echo.
    echo  Your app URL will be:
    echo  https://ias-cloud.streamlit.app
    echo  ============================================================
)

:: -- CLEAR TOKEN FROM MEMORY -----------------------------------
set GITHUB_TOKEN=
git remote remove origin >nul 2>&1
git remote add origin https://github.com/%GITHUB_USER%/%GITHUB_REPO%.git

echo.
pause
