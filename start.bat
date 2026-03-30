@echo off
REM Start BioCodeTeacher - Backend + Frontend in one command

echo ==========================================
echo   Starting BioCodeTeacher
echo ==========================================
echo.
echo Backend will start in a separate window.
echo Frontend will run here. Press Ctrl+C to stop.
echo.

REM Start backend in a separate minimized window
start "BioCodeTeacher Backend" /MIN cmd /c "%~dp0start-backend.bat"

REM Brief delay to let backend start first
timeout /t 3 /nobreak >nul

REM Start frontend in this window
call "%~dp0start-frontend.bat"
