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

## Authentication

Premium forecast models (Beta-WRF, iK-WRF, etc.) require a paid iKitesurf subscription. Store credentials in macOS Keychain:

```bash
security add-generic-password -s "ikitesurf" -a "your@email.com" -w "yourpassword" -U
```

The skill reads these automatically. After first login, session cookies are cached at `~/.config/windspot/cookies.json`.

## Usage

Trigger by mentioning a spot name, ID, or iKitesurf URL in your OpenClaw conversation:

```
windspot Crissy Field
windspot 427
windspot https://wx.ikitesurf.com/spot/1374
```

## Requirements

- macOS
- Python 3.10+
- Google Chrome
- `playwright` pip package + Chromium (`python3.13 -m playwright install chromium`)
