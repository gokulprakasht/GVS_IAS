@echo off
echo ============================================
echo IAS v9.0 - Direct Patch and Push
echo ============================================

cd /d C:\IAS\IAS_CLOUD_FULL

echo Patching app.py directly...
python patch_app.py

if %ERRORLEVEL% NEQ 0 (
    echo PATCH FAILED
    pause
    exit /b 1
)

echo.
echo Pushing to GitHub...
git add app.py
git commit -m "Fix: CV upload BytesIO cloud compatible"
git push origin main

echo.
echo ============================================
echo DONE! Visit: https://gvs-ias.streamlit.app
echo ============================================
pause
