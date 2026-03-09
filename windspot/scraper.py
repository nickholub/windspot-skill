"""Core browser automation and iKitesurf scraping logic."""

import json
import os
import sys
import time
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Error: playwright not installed. Run: pip install playwright && playwright install chromium", file=sys.stderr)
    sys.exit(1)

from .models import PREMIUM_MODELS, resolve_model_name
from .tides import calc_3ft_crossings, calc_crossings_at, build_tide_schedule

_SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "page_scripts.js")
_PAGE_SCRIPTS_JS = open(_SCRIPT_PATH).read() if os.path.exists(_SCRIPT_PATH) else ""


def login_ikitesurf(page, username: str, password: str) -> bool:
    """Log in to iKitesurf via the Sign In modal. Returns True on success."""
    print("Logging in to iKitesurf...", file=sys.stderr)
    page.goto("https://wx.ikitesurf.com/", wait_until="domcontentloaded", timeout=30000)
    time.sleep(2)

    page.evaluate("() => PageScripts.clickSignIn()")
    time.sleep(1)

    try:
        page.wait_for_selector('input[type="password"]', timeout=15000)
    except Exception:
        print("Warning: Could not find login form.", file=sys.stderr)
        return False
    time.sleep(1)

    page.locator('input[type="email"], input[type="text"]').first.fill(username)
    pw_field = page.locator('input[type="password"]').first
    pw_field.fill(password)
    pw_field.press("Enter")
    time.sleep(5)

    if page.evaluate("() => PageScripts.isLoginFormVisible()"):
        print("Warning: Login may have failed (password field still visible).", file=sys.stderr)
        return False

    print("Login successful.", file=sys.stderr)
    return True


