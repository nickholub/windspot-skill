"""Forecast model name mapping and spot ID parsing."""

import re
import sys

MODEL_BUTTONS: dict[str, str] = {
    "beta-wrf": "Beta-WRF 1km",
    "beta-wrf-1km": "Beta-WRF 1km",
    "ik-wrf": "iK-WRF 1km",
    "ik-wrf-1km": "iK-WRF 1km",
    "ik-trrm": "iK-TRRM",
    "ik-hrrr": "iK-HRRR",
    "blend": "BLEND",
    "nam-3km": "NAM 3km",
    "nam-12km": "NAM 12km",
    "gfs": "GFS",
    "icon": "ICON",
}

PREMIUM_MODELS: set[str] = {"Beta-WRF 1km", "iK-WRF 1km", "iK-TRRM", "iK-HRRR"}


def parse_spot_id(spot_input: str) -> str:
    """Extract spot ID from a URL or raw numeric ID."""
    m = re.search(r"spot/(\d+)", spot_input)
    if m:
        return m.group(1)
    if spot_input.isdigit():
        return spot_input
    print(f"Error: Cannot parse spot ID from '{spot_input}'", file=sys.stderr)
    sys.exit(1)


def resolve_model_name(model: str) -> str:
    """Resolve a model key or alias to its display name."""
    return MODEL_BUTTONS.get(model.lower(), model)
