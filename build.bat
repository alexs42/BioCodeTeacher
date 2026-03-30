@echo off
setlocal EnableDelayedExpansion
REM ============================================
REM  Build BioCodeTeacher as a packaged application
REM ============================================

echo [1/5] Checking prerequisites...

where npm >nul 2>&1 || (echo ERROR: npm not found in PATH && exit /b 1)

REM Find a compatible Python (3.10-3.13). Python 3.14+ lacks pre-built wheels
REM for pydantic-core and other deps that require Rust compilation.
set "PYTHON_CMD="
for %%V in (3.13 3.12 3.11 3.10) do (
    if not defined PYTHON_CMD (
        py -%%V --version >nul 2>&1 && set "PYTHON_CMD=py -%%V"
    )
)
if not defined PYTHON_CMD (
    REM Fall back to plain "python" and check its version
    where python >nul 2>&1 || (
        echo ERROR: Python not found. Install Python 3.12 or 3.13.
        exit /b 1
    )
    for /f "tokens=2 delims= " %%A in ('python --version 2^>^&1') do set "PY_VER=%%A"
    for /f "tokens=1,2 delims=." %%M in ("!PY_VER!") do (
        set "PY_MAJOR=%%M"
        set "PY_MINOR=%%N"
    )
    if !PY_MAJOR! LSS 3 (
        echo ERROR: Python !PY_VER! is too old. Install Python 3.12 or 3.13.
        exit /b 1
    )
    if !PY_MINOR! LSS 10 (
        echo ERROR: Python !PY_VER! is too old. Install Python 3.12 or 3.13.
        exit /b 1
    )
    if !PY_MINOR! GEQ 14 (
        echo ERROR: Python !PY_VER! is too new. Pre-built wheels are not
        echo        available for Python 3.14+. Install Python 3.12 or 3.13.
        exit /b 1
    )
    set "PYTHON_CMD=python"
)

for /f "tokens=*" %%A in ('!PYTHON_CMD! --version 2^>^&1') do echo       %%A
echo       npm:    OK

echo.
echo [2/5] Building frontend...
cd /d "%~dp0frontend"

REM Pre-clean node_modules to avoid Dropbox partial-sync corruption.
REM lucide-react and other packages can end up with missing icon files
REM when Dropbox locks files mid-install.
if exist "node_modules" (
    echo       Cleaning node_modules for fresh install...
    rd /s /q "node_modules" 2>nul
    if exist "node_modules" (
        echo       Retry - node_modules locked, waiting 3s...
        timeout /t 3 /nobreak >nul
        rd /s /q "node_modules" 2>nul
    )
)

call npm install
if errorlevel 1 (
    echo ERROR: npm install failed
    exit /b 1
)

REM Pre-clean frontend/dist to avoid EBUSY from Dropbox locks during Vite build
if exist "dist" (
    set "FE_CLEAN=0"
    for /L %%i in (1,1,3) do (
        if !FE_CLEAN! EQU 0 (
            rd /s /q "dist" 2>nul
            if not exist "dist" set "FE_CLEAN=1"
            if !FE_CLEAN! EQU 0 (
                echo       Retry %%i/3 - frontend dist locked, waiting 3s...
                timeout /t 3 /nobreak >nul
            )
        )
    )
    if exist "dist" (
        echo WARNING: Could not fully clean frontend\dist - Vite will retry.
    ) else (
        echo       Cleaned frontend dist.
    )
)

call npm run build
if errorlevel 1 (
    echo ERROR: Frontend build failed
    exit /b 1
)
echo       Frontend build: OK

echo.
echo [3/5] Setting up Python build environment...
cd /d "%~dp0"

REM Get target Python major.minor version
for /f "tokens=2 delims= " %%A in ('!PYTHON_CMD! --version 2^>^&1') do set "TARGET_VER=%%A"
for /f "tokens=1,2 delims=." %%M in ("!TARGET_VER!") do set "TARGET_MM=%%M.%%N"

REM If build_venv exists, check its Python matches the target version
if exist "build_venv\Scripts\python.exe" (
    for /f "tokens=2 delims= " %%A in ('build_venv\Scripts\python --version 2^>^&1') do set "VENV_VER=%%A"
    for /f "tokens=1,2 delims=." %%M in ("!VENV_VER!") do set "VENV_MM=%%M.%%N"
    if not "!VENV_MM!"=="!TARGET_MM!" (
        echo       Existing build_venv uses Python !VENV_VER!, need !TARGET_MM! - recreating...
        rd /s /q build_venv
    )
)

if not exist "build_venv" (
    echo       Creating build_venv with Python !TARGET_VER!...
    !PYTHON_CMD! -m venv build_venv
)
call build_venv\Scripts\activate

pip install -q -r backend\requirements.txt
if errorlevel 1 (
    echo ERROR: pip install failed. Check Python version and network.
    exit /b 1
)
pip install -q pyinstaller
if errorlevel 1 (
    echo ERROR: Failed to install PyInstaller.
    exit /b 1
)

echo       Build environment: OK

echo.
echo [4/5] Cleaning previous build output...
REM Pre-clean dist/BioCodeTeacher to avoid PermissionError from Dropbox file locks.
REM PyInstaller's --noconfirm tries this itself but can't retry on locked files.
if exist "dist\BioCodeTeacher" (
    set "CLEAN_OK=0"
    for /L %%i in (1,1,3) do (
        if !CLEAN_OK! EQU 0 (
            rd /s /q "dist\BioCodeTeacher" 2>nul
            if not exist "dist\BioCodeTeacher" set "CLEAN_OK=1"
            if !CLEAN_OK! EQU 0 (
                echo       Retry %%i/3 - dist folder locked, waiting 3s...
                timeout /t 3 /nobreak >nul
            )
        )
    )
    if exist "dist\BioCodeTeacher" (
        echo ERROR: Cannot delete dist\BioCodeTeacher - another process has it locked.
        echo        Close Dropbox or any explorer windows showing that folder, then retry.
        exit /b 1
    )
    echo       Cleaned previous build.
) else (
    echo       No previous build to clean.
)

echo.
echo [5/5] Running PyInstaller...
pyinstaller biocodeteacher.spec --noconfirm

if errorlevel 1 (
    echo ERROR: PyInstaller build failed
    exit /b 1
)

echo.
echo ============================================
echo  Build complete!
echo  Output: dist\BioCodeTeacher\BioCodeTeacher.exe
echo ============================================
echo.
echo To distribute: zip the dist\BioCodeTeacher folder.
echo Users just unzip and double-click BioCodeTeacher.exe.
