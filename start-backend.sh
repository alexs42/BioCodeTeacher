#!/bin/bash
# Start BioCodeTeacher Backend - Single command setup & run

set -e  # Exit on error

cd "$(dirname "$0")/backend"

# Create venv if needed (use python3 for Debian/Ubuntu compatibility)
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate and install deps quietly, then start server
source venv/bin/activate
pip install -q -r requirements.txt
echo "Starting BioCodeTeacher API server on http://localhost:8000"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
