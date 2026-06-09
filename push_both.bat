@echo off
cd /d C:\IAS\IAS_v8_Phase3\IAS_FINAL

echo Copying app.py...
copy /Y "%USERPROFILE%\Downloads\app.py" "app.py"

echo Copying config.py...
copy /Y "%USERPROFILE%\Downloads\config.py" "core\config.py"

echo Git status...
git status

echo Adding both files...
git add app.py core/config.py

echo Committing...
git commit -m "Fix FileNotFoundError: auto-create data/ dir on Render + UX left-menu settings"

echo Pushing...
git push origin main

echo.
echo Done. Render redeploys in 2 minutes.
pause
