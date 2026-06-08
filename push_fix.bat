@echo off
echo IAS Licence Gate Fix
echo =====================
cd /d C:\IAS\IAS_v8_Phase3\IAS_FINAL

echo Step 1: Copying new app.py from Downloads...
copy /Y "%USERPROFILE%\Downloads\app.py" "app.py"

echo Step 2: Checking file size...
for %%A in (app.py) do echo File size: %%~zA bytes

echo Step 3: Force-touching file to trigger git change detection...
copy /b app.py +,,

echo Step 4: Git status...
git status

echo Step 5: Adding...
git add app.py

echo Step 6: Committing...
git commit -m "Fix licence gate - CV upload always visible"

echo Step 7: Pushing...
git push origin main

echo Done. Check Render dashboard in 2 minutes.
pause
