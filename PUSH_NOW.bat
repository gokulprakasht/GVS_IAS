@echo off
title IAS Final Fix - Single Push
cd /d C:\IAS\IAS_v8_Phase3\IAS_FINAL

echo ============================================
echo  IAS FINAL FIX - ALL ISSUES IN ONE PUSH
echo ============================================
echo.

echo [1/4] Copying app.py from Downloads...
copy /Y "%USERPROFILE%\Downloads\app.py" "app.py"
if errorlevel 1 (echo ERROR: Could not copy app.py & pause & exit)
echo      OK - app.py copied

echo [2/4] Verifying file size...
for %%A in (app.py) do echo      Size: %%~zA bytes (must be above 800000)

echo [3/4] Git add and commit...
git add app.py
git diff --cached --stat
git commit -m "FINAL FIX: runtime mkdir patch + all config fixes in app.py"
if errorlevel 1 (
    echo Nothing new to commit - forcing empty commit to trigger redeploy...
    git commit --allow-empty -m "Force redeploy - FINAL FIX"
)

echo [4/4] Pushing to GitHub...
git push origin main

echo.
echo ============================================
echo  DONE - Render redeploys in 2-3 minutes
echo  Open: https://gvs-ias.onrender.com
echo ============================================
pause
