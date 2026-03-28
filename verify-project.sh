#!/bin/bash
# CodeTeacher Project Verification Script
# Run this to verify the project is fully functional

set -e

echo "=========================================="
echo "  CodeTeacher Project Verification"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

PASS="${GREEN}PASS${NC}"
FAIL="${RED}FAIL${NC}"

cd "$(dirname "$0")"

# 1. Check backend structure
echo "1. Checking backend structure..."
BACKEND_FILES=(
    "backend/main.py"
    "backend/requirements.txt"
    "backend/routers/repos.py"
    "backend/routers/files.py"
    "backend/routers/explain.py"
    "backend/routers/chat.py"
    "backend/services/openrouter.py"
    "backend/services/repo_manager.py"
    "backend/services/code_parser.py"
    "backend/services/explanation_cache.py"
    "backend/models/schemas.py"
)

for file in "${BACKEND_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "   [$PASS] $file"
    else
        echo -e "   [$FAIL] $file - MISSING"
        exit 1
    fi
done

# 2. Check frontend structure
echo ""
echo "2. Checking frontend structure..."
FRONTEND_FILES=(
    "frontend/package.json"
    "frontend/vite.config.ts"
    "frontend/src/App.tsx"
    "frontend/src/main.tsx"
    "frontend/src/components/code/CodeEditor.tsx"
    "frontend/src/components/code/FileTree.tsx"
    "frontend/src/components/explanation/ExplanationPanel.tsx"
    "frontend/src/components/chat/ChatBox.tsx"
    "frontend/src/components/setup/SetupModal.tsx"
    "frontend/src/services/api.ts"
    "frontend/src/store/codeStore.ts"
)

for file in "${FRONTEND_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "   [$PASS] $file"
    else
        echo -e "   [$FAIL] $file - MISSING"
        exit 1
    fi
done

# 3. Check test files
echo ""
echo "3. Checking test files..."
TEST_FILES=(
    "backend/tests/conftest.py"
    "backend/tests/test_repos.py"
    "backend/tests/test_files.py"
    "backend/tests/test_services.py"
)

for file in "${TEST_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "   [$PASS] $file"
    else
        echo -e "   [$FAIL] $file - MISSING"
        exit 1
    fi
done

# 4. Run backend tests
echo ""
echo "4. Running backend tests..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
    venv/bin/pip install -q -r requirements.txt
fi

TEST_RESULT=$(venv/bin/python -m pytest tests/ -v --tb=short 2>&1)
PASSED=$(echo "$TEST_RESULT" | grep -oP '\d+(?= passed)')
FAILED=$(echo "$TEST_RESULT" | grep -oP '\d+(?= failed)' || echo "0")

if [ "$FAILED" = "0" ] || [ -z "$FAILED" ]; then
    echo -e "   [$PASS] All $PASSED tests passed"
else
    echo -e "   [$FAIL] $FAILED tests failed"
    echo "$TEST_RESULT"
    exit 1
fi

cd ..

# 5. Check frontend build
echo ""
echo "5. Checking frontend build..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install --silent
fi

if [ -d "dist" ]; then
    echo -e "   [$PASS] Production build exists"
else
    echo "   Building frontend..."
    npm run build --silent
    if [ -d "dist" ]; then
        echo -e "   [$PASS] Production build created"
    else
        echo -e "   [$FAIL] Build failed"
        exit 1
    fi
fi

cd ..

echo ""
echo "=========================================="
echo -e "  ${GREEN}ALL VERIFICATIONS PASSED${NC}"
echo "=========================================="
echo ""
echo "To start the application:"
echo "  1. Backend:  cd backend && ./start-backend.sh"
echo "  2. Frontend: cd frontend && npm run dev"
echo ""
echo "Then open http://localhost:5173 in your browser"
