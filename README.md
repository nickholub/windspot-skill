# windspot-skill

OpenClaw / Claude Code skill for generating iKitesurf wind and tide forecast summaries.

Captures screenshots of the Forecast Table and Nearby Tides sections, extracts tide schedule, calculates 3ft crossing times, and sends results via Telegram.

## Install

### 1. Clone the repo

```bash
git clone https://github.com/nickholub/windspot-skill ~/projects/windspot-skill
```

### 2. Install Python dependency

```bash
python3.13 -m pip install playwright
python3.13 -m playwright install chromium
```

### 3. Symlink into OpenClaw skills directory

```bash
ln -s ~/projects/windspot-skill ~/.openclaw/workspace/skills/windspot
```

Restart OpenClaw — the skill is detected automatically.
```bash
openclaw gateway restart
```

## Authentication

Premium forecast models (Beta-WRF, iK-WRF, etc.) require a paid iKitesurf subscription. Store credentials in macOS Keychain:

```bash
security add-generic-password -s "ikitesurf" -a "your@email.com" -w "yourpassword" -U
```

The skill reads these automatically. After first login, session cookies are cached at `~/.config/windspot/cookies.json`.

## Usage

Trigger by mentioning a spot name, ID, or iKitesurf URL in your OpenClaw conversation:

```
/windspot 3rd Ave Channel
/windspot 1374
/windspot https://wx.ikitesurf.com/spot/1374
```

## Models

| Model | Flag | Login Required |
|-------|------|----------------|
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

## CLI reference

The `windspot/` package can also be run directly:

```bash
PYTHONPATH=. python3.13 -m windspot.cli 427 --3ft --json --model "Beta-WRF 1km" --output-dir /tmp/windspot
```

| Flag | Description |
|------|-------------|
| `--model`, `-m` | Forecast model (default: `blend`) |
| `--3ft` | Calculate 3ft tide crossing times |
| `--json` | Output structured JSON to stdout |
| `--output-dir`, `-o` | Directory for screenshots and JSON (default: `/tmp/windspot`) |
| `--no-login` | Skip authentication (anonymous mode) |
| `--headless` | Run Chrome in headless mode |
| `--cdp-url` | Connect to an existing Chrome instance via CDP |

## JSON output

```json
{
  "spot_id": "427",
  "spot_name": "Half Moon Bay",
  "model": "Beta-WRF 1km",
  "forecast_screenshot": "/tmp/windspot/forecast_427.png",
  "tides_screenshot": "/tmp/windspot/tides_427.png",
  "tide_station": "Princeton, Half Moon Bay",
  "tide_date": "February 16, 2026",
  "tides": [
    {"type": "Low", "time": "3:30 AM", "height": 2.63},
    {"type": "High", "time": "9:14 AM", "height": 5.89}
  ],
  "crossings_3ft": [
    {"time": "12:24 PM", "direction": "falling", "from": "5.89", "to": "-0.43"}
  ],
  "timestamp": "2026-02-16T09:35:56"
}
```

## Source

| File | Description |
|------|-------------|
| `windspot/cli.py` | Entry point |
| `windspot/scraper.py` | Playwright browser automation |
| `windspot/browser.py` | Chrome/CDP process management |
| `windspot/auth.py` | macOS Keychain credential lookup |
| `windspot/models.py` | Model name mapping, spot ID parsing |
| `windspot/tides.py` | 3ft crossing interpolation |
| `windspot/page_scripts.js` | JS injected into browser page |

## Requirements

- macOS
- Python 3.10+
- Google Chrome
- `playwright` pip package + Chromium
