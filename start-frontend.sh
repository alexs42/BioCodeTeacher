#!/bin/bash
# Start CodeTeacher Frontend - Single command setup & run

set -e  # Exit on error

cd "$(dirname "$0")/frontend"

# Install deps if needed, or if package.json is newer than node_modules
if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules/.package-lock.json" ]; then
  echo "Installing dependencies..."
  npm install --silent
fi

echo "Starting CodeTeacher frontend on http://localhost:5173"
npm run dev
