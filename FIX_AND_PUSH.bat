@echo off
title IAS - Fix File Locations and Push
cd /d C:\IAS\IAS_v8_Phase3\IAS_FINAL

echo ============================================
echo  STEP 1: Copy files to correct locations
echo ============================================

echo Copying app.py to root...
copy /Y "%USERPROFILE%\Downloads\app.py" "app.py"

echo Copying gmail_monitor.py to core\ folder...
copy /Y "%USERPROFILE%\Downloads\gmail_monitor.py" "core\gmail_monitor.py"

echo Copying config.py to core\ folder...
copy /Y "%USERPROFILE%\Downloads\config.py" "core\config.py"

echo.
echo ============================================
echo  STEP 2: Verify files are in right place
echo ============================================
echo Checking core\ folder:
dir core\

echo.
echo ============================================
echo  STEP 3: Git add ALL changed files
echo ============================================
git add app.py
git add core\gmail_monitor.py
git add core\config.py

git status

echo.
echo ============================================
echo  STEP 4: Commit and Push
echo ============================================
git commit -m "Fix: gmail_monitor + config in core/ + runtime mkdir patch"
if errorlevel 1 (
    echo Nothing to commit - forcing redeploy...
    git commit --allow-empty -m "Force redeploy - gmail monitor + config fix"
)

git push origin main

echo.
echo ============================================
echo  DONE - Wait 3 minutes then:
echo  1. Open gvs-ias.onrender.com
echo  2. Settings - Notifications
echo  3. Enter Gmail + App Password
echo  4. Click Save and Start Monitor
echo ============================================
pause
