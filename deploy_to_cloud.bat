@echo off
title IAS v8 - Cloud Deploy
cd /d %~dp0

echo ===============================================
echo   IAS v8 - Auto Cloud Deploy to Render
echo ===============================================
echo.

REM Check git installed
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git not installed.
    echo Download from: https://git-scm.com/download/win
    echo Install it, then run this script again.
    pause
    exit /b
)

echo Your GitHub username is: gokulprakasht
echo Your GitHub repo is:     GVS_IAS
echo.

REM Get GitHub token
echo Enter your GitHub Personal Access Token
echo (github.com - Settings - Developer Settings - Personal Access Tokens - Tokens classic - Generate - check repo^)
echo.
set /p GH_TOKEN=GitHub Token: 

echo.
echo [1/3] Setting up local git...
if exist .git rmdir /s /q .git
git init
git add .
git commit -m "IAS v8 complete deploy"
git branch -M main
git remote add origin https://gokulprakasht:%GH_TOKEN%@github.com/gokulprakasht/GVS_IAS.git

echo [2/3] Pushing all files to GitHub...
git push -u origin main --force

if errorlevel 1 (
    echo.
    echo ERROR: Push failed. Check your token and try again.
    pause
    exit /b
)

echo [3/3] Done! Render will auto-redeploy in 2 minutes.
echo.
echo ===============================================
echo   Your live URL: https://gvs-ias.onrender.com
echo   Opens automatically in 10 seconds...
echo ===============================================
echo.
timeout /t 10 >nul
start https://gvs-ias.onrender.com
pause
