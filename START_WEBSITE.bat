@echo off
title I LOVE EXAM MATCHER - Web Server
color 0B
echo.
echo =======================================================
echo          I LOVE EXAM MATCHER - SERVER STARTING
echo =======================================================
echo.
echo  Website Address: http://localhost:8000
echo.
echo  Opening browser automatically in 2 seconds...
echo.

start "" "http://localhost:8000"

cd /d "%~dp0backend"
python -m uvicorn main:app --reload --port 8000

pause
