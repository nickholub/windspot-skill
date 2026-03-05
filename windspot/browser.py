"""Chrome browser process management via CDP."""

import os
import platform
import socket
import subprocess
import sys
import time


def find_chrome_path() -> str | None:
    """Find the Chrome executable on the current system."""
    system = platform.system()
    candidates: list[str] = []

    if system == "Darwin":
        candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        ]
    elif system == "Linux":
        candidates = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
            "/snap/bin/chromium",
        ]
    elif system == "Windows":
        for base in [
            os.environ.get("PROGRAMFILES", ""),
            os.environ.get("PROGRAMFILES(X86)", ""),
            os.environ.get("LOCALAPPDATA", ""),
        ]:
            if base:
                candidates.append(os.path.join(base, "Google", "Chrome", "Application", "chrome.exe"))

    return next((p for p in candidates if os.path.exists(p)), None)


def find_free_port() -> int:
    """Return an available TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def launch_chrome_cdp(
    chrome_path: str | None = None,
    user_data_dir: str | None = None,
    headless: bool = False,
) -> tuple[subprocess.Popen, str, str | None]:
    """Launch Chrome with CDP remote debugging.

    Returns (process, cdp_url, tmp_profile_dir).
    tmp_profile_dir is set only when a temporary profile was created and
    the caller is responsible for deleting it after Chrome exits.
    """
    if not chrome_path:
        chrome_path = find_chrome_path()
    if not chrome_path:
        print("Error: Chrome not found. Install Google Chrome or pass --chrome-path.", file=sys.stderr)
        sys.exit(1)

    port = find_free_port()
    args = [
        chrome_path,
        f"--remote-debugging-port={port}",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-extensions",
    ]
    if headless:
        args.append("--headless=new")

    tmp_profile: str | None = None
    if user_data_dir:
        profile = user_data_dir
    else:
        # Use a persistent profile so login/session can survive between runs.
        profile = os.path.join(os.path.expanduser("~"), ".config", "windspot", "chrome-profile")
        os.makedirs(profile, mode=0o700, exist_ok=True)
    args.append(f"--user-data-dir={profile}")

    proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    cdp_url = f"http://127.0.0.1:{port}"

    for _ in range(20):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                break
        except (ConnectionRefusedError, OSError):
            time.sleep(0.5)
    else:
        proc.kill()
        print("Error: Chrome failed to start with CDP.", file=sys.stderr)
        sys.exit(1)

    print(f"Chrome launched (pid={proc.pid}, port={port})", file=sys.stderr)
    return proc, cdp_url, tmp_profile
