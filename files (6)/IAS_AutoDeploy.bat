@echo off
title IAS v9.0 - Auto Deploy
color 0A
cd /d "C:\IAS\IAS_v9_FINAL\IAS_v9_FINAL"
copy /y "%~dp0IAS_AutoDeploy.py" "C:\IAS\IAS_v9_FINAL\IAS_v9_FINAL\IAS_AutoDeploy.py" >nul 2>&1
python IAS_AutoDeploy.py
