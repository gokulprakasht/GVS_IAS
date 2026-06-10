@echo off
title IAS - Fix All Conflicts
color 0A
cd /d "C:\IAS\IAS_v9_FINAL\IAS_v9_FINAL"

echo Step 1: Copying fix script...
copy /y "%~dp0fix_conflict.py" "C:\IAS\IAS_v9_FINAL\IAS_v9_FINAL\fix_conflict.py" >nul 2>&1

echo Step 2: Fixing all merge conflicts...
python "C:\IAS\IAS_v9_FINAL\IAS_v9_FINAL\fix_conflict.py"

echo Step 3: Staging fixed files...
git add app.py .gitignore requirements.txt .streamlit\config.toml

echo Step 4: Committing...
git commit -m "Fix all merge conflicts - IAS v9.0 clean"

echo Step 5: Pushing to GitHub...
git push gvsias main

echo.
echo Step 6: Starting IAS...
python -m streamlit run app.py --server.port 8503