def run(
    spot_id: str,
    output_dir: str,
    model: str,
    cdp_url: str,
    username: str | None = None,
    password: str | None = None,
    viewport_width: int = 1200,
    viewport_height: int = 900,
    calc_3ft: bool = False,
) -> dict:
    """Scrape wind forecast and tide data for a spot. Returns result dict."""
    url = f"https://wx.ikitesurf.com/spot/{spot_id}"
    os.makedirs(output_dir, exist_ok=True)

    forecast_path = os.path.join(output_dir, f"forecast_{spot_id}.png")
    tides_path = os.path.join(output_dir, f"tides_{spot_id}.png")
    data_path = os.path.join(output_dir, f"data_{spot_id}.json")

    model_name = resolve_model_name(model)
    needs_login = model_name in PREMIUM_MODELS

    with sync_playwright() as p:
        connect_url = cdp_url if cdp_url.startswith("http") else f"http://{cdp_url}"
        browser = p.chromium.connect_over_cdp(connect_url)
        context = browser.contexts[0] if browser.contexts else browser.new_context(
            viewport={"width": viewport_width, "height": viewport_height},
        )
        page = context.new_page()
        if _PAGE_SCRIPTS_JS:
            page.add_init_script(_PAGE_SCRIPTS_JS)

        cookies_dir = os.path.join(os.path.expanduser("~"), ".config", "windspot")
        os.makedirs(cookies_dir, mode=0o700, exist_ok=True)
        cookies_path = os.path.join(cookies_dir, "cookies.json")

        def save_cookies() -> None:
            data = json.dumps(context.cookies(), indent=2)
            fd = os.open(cookies_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w") as f:
                f.write(data)
            print(f"Cookies saved to {cookies_path}", file=sys.stderr)

        def load_cookies() -> bool:
            if os.path.exists(cookies_path):
                with open(cookies_path) as f:
                    context.add_cookies(json.load(f))
                return True
            return False

        def try_login() -> bool:
            if not username or not password:
                return False
            success = login_ikitesurf(page, username, password)
            if success:
                save_cookies()
            return success

        had_cookies = False
        if username or password:
            had_cookies = load_cookies()

        if needs_login and not had_cookies and username and password:
            print(f"Premium model '{model_name}' requested. Logging in...", file=sys.stderr)
            try_login()

        page.set_viewport_size({"width": viewport_width, "height": viewport_height})
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)

        error = page.evaluate("() => PageScripts.checkPageError()")
        if error == "401":
            if username and password:
                print("Session expired. Attempting re-login...", file=sys.stderr)
                if try_login():
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    time.sleep(3)
                    error = page.evaluate("() => PageScripts.checkPageError()")
            if error:
                print(f"Error: iKitesurf returned {error}.", file=sys.stderr)
                page.close()
                sys.exit(1)

        try:
            page.wait_for_function(
                "() => [...document.querySelectorAll('h2')].some(h => h.textContent.includes('Forecast Table'))",
                timeout=20000,
            )
        except Exception:
            pass

        page.evaluate(f"() => PageScripts.scrollToSections({json.dumps(['Forecast Table', 'Nearby Tides'])})")
        time.sleep(5)

        spot_name = page.evaluate("() => PageScripts.getSpotName()")

        page.evaluate("() => PageScripts.scrollToSection('Forecast Table')")
        time.sleep(1)

        def click_model(name: str) -> bool:
            return page.evaluate(f"() => PageScripts.clickModel('{name}')")

        def get_active_model() -> str | None:
            return page.evaluate("() => PageScripts.getActiveModel()")

        def has_model_button(name: str) -> bool:
            return bool(page.evaluate(f"() => PageScripts.hasModelButton('{name}')"))

        click_model(model_name)
        time.sleep(2)

        active = get_active_model()
        model_switched = bool(active and model_name.split()[0] in active)

        if needs_login and not model_switched and username and password:
            # Hard checks before re-login: only login if clearly logged out, no cookies,
            # or the requested premium model button is not present at all.
            likely_logged_out = page.evaluate("() => PageScripts.isLikelyLoggedOut()")
            has_requested_model = has_model_button(model_name)
            should_relogin = (not had_cookies) or bool(likely_logged_out) or (not has_requested_model)

            if should_relogin:
                print(
                    f"Model '{model_name}' did not activate. "
                    f"had_cookies={had_cookies}, likely_logged_out={bool(likely_logged_out)}, "
                    f"has_model_button={has_requested_model}. Attempting login and retry...",
                    file=sys.stderr,
                )
                if try_login():
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    time.sleep(5)
                    page.evaluate("() => PageScripts.scrollToSection('Forecast Table')")
                    time.sleep(3)
                    click_model(model_name)
                    time.sleep(2)
                    active = get_active_model()
                    model_switched = bool(active and model_name.split()[0] in active)
                    if not model_switched:
                        print(f"Warning: '{model_name}' not available after login (subscription/access issue?). Falling back to BLEND.", file=sys.stderr)
                        model_name = "BLEND"
                        click_model(model_name)
                        time.sleep(2)
                else:
                    print("Warning: Login failed. Falling back to BLEND.", file=sys.stderr)
                    model_name = "BLEND"
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    time.sleep(5)
                    page.evaluate("() => PageScripts.scrollToSection('Forecast Table')")
                    time.sleep(3)
                    click_model(model_name)
                    time.sleep(2)
            else:
                print("Model activation check failed, but session appears logged in; not forcing re-login.", file=sys.stderr)

        page.evaluate("() => PageScripts.scrollToSection('Forecast Table')")
        time.sleep(0.5)
        page.screenshot(path=forecast_path, full_page=False)

        # Nearby Tides content can lazy-load; scroll there before extracting.
        page.evaluate("() => PageScripts.scrollToSection('Nearby Tides')")
        time.sleep(2)
        tide_data = page.evaluate("() => PageScripts.extractTideData()")
        page.screenshot(path=tides_path, full_page=False)

        tide_list = tide_data.get("tides", []) if tide_data else []
        crossings = calc_3ft_crossings(tide_list) if (calc_3ft and tide_list) else []
        crossings_5ft = calc_crossings_at(tide_list, 5.0) if (calc_3ft and tide_list) else []
        schedule = build_tide_schedule(tide_list, crossings, crossings_5ft) if (calc_3ft and tide_list) else []

        result = {
            "spot_id": spot_id,
            "spot_name": spot_name,
            "url": url,
            "model": model_name,
            "forecast_screenshot": forecast_path,
            "tides_screenshot": tides_path,
            "tide_station": tide_data.get("station", "") if tide_data else "",
            "tide_date": tide_data.get("date", "") if tide_data else "",
            "tides": tide_list,
            "crossings_3ft": crossings,
            "crossings_5ft": crossings_5ft,
            "tide_schedule": schedule,
            "timestamp": datetime.now().isoformat(),
        }

        with open(data_path, "w") as f:
            json.dump(result, f, indent=2)

        page.close()

    return result
