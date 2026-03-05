"""Tide crossing calculations."""

from datetime import datetime

_TARGET_FT = 3.0


def calc_3ft_crossings(tides: list[dict]) -> list[dict]:
    """Return times when the tide crosses 3 ft, interpolated between tide entries."""
    crossings = []

    for i in range(len(tides) - 1):
        t1, t2 = tides[i], tides[i + 1]
        h1, h2 = t1["height"], t2["height"]

        if (h1 - _TARGET_FT) * (h2 - _TARGET_FT) < 0:
            frac = abs(h1 - _TARGET_FT) / abs(h2 - h1)

            dt1 = datetime.strptime(t1["time"], "%I:%M %p")
            dt2 = datetime.strptime(t2["time"], "%I:%M %p")
            mins1 = dt1.hour * 60 + dt1.minute
            mins2 = dt2.hour * 60 + dt2.minute
            if mins2 < mins1:
                mins2 += 24 * 60

            cross_mins = (mins1 + frac * (mins2 - mins1)) % (24 * 60)
            cross_dt = datetime(2000, 1, 1, int(cross_mins // 60), int(cross_mins % 60))
            crossings.append({
                "time": cross_dt.strftime("%I:%M %p").lstrip("0"),
                "direction": "falling" if h1 > h2 else "rising",
                "from": f"{h1:.2f}",
                "to": f"{h2:.2f}",
            })
        elif abs(h1 - _TARGET_FT) < 0.1:
            prev_h = tides[i - 1]["height"] if i > 0 else h2
            crossings.append({
                "time": t1["time"],
                "direction": "falling" if prev_h > h1 else "rising",
                "from": f"{h1:.2f}",
                "to": f"{h2:.2f}",
            })

    return crossings
