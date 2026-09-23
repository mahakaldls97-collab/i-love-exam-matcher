@echo off
title I LOVE EXAM MATCHER
echo Starting website...
start "" "http://localhost:8000"
cd /d "%~dp0backend"
python -m uvicorn main:app --reload --port 8000
pause
