@echo off
REM BioCodeTeacher Project Verification Script
REM Run this to verify the project is fully functional

cd /d "%~dp0"

echo ==========================================
echo   BioCodeTeacher Project Verification
echo ==========================================
echo.

REM 1. Check backend structure
echo 1. Checking backend structure...
set FAIL=0
for %%f in (
    backend\main.py
    backend\requirements.txt
    backend\routers\repos.py
    backend\routers\files.py
    backend\routers\explain.py
    backend\routers\chat.py
    backend\services\openrouter.py
    backend\services\repo_manager.py
    backend\services\code_parser.py
    backend\services\explanation_cache.py
    backend\models\schemas.py
) do (
    if exist "%%f" (
        echo    [PASS] %%f
    ) else (
        echo    [FAIL] %%f - MISSING
        set FAIL=1
    )
)
if %FAIL%==1 (
    echo    Backend structure check FAILED
    exit /b 1
)

REM 2. Check frontend structure
echo.
echo 2. Checking frontend structure...
set FAIL=0
for %%f in (
    frontend\package.json
    frontend\vite.config.ts
    frontend\src\App.tsx
    frontend\src\main.tsx
    frontend\src\components\code\CodeEditor.tsx
    frontend\src\components\code\FileTree.tsx
    frontend\src\components\explanation\ExplanationPanel.tsx
    frontend\src\components\chat\ChatBox.tsx
    frontend\src\components\setup\SetupModal.tsx
    frontend\src\services\api.ts
    frontend\src\store\codeStore.ts
) do (
    if exist "%%f" (
        echo    [PASS] %%f
    ) else (
        echo    [FAIL] %%f - MISSING
        set FAIL=1
    )
)
if %FAIL%==1 (
    echo    Frontend structure check FAILED
    exit /b 1
)

REM 3. Check test files
echo.
echo 3. Checking test files...
set FAIL=0
for %%f in (
    backend\tests\conftest.py
    backend\tests\test_repos.py
    backend\tests\test_files.py
    backend\tests\test_services.py
) do (
    if exist "%%f" (
        echo    [PASS] %%f
    ) else (
        echo    [FAIL] %%f - MISSING
        set FAIL=1
    )
)
if %FAIL%==1 (
    echo    Test files check FAILED
    exit /b 1
)

REM 4. Run backend tests
echo.
echo 4. Running backend tests...
cd /d "%~dp0backend"
if not exist "venv" (
    echo    Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate
    pip install -q -r requirements.txt
) else (
    call venv\Scripts\activate
)

python -m pytest tests/ -v --tb=short
if %ERRORLEVEL% NEQ 0 (
    echo    [FAIL] Backend tests failed
    exit /b 1
)
echo    [PASS] Backend tests passed

cd /d "%~dp0"

REM 5. Check frontend build
echo.
echo 5. Checking frontend build...
cd /d "%~dp0frontend"
if not exist "node_modules" (
    echo    Installing dependencies...
    call npm install --silent
)

if exist "dist" (
    echo    [PASS] Production build exists
) else (
    echo    Building frontend...
    call npm run build
    if exist "dist" (
        echo    [PASS] Production build created
    ) else (
        echo    [FAIL] Build failed
        exit /b 1
    )
)

cd /d "%~dp0"

echo.
echo ==========================================
echo   ALL VERIFICATIONS PASSED
echo ==========================================
echo.
echo To start the application:
echo   start.bat                  (both servers)
echo   start-backend.bat          (backend only)
echo   start-frontend.bat         (frontend only)
echo.
echo Then open http://localhost:5173 in your browser
