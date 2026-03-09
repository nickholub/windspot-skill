"""Tide crossing calculations."""

from datetime import datetime


def _time_to_mins(time_str: str) -> int:
    """Convert time string like '6:30 AM' to minutes since midnight."""
    dt = datetime.strptime(time_str.strip(), "%I:%M %p")
    return dt.hour * 60 + dt.minute


def _mins_to_time(mins: float) -> str:
    mins = int(mins) % (24 * 60)
    dt = datetime(2000, 1, 1, mins // 60, mins % 60)
    return dt.strftime("%I:%M %p").lstrip("0")


def calc_crossings_at(tides: list[dict], target_ft: float) -> list[dict]:
    """Return times when the tide crosses target_ft, interpolated between tide entries."""
    crossings = []

    for i in range(len(tides) - 1):
        t1, t2 = tides[i], tides[i + 1]
        h1, h2 = t1["height"], t2["height"]

        if (h1 - target_ft) * (h2 - target_ft) < 0:
            frac = abs(h1 - target_ft) / abs(h2 - h1)

            mins1 = _time_to_mins(t1["time"])
            mins2 = _time_to_mins(t2["time"])
            if mins2 < mins1:
                mins2 += 24 * 60

            cross_mins = (mins1 + frac * (mins2 - mins1)) % (24 * 60)
            crossings.append({
                "time": _mins_to_time(cross_mins),
                "direction": "falling" if h1 > h2 else "rising",
                "from": f"{h1:.2f}",
                "to": f"{h2:.2f}",
            })
        elif abs(h1 - target_ft) < 0.1:
            prev_h = tides[i - 1]["height"] if i > 0 else h2
            crossings.append({
                "time": t1["time"],
                "direction": "falling" if prev_h > h1 else "rising",
                "from": f"{h1:.2f}",
                "to": f"{h2:.2f}",
            })

    return crossings


def calc_3ft_crossings(tides: list[dict]) -> list[dict]:
    return calc_crossings_at(tides, 3.0)


def build_tide_schedule(
    tides: list[dict],
    crossings_3ft: list[dict],
    crossings_5ft: list[dict],
) -> list[dict]:
    """Build a sorted schedule of all tide events (low, 3ft, 5ft, high)."""
    events = []

    for t in tides:
        events.append({
            "time": t["time"],
            "mins": _time_to_mins(t["time"]),
            "label": t["type"].lower(),  # "low" or "high"
            "height": t["height"],
        })

    for c in crossings_3ft:
        events.append({
            "time": c["time"],
            "mins": _time_to_mins(c["time"]),
            "label": f"3ft {c['direction']}",
            "height": 3.0,
        })

    for c in crossings_5ft:
        events.append({
            "time": c["time"],
            "mins": _time_to_mins(c["time"]),
            "label": f"5ft {c['direction']}",
            "height": 5.0,
        })

    events.sort(key=lambda e: e["mins"])

    return [{"time": e["time"], "label": e["label"], "height": e["height"]} for e in events]
