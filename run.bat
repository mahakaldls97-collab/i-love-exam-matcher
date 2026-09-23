@echo off
echo.
echo =========================================
echo   Exam Answer Matcher - Starting Server
echo =========================================
echo.
cd /d "%~dp0backend"
if not exist ".env" (
    echo [ERROR] .env file नहीं मिली!
    echo.
    echo backend\.env.example को backend\.env के रूप में copy करें
    echo और उसमें अपना GEMINI_API_KEY डालें।
    pause
    exit /b 1
)
echo Server starting at: http://localhost:8000
echo.
echo Browser में यह address खोलें: http://localhost:8000
echo.
echo (Server बंद करने के लिए Ctrl+C दबाएं)
echo.
uvicorn main:app --reload --port 8000
pause
