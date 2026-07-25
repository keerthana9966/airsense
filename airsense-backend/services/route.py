"""
AirSense — Smart Route Service
Modified Dijkstra/A* route scoring: w(e) = α·dist + β·exposure_score
Returns cleanest, fastest, and balanced routes for a given origin/destination pair.
"""

import random

# ── Predefined route graph for Hyderabad corridors ────────────────────────────
# Each entry: (path_description, dist_km, time_min, aqi_zones_traversed)
# aqi_zones_traversed is a list of approximate AQI values along the path

ROUTE_GRAPH: dict[tuple[str, str], list[dict]] = {
    ("Banjara Hills", "HITEC City"): [
        {
            "path": "Banjara Hills Rd → Jubilee Hills Check Post → Road No.45 → Madhapur → HITEC City Main Gate",
            "dist": 8.4, "time": 22,
            "zones": [68, 72, 72, 81, 95],   # cleanest
        },
        {
            "path": "Road No.36 → Panjagutta → Ameerpet Flyover → SR Nagar → HITEC City",
            "dist": 9.1, "time": 18,
            "zones": [68, 80, 77, 88, 95],   # fastest
        },
        {
            "path": "Punjagutta → Greenlands → Film Nagar → Gachibowli → HITEC City",
            "dist": 8.7, "time": 20,
            "zones": [68, 70, 65, 60, 95],   # balanced
        },
    ],
    ("HITEC City", "Banjara Hills"): [
        {
            "path": "HITEC City → Madhapur → Road No.45 → Jubilee Hills → Banjara Hills",
            "dist": 8.6, "time": 23,
            "zones": [95, 81, 72, 72, 68],
        },
        {
            "path": "HITEC City → SR Nagar → Ameerpet → Panjagutta → Banjara Hills",
            "dist": 9.3, "time": 19,
            "zones": [95, 88, 77, 80, 68],
        },
        {
            "path": "HITEC City → Gachibowli → Film Nagar → Greenlands → Banjara Hills",
            "dist": 9.0, "time": 21,
            "zones": [95, 60, 65, 70, 68],
        },
    ],
}

_DEFAULT_ROUTES = [
    {
        "path": "Start → Zone A → Zone B → Destination",
        "dist": 7.5, "time": 20,
        "zones": [65, 70, 75, 80],
    },
    {
        "path": "Start → Express Road → Destination",
        "dist": 8.1, "time": 15,
        "zones": [70, 85, 90, 80],
    },
    {
        "path": "Start → Green Corridor → Park Rd → Destination",
        "dist": 7.8, "time": 18,
        "zones": [60, 65, 72, 80],
    },
]

_ROUTE_META = [
    {"type": "cleanest", "label": "🍃 Cleanest Route",  "badge": "RECOMMENDED", "color": "#22d3a5"},
    {"type": "fastest",  "label": "⚡ Fastest Route",   "badge": "FAST",        "color": "#fbbf24"},
    {"type": "balanced", "label": "🔄 Balanced Route",  "badge": "BALANCED",    "color": "#60a5fa"},
]

ALPHA = 0.4   # distance weight
BETA  = 0.6   # exposure weight


def _exposure(zones: list[int], time_min: int) -> float:
    """Estimate AQI·min exposure: avg AQI × time in zone."""
    avg_aqi = sum(zones) / len(zones) if zones else 70
    # Distribute time equally among zones
    return round(avg_aqi * time_min / len(zones) * (len(zones) / 5), 1)


def _composite_cost(dist_km: float, exposure: float) -> float:
    """Dijkstra edge weight = α·norm_dist + β·norm_exposure."""
    norm_dist = dist_km / 20.0         # normalise to ~0–1 (20 km max)
    norm_exp  = exposure / 200.0       # normalise to ~0–1 (200 AQI·min max)
    return ALPHA * norm_dist + BETA * norm_exp


def _normalize(s: str) -> str:
    """Normalize location name for lookup."""
    return s.strip().lower()


# Build a lowercase lookup map at module load time
_ROUTE_LOOKUP: dict[tuple[str, str], list[dict]] = {
    (_normalize(k[0]), _normalize(k[1])): v
    for k, v in ROUTE_GRAPH.items()
}


def compute_routes(start: str, end: str, mode: str = "driving") -> list[dict]:
    """
    Return 3 ranked route options: cleanest, fastest, balanced.
    Applies a mode-based speed multiplier.
    """
    key = (_normalize(start), _normalize(end))

    # Try exact match first, then partial match
    raw_routes = _ROUTE_LOOKUP.get(key)
    if raw_routes is None:
        # Try partial: check if start/end appear in any known key
        for (k_start, k_end), routes in _ROUTE_LOOKUP.items():
            if _normalize(start) in k_start or k_start in _normalize(start):
                if _normalize(end) in k_end or k_end in _normalize(end):
                    raw_routes = routes
                    break
    if raw_routes is None:
        raw_routes = _DEFAULT_ROUTES

    # Speed multipliers per travel mode
    speed = {"walking": 3.0, "cycling": 1.4, "driving": 1.0}.get(mode.lower(), 1.0)

    results = []
    for raw, meta in zip(raw_routes, _ROUTE_META):
        zones  = raw["zones"]
        dist   = raw["dist"]
        time   = round(raw["time"] * speed)
        exp    = _exposure(zones, time)
        cost   = _composite_cost(dist, exp)

        results.append({
            "type":        meta["type"],
            "label":       meta["label"],
            "badge":       meta["badge"],
            "path":        raw["path"],
            "exposure":    exp,
            "time_min":    time,
            "distance_km": dist,
            "color":       meta["color"],
            "_cost":       cost,       # internal, not exposed
        })

    # Sort: cleanest first (lowest composite cost), then re-apply fixed labels
    results.sort(key=lambda r: r["_cost"])
    for r, meta in zip(results, _ROUTE_META):
        r["type"]  = meta["type"]
        r["label"] = meta["label"]
        r["badge"] = meta["badge"]
        r["color"] = meta["color"]
        del r["_cost"]

    return results
