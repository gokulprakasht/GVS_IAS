@echo off
echo ============================================
echo IAS v9.0 - FINAL FIX AND PUSH
echo ============================================
cd /d C:\IAS\IAS_CLOUD_FULL
echo Applying fixes...
python FINAL_FIX.py
if %ERRORLEVEL% NEQ 0 (echo FAILED & pause & exit /b 1)
echo.
echo Pushing to GitHub...
git add app.py
git commit -m "FINAL: CV upload + API key cloud fix"
git push origin main
echo.
echo DONE! https://gvs-ias.streamlit.app
echo Wait 60 seconds then test CV upload.
pause
