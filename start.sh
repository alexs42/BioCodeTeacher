#!/bin/bash
# Start BioCodeTeacher - Backend + Frontend in one command

set -e

DIR="$(dirname "$0")"

# Cleanup on exit (Ctrl+C kills both)
trap 'kill 0' EXIT

echo "Starting BioCodeTeacher..."
"$DIR/start-backend.sh" &
"$DIR/start-frontend.sh" &

wait
