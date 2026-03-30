# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for BioCodeTeacher single-directory bundle.
Run: pyinstaller codeteacher.spec --noconfirm
"""

import os
from PyInstaller.utils.hooks import collect_all

block_cipher = None

backend_dir = os.path.join('.', 'backend')
frontend_dist = os.path.join('.', 'frontend', 'dist')

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
    upx=True,
    console=True,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BioCodeTeacher',
)
