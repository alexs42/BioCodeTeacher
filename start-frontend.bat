@echo off
REM Start BioCodeTeacher Frontend

cd /d "%~dp0frontend"

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing dependencies...
    npm install
)

REM Start the dev server
echo Starting BioCodeTeacher frontend on http://localhost:5173
npm run dev
