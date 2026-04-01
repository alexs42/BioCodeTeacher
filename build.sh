#!/usr/bin/env bash
set -euo pipefail

# ============================================
#  Build BioCodeTeacher as a packaged application
#  macOS: produces .app bundle + .dmg installer
#  Linux: produces directory bundle
# ============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

IS_MACOS=false
[[ "$(uname -s)" == "Darwin" ]] && IS_MACOS=true

# ── 1/5  Prerequisites ──────────────────────────────────────────────

echo "[1/5] Checking prerequisites..."

command -v npm >/dev/null 2>&1 || { echo "ERROR: npm not found in PATH"; exit 1; }

# Find a compatible Python (3.10-3.13).
# Python 3.14+ lacks pre-built wheels for pydantic-core and other deps.
PYTHON_CMD=""
for cmd in python3 python; do
    if command -v "$cmd" >/dev/null 2>&1; then
        PY_VER=$("$cmd" --version 2>&1 | awk '{print $2}')
        PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
        PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
        if [[ "$PY_MAJOR" -eq 3 && "$PY_MINOR" -ge 10 && "$PY_MINOR" -le 13 ]]; then
            PYTHON_CMD="$cmd"
            break
        fi
    fi
done

if [[ -z "$PYTHON_CMD" ]]; then
    echo "ERROR: Python 3.10-3.13 not found. Install Python 3.12 or 3.13."
    echo "       Python 3.14+ is not supported (missing pre-built wheels)."
    exit 1
fi

echo "      $($PYTHON_CMD --version 2>&1)"
echo "      npm:    OK"

# ── 2/5  Frontend build ─────────────────────────────────────────────

echo ""
echo "[2/5] Building frontend..."
cd "$SCRIPT_DIR/frontend"

npm install
npm run build

echo "      Frontend build: OK"

# ── 3/5  Python build environment ───────────────────────────────────

echo ""
echo "[3/5] Setting up Python build environment..."
cd "$SCRIPT_DIR"

# Recreate venv if Python version changed or binary is missing
if [[ -d "build_venv" && ! -x "build_venv/bin/python" ]]; then
    echo "      build_venv is corrupted (missing python binary) — recreating..."
    rm -rf build_venv
elif [[ -x "build_venv/bin/python" ]]; then
    VENV_VER=$(build_venv/bin/python --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
    TARGET_VER=$("$PYTHON_CMD" --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
    if [[ "$VENV_VER" != "$TARGET_VER" ]]; then
        echo "      Existing build_venv uses Python $VENV_VER, need $TARGET_VER — recreating..."
        rm -rf build_venv
    fi
fi

if [[ ! -d "build_venv" ]]; then
    echo "      Creating build_venv..."
    "$PYTHON_CMD" -m venv build_venv
fi

# Call venv binaries directly instead of 'source activate' to avoid
# set -u conflicts with activate scripts and PATH pollution.
build_venv/bin/pip install -q -r backend/requirements.txt
build_venv/bin/pip install -q pyinstaller

echo "      Build environment: OK"

# ── 4/5  PyInstaller ────────────────────────────────────────────────

echo ""
echo "[4/5] Cleaning previous build output..."
if [[ -d "dist/BioCodeTeacher" ]]; then
    rm -rf dist/BioCodeTeacher
    echo "      Cleaned previous directory bundle."
fi
if $IS_MACOS && [[ -d "dist/BioCodeTeacher.app" ]]; then
    rm -rf dist/BioCodeTeacher.app
    echo "      Cleaned previous .app bundle."
fi

echo ""
echo "[5/5] Running PyInstaller..."
build_venv/bin/pyinstaller biocodeteacher.spec --noconfirm

# ── DMG creation (macOS only) ───────────────────────────────────────

if $IS_MACOS; then
    echo ""
    echo "Creating DMG installer..."

    DMG_PATH="dist/BioCodeTeacher.dmg"
    APP_PATH="dist/BioCodeTeacher.app"

    if [[ ! -d "$APP_PATH" ]]; then
        echo "ERROR: .app bundle not found at $APP_PATH"
        exit 1
    fi

    # Remove old DMG if present
    [[ -f "$DMG_PATH" ]] && rm -f "$DMG_PATH"

    # Stage .app + Applications symlink for standard drag-and-drop install
    DMG_STAGING="dist/.dmg_staging"
    rm -rf "$DMG_STAGING"
    mkdir -p "$DMG_STAGING"
    cp -R "$APP_PATH" "$DMG_STAGING/"
    ln -s /Applications "$DMG_STAGING/Applications"

    hdiutil create \
        -volname "BioCodeTeacher" \
        -srcfolder "$DMG_STAGING" \
        -ov \
        -format UDZO \
        "$DMG_PATH"

    rm -rf "$DMG_STAGING"

    echo "      DMG created: $DMG_PATH"
fi

# ── Done ────────────────────────────────────────────────────────────

echo ""
echo "============================================"
if $IS_MACOS; then
    echo "  Build complete!"
    echo "  App:  dist/BioCodeTeacher.app"
    echo "  DMG:  dist/BioCodeTeacher.dmg"
    echo "============================================"
    echo ""
    echo "To install: open the DMG and drag BioCodeTeacher to Applications."
    echo "First launch: right-click > Open to bypass Gatekeeper."
else
    echo "  Build complete!"
    echo "  Output: dist/BioCodeTeacher/"
    echo "============================================"
    echo ""
    echo "To run: ./dist/BioCodeTeacher/BioCodeTeacher"
fi
