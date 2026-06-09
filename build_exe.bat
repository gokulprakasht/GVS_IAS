@echo off
title IAS v8 - Build EXE
cd /d %~dp0

echo ===============================================
echo   IAS v8 - Building Windows EXE
echo ===============================================

python -m pip install pyinstaller --quiet

python -m PyInstaller --onefile --console --name "IAS_v8" ias_launcher.py

if exist dist\IAS_v8.exe (
    copy /Y dist\IAS_v8.exe IAS_v8.exe
    echo.
    echo ===============================================
    echo   SUCCESS! IAS_v8.exe is ready in THIS folder
    echo   Double-click IAS_v8.exe to launch IAS v8
    echo ===============================================
) else (
    echo ERROR: Build failed. Check output above.
)
pause
