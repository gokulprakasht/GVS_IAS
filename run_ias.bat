@echo off
title IAS v8
cd /d %~dp0

echo ===============================================
echo   IAS v8 - Interview Assessment System
echo ===============================================

echo [1/3] Stopping old container...
docker rm -f ias-v8 2>nul

echo [2/3] Building image (3-5 mins first time)...
docker build -t gvstechnologies/ias-v8:latest .

echo [3/3] Starting IAS v8...
docker run -d --name ias-v8 -p 8502:8501 --env-file .env gvstechnologies/ias-v8:latest

echo.
echo ===============================================
echo   IAS v8 RUNNING at http://localhost:8502
echo ===============================================
timeout /t 3 >nul
start http://localhost:8502
pause
