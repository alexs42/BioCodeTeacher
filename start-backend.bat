@echo off
REM Start CodeTeacher Backend

cd /d "%~dp0backend"

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install dependencies
pip install -q -r requirements.txt

REM Start the server
echo Starting CodeTeacher API server on http://localhost:8000
uvicorn main:app --reload --host 0.0.0.0 --port 8000
