@echo off
cd /d C:\IAS\IAS_v8_Phase3\IAS_FINAL
echo Forcing Render redeploy...
git commit --allow-empty -m "Force redeploy - clear Render cache"
git push origin main
echo Done. Render will redeploy in 2 minutes.
pause
