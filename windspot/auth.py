"""macOS Keychain authentication for iKitesurf."""

import platform
import re
import subprocess


def get_keychain_credentials(service: str = "ikitesurf") -> tuple[str | None, str | None]:
    """Read username and password from macOS Keychain.

    Returns (username, password) or (None, None) if not found.
    Store credentials with:
        security add-generic-password -s ikitesurf -a user@email.com -w password -U
    """
    if platform.system() != "Darwin":
        return None, None
    try:
        pw_result = subprocess.run(
            ["security", "find-generic-password", "-s", service, "-w"],
            capture_output=True, text=True, timeout=5,
        )
        if pw_result.returncode != 0:
            return None, None

        info_result = subprocess.run(
            ["security", "find-generic-password", "-s", service],
            capture_output=True, text=True, timeout=5,
        )
        username = None
        for line in info_result.stdout.splitlines():
            if '"acct"' in line:
                m = re.search(r'"acct"<blob>="(.+?)"', line)
                if m:
                    username = m.group(1)
                break

        return username, pw_result.stdout.strip()
    except Exception:
        return None, None
