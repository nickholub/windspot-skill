"""Command-line interface for WindSpotExtract."""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys

from .auth import get_keychain_credentials
from .browser import launch_chrome_cdp
from .models import parse_spot_id
from .scraper import run


def format_output(result: dict) -> str:
    """Format a result dict as human-readable text."""
    lines = [
        f"🏄 {result['spot_name']} — {result['model']} Forecast",
        f"📍 {result['url']}",
        f"📸 Forecast: {result['forecast_screenshot']}",
        f"📸 Tides: {result['tides_screenshot']}",
        "",
    ]

    if result.get("tide_schedule"):
        lines.append("📊 Tide Schedule:")
        for e in result["tide_schedule"]:
            ht = e["height"]
            ht_str = f"{ht:.1f}ft" if isinstance(ht, float) else f"{ht}ft"
            line = f"  • {e['time']} -> {ht_str} ({e['label']})"
            if e["label"] in {"low", "high"}:
                line = f"**{line}**"
            lines.append(line)
    elif result["tides"]:
        lines.append("📊 Tides:")
        for t in result["tides"]:
            lines.append(f"  • {t['type']} Tide {t['time']} — {t['height']} ft")

    if result["crossings_3ft"]:
        lines.append("")
        lines.append("🎯 3ft Crossings:")
        for i, c in enumerate(result["crossings_3ft"], 1):
            lines.append(f"  {i}. ~{c['time']} ({c['direction']}, {c['from']}→{c['to']})")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract iKitesurf wind forecast and tide data")
    parser.add_argument("spot", help="Spot ID or URL (e.g. 427 or https://wx.ikitesurf.com/spot/427)")
    parser.add_argument("--output-dir", "-o", default="/tmp/windspot", help="Output directory (default: /tmp/windspot)")
    parser.add_argument("--model", "-m", default="blend", help="Forecast model (default: blend)")
    parser.add_argument("--headless", action="store_true", help="Run Chrome in headless mode")
    parser.add_argument("--chrome-path", help="Path to Chrome executable (auto-detected if omitted)")
    parser.add_argument("--cdp-url", help="Connect to an already-running Chrome instance via CDP URL")
    parser.add_argument("--user-data-dir", help="Chrome user data directory for persistent session")
    parser.add_argument("--width", type=int, default=1200, help="Viewport width (default: 1200)")
    parser.add_argument("--height", type=int, default=900, help="Viewport height (default: 900)")
    parser.add_argument("--3ft", dest="calc_3ft", action="store_true", help="Calculate 3ft tide crossing times")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--open", dest="open_preview", action="store_true", default=False, help="Open screenshots in Preview after capture")
    parser.add_argument("--no-login", action="store_true", help="Skip authentication (anonymous mode)")
    args = parser.parse_args()

    spot_id = parse_spot_id(args.spot)

    username, password = None, None
    if not args.no_login:
        username, password = get_keychain_credentials()
        if username and password:
            print("Using credentials from macOS Keychain.", file=sys.stderr)
        else:
            print(
                "No credentials found in Keychain. Running anonymously.\n"
                "To store credentials: security add-generic-password -s ikitesurf -a user@email.com -w password -U",
                file=sys.stderr,
            )

    chrome_proc = None
    chrome_tmp_profile = None
    cdp_url = args.cdp_url
    if not cdp_url:
        chrome_proc, cdp_url, chrome_tmp_profile = launch_chrome_cdp(
            chrome_path=args.chrome_path,
            user_data_dir=args.user_data_dir,
            headless=args.headless,
        )

    try:
        result = run(
            spot_id=spot_id,
            output_dir=args.output_dir,
            model=args.model,
            cdp_url=cdp_url,
            username=username,
            password=password,
            viewport_width=args.width,
            viewport_height=args.height,
            calc_3ft=args.calc_3ft,
        )

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(format_output(result))

        if args.open_preview and platform.system() == "Darwin":
            screenshots = [result["forecast_screenshot"]]
            if result.get("tides_screenshot"):
                screenshots.append(result["tides_screenshot"])
            subprocess.run(["open"] + screenshots, check=False)
    finally:
        if chrome_proc:
            chrome_proc.terminate()
            try:
                chrome_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                chrome_proc.kill()
            print("Chrome stopped.", file=sys.stderr)
        if chrome_tmp_profile and os.path.isdir(chrome_tmp_profile):
            shutil.rmtree(chrome_tmp_profile, ignore_errors=True)
            print(f"Chrome temp profile removed: {chrome_tmp_profile}", file=sys.stderr)


if __name__ == "__main__":
    main()
