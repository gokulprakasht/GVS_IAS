@echo off
echo ============================================
echo IAS v9.0 - Auto Fix and Push
echo ============================================

cd /d C:\IAS\IAS_CLOUD_FULL

echo Step 1: Finding fixed app.py...
set FOUND=0

if exist "%USERPROFILE%\Downloads\app.py" (
    echo Found in Downloads folder
    copy /Y "%USERPROFILE%\Downloads\app.py" "C:\IAS\IAS_CLOUD_FULL\app.py"
    set FOUND=1
)

if %FOUND%==0 (
    echo.
    echo ERROR: Could not find the fixed app.py
    echo Please download it from Claude chat first
    echo Then run this batch file again
    pause
    exit /b 1
)

echo.
echo Step 2: Verifying file...
dir app.py

echo.
echo Step 3: Pushing to GitHub...
git add app.py
git commit -m "Fix: CV upload BytesIO cloud compatible"
git push origin main

echo.
echo ============================================
echo DONE! Streamlit will redeploy in ~60 seconds
echo Visit: https://gvs-ias.streamlit.app
echo ============================================
pause
