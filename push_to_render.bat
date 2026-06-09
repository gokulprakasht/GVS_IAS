@echo off
title IAS v8 - Push to Render
cd /d C:\IAS\IAS_v8_Phase3\IAS_FINAL

echo ===============================================
echo   IAS v8 - Deploying Phase 3 to Render
echo ===============================================

echo [1/6] Removing old git...
if exist .git rmdir /s /q .git

echo [2/6] Wiping secrets...
echo. > .env
echo. > api_key.txt

echo [3/6] Creating .gitignore...
echo .env > .gitignore
echo api_key.txt >> .gitignore

echo [4/6] Committing...
git init
git add .
git commit -m "IAS v8 Phase 3"
git branch -M main

echo [5/6] Enter your GitHub token when asked...
git remote add origin https://github.com/gokulprakasht/GVS_IAS.git
git push origin main --force

echo.
echo ===============================================
echo   LIVE in 2 mins: https://gvs-ias.onrender.com
echo ===============================================
timeout /t 5 >nul
start https://gvs-ias.onrender.com
pause
