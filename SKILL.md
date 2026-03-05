---
name: windspot
description: Generate and send wind spot forecast summary from iKitesurf. Triggers when message starts with "windspot" followed by a spot name, ID, or URL (e.g. "windspot Crissy Field", "windspot 427", "windspot wx.ikitesurf.com/spot/408"). Also triggers on iKitesurf spot URLs (wx.ikitesurf.com/spot/*). Uses WindSpotExtract CLI tool to capture screenshots. Sends results to Telegram.
---

# Wind Spot Summary

Generate a wind+tide forecast summary for any iKitesurf spot and send via Telegram.

## Trigger Detection

Activate when the user provides any of:
- A URL like `https://wx.ikitesurf.com/spot/427`
- A spot ID (e.g., "spot 427", "ikitesurf 427")
- A spot name (e.g., "Half Moon Bay wind", "HMB forecast", "Cowells")

For spot names, use known mappings:
- Half Moon Bay / HMB → 427
- Cowells → 147
- 3rd Avenue → 149
- 3rd Ave Beach / 3rd Ave Beach Foster City → 423
- Waddell Creek → 148
- Ocean Beach → 152
- Coyote Point → 408
- 3rd Ave Channel → 1374
- Crissy Field / Anita Rock → 411

## Tool: WindSpotExtract

The `windspot/` package is bundled in this skill's project directory. No installation needed — run it directly via `PYTHONPATH`.

### Prerequisite

`playwright` Python package and Chromium must be available (one-time setup):

```bash
python3.13 -m pip install playwright
python3.13 -m playwright install chromium
```

### Command

Set `SKILL_DIR` to the absolute path of this skill's project directory (where `SKILL.md` lives), then:

```bash
PYTHONPATH="$SKILL_DIR" python3.13 -m windspot.cli {spot_id} --3ft --json --model "Beta-WRF 1km" --output-dir "/tmp/windspot"
```

**Flags:**
- `--3ft` — calculate 3ft tide crossing times (always use)
- `--json` — structured JSON output to stdout
- `--model "Beta-WRF 1km"` — use Beta-WRF forecast model (always use when logged in)
- `--output-dir "/tmp/windspot"` — output directory for screenshots and JSON
- `--no-login` — only add if user explicitly asks for no login (also drop `--model` since Beta-WRF requires login)

**Output dir:** `/tmp/windspot/` (or any writable path you choose)

### Output Files
- `/tmp/windspot/forecast_{spot_id}.png` — Forecast table screenshot
- `/tmp/windspot/tides_{spot_id}.png` — Tides screenshot

### JSON Output Structure
```json
{
  "spot_id": "427",
  "spot_name": "Half Moon Bay",
  "model": "BLEND",
  "forecast_screenshot": ".../forecast_427.png",
  "tides_screenshot": ".../tides_427.png",
  "tide_station": "Princeton, Half Moon Bay",
  "tide_date": "February 16, 2026",
  "tides": [
    {"type": "Low", "time": "3:30 AM", "height": 2.63},
    {"type": "High", "time": "9:14 AM", "height": 5.89}
  ],
  "timestamp": "2026-02-16T09:35:56"
}
```

When `--3ft` is included, the JSON also contains:
```json
"crossings_3ft": [
  {"time": "12:24 PM", "direction": "falling", "from": "5.89", "to": "-0.43"}
]
```

## Workflow

### 1. Run WindSpotExtract

`SKILL_DIR` = absolute path to this skill's project directory.

```bash
PYTHONPATH="$SKILL_DIR" python3.13 -m windspot.cli {spot_id} --3ft --json --model "Beta-WRF 1km" --output-dir "/tmp/windspot"
```

If `--no-login` is used, omit `--model` (Beta-WRF requires login):
```bash
PYTHONPATH="$SKILL_DIR" python3.13 -m windspot.cli {spot_id} --3ft --json --no-login --output-dir "/tmp/windspot"
```

Set timeout to 60 seconds.

### 3. Send results to user
Send three messages to the requesting user (or configured destination):

1. **Forecast screenshot** with caption:
   `🏄 {Spot Name} — Forecast`
   Use file: `{output_dir}/forecast_{spot_id}.png` (value of `forecast_screenshot` in JSON output)

2. **Tides screenshot** with caption:
   `🌊 {Spot Name} Tides — {Date}`
   Use file: `{output_dir}/tides_{spot_id}.png` (value of `tides_screenshot` in JSON output)

3. **Tide above 3ft summary** — Calculate time windows when the tide is above 3ft using crossing data:
   ```
   🌊 Tide above 3ft windows:
   • {start_time} – {end_time} ({duration})
   ```
   Use `crossings_3ft`: a `rising` crossing starts an above-3ft window, and a `falling` crossing ends it. If the first tide is already above 3ft, start at midnight. If the last crossing is `rising`, extend to midnight.

## Notes
- No browser relay needed — the script launches Chrome directly via CDP
- Login via macOS Keychain (`ikitesurf`) is used by default; falls back to anonymous
- `--no-login` only if explicitly requested
- Keep `--3ft` enabled to generate crossing data
- Cookies are cached at `~/.config/windspot/cookies.json`
- Timeout: 60 seconds (typical run time: ~20–30s)
- Output paths are returned in JSON as `forecast_screenshot` and `tides_screenshot` — always use those values rather than constructing paths manually
- No installation required — run via `PYTHONPATH="$SKILL_DIR" python3.13 -m windspot.cli`
- Only external dependency is the `playwright` pip package + Chromium

---

## Source

The CLI source lives in `windspot/` within this skill's project directory.

**Prerequisites:** Python 3.10+ (code uses `X | None` union syntax), Google Chrome, `playwright` pip package.

### Files

| File | Description |
|------|-------------|
| `windspot/cli.py` | Entry point (`main()`) |
| `windspot/scraper.py` | Playwright browser automation |
| `windspot/browser.py` | Chrome/CDP process management |
| `windspot/auth.py` | macOS Keychain credential lookup |
| `windspot/models.py` | Model name mapping, spot ID parsing |
| `windspot/tides.py` | 3ft crossing interpolation |
| `windspot/page_scripts.js` | JS injected into browser page |
| `pyproject.toml` | Package definition |

---
## Reference: README

# WindSpotExtract

CLI tool to extract iKitesurf wind forecast and tide data. Takes screenshots of the Forecast Table and Nearby Tides sections, extracts tide schedule, and calculates 3ft tide crossing times.

## Install

```bash
python3.13 -m pip install playwright
python3.13 -m playwright install chromium
```

## Quick Start

```bash
# BLEND forecast (no login needed)
windspot 427

# With real Chrome (recommended, avoids headless detection)
windspot 427

# Premium model
windspot 427 --model beta-wrf
```

## Models

| Model | Flag | Login Required |
|-------|------|---------------|
| BLEND | `blend` (default) | No |
| NAM 3km | `nam-3km` | No |
| NAM 12km | `nam-12km` | No |
| GFS | `gfs` | No |
| ICON | `icon` | No |
| WW3 | `ww3` | No |
| Beta-WRF 1km | `beta-wrf` | Yes (paid) |
| iK-WRF 1km | `ik-wrf` | Yes (paid) |
| iK-TRRM | `ik-trrm` | Yes (paid) |
| iK-HRRR | `ik-hrrr` | Yes (paid) |

## Authentication

Store credentials in macOS Keychain:

```bash
security add-generic-password -s "ikitesurf" -a "your@email.com" -w "yourpassword" -U
```

Credentials are resolved in order: macOS Keychain → env vars (`IKITESURF_USERNAME`, `IKITESURF_PASSWORD`) → CLI flags (`-u`, `-p`).

After login, cookies are saved to `~/.config/windspot/cookies.json` and reused on subsequent runs.

## Spot IDs

| Spot | ID |
|------|----|
| Half Moon Bay | 427 |
| Coyote Point | 408 |
| Cowells | 147 |
| 3rd Avenue | 149 |
| Waddell Creek | 148 |
| Ocean Beach | 152 |
| 3rd Ave Channel | 1374 |
| Crissy Field / Anita Rock | 411 |
