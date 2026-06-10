@echo off
title IAS - Fix Merge Conflict
color 0A
cd /d "C:\IAS\IAS_v9_FINAL\IAS_v9_FINAL"
echo Fixing merge conflict...
python fix_conflict.py
echo.
echo Pushing to GitHub...
git add app.py
git commit -m "Fix merge conflict in app.py"
git push gvsias main
echo.
echo Restarting IAS...
python -m streamlit run app.py --server.port 8503
