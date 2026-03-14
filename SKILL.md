---
name: windspot
description: Generate and send wind spot forecast summary from iKitesurf. Triggers when message starts with "windspot" or "/windspot", optionally followed by a spot name, ID, or URL (e.g. "windspot Crissy Field", "/windspot 427", "windspot wx.ikitesurf.com/spot/408"). Also triggers on iKitesurf spot URLs (wx.ikitesurf.com/spot/*). If no spot is specified, defaults to 3rd Ave Channel (ID 1374). Use the local windspot skill CLI module (python -m windspot.cli), not legacy external scripts.
---

# Wind Spot Summary

Generate a wind+tide forecast summary for any iKitesurf spot and send via Telegram.

## Trigger Detection

Activate when the user sends "windspot" or "/windspot", with or without a spot argument. If no spot is provided, default to **3rd Ave Channel** (ID 1374).

Spot name mappings:
- Half Moon Bay / HMB → 427
- Cowells → 147
- 3rd Avenue → 149
- 3rd Ave Beach / 3rd Ave Beach Foster City → 423
- Waddell Creek → 148
- Ocean Beach → 152
- Coyote Point → 408
- 3rd Ave Channel → 1374
- Crissy Field / Anita Rock → 411

## Workflow

### 1. Run CLI

`SKILL_DIR` = absolute path to this skill's project directory.

```bash
PYTHONPATH="$SKILL_DIR" python3.13 -m windspot.cli {spot_id} --3ft --json --model "Beta-WRF 1km" --output-dir "/tmp/windspot"
```

Without login (drop `--model` too):
```bash
PYTHONPATH="$SKILL_DIR" python3.13 -m windspot.cli {spot_id} --3ft --json --no-login --output-dir "/tmp/windspot"
```

Timeout: 60 seconds. Use `forecast_screenshot` and `tides_screenshot` from JSON output for file paths.

### 2. Send results

Send three messages:

1. **Forecast screenshot** — `forecast_screenshot` from JSON, caption: `🏄 {spot_name} — Forecast`
2. **Tides screenshot** — `tides_screenshot` from JSON, caption: `🌊 {spot_name} Tides — {tide_date}`
3. **Tide schedule + above-3ft windows** — two sections:

   **Tide schedule** from `tide_schedule` (sorted by time, all key tide events):
   ```
   🌊 Tide Schedule:
   • {time} -> {height}ft ({label})
   ```
   Formatting rule: if `{label}` is `low` or `high`, render the entire schedule line in **Telegram HTML bold** using `<b>...</b>` (do not use markdown `**...**`, as message-tool sends may show raw asterisks).
   Labels: `low`, `high`, `3ft rising`, `3ft falling`, `5ft rising`, `5ft falling`

   **Tide above 3ft windows** from `crossings_3ft`: a `rising` crossing starts a window, `falling` ends it. If first tide is already above 3ft, start at midnight. If last crossing is `rising`, extend to midnight.
   ```
   🎯 Tide above 3ft:
   • {start_time} – {end_time} ({duration})
   ```
