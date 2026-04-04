# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for BioCodeTeacher single-directory bundle.

Cross-platform:
  Windows: pyinstaller biocodeteacher.spec --noconfirm
  macOS:   pyinstaller biocodeteacher.spec --noconfirm
"""

import os
import platform
from PyInstaller.utils.hooks import collect_all

block_cipher = None

IS_MACOS = platform.system() == 'Darwin'
IS_WINDOWS = platform.system() == 'Windows'

backend_dir = os.path.join('.', 'backend')
frontend_dist = os.path.join('.', 'frontend', 'dist')

# Icon file (platform-specific format, None if not present)
_icns_path = os.path.join('.', 'assets', 'icon.icns')
_ico_path = os.path.join('.', 'assets', 'icon.ico')
if IS_MACOS and os.path.exists(_icns_path):
    app_icon = _icns_path
elif IS_WINDOWS and os.path.exists(_ico_path):
    app_icon = _ico_path
else:
    app_icon = None

# Collect entire packages that PyInstaller's static analysis may miss
uvicorn_datas, uvicorn_binaries, uvicorn_hiddenimports = collect_all('uvicorn')
httpx_datas, httpx_binaries, httpx_hiddenimports = collect_all('httpx')
httpcore_datas, httpcore_binaries, httpcore_hiddenimports = collect_all('httpcore')

a = Analysis(
    [os.path.join(backend_dir, 'run_app.py')],
    pathex=[backend_dir],
    binaries=uvicorn_binaries + httpx_binaries + httpcore_binaries,
    datas=uvicorn_datas + httpx_datas + httpcore_datas + [
        # Frontend static files
        (frontend_dist, 'frontend_dist'),
        # Backend source (string import "main:app" needs these on disk)
        (os.path.join(backend_dir, 'main.py'), '.'),
        (os.path.join(backend_dir, 'routers'), 'routers'),
        (os.path.join(backend_dir, 'services'), 'services'),
        (os.path.join(backend_dir, 'models'), 'models'),
    ],
    hiddenimports=uvicorn_hiddenimports + httpx_hiddenimports + httpcore_hiddenimports + [
        # uvicorn internals
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.loops.asyncio',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.protocols.http.httptools_impl',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.protocols.websockets.websockets_impl',
        'uvicorn.protocols.websockets.wsproto_impl',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        # FastAPI / Starlette
        'fastapi',
        'fastapi.staticfiles',
        'fastapi.responses',
        'starlette.responses',
        'starlette.staticfiles',
        'starlette.websockets',
        'multipart',
        'multipart.multipart',
        # httpx / httpcore
        'httpx',
        'httpx._transports',
        'httpx._transports.default',
        'httpcore',
        'httpcore._async',
        'httpcore._async.http11',
        'httpcore._backends',
        'httpcore._backends.auto',
        'httpcore._backends.anyio',
        'h11',
        'anyio',
        'anyio._backends',
        'anyio._backends._asyncio',
        'sniffio',
        # websockets
        'websockets',
        'websockets.legacy',
        'websockets.legacy.server',
        # pydantic
        'pydantic',
        'pydantic_core',
        # gitpython
        'git',
        'git.cmd',
        'git.repo',
        'git.remote',
        # pathspec
        'pathspec',
        'pathspec.patterns',
        'pathspec.patterns.gitwildmatch',
        # email (required by httpx)
        'email.mime.multipart',
        'email.mime.text',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        'pytest_asyncio',
        'pytest_cov',
        'tkinter',
        '_tkinter',
        'matplotlib',
        'numpy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='BioCodeTeacher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=not IS_MACOS,       # UPX breaks macOS Gatekeeper checks
    console=not IS_MACOS,   # macOS .app should be windowed (opens browser)
    icon=app_icon,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=not IS_MACOS,
    upx_exclude=[],
    name='BioCodeTeacher',
)

# macOS: wrap into a .app bundle
if IS_MACOS:
    app = BUNDLE(
        coll,
        name='BioCodeTeacher.app',
        icon=app_icon,
        bundle_identifier='com.biocodeteacher.app',
        info_plist={
            'CFBundleDisplayName': 'BioCodeTeacher',
            'CFBundleShortVersionString': '0.45',
            'CFBundleVersion': '0.45',
            'NSHighResolutionCapable': True,
            'LSBackgroundOnly': False,
        },
    )
