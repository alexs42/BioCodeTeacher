"""
BioCodeTeacher entry point for packaged (PyInstaller) and direct execution.
Starts uvicorn serving the FastAPI app and opens the default browser.
"""

import sys
import os
import socket
import webbrowser
import threading
import time
import uvicorn  # Must be top-level for PyInstaller to detect

# When frozen, ensure _MEIPASS is on sys.path BEFORE app imports
# so that 'from routers import ...' etc. resolve correctly.
if getattr(sys, 'frozen', False):
    base = sys._MEIPASS
    if base not in sys.path:
        sys.path.insert(0, base)

from main import app  # noqa: E402 — must come after sys.path fix


def find_free_port(preferred: int = 8765) -> int:
    """Find a free TCP port, preferring the given port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", preferred))
            return preferred
        except OSError:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]


def open_browser_delayed(port: int, delay: float = 1.5):
    """Open the browser after a short delay to let the server start."""
    time.sleep(delay)
    webbrowser.open(f"http://localhost:{port}")


def main():
    port = find_free_port(8765)

    print("================================================")
    print("  BioCodeTeacher — Bioinformatics Code Educator")
    print("================================================")
    print(f"  Server: http://localhost:{port}")
    print("  Press Ctrl+C to stop.")
    print("================================================")

    # Open browser in background thread
    threading.Thread(target=open_browser_delayed, args=(port,), daemon=True).start()

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
