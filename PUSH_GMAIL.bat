@echo off
title IAS Gmail Monitor Push
cd /d C:\IAS\IAS_v8_Phase3\IAS_FINAL

echo Copying files...
copy /Y "%USERPROFILE%\Downloads\app.py" "app.py"
copy /Y "%USERPROFILE%\Downloads\gmail_monitor.py" "core\gmail_monitor.py"

echo Adding to git...
git add app.py core/gmail_monitor.py core/config.py

echo Committing...
git commit -m "Feature: continuous Gmail monitor - auto-load interview emails into workflow"
if errorlevel 1 (
    git commit --allow-empty -m "Force redeploy - Gmail monitor"
)

echo Pushing...
git push origin main

echo.
echo DONE - Render redeploys in 3 minutes
echo After deploy: Settings → Notifications → Enter Gmail + App Password → Save and Start Monitor
pause
